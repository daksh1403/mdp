"""
============================================================
 Flask Backend — Autonomous Painting System (FIXED)
 VIT Chennai Multi-Disciplinary Project
============================================================

FIXES APPLIED:
  1. Robust ESP32 reconnection with exponential backoff
  2. Better stream handling to prevent crashes
  3. Heartbeat-based connectivity checking
  4. Retry logic for spray commands with proper delays
  5. SSE keep-alive to prevent connection drops
  6. Proper error recovery during spray sequences

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
from collections import deque

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
SPRAY_RETRY_ATTEMPTS = 5  # Increased retries
SPRAY_RETRY_DELAY = 0.3   # Delay between retries

# Connection settings
CONNECTION_TIMEOUT = 3    # Reduced timeout for faster retries
STREAM_TIMEOUT = 10
PING_TIMEOUT = 2

# ══════════════════════════════════════════════════════════════
#  Flask App
# ══════════════════════════════════════════════════════════════

app = Flask(__name__, static_folder="static")
CORS(app)

# ESP32-CAM connection state
_esp32_lock = threading.Lock()
_last_esp32_contact = 0.0
_esp32_connected = False
_connection_errors = deque(maxlen=10)  # Track recent errors

def update_esp32_contact():
    """Update last contact time and mark as connected."""
    global _last_esp32_contact, _esp32_connected
    with _esp32_lock:
        _last_esp32_contact = time.time()
        _esp32_connected = True

def mark_esp32_disconnected(error_msg=""):
    """Mark ESP32 as disconnected."""
    global _esp32_connected
    with _esp32_lock:
        _esp32_connected = False
        if error_msg:
            _connection_errors.append((time.time(), error_msg))

def is_esp32_connected():
    """Check if ESP32 was recently connected."""
    with _esp32_lock:
        age = time.time() - _last_esp32_contact
        return _esp32_connected and age < 10  # 10 second timeout

def wait_for_esp32(max_wait=5):
    """
    Wait for ESP32 to reconnect with exponential backoff.
    Returns True if connected, False if timeout.
    """
    delays = [0.1, 0.2, 0.4, 0.8, 1.0, 1.5, 2.0]
    total_waited = 0
    
    for delay in delays:
        if total_waited >= max_wait:
            break
        try:
            r = requests.get(f"{ESP32_CONTROL}/ping", timeout=PING_TIMEOUT)
            if r.ok:
                update_esp32_contact()
                print(f"[ESP32] Reconnected after {total_waited:.1f}s")
                return True
        except:
            pass
        time.sleep(delay)
        total_waited += delay
    
    mark_esp32_disconnected("Reconnection timeout")
    return False

def send_spray_command(duration_ms, retries=SPRAY_RETRY_ATTEMPTS):
    """
    Send spray command with robust retry logic.
    Returns (success, message)
    """
    for attempt in range(retries):
        try:
            resp = requests.post(
                f"{ESP32_CONTROL}/spray",
                json={"duration_ms": duration_ms},
                timeout=CONNECTION_TIMEOUT
            )
            if resp.status_code == 200:
                update_esp32_contact()
                return True, "OK"
            elif resp.status_code == 409:
                # Spray in progress, wait and retry
                time.sleep(0.5)
                continue
            else:
                mark_esp32_disconnected(f"HTTP {resp.status_code}")
        except requests.exceptions.Timeout:
            print(f"[SPRAY] Attempt {attempt+1} timeout, retrying...")
            mark_esp32_disconnected("Timeout")
        except requests.exceptions.ConnectionError:
            print(f"[SPRAY] Attempt {attempt+1} connection error, waiting for ESP32...")
            mark_esp32_disconnected("Connection error")
            # Try to reconnect before next attempt
            if attempt < retries - 1:
                wait_for_esp32(max_wait=2)
        except Exception as e:
            print(f"[SPRAY] Attempt {attempt+1} error: {e}")
            mark_esp32_disconnected(str(e))
        
        if attempt < retries - 1:
            time.sleep(SPRAY_RETRY_DELAY * (attempt + 1))  # Increasing delay
    
    return False, f"Failed after {retries} attempts"


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
#  Routes — ESP32-CAM Proxy (IMPROVED)
# ══════════════════════════════════════════════════════════════

@app.route("/video_feed")
def video_feed():
    """
    Proxy MJPEG stream from ESP32-CAM with improved error handling.
    """
    def generate():
        global _last_esp32_contact
        reconnect_attempts = 0
        max_reconnect = 3
        
        while True:
            try:
                print("[VIDEO] Connecting to ESP32-CAM stream...")
                resp = requests.get(
                    f"{ESP32_STREAM}/stream",
                    stream=True, 
                    timeout=STREAM_TIMEOUT
                )
                
                reconnect_attempts = 0  # Reset on successful connect
                update_esp32_contact()
                print("[VIDEO] Stream connected")
                
                for chunk in resp.iter_content(chunk_size=4096):
                    if chunk:
                        update_esp32_contact()
                        yield chunk
                        
            except requests.exceptions.Timeout:
                print("[VIDEO] Stream timeout")
                mark_esp32_disconnected("Stream timeout")
            except requests.exceptions.ConnectionError:
                print("[VIDEO] Stream connection error")
                mark_esp32_disconnected("Stream connection error")
            except Exception as e:
                print(f"[VIDEO] Stream error: {e}")
                mark_esp32_disconnected(str(e))
            
            # Reconnection logic
            reconnect_attempts += 1
            if reconnect_attempts > max_reconnect:
                print("[VIDEO] Max reconnection attempts reached")
                # Send a placeholder frame to indicate disconnection
                placeholder = b'--frame\r\nContent-Type: text/plain\r\n\r\nDisconnected\r\n'
                yield placeholder
                break
            
            print(f"[VIDEO] Reconnecting (attempt {reconnect_attempts}/{max_reconnect})...")
            time.sleep(1)  # Wait before reconnecting

    return Response(
        generate(),
        mimetype="multipart/x-mixed-replace; boundary=----frame"
    )


@app.route("/ping")
def ping():
    """Check ESP32-CAM connectivity."""
    # Check recent stream activity first
    if is_esp32_connected():
        return jsonify({"status": "ok", "source": "stream"})

    # Try direct ping
    try:
        r = requests.get(f"{ESP32_CONTROL}/ping", timeout=PING_TIMEOUT)
        if r.ok:
            update_esp32_contact()
            return jsonify({"status": "ok", "source": "direct"})
    except requests.exceptions.RequestException:
        pass

    mark_esp32_disconnected("Ping failed")
    return jsonify({"status": "offline"}), 503


@app.route("/esp_ping", methods=["GET"])
def esp_ping():
    """Check ESP32-CAM connectivity with detailed status."""
    try:
        resp = requests.get(f"{ESP32_CONTROL}/ping", timeout=PING_TIMEOUT)
        if resp.status_code == 200:
            update_esp32_contact()
            return jsonify({"status": "ok", "connected": True})
        return jsonify({"status": "error", "code": resp.status_code, "connected": False}), 502
    except requests.exceptions.Timeout:
        mark_esp32_disconnected("Timeout")
        return jsonify({"status": "error", "message": "Timeout", "connected": False}), 502
    except Exception as e:
        mark_esp32_disconnected(str(e))
        return jsonify({"status": "error", "message": str(e), "connected": False}), 502


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
        
        # Capture frame with retry logic
        frame_data = None
        for attempt in range(3):
            try:
                resp = requests.get(f"{ESP32_CONTROL}/capture_frame", timeout=CONNECTION_TIMEOUT)
                if resp.status_code == 200:
                    frame_data = resp.content
                    update_esp32_contact()
                    break
            except:
                if attempt < 2:
                    wait_for_esp32(max_wait=2)
        
        if not frame_data:
            return jsonify({"success": False, "error": "Failed to capture frame"}), 502

        # Decode JPEG
        np_arr = np.frombuffer(frame_data, dtype=np.uint8)
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
#  Routes — Direct Spray Control (IMPROVED)
# ══════════════════════════════════════════════════════════════

@app.route("/spray", methods=["POST"])
def spray_once():
    """Fire spray for specified duration (precision mode) with retries."""
    try:
        data = request.get_json(force=True) if request.data else {}
        duration_ms = data.get("duration_ms", SPRAY_DURATION_MS)
        
        # Limit duration for safety
        duration_ms = max(100, min(5000, int(duration_ms)))
        
        success, message = send_spray_command(duration_ms)
        
        if success:
            return jsonify({"sprayed": True, "duration_ms": duration_ms})
        else:
            return jsonify({"sprayed": False, "error": message}), 502
            
    except Exception as e:
        return jsonify({"sprayed": False, "error": str(e)}), 502


@app.route("/spray_start", methods=["POST"])
def spray_start():
    """Start continuous spray (continuous mode) with retries."""
    for attempt in range(SPRAY_RETRY_ATTEMPTS):
        try:
            resp = requests.post(f"{ESP32_CONTROL}/spray_start", timeout=CONNECTION_TIMEOUT)
            
            if resp.status_code == 200:
                update_esp32_contact()
                return jsonify({"status": "spraying", "mode": "continuous"})
            else:
                mark_esp32_disconnected(f"HTTP {resp.status_code}")
        except requests.exceptions.Timeout:
            print(f"[SPRAY_START] Attempt {attempt+1} timeout")
            mark_esp32_disconnected("Timeout")
        except requests.exceptions.ConnectionError:
            print(f"[SPRAY_START] Attempt {attempt+1} connection error")
            mark_esp32_disconnected("Connection error")
            if attempt < SPRAY_RETRY_ATTEMPTS - 1:
                wait_for_esp32(max_wait=2)
        except Exception as e:
            mark_esp32_disconnected(str(e))
        
        if attempt < SPRAY_RETRY_ATTEMPTS - 1:
            time.sleep(SPRAY_RETRY_DELAY * (attempt + 1))
    
    return jsonify({"status": "error", "message": "Failed to start spray"}), 502


@app.route("/spray_stop", methods=["POST"])
def spray_stop():
    """Stop spray immediately with retries."""
    for attempt in range(SPRAY_RETRY_ATTEMPTS):
        try:
            resp = requests.post(f"{ESP32_CONTROL}/spray_stop", timeout=CONNECTION_TIMEOUT)
            
            if resp.status_code == 200:
                update_esp32_contact()
                return jsonify({"status": "stopped"})
        except:
            pass
        
        if attempt < SPRAY_RETRY_ATTEMPTS - 1:
            time.sleep(0.2)
    
    # Return success anyway - better to assume spray is stopped
    return jsonify({"status": "stopped", "warning": "Could not confirm with ESP32"})


@app.route("/camera_proxy")
def camera_proxy():
    """
    Proxy MJPEG stream from ESP32-CAM to solve CORS issues.
    """
    try:
        resp = requests.get(f"{ESP32_STREAM}/stream", stream=True, timeout=STREAM_TIMEOUT)
        return Response(
            resp.iter_content(chunk_size=4096),
            mimetype='multipart/x-mixed-replace; boundary=----frame',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    except Exception as e:
        placeholder = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00'
        return Response(placeholder, mimetype='image/jpeg')


# ══════════════════════════════════════════════════════════════
#  Routes — Spray Sequences (IMPROVED with robust reconnection)
# ══════════════════════════════════════════════════════════════

@app.route("/spray_sequence", methods=["GET", "POST"])
def spray_sequence():
    """
    PRECISION MODE with robust ESP32 connection handling.
    Now includes:
    - Connection verification before each spray
    - Automatic reconnection on failure
    - SSE keep-alive messages
    - Error recovery
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
        failed_cells = []
        
        # Initial connection check
        if not is_esp32_connected():
            yield f"data: {json.dumps({'event':'connecting','message':'Connecting to ESP32...'})}\n\n"
            if not wait_for_esp32(max_wait=5):
                yield f"data: {json.dumps({'event':'error','message':'ESP32 not connected'})}\n\n"
                return

        for i, (row, col) in enumerate(cells):
            # Send keep-alive/heartbeat every few iterations
            if i > 0 and i % 3 == 0:
                yield f"data: {json.dumps({'event':'heartbeat','progress':i,'total':n})}\n\n"

            # Send "moving" event
            yield f"data: {json.dumps({'event':'moving','cell':i+1,'total':n,'row':row,'col':col})}\n\n"

            # Verify connection before spray
            if not is_esp32_connected():
                yield f"data: {json.dumps({'event':'reconnecting','cell':i+1,'row':row,'col':col})}\n\n"
                if not wait_for_esp32(max_wait=3):
                    yield f"data: {json.dumps({'event':'connection_lost','cell':i+1,'row':row,'col':col})}\n\n"
                    failed_cells.append((row, col))
                    continue  # Skip this cell but continue with others

            # Wait for manual positioning (reduced for first cell)
            time.sleep(0.5 if i == 0 else 1.5)

            # Send "spraying" event
            yield f"data: {json.dumps({'event':'spraying','cell':i+1,'row':row,'col':col})}\n\n"

            # Fire spray with robust retry
            success, error_msg = send_spray_command(SPRAY_DURATION_MS)
            
            if not success:
                print(f"[SPRAY] Cell ({row},{col}) FAILED: {error_msg}")
                yield f"data: {json.dumps({'event':'spray_failed','cell':i+1,'row':row,'col':col,'error':error_msg})}\n\n"
                failed_cells.append((row, col))
                # Try to reconnect for next cell
                wait_for_esp32(max_wait=2)
            else:
                print(f"[SPRAY] Cell ({row},{col}) OK")
                # Wait for spray to complete
                time.sleep(SPRAY_DURATION_MS / 1000.0 + 0.3)
                
                # Send "done" event
                yield f"data: {json.dumps({'event':'done','cell':i+1,'row':row,'col':col})}\n\n"

        # Summary
        successful = n - len(failed_cells)
        yield f"data: {json.dumps({'event':'complete','total':n,'successful':successful,'failed':len(failed_cells),'failed_cells':failed_cells})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no",
                             "Access-Control-Allow-Origin": "*",
                             "Connection": "keep-alive"})


