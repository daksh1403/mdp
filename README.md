# 🎨 Autonomous Painting System

## VIT Chennai Multi-Disciplinary Project

An autonomous wall painting system using computer vision for paint detection and ESP32-CAM for spray control.

---

## 🔧 Hardware Configuration

| Component | Specification |
|-----------|---------------|
| Camera | ESP32-CAM (AI Thinker) |
| Microcontroller | ESP32-S3 (USB programmer) |
| Spray Control | Relay module on GPIO 13 |

---

## 📁 Repository Structure

```
mdp/
├── backend/
│   ├── app.py                ← Flask web server
│   └── static/index.html     ← Web UI
├── esp32cam/
│   └── esp32cam.ino          ← Camera + spray control
├── esp32s3/
│   └── esp32s3.ino           ← USB programmer bridge
├── requirements.txt          ← Python dependencies
└── README.md
```

---

## ⚡ Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/daksh1403/mdp.git
cd mdp
pip install -r requirements.txt
```

### 2. Flash ESP32-CAM
1. Connect ESP32-S3 as programmer (see `esp32s3/esp32s3.ino`)
2. Connect IO0 to GND on ESP32-CAM
3. Upload `esp32cam/esp32cam.ino`
4. Remove IO0-GND jumper
5. Press RESET on ESP32-CAM

### 3. Connect to ESP32-CAM WiFi
- **SSID:** PaintSystem
- **Password:** paintdrone123
- **IP:** 192.168.4.1

### 4. Run Web Server
```bash
cd backend
python app.py
# Open http://localhost:5000
```

---

## 🌐 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Web UI |
| GET | `/video_feed` | MJPEG camera stream |
| GET | `/ping` | ESP32-CAM connectivity check |
| POST | `/capture` | Capture frame + paint detection |
| POST | `/spray` | Fire spray (precision mode) |
| POST | `/spray_start` | Start continuous spray |
| POST | `/spray_stop` | Stop spray immediately |
| GET | `/spray_sequence` | Execute spray sequence (SSE) |
| GET | `/smart_spray_sequence` | Smart spray with segments (SSE) |

---

## 🎯 Features

- **Paint Detection:** 6-method weighted voting algorithm for detecting unpainted (white) areas
- **Grid-Based Detection:** Divides camera view into 8×12 grid for cell-by-cell painting
- **Precision Spray:** Spray individual cells with configurable duration
- **Continuous Spray:** Spray multiple adjacent cells in one sweep
- **Smart Mode:** Automatically chooses precision or continuous based on cell layout
- **Live Camera Feed:** Real-time MJPEG stream from ESP32-CAM
- **Web Interface:** Modern, responsive UI for monitoring and control

---

## 📖 System Overview

### Paint Detection Algorithm

The system uses computer vision to detect unpainted (white) areas:

1. **Adaptive Threshold** (30%) — Local contrast detection
2. **Relative Brightness** (20%) — Global brightness comparison
3. **Low Saturation** (25%) — Color saturation analysis
4. **Otsu Threshold** (10%) — Automatic threshold selection
5. **LAB Lightness** (10%) — Perceptual lightness detection
6. **Blurred Threshold** (5%) — Noise-resistant detection

Results are combined using weighted voting and morphological cleanup.

### ESP32-CAM Controller

The ESP32-CAM runs a dual-port HTTP server:
- **Port 80:** Control API (ping, status, spray commands)
- **Port 81:** MJPEG video stream

The relay on GPIO 13 controls the spray mechanism with:
- Precision mode (timed spray)
- Continuous mode (manual start/stop)
- Safety watchdog (30-second auto-shutoff)

---

## 🛠️ Development

### Requirements

- Python 3.8+
- OpenCV 4.8+
- Flask 2.3+
- Arduino IDE (for ESP32 programming)

### ESP32-CAM Pin Configuration

| Pin | Function |
|-----|----------|
| GPIO 13 | Relay control (spray) |
| GPIO 0-35 | Camera interface |

---

## 🔮 Future Plans

- Drone integration for autonomous positioning
- Multi-axis robotic arm support
- Advanced path planning algorithms
- Multi-color paint support

---

*VIT Chennai MDP Team*
