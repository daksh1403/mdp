/*
 * ============================================================
 *  ESP32-CAM — Autonomous Painting System Controller (FIXED)
 * ============================================================
 *
 *  FIXES APPLIED:
 *    1. Changed relay to ACTIVE-LOW (most common relay modules)
 *    2. Initialize relay to OFF state on boot
 *    3. Added startup delay to ensure relay is OFF before WiFi
 *    4. Better spray timing and acknowledgment
 *
 *  Dual-port HTTP server for autonomous wall painting system:
 *    Port 80 → Control: /ping /status /spray /spray_start
 *                       /spray_stop /capture_frame
 *    Port 81 → Stream:  /stream (MJPEG)
 *
 *  WiFi AP:   SSID = PaintSystem, Password = paintdrone123
 *  AP IP:     192.168.4.1
 *  Relay:     GPIO 13 (ACTIVE-LOW - relay turns ON when pin is LOW)
 *
 *  Board:     AI Thinker ESP32-CAM
 *  Partition: Huge APP (3MB No OTA/1MB SPIFFS)
 *
 *  FLASHING STEPS:
 *    1. Connect ESP32-S3 as programmer (see esp32s3.ino)
 *    2. Connect IO0 to GND on ESP32-CAM
 *    3. Upload this sketch
 *    4. Remove IO0-GND jumper
 *    5. Press RESET on ESP32-CAM
 *    6. "PaintSystem" WiFi should appear
 * ============================================================
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>

// ══════════════════════════════════════════════════════════════
//  WiFi AP Configuration
// ══════════════════════════════════════════════════════════════
const char* AP_SSID     = "PaintSystem";
const char* AP_PASSWORD = "paintdrone123";

// ══════════════════════════════════════════════════════════════
//  Relay / Spray Configuration — ACTIVE LOW
// ══════════════════════════════════════════════════════════════
//  IMPORTANT: Most relay modules are ACTIVE-LOW
//  This means: 
//    - Pin HIGH = Relay OFF (pump stops)
//    - Pin LOW  = Relay ON  (pump runs)
// ══════════════════════════════════════════════════════════════
#define RELAY_PIN  13

// ACTIVE-LOW configuration (most common relay modules)
// If your relay is ACTIVE-HIGH, swap these values
#define RELAY_ON   LOW    // LOW turns relay ON (closes circuit)
#define RELAY_OFF  HIGH   // HIGH turns relay OFF (opens circuit)

// Safety watchdog: auto-shutoff after 30 seconds in continuous mode
#define WATCHDOG_TIMEOUT_MS 30000

// ══════════════════════════════════════════════════════════════
//  Relay State Variables
// ══════════════════════════════════════════════════════════════
bool          relayActive      = false;
bool          continuousMode   = false;
unsigned long relayOnTime      = 0;
unsigned long relayDuration    = 0;
unsigned long continuousStart  = 0;    // Watchdog timer for continuous mode

// ══════════════════════════════════════════════════════════════
//  AI-Thinker ESP32-CAM Pin Definitions
// ══════════════════════════════════════════════════════════════
#define PWDN_GPIO_NUM   32
#define RESET_GPIO_NUM  -1
#define XCLK_GPIO_NUM    0
#define SIOD_GPIO_NUM   26
#define SIOC_GPIO_NUM   27
#define Y9_GPIO_NUM     35
#define Y8_GPIO_NUM     34
#define Y7_GPIO_NUM     39
#define Y6_GPIO_NUM     36
#define Y5_GPIO_NUM     21
#define Y4_GPIO_NUM     19
#define Y3_GPIO_NUM     18
#define Y2_GPIO_NUM      5
#define VSYNC_GPIO_NUM  25
#define HREF_GPIO_NUM   23
#define PCLK_GPIO_NUM   22

// ══════════════════════════════════════════════════════════════
//  Dual HTTP Servers
// ══════════════════════════════════════════════════════════════
WebServer controlServer(80);
WebServer streamServer(81);

// ══════════════════════════════════════════════════════════════
//  CORS Helper
// ══════════════════════════════════════════════════════════════
void addCors(WebServer& srv) {
  srv.sendHeader("Access-Control-Allow-Origin", "*");
  srv.sendHeader("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
  srv.sendHeader("Access-Control-Allow-Headers", "Content-Type");
}

/* ============================================================
 *  setup()
 * ============================================================ */
