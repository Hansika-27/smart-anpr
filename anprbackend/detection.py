import cv2
import numpy as np
import re
from datetime import datetime

_yolo_model = None
_ocr_reader = None

def get_yolo():
    global _yolo_model
    if _yolo_model is None:
        from ultralytics import YOLO
        _yolo_model = YOLO('yolov8n.pt')
    return _yolo_model

def get_ocr():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        _ocr_reader = easyocr.Reader(['en'], gpu=False)
    return _ocr_reader

def clean_plate_text(text: str) -> str:
    text = text.upper().replace(" ", "").replace("-", "")
    if len(text) >= 2:
        text = list(text)
        for i in range(min(2, len(text))):
            text[i] = text[i].replace('0', 'O').replace('1', 'I').replace('8', 'B')
        text = ''.join(text)
    text = re.sub(r'[^A-Z0-9]', '', text)
    return text

def is_valid_indian_plate(text: str) -> bool:
    patterns = [
        r'^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$',
        r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{1,4}$',
        r'^BH[0-9]{2}[A-Z]{2}[0-9]{4}$',
    ]
    return any(re.fullmatch(p, text) for p in patterns)

def extract_plate_from_vehicle(frame: np.ndarray, box) -> np.ndarray:
    x1, y1, x2, y2 = map(int, box.xyxy[0])
    vehicle_crop = frame[y1:y2, x1:x2]
    h, w = vehicle_crop.shape[:2]
    plate_region = vehicle_crop[int(h * 0.55):h, int(w * 0.1):int(w * 0.9)]
    return plate_region

def run_ocr_on_plate(plate_img: np.ndarray) -> tuple:
    if plate_img is None or plate_img.size == 0:
        return None, 0.0
    try:
        reader = get_ocr()
        plate_img = cv2.resize(plate_img, (300, 100))
        gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        results = reader.readtext(thresh)
        if not results:
            return None, 0.0
        full_text = ''.join([r[1] for r in results])
        avg_conf = sum([r[2] for r in results]) / len(results)
        cleaned = clean_plate_text(full_text)
        if is_valid_indian_plate(cleaned):
            return cleaned, round(avg_conf * 100, 1)
        return None, 0.0
    except Exception as e:
        print(f"OCR error: {e}")
        return None, 0.0

def detect_from_frame(frame: np.ndarray) -> list:
    model = get_yolo()
    results = []
    detections = model(frame, classes=[2, 3, 5, 7], conf=0.4, verbose=False)
    for result in detections:
        for box in result.boxes:
            plate_img = extract_plate_from_vehicle(frame, box)
            plate_text, confidence = run_ocr_on_plate(plate_img)
            if plate_text and confidence > 40:
                results.append({
                    "plate": plate_text,
                    "confidence": confidence,
                    "timestamp": datetime.now().isoformat()
                })
    return results

def detect_from_image_bytes(image_bytes: bytes) -> list:
    nparr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if frame is None:
        return []
    return detect_from_frame(frame)