@app.route("/smart_spray_sequence", methods=["GET"])
def smart_spray_sequence():
    """
    SMART MODE with robust connection handling.
    Automatically uses continuous spray for adjacent cells
    and precision spray for isolated cells.
    """
    cells_json = request.args.get("cells", "[]")
    try:
        cells_raw = json.loads(cells_json)
    except:
        return jsonify({"error": "Invalid cells JSON"}), 400

    # Normalize cells
    cells = []
    for c in cells_raw:
        if isinstance(c, dict):
            cells.append((c.get("row", 0), c.get("col", 0)))
        elif isinstance(c, (list, tuple)) and len(c) >= 2:
            cells.append((c[0], c[1]))

    if not cells:
        return jsonify({"error": "No cells provided"}), 400

    # Group adjacent cells in same row
    def segment_cells(cell_list):
        """Group cells into continuous segments."""
        segments = []
        
        # Sort by row, then col
        sorted_cells = sorted(cell_list, key=lambda x: (x[0], x[1]))
        
        current_segment = None
        for row, col in sorted_cells:
            if (current_segment is None or 
                current_segment['row'] != row or 
                col != current_segment['endCol'] + 1):
                # Start new segment
                if current_segment:
                    segments.append(current_segment)
                current_segment = {
                    'row': row,
                    'startCol': col,
                    'endCol': col,
                    'cells': [(row, col)],
                    'type': 'precision'
                }
            else:
                # Extend current segment
                current_segment['endCol'] = col
                current_segment['cells'].append((row, col))
        
        if current_segment:
            segments.append(current_segment)
        
        # Mark segments with 3+ cells as continuous
        for seg in segments:
            if len(seg['cells']) >= 3:
                seg['type'] = 'continuous'
        
        return segments

    segments = segment_cells(cells)

    def generate():
        total_cells = sum(len(seg['cells']) for seg in segments)
        cells_done = 0
        failed_cells = []
        
        # Initial connection check
        if not is_esp32_connected():
            yield f"data: {json.dumps({'event':'connecting','message':'Connecting to ESP32...'})}\n\n"
            if not wait_for_esp32(max_wait=5):
                yield f"data: {json.dumps({'event':'error','message':'ESP32 not connected'})}\n\n"
                return

        for seg_idx, segment in enumerate(segments):
            seg_type = segment['type']
            row = segment['row']
            start_col = segment['startCol']
            end_col = segment['endCol']
            seg_cells = segment['cells']
            
            yield f"data: {json.dumps({'event':'segment_start','type':seg_type,'row':row,'startCol':start_col,'endCol':end_col,'segment':seg_idx+1,'total_segments':len(segments)})}\n\n"
            
            if seg_type == 'continuous':
                # Continuous spray for the segment
                time.sleep(1.0)
                
                yield f"data: {json.dumps({'event':'continuous_spray_start','row':row,'startCol':start_col,'endCol':end_col})}\n\n"
                
                # Start continuous spray
                for attempt in range(SPRAY_RETRY_ATTEMPTS):
                    try:
                        resp = requests.post(f"{ESP32_CONTROL}/spray_start", timeout=CONNECTION_TIMEOUT)
                        if resp.status_code == 200:
                            update_esp32_contact()
                            break
                    except:
                        if attempt < SPRAY_RETRY_ATTEMPTS - 1:
                            wait_for_esp32(max_wait=1)
                
                # Duration based on number of cells
                spray_duration = len(seg_cells) * 1.0  # 1 second per cell
                time.sleep(spray_duration)
                
                # Stop spray
                for attempt in range(3):
                    try:
                        requests.post(f"{ESP32_CONTROL}/spray_stop", timeout=CONNECTION_TIMEOUT)
                        break
                    except:
                        time.sleep(0.2)
                
                yield f"data: {json.dumps({'event':'continuous_spray_stop','row':row,'cells_count':len(seg_cells)})}\n\n"
                
                # Mark all cells as done
                for r, c in seg_cells:
                    cells_done += 1
                    yield f"data: {json.dumps({'event':'done','cell':cells_done,'row':r,'col':c})}\n\n"
                
            else:
                # Precision spray for isolated cells
                for r, c in seg_cells:
                    yield f"data: {json.dumps({'event':'moving','cell':cells_done+1,'total':total_cells,'row':r,'col':c})}\n\n"
                    time.sleep(1.0)
                    
                    yield f"data: {json.dumps({'event':'spraying','cell':cells_done+1,'row':r,'col':c})}\n\n"
                    
                    success, error_msg = send_spray_command(SPRAY_DURATION_MS)
                    
                    if success:
                        time.sleep(SPRAY_DURATION_MS / 1000.0 + 0.2)
                        cells_done += 1
                        yield f"data: {json.dumps({'event':'done','cell':cells_done,'row':r,'col':c})}\n\n"
                    else:
                        failed_cells.append((r, c))
                        yield f"data: {json.dumps({'event':'spray_failed','row':r,'col':c,'error':error_msg})}\n\n"
                        cells_done += 1

        successful = total_cells - len(failed_cells)
        yield f"data: {json.dumps({'event':'complete','total':total_cells,'successful':successful,'failed':len(failed_cells)})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache",
                             "X-Accel-Buffering": "no",
                             "Access-Control-Allow-Origin": "*",
                             "Connection": "keep-alive"})