void setup() {
  Serial.begin(115200);
  Serial.println("\n");
  Serial.println("╔══════════════════════════════════════════╗");
  Serial.println("║   ESP32-CAM Painting System (FIXED)      ║");
  Serial.println("║   VIT Chennai MDP Project                ║");
  Serial.println("║   Relay: ACTIVE-LOW Configuration        ║");
  Serial.println("╚══════════════════════════════════════════╝");

  // ═══════════════════════════════════════════════════════════
  // CRITICAL: Initialize relay pin FIRST and set to OFF
  // This ensures pump doesn't run during boot
  // ═══════════════════════════════════════════════════════════
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_OFF);  // Ensure relay is OFF
  delay(100);                          // Give relay time to settle
  digitalWrite(RELAY_PIN, RELAY_OFF);  // Double-ensure relay is OFF
  
  Serial.println("[INIT] Relay pin configured (GPIO 13) - ACTIVE LOW");
  Serial.println("[INIT] Relay state: OFF (pump should be stopped)");

  // Wait a moment to ensure relay is definitely OFF before continuing
  delay(500);

  // Initialize camera
  setupCamera();

  // Start WiFi Access Point
  WiFi.mode(WIFI_AP);
  WiFi.softAP(AP_SSID, AP_PASSWORD);
  delay(500);
  
  // Re-ensure relay is OFF after WiFi init (just to be safe)
  digitalWrite(RELAY_PIN, RELAY_OFF);
  
  Serial.print("[WIFI] AP Started: ");
  Serial.println(AP_SSID);
  Serial.print("[WIFI] AP IP: ");
  Serial.println(WiFi.softAPIP());
  Serial.print("[WIFI] Password: ");
  Serial.println(AP_PASSWORD);

  // Setup control server routes (port 80)
  controlServer.on("/ping",          HTTP_GET,     handlePing);
  controlServer.on("/status",        HTTP_GET,     handleStatus);
  controlServer.on("/spray",         HTTP_POST,    handleSpray);
  controlServer.on("/spray_start",   HTTP_POST,    handleSprayStart);
  controlServer.on("/spray_stop",    HTTP_POST,    handleSprayStop);
  controlServer.on("/capture_frame", HTTP_GET,     handleCaptureFrame);
  
  // Force stop endpoint (for emergency)
  controlServer.on("/force_stop",    HTTP_POST,    handleForceStop);
  controlServer.on("/force_stop",    HTTP_GET,     handleForceStop);

  // CORS preflight handlers
  controlServer.on("/spray",       HTTP_OPTIONS, handleOptions);
  controlServer.on("/spray_start", HTTP_OPTIONS, handleOptions);
  controlServer.on("/spray_stop",  HTTP_OPTIONS, handleOptions);
  controlServer.on("/ping",        HTTP_OPTIONS, handleOptions);
  controlServer.on("/status",      HTTP_OPTIONS, handleOptions);

  controlServer.begin();
  Serial.println("[HTTP] Control server started on port 80");

  // Setup stream server (port 81)
  streamServer.on("/stream", HTTP_GET, handleStream);
  streamServer.begin();
  Serial.println("[HTTP] Stream server started on port 81");

  // Final relay check
  digitalWrite(RELAY_PIN, RELAY_OFF);
  
  Serial.println("\n[READY] ESP32-CAM is ready!");
  Serial.println("        Connect to WiFi: PaintSystem");
  Serial.println("        Test: http://192.168.4.1/ping");
  Serial.println("        Stream: http://192.168.4.1:81/stream");
  Serial.println("\n[RELAY] Configuration: ACTIVE-LOW");
  Serial.println("        Pin HIGH = Relay OFF (pump stops)");
  Serial.println("        Pin LOW  = Relay ON  (pump runs)\n");
}

/* ============================================================
 *  loop()
 * ============================================================ */
