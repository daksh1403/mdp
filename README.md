# 🎨 PaintDrone — Autonomous Wall Painting System

## VIT Chennai Multi-Disciplinary Project — Drone #3

---

## 🚁 Hardware Configuration

| Component | Specification |
|-----------|---------------|
| Flight Controller | **Pixhawk 2.4.8** |
| Frame | F450 Quadcopter X-config |
| ESCs | 4x 30A Brushless |
| RC Receiver | FlySky FS-IA6B (6-channel) |
| Battery | Orange 3S 3300mAh 35C LiPo |
| Camera | ESP32-CAM (AI Thinker) |

---

## 📁 Repository Structure

```
mdp_repo/
├── backend/
│   ├── app.py                ← Flask web server
│   ├── drone_controller.py   ← DroneKit Pixhawk control
│   ├── test_connection.py    ← USB connection test
│   ├── test_arm.py           ← Arm test (props OFF)
│   ├── test_hover.py         ← 1m hover test
│   └── static/index.html     ← Web UI
├── esp32cam/
│   └── esp32cam.ino          ← Camera + spray control
├── esp32s3/
│   └── esp32s3.ino           ← USB programmer bridge
└── docs/
    ├── COMPLETE_LAB_PROCEDURE.md  ← Full testing guide
    ├── LAB_SAFETY_CHECKLIST.md    ← Safety checkpoints
    ├── DRONE_PARAMETERS.md        ← Configuration
    └── drone_specs.md             ← Hardware specs
```

---

## ⚡ Quick Start

### 1. Clone & Setup
```bash
git clone https://github.com/daksh1403/mdp.git
cd mdp
pip install -r requirements.txt
```

### 2. Test Connection
```bash
cd backend
python test_connection.py
```

### 3. Run Web Server
```bash
python app.py
# Open http://localhost:5000
```

---

## ⚠️ Indoor Lab Settings

| Parameter | Value |
|-----------|-------|
| Max Altitude | **1.5m** |
| Painting Altitude | **1.0m** |
| Geofence Radius | **3.0m** |
| Connection | **COM3** @ 115200 baud |

---

## 📖 Documentation

- **[COMPLETE_LAB_PROCEDURE.md](COMPLETE_LAB_PROCEDURE.md)** — Step-by-step testing guide
- **[LAB_SAFETY_CHECKLIST.md](LAB_SAFETY_CHECKLIST.md)** — Safety checkpoints
- **[DRONE_PARAMETERS.md](DRONE_PARAMETERS.md)** — Configurable parameters
- **[PROJECT_EXPLANATION.md](PROJECT_EXPLANATION.md)** — How the system works

---

## 🛡️ Safety First

⚠️ **ALWAYS follow the [LAB_SAFETY_CHECKLIST.md](LAB_SAFETY_CHECKLIST.md)**
- Remove propellers for initial tests
- Have a safety pilot with RC ready
- Never fly above 1.5m indoors

---

*VIT Chennai MDP Team*