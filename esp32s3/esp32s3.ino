/*
 * ============================================================
 *  ESP32-S3 — USB-to-Serial Bridge for ESP32-CAM Flashing
 * ============================================================
 *
 *  PURPOSE:
 *    The ESP32-CAM has no USB port. This sketch turns an
 *    ESP32-S3 dev board into a USB-to-Serial programmer.
 *
 *  WIRING (ESP32-S3 → ESP32-CAM):
 *    GPIO17 (TX) → U0R (RX)
 *    GPIO18 (RX) → U0T (TX)
 *    GND         → GND
 *    5V          → 5V
 *
 *  FOR FLASHING ESP32-CAM:
 *    Also connect: ESP32-CAM IO0 → GND (boot mode)
 *
 *  AFTER FLASHING:
 *    1. Remove IO0-GND jumper from ESP32-CAM
 *    2. Press RESET on ESP32-CAM
 *    3. Disconnect ESP32-S3 entirely (not needed anymore)
 *
 *  IN ARDUINO IDE:
 *    1. Upload THIS sketch to ESP32-S3 first
 *    2. Then select "AI Thinker ESP32-CAM" as board
 *    3. Upload esp32cam.ino (it goes through the S3 bridge)
 * ============================================================
 */

#define TX_PIN 17  // ESP32-S3 TX → ESP32-CAM RX
#define RX_PIN 18  // ESP32-S3 RX → ESP32-CAM TX

void setup() {
  // USB Serial to laptop
  Serial.begin(115200);
  
  // Hardware Serial1 to ESP32-CAM
  Serial1.begin(115200, SERIAL_8N1, RX_PIN, TX_PIN);
  
  Serial.println("[Bridge] ESP32-S3 USB-to-Serial bridge ready");
  Serial.println("[Bridge] GPIO17 (TX) → ESP32-CAM U0R");
  Serial.println("[Bridge] GPIO18 (RX) → ESP32-CAM U0T");
}

void loop() {
  // Forward USB → ESP32-CAM
  while (Serial.available()) {
    Serial1.write(Serial.read());
  }
  
  // Forward ESP32-CAM → USB
  while (Serial1.available()) {
    Serial.write(Serial1.read());
  }
}