void loop() {
  controlServer.handleClient();
  streamServer.handleClient();

  // Non-blocking relay timer for precision mode
  if (relayActive && !continuousMode) {
    if (millis() - relayOnTime >= relayDuration) {
      digitalWrite(RELAY_PIN, RELAY_OFF);
      relayActive = false;
      Serial.println("[SPRAY] Relay OFF (precision spray complete)");
    }
  }

  // Watchdog timer for continuous mode (safety feature)
  if (relayActive && continuousMode) {
    if (millis() - continuousStart >= WATCHDOG_TIMEOUT_MS) {
      digitalWrite(RELAY_PIN, RELAY_OFF);
      relayActive = false;
      continuousMode = false;
      Serial.println("[SAFETY] WATCHDOG: Auto-shutoff after 30 seconds!");
    }
  }
}

/* ============================================================
 *  Camera Initialization
 * ============================================================ */
void setupCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode    = CAMERA_GRAB_LATEST;
  config.frame_size   = FRAMESIZE_VGA;    // 640x480
  config.jpeg_quality = 10;                // 0-63, lower = better
  config.fb_count     = 2;
  config.fb_location  = CAMERA_FB_IN_PSRAM;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("[ERROR] Camera init FAILED!");
    Serial.println("[ERROR] Check: IO0 not grounded, camera ribbon secure");
    delay(3000);
    ESP.restart();
  }

  // Adjust camera settings
  sensor_t* s = esp_camera_sensor_get();
  s->set_vflip(s, 1);       // Flip vertically
  s->set_hmirror(s, 1);     // Mirror horizontally
  s->set_brightness(s, 1);  // Slight brightness boost
  s->set_saturation(s, -1); // Reduce saturation for white detection

  Serial.println("[CAM] Camera initialized successfully");
}

/* ============================================================
 *  GET /ping — Health check
 * ============================================================ */
void handlePing() {
  addCors(controlServer);
  
  // Also report relay state in ping for debugging
  String relayState = relayActive ? "on" : "off";
  String response = "{\"status\":\"ok\",\"device\":\"ESP32-CAM\",\"relay\":\"" + relayState + "\",\"relay_config\":\"active-low\"}";
  
  controlServer.send(200, "application/json", response);
  Serial.println("[REQ] /ping → OK (relay: " + relayState + ")");
}

/* ============================================================
 *  GET /status — Current relay state
 * ============================================================ */
void handleStatus() {
  addCors(controlServer);
  StaticJsonDocument<256> doc;
  doc["relay"]      = relayActive ? "on" : "off";
  doc["mode"]       = continuousMode ? "continuous" : "precision";
  doc["relay_config"] = "active-low";
  doc["uptime_ms"]  = millis();
  doc["wifi_clients"] = WiFi.softAPgetStationNum();
  
  String output;
  serializeJson(doc, output);
  controlServer.send(200, "application/json", output);
  Serial.println("[REQ] /status → " + output);
}

/* ============================================================
 *  POST /spray — Precision spray for duration_ms
 *  Body: {"duration_ms": 800}
 * ============================================================ */
void handleSpray() {
  addCors(controlServer);
  
  // Reject if already spraying
  if (relayActive) {
    controlServer.send(409, "application/json",
      "{\"error\":\"spray already in progress\"}");
    Serial.println("[REQ] /spray → REJECTED (already spraying)");
    return;
  }

  // Parse duration from JSON body
  StaticJsonDocument<128> doc;
  deserializeJson(doc, controlServer.arg("plain"));
  unsigned long dur = doc["duration_ms"] | 800UL;
  dur = constrain(dur, 50, 5000);  // Limit: 50ms to 5 seconds

  Serial.printf("[SPRAY] Precision spray: %lu ms\n", dur);
  Serial.println("[SPRAY] Turning relay ON (pin LOW for active-low)");
  
  // Turn relay ON (LOW for active-low relay)
  digitalWrite(RELAY_PIN, RELAY_ON);
  relayActive    = true;
  continuousMode = false;
  relayOnTime    = millis();
  relayDuration  = dur;

  String response = "{\"sprayed\":true,\"duration_ms\":" + String(dur) + ",\"relay_config\":\"active-low\"}";
  controlServer.send(200, "application/json", response);
  
  Serial.println("[SPRAY] Response sent, relay is ON");
}

