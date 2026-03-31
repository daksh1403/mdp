"""
============================================================
 Flask Backend — Autonomous Painting System
 VIT Chennai Multi-Disciplinary Project
============================================================

Runs on laptop. Connects to:
  - ESP32-CAM (192.168.4.1) for camera and spray control

Endpoints:
  GET  /               → Web UI
  GET  /video_feed     → Proxy MJPEG stream from ESP32-CAM
  GET  /ping           → ESP32-CAM connectivity check
  POST /capture        → Capture frame + run paint detection
  POST /spray          → Fire spray for specified duration
  POST /spray_start    → Start continuous spray
  POST /spray_stop     → Stop spray immediately
  GET  /spray_sequence → Precision spray (cell by cell)
  GET  /smart_spray_sequence → Smart spray (continuous + precision)

Run: python app.py
============================================================
"""

import cv2
import numpy as np
import base64
import time
import json
import threading
import requests
from flask import Flask, Response, request, jsonify, send_from_directory
from flask_cors import CORS

# ══════════════════════════════════════════════════════════════
#  Configuration
# ══════════════════════════════════════════════════════════════

# ESP32-CAM addresses
ESP32_CONTROL = "http://192.168.4.1"      # Port 80 - control
ESP32_STREAM  = "http://192.168.4.1:81"   # Port 81 - MJPEG stream

# Detection grid size
GRID_ROWS = 8
GRID_COLS = 12

# Spray settings
SPRAY_DURATION_MS = 800  # milliseconds per cell

# ══════════════════════════════════════════════════════════════
#  Flask App
# ══════════════════════════════════════════════════════════════

app = Flask(__name__, static_folder="static")
CORS(app)

# ESP32-CAM last contact timestamp (for connectivity check)
_esp32_lock = threading.Lock()
_last_esp32_contact = 0.0


# ══════════════════════════════════════════════════════════════
#  Paint Detection Algorithm
# ══════════════════════════════════════════════════════════════