# ══════════════════════════════════════════════════════════════
#  Debug Routes
# ══════════════════════════════════════════════════════════════

@app.route("/debug/connection_status")
def debug_connection_status():
    """Debug endpoint to check connection state."""
    with _esp32_lock:
        age = time.time() - _last_esp32_contact
        errors = list(_connection_errors)
    
    return jsonify({
        "connected": _esp32_connected,
        "last_contact_age_seconds": round(age, 2),
        "recent_errors": [{"time": t, "error": e} for t, e in errors[-5:]]
    })


# ══════════════════════════════════════════════════════════════
#  Main
# ══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  Autonomous Painting System — Flask Backend (FIXED)")
    print("  VIT Chennai MDP Project")
    print("=" * 60)
    print(f"\n  ESP32-CAM Control: {ESP32_CONTROL}")
    print(f"  ESP32-CAM Stream:  {ESP32_STREAM}")
    print(f"  Grid Size:         {GRID_ROWS} x {GRID_COLS}")
    print(f"  Spray Duration:    {SPRAY_DURATION_MS}ms")
    print(f"  Retry Attempts:    {SPRAY_RETRY_ATTEMPTS}")
    print("\n  Open http://localhost:5000 in your browser")
    print("=" * 60 + "\n")
    
    app.run(host="0.0.0.0", port=5000, debug=True, threaded=True)