/* ============================================================
 *  POST /spray_start — Start continuous spray
 * ============================================================ */
void handleSprayStart() {
  addCors(controlServer);

  Serial.println("[SPRAY] CONTINUOUS spray START");
  Serial.println("[SPRAY] Turning relay ON (pin LOW for active-low)");
  
  digitalWrite(RELAY_PIN, RELAY_ON);  // LOW for active-low
  relayActive     = true;
  continuousMode  = true;
  continuousStart = millis();  // Start watchdog timer

  controlServer.send(200, "application/json",
    "{\"status\":\"spraying\",\"mode\":\"continuous\",\"watchdog_ms\":30000,\"relay_config\":\"active-low\"}");
}

/* ============================================================
 *  POST /spray_stop — Stop spray immediately
 * ============================================================ */
void handleSprayStop() {
  addCors(controlServer);

  Serial.println("[SPRAY] SPRAY STOP");
  Serial.println("[SPRAY] Turning relay OFF (pin HIGH for active-low)");
  
  digitalWrite(RELAY_PIN, RELAY_OFF);  // HIGH for active-low
  relayActive    = false;
  continuousMode = false;

  controlServer.send(200, "application/json",
    "{\"status\":\"stopped\",\"relay_config\":\"active-low\"}");
}

/* ============================================================
 *  POST/GET /force_stop — Emergency force stop
 * ============================================================ */
void handleForceStop() {
  addCors(controlServer);

  Serial.println("[EMERGENCY] FORCE STOP - Turning relay OFF");
  
  // Force relay OFF regardless of state
  digitalWrite(RELAY_PIN, RELAY_OFF);
  digitalWrite(RELAY_PIN, RELAY_OFF);  // Double-ensure
  
  relayActive    = false;
  continuousMode = false;

  controlServer.send(200, "application/json",
    "{\"status\":\"force_stopped\",\"relay\":\"off\"}");
}

/* ============================================================
 *  GET /capture_frame — Single JPEG capture
 * ============================================================ */
void handleCaptureFrame() {
  addCors(controlServer);
  
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    controlServer.send(500, "application/json",
      "{\"error\":\"capture failed\"}");
    Serial.println("[REQ] /capture_frame → FAILED");
    return;
  }

  controlServer.sendHeader("Content-Disposition", "inline; filename=frame.jpg");
  controlServer.send_P(200, "image/jpeg", (const char*)fb->buf, fb->len);
  esp_camera_fb_return(fb);
  
  Serial.printf("[REQ] /capture_frame → OK (%u bytes)\n", fb->len);
}

/* ============================================================
 *  OPTIONS — CORS preflight
 * ============================================================ */
void handleOptions() {
  addCors(controlServer);
  controlServer.send(204);
}

/* ============================================================
 *  GET /stream (port 81) — MJPEG continuous stream
 * ============================================================ */
#define BOUNDARY "----frame"

void handleStream() {
  WiFiClient client = streamServer.client();
  
  // Send HTTP headers
  client.println("HTTP/1.1 200 OK");
  client.println("Content-Type: multipart/x-mixed-replace; boundary=" BOUNDARY);
  client.println("Access-Control-Allow-Origin: *");
  client.println("Cache-Control: no-cache");
  client.println();

  Serial.println("[STREAM] Client connected");

  while (client.connected()) {
    // Keep control server responsive during streaming
    controlServer.handleClient();

    camera_fb_t* fb = esp_camera_fb_get();
    if (!fb) {
      delay(30);
      continue;
    }

    // Send frame with boundary
    client.printf("--%s\r\n", BOUNDARY);
    client.println("Content-Type: image/jpeg");
    client.printf("Content-Length: %u\r\n\r\n", fb->len);
    client.write(fb->buf, fb->len);
    client.println();

    esp_camera_fb_return(fb);
    delay(50);  // ~20 FPS
  }

  Serial.println("[STREAM] Client disconnected");
}