class PaintDetector:
    """
    Detects unpainted (white) areas using 6-method weighted voting.
    """
    
    def __init__(self):
        self.clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))

    def detect_whites(self, frame, sensitivity=50):
        """
        Run multi-method white detection on frame.
        Returns dict with 'regions' and 'combined_mask'.
        """
        h, w = frame.shape[:2]

        # Convert to different color spaces
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        gray_enhanced = self.clahe.apply(gray)
        lab  = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l_enhanced = self.clahe.apply(lab[:, :, 0])

        # Method 1: Adaptive threshold (30%)
        adaptive_mask = cv2.adaptiveThreshold(
            gray_enhanced, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            blockSize=51,
            C=-5 - (sensitivity // 10)
        )

        # Method 2: Relative brightness (20%)
        mean_brightness = gray.mean()
        threshold = max(50, mean_brightness - 20 + (sensitivity // 2))
        _, relative_mask = cv2.threshold(gray, int(threshold), 255,
                                         cv2.THRESH_BINARY)

        # Method 3: Low saturation + not dark (25%)
        s_channel = hsv[:, :, 1]
        v_channel = hsv[:, :, 2]
        max_saturation = 40 + sensitivity
        min_brightness = max(30, 80 - sensitivity)
        low_sat  = (s_channel < max_saturation).astype(np.uint8) * 255
        not_dark = (v_channel > min_brightness).astype(np.uint8) * 255
        saturation_mask = cv2.bitwise_and(low_sat, not_dark)

        # Method 4: Otsu threshold (10%)
        _, otsu_mask = cv2.threshold(gray_enhanced, 0, 255,
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Method 5: LAB lightness (10%)
        l_mean = l_enhanced.mean()
        l_threshold = max(80, l_mean - 10 + (sensitivity // 3))
        _, lab_mask = cv2.threshold(l_enhanced, int(l_threshold), 255,
                                     cv2.THRESH_BINARY)

        # Method 6: Blurred threshold (5%)
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        blur_threshold = max(40, blurred.mean() - 15 + (sensitivity // 2))
        _, blur_mask = cv2.threshold(blurred, int(blur_threshold), 255,
                                      cv2.THRESH_BINARY)

        # Weighted combination
        combined = np.zeros_like(gray, dtype=np.float32)
        combined += adaptive_mask.astype(np.float32)   * 0.30
        combined += relative_mask.astype(np.float32)   * 0.20
        combined += saturation_mask.astype(np.float32) * 0.25
        combined += otsu_mask.astype(np.float32)       * 0.10
        combined += lab_mask.astype(np.float32)        * 0.10
        combined += blur_mask.astype(np.float32)       * 0.05

        combined = np.clip(combined, 0, 255).astype(np.uint8)
        _, combined_mask = cv2.threshold(combined, 100, 255,
                                          cv2.THRESH_BINARY)

        # Morphological cleanup
        kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN,
                                          kernel_small)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE,
                                          kernel_large)

        # Extract region info
        regions = []
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL,
                                        cv2.CHAIN_APPROX_SIMPLE)
        min_area = (w * h) * 0.005

        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue

            x, y, rw, rh = cv2.boundingRect(contour)
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / hull_area if hull_area > 0 else 0
            roi_gray = gray[y:y + rh, x:x + rw]
            roi_sat  = s_channel[y:y + rh, x:x + rw]

            size_score    = min(1.0, area / (w * h * 0.1))
            sat_score     = 1.0 - (roi_sat.mean() / 255)
            uniform_score = 1.0 - min(1.0, roi_gray.std() / 50)
            confidence = (size_score * 0.25 + solidity * 0.25 +
                          sat_score * 0.30 + uniform_score * 0.20)

            regions.append({
                'box':        (x, y, rw, rh),
                'center':     (x + rw // 2, y + rh // 2),
                'confidence': confidence,
                'contour':    contour
            })

        regions.sort(key=lambda r: r['confidence'], reverse=True)
        return {'regions': regions, 'combined_mask': combined_mask}


def build_grid_from_mask(mask):
    """
    Divide mask into GRID_ROWS × GRID_COLS grid.
    Cell is "unpainted" if ≥40% white pixels.
    """
    h, w = mask.shape[:2]
    cell_w = max(1, w // GRID_COLS)
    cell_h = max(1, h // GRID_ROWS)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    clean = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    clean = cv2.morphologyEx(clean, cv2.MORPH_CLOSE, kernel)

    grid = []
    for r in range(GRID_ROWS):
        row = []
        for c in range(GRID_COLS):
            x0 = c * cell_w
            y0 = r * cell_h
            x1 = w if c == GRID_COLS - 1 else (c + 1) * cell_w
            y1 = h if r == GRID_ROWS - 1 else (r + 1) * cell_h
            cell = clean[y0:y1, x0:x1]
            if cell.size == 0:
                row.append(False)
                continue
            filled = float(np.count_nonzero(cell)) / float(cell.size)
            row.append(filled >= 0.4)
        grid.append(row)
    return grid


# Instantiate detector
detector = PaintDetector()


# ══════════════════════════════════════════════════════════════
#  Routes — Web UI
# ══════════════════════════════════════════════════════════════

@app.route("/")
def index():
    """Serve the web UI."""
    return send_from_directory("static", "index.html")


@app.route("/mobile")
@app.route("/mobile.html")
def mobile():
    """Serve the mobile PWA."""
    return send_from_directory("static", "mobile.html")


@app.route("/manifest.json")
def manifest():
    """Serve PWA manifest."""
    return send_from_directory("static", "manifest.json")


@app.route("/sw.js")
def service_worker():
    """Serve service worker."""
    return send_from_directory("static", "sw.js")


# ══════════════════════════════════════════════════════════════
#  Routes — ESP32-CAM Proxy
# ══════════════════════════════════════════════════════════════

@app.route("/video_feed")
def video_feed():
    """Proxy MJPEG stream from ESP32-CAM."""
    def generate():
        global _last_esp32_contact
        try:
            resp = requests.get(f"{ESP32_STREAM}/stream",
                                stream=True, timeout=10)
            for chunk in resp.iter_content(chunk_size=4096):
                with _esp32_lock:
                    _last_esp32_contact = time.time()
                yield chunk
        except requests.exceptions.RequestException as e:
            print(f"[video_feed] Stream error: {e}")
            return

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=----frame"
    )


@app.route("/ping")
def ping():
    """Check ESP32-CAM connectivity."""
    global _last_esp32_contact
    
    with _esp32_lock:
        age = time.time() - _last_esp32_contact

    # Stream recently active = ESP32 is online
    if age < 5:
        return jsonify({"status": "ok", "source": "stream"})

    # Try direct ping
    try:
        r = requests.get(f"{ESP32_CONTROL}/ping", timeout=2)
        if r.ok:
            with _esp32_lock:
                _last_esp32_contact = time.time()
            return jsonify({"status": "ok", "source": "direct"})
    except requests.exceptions.RequestException:
        pass

    return jsonify({"status": "offline"}), 503


# ══════════════════════════════════════════════════════════════
#  Routes — Paint Detection
# ══════════════════════════════════════════════════════════════

@app.route("/capture", methods=["POST"])
def capture():
    """Capture frame from ESP32-CAM and run paint detection."""
    try:
        # Get sensitivity from request (default 50)
        data = request.get_json(force=True) if request.data else {}
        sensitivity = data.get("sensitivity", 50)
        
        # Capture frame from ESP32-CAM
        resp = requests.get(f"{ESP32_CONTROL}/capture_frame", timeout=10)

        if resp.status_code != 200:
            return jsonify({"success": False, "error": f"Camera returned {resp.status_code}"}), 502

        # Decode JPEG
        np_arr = np.frombuffer(resp.content, dtype=np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
            return jsonify({"success": False, "error": "Frame decode failed"}), 500

        # Run detection
        results = detector.detect_whites(frame, sensitivity=sensitivity)
        mask = results["combined_mask"]
        grid = build_grid_from_mask(mask)
        
        # Build list of unpainted cells for the UI
        unpainted_cells = []
        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                if grid[r][c] == 1:  # 1 = unpainted (white)
                    unpainted_cells.append({"row": r, "col": c})

        # Encode frame as base64
        _, jpeg_encoded = cv2.imencode(".jpg", frame,
                                        [cv2.IMWRITE_JPEG_QUALITY, 90])
        b64_image = base64.b64encode(jpeg_encoded.tobytes()).decode("utf-8")

        return jsonify({
            "success": True,
            "image_base64": b64_image,
            "unpainted_cells": unpainted_cells,
            "grid": grid,
            "grid_rows": GRID_ROWS,
            "grid_cols": GRID_COLS
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Camera connection failed: {e}"}), 502
    except Exception as e:
        return jsonify({"success": False, "error": f"Capture failed: {e}"}), 500


# ══════════════════════════════════════════════════════════════
#  Routes — Direct Spray Control
# ══════════════════════════════════════════════════════════════

@app.route("/esp_ping", methods=["GET"])
def esp_ping():
    """Check ESP32-CAM connectivity."""
    try:
        resp = requests.get(f"{ESP32_CONTROL}/ping", timeout=2)
        if resp.status_code == 200:
            return jsonify({"status": "ok"})
        return jsonify({"status": "error", "code": resp.status_code}), 502
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502


@app.route("/spray", methods=["POST"])
def spray_once():
    """Fire spray for specified duration (precision mode)."""
    try:
        data = request.get_json(force=True) if request.data else {}
        duration_ms = data.get("duration_ms", SPRAY_DURATION_MS)
        
        # Limit duration for safety
        duration_ms = max(100, min(5000, int(duration_ms)))
        
        resp = requests.post(
            f"{ESP32_CONTROL}/spray",
            json={"duration_ms": duration_ms},
            timeout=10
        )
        
        if resp.status_code == 200:
            return jsonify({"sprayed": True, "duration_ms": duration_ms})
        else:
            return jsonify({"sprayed": False, "error": f"ESP32 returned {resp.status_code}"}), 502
            
    except Exception as e:
        return jsonify({"sprayed": False, "error": str(e)}), 502


@app.route("/spray_start", methods=["POST"])
def spray_start():
    """Start continuous spray (continuous mode)."""
    try:
        resp = requests.post(f"{ESP32_CONTROL}/spray_start", timeout=5)
        
        if resp.status_code == 200:
            return jsonify({"status": "spraying", "mode": "continuous"})
        else:
            return jsonify({"status": "error", "code": resp.status_code}), 502
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502


@app.route("/spray_stop", methods=["POST"])
def spray_stop():
    """Stop spray immediately."""
    try:
        resp = requests.post(f"{ESP32_CONTROL}/spray_stop", timeout=5)
        
        if resp.status_code == 200:
            return jsonify({"status": "stopped"})
        else:
            return jsonify({"status": "error", "code": resp.status_code}), 502
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 502


@app.route("/camera_proxy")
def camera_proxy():
    """
    Proxy MJPEG stream from ESP32-CAM to solve CORS issues.
    Alternative to /video_feed for single image mode.
    """
    try:
        resp = requests.get(f"{ESP32_STREAM}/stream", stream=True, timeout=5)
        return Response(
            resp.iter_content(chunk_size=4096),
            mimetype='multipart/x-mixed-replace; boundary=----frame',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    except Exception as e:
        # Return placeholder image
        placeholder = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        return Response(placeholder, mimetype='image/jpeg')


# ══════════════════════════════════════════════════════════════
#  Routes — Spray Sequences
# ══════════════════════════════════════════════════════════════

@app.route("/spray_sequence", methods=["GET", "POST"])
def spray_sequence():
    """
    PRECISION MODE: Move to each cell, spray.
    Supports both POST body and GET query params for SSE.
    
    POST Body or GET ?cells=JSON:
      cells: [{row: 0, col: 1}, ...] or [[row,col], ...]
    """
    # Handle both GET (SSE from browser) and POST
    if request.method == "GET":
        cells_json = request.args.get("cells", "[]")
        try:
            cells_raw = json.loads(cells_json)
        except:
            cells_raw = []
    else:
        data = request.get_json(force=True) if request.data else {}
        cells_raw = data.get("cells", [])

    # Normalize cells to (row, col) tuples
    cells = []
    for c in cells_raw:
        if isinstance(c, dict):
            cells.append((c.get("row", 0), c.get("col", 0)))
        elif isinstance(c, (list, tuple)) and len(c) >= 2:
            cells.append((c[0], c[1]))

    if not cells:
        return jsonify({"error": "No cells provided"}), 400

    def generate():
        n = len(cells)

        for i, (row, col) in enumerate(cells):

            # Send "moving" event
            yield f"data: {json.dumps({'event':'moving','cell':i+1,'total':n,'row':row,'col':col})}\n\n"

            # Wait for manual positioning
            time.sleep(2)

            # Send "spraying" event
            yield f"data: {json.dumps({'event':'spraying','cell':i+1,'row':row,'col':col})}\n\n"

            # Fire spray with retry
            for attempt in range(3):
                try:
                    resp = requests.post(
                        f"{ESP32_CONTROL}/spray",
                        json={"duration_ms": SPRAY_DURATION_MS},
                        timeout=5)
                    resp.raise_for_status()
                    print(f"[spray] Cell ({row},{col}) OK")
                    break
                except Exception as e:
                    print(f"[spray] Attempt {attempt+1} failed: {e}")
                    time.sleep(0.5)

            time.sleep(1.0)  # Wait for spray to complete

            # Send "done" event
            yield f"data: {json.dumps({'event':'done','cell':i+1,'row':row,'col':col})}\n\n"

        yield f"data: {json.dumps({'event':'complete','total':n})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no",
                             "Access-Control-Allow-Origin": "*"})


@app.route("/smart_spray_sequence", methods=["GET"])
def smart_spray_sequence():
    """
    SMART MODE: Automatically uses continuous spray for adjacent cells
    and precision spray for isolated cells.
    
    Query param: segments = JSON array of:
      { type: 'continuous' | 'precision', row, startCol, endCol, cells }
    
    Example:
      segments = [
        { type: 'continuous', row: 0, startCol: 2, endCol: 5, cells: [...] },
        { type: 'precision', row: 1, startCol: 3, endCol: 3, cells: [...] }
      ]
    """
    segments_json = request.args.get("segments", "[]")
    try:
        segments = json.loads(segments_json)
    except:
        return jsonify({"error": "Invalid segments JSON"}), 400

    if not segments:
        return jsonify({"error": "No segments provided"}), 400

    def generate():
        total_segments = len(segments)
        total_cells = sum(len(seg.get('cells', [])) for seg in segments)
        
        for idx, segment in enumerate(segments):
            seg_type = segment.get('type', 'precision')
            row = segment.get('row', 0)
            start_col = segment.get('startCol', 0)
            end_col = segment.get('endCol', start_col)
            cells = segment.get('cells', [])
            
            if seg_type == 'continuous':
                # CONTINUOUS SPRAY: Multiple adjacent cells in a row
                
                # Event: Starting segment
                yield f"data: {json.dumps({'event':'segment_start','type':'continuous','row':row,'startCol':start_col,'endCol':end_col,'segment':idx+1,'total_segments':total_segments})}\n\n"
                
                # Wait for manual positioning
                time.sleep(1.5)
                
                # Start continuous spray
                yield f"data: {json.dumps({'event':'continuous_spray_start','row':row,'startCol':start_col,'endCol':end_col})}\n\n"
                
                try:
                    requests.post(f"{ESP32_CONTROL}/spray_start", timeout=5)
                except Exception as e:
                    print(f"[smart] spray_start failed: {e}")
                
                # Time proportional to number of cells
                fly_time = len(cells) * 1.2  # ~1.2 seconds per cell
                time.sleep(fly_time)
                
                # Stop spray
                try:
                    requests.post(f"{ESP32_CONTROL}/spray_stop", timeout=5)
                except Exception as e:
                    print(f"[smart] spray_stop failed: {e}")
                
                # Event: Segment complete
                yield f"data: {json.dumps({'event':'continuous_spray_end','row':row,'startCol':start_col,'endCol':end_col,'cells_count':len(cells),'cells':cells})}\n\n"
                
            else:
                # PRECISION SPRAY: Single isolated cell
                
                col = cells[0].get('col', start_col) if cells else start_col
                
                # Event: Starting segment
                yield f"data: {json.dumps({'event':'segment_start','type':'precision','row':row,'col':col,'segment':idx+1,'total_segments':total_segments})}\n\n"
                
                # Wait for manual positioning
                time.sleep(1.5)
                
                # Event: Spraying
                yield f"data: {json.dumps({'event':'precision_spray','row':row,'col':col})}\n\n"
                
                # Fire precision spray
                for attempt in range(3):
                    try:
                        resp = requests.post(
                            f"{ESP32_CONTROL}/spray",
                            json={"duration_ms": SPRAY_DURATION_MS},
                            timeout=5)
                        resp.raise_for_status()
                        break
                    except Exception as e:
                        print(f"[smart] precision spray attempt {attempt+1} failed: {e}")
                        time.sleep(0.3)
                
                time.sleep(1.0)  # Wait for spray to complete
                
                # Event: Done
                yield f"data: {json.dumps({'event':'precision_done','row':row,'col':col})}\n\n"
        
        # Mission complete
        yield f"data: {json.dumps({'event':'complete','total_segments':total_segments,'total_cells':total_cells})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no",
                             "Access-Control-Allow-Origin": "*"})


# ══════════════════════════════════════════════════════════════
#  Main Entry Point
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 60)
    print("  Autonomous Painting System — Flask Backend")
    print("  VIT Chennai Multi-Disciplinary Project")
    print("=" * 60)
    print(f"  ESP32 Control : {ESP32_CONTROL}")
    print(f"  ESP32 Stream  : {ESP32_STREAM}")
    print(f"  Web UI        : http://localhost:5000")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
