from fastapi import FastAPI, BackgroundTasks, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
import os
import tempfile
import uuid

from models import get_db, Detection, VehicleSession, Vehicle, Alert, AuditLog
from detection import clean_plate_text, detect_from_image_bytes, is_valid_indian_plate
from sessions import handle_detection, get_session_stats

app = FastAPI(title="Smart ANPR System - MCL Coal India", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class VehicleCreate(BaseModel):
    plate_number: str
    owner_name: Optional[str] = None
    vehicle_type: Optional[str] = None
    is_blacklisted: bool = False

class ManualDetection(BaseModel):
    plate_number: str
    camera_id: str = "CAM-1"
    confidence: float = Field(default=95.0, ge=0, le=100)

VALID_CAMERA_IDS = {"CAM-1", "CAM-2", "CAM-SERVICE"}

def normalise_and_validate_plate(plate_number: str) -> str:
    plate = clean_plate_text(plate_number)
    if not is_valid_indian_plate(plate):
        raise HTTPException(status_code=422, detail="Invalid Indian vehicle registration number")
    return plate

def validate_camera_id(camera_id: str) -> str:
    if camera_id not in VALID_CAMERA_IDS:
        raise HTTPException(status_code=422, detail="Invalid camera ID")
    return camera_id

@app.post("/api/detect/upload")
async def detect_from_upload(
    file: UploadFile = File(...),
    camera_id: str = "CAM-1",
    db: Session = Depends(get_db)
):
    validate_camera_id(camera_id)
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Only image uploads are supported")
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=422, detail="Uploaded image is empty")
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Image must be 10 MB or smaller")
    results = detect_from_image_bytes(image_bytes)
    processed = []
    for r in results:
        result = handle_detection(r["plate"], camera_id, r["confidence"], db)
        processed.append({**r, "session_action": result["action"]})
    return {"detections": processed, "count": len(processed)}

@app.post("/api/detect/manual")
def manual_detection(data: ManualDetection, db: Session = Depends(get_db)):
    plate = normalise_and_validate_plate(data.plate_number)
    validate_camera_id(data.camera_id)
    result = handle_detection(plate, data.camera_id, data.confidence, db)
    log = AuditLog(id=str(uuid.uuid4()), action="MANUAL_DETECTION", resource=plate)
    db.add(log)
    db.commit()
    return result

@app.get("/api/detections")
def get_detections(limit: int = 50, plate: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Detection).order_by(desc(Detection.timestamp))
    if plate:
        query = query.filter(Detection.plate_number.contains(plate.upper()))
    detections = query.limit(limit).all()
    return [{"id": d.id, "plate": d.plate_number, "camera": d.camera_id,
             "confidence": d.confidence, "timestamp": d.timestamp.isoformat()} for d in detections]

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    return get_session_stats(db)

@app.get("/api/sessions")
def get_sessions(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(VehicleSession).order_by(desc(VehicleSession.entry_time))
    if status:
        query = query.filter(VehicleSession.status == status.upper())
    sessions = query.limit(100).all()
    return [{"id": s.id, "plate": s.plate_number, "entry_time": s.entry_time.isoformat(),
             "exit_time": s.exit_time.isoformat() if s.exit_time else None,
             "duration_minutes": s.duration_minutes, "status": s.status,
             "camera": s.camera_id} for s in sessions]

@app.get("/api/sessions/active")
def get_active_sessions(db: Session = Depends(get_db)):
    sessions = db.query(VehicleSession).filter(
        VehicleSession.status == "ACTIVE"
    ).order_by(desc(VehicleSession.entry_time)).all()
    now = datetime.now()
    return [{"plate": s.plate_number, "entry_time": s.entry_time.isoformat(),
             "duration_minutes": round((now - s.entry_time).total_seconds() / 60, 1),
             "camera": s.camera_id} for s in sessions]

@app.patch("/api/sessions/{session_id}/exit")
def mark_session_exited(session_id: str, db: Session = Depends(get_db)):
    session = db.query(VehicleSession).filter(VehicleSession.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status == "EXITED":
        raise HTTPException(status_code=409, detail="Session has already been marked as exited")
    now = datetime.now()
    session.status = "EXITED"
    session.exit_time = now
    session.duration_minutes = round((now - session.entry_time).total_seconds() / 60, 1)
    db.add(AuditLog(id=str(uuid.uuid4()), action="SESSION_EXITED", resource=session.plate_number))
    db.commit()
    return {"message": "Session marked as exited"}

@app.get("/api/sessions/export")
def export_sessions(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    from openpyxl import Workbook
    sessions = db.query(VehicleSession).order_by(desc(VehicleSession.entry_time)).all()
    wb = Workbook()
    ws = wb.active
    ws.title = "Vehicle Sessions"
    ws.append(["Plate Number", "Entry Time", "Exit Time", "Duration (min)", "Status", "Camera"])
    for s in sessions:
        ws.append([s.plate_number,
                   s.entry_time.strftime("%Y-%m-%d %H:%M:%S") if s.entry_time else "",
                   s.exit_time.strftime("%Y-%m-%d %H:%M:%S") if s.exit_time else "Still Inside",
                   s.duration_minutes or "", s.status, s.camera_id])
    file_descriptor, filepath = tempfile.mkstemp(prefix="anpr_sessions_", suffix=".xlsx")
    os.close(file_descriptor)
    wb.save(filepath)
    log = AuditLog(id=str(uuid.uuid4()), action="SESSION_EXPORT", resource="all_sessions")
    db.add(log)
    db.commit()
    background_tasks.add_task(os.unlink, filepath)
    return FileResponse(filepath, filename="MCL_ANPR_Sessions.xlsx")

@app.get("/api/vehicles")
def get_vehicles(db: Session = Depends(get_db)):
    vehicles = db.query(Vehicle).all()
    return [{"plate": v.plate_number, "owner": v.owner_name, "type": v.vehicle_type,
             "blacklisted": v.is_blacklisted, "registered": v.registered_at.isoformat()} for v in vehicles]

@app.post("/api/vehicles")
def register_vehicle(data: VehicleCreate, db: Session = Depends(get_db)):
    plate = normalise_and_validate_plate(data.plate_number)
    existing = db.query(Vehicle).filter(Vehicle.plate_number == plate).first()
    if existing:
        existing.owner_name = data.owner_name
        existing.vehicle_type = data.vehicle_type
        existing.is_blacklisted = data.is_blacklisted
        db.add(AuditLog(id=str(uuid.uuid4()), action="VEHICLE_UPDATED", resource=plate))
        db.commit()
        return {"message": "Vehicle updated", "plate": plate}
    vehicle = Vehicle(plate_number=plate, owner_name=data.owner_name,
                      vehicle_type=data.vehicle_type, is_blacklisted=data.is_blacklisted)
    db.add(vehicle)
    log = AuditLog(id=str(uuid.uuid4()), action="VEHICLE_REGISTERED", resource=plate)
    db.add(log)
    db.commit()
    return {"message": "Vehicle registered", "plate": plate}

@app.patch("/api/vehicles/{plate}/blacklist")
def toggle_blacklist(plate: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.plate_number == plate.upper()).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    vehicle.is_blacklisted = not vehicle.is_blacklisted
    log = AuditLog(id=str(uuid.uuid4()), action="BLACKLIST_TOGGLE", resource=plate)
    db.add(log)
    db.commit()
    return {"plate": plate, "blacklisted": vehicle.is_blacklisted}

@app.delete("/api/vehicles/{plate}")
def delete_vehicle(plate: str, db: Session = Depends(get_db)):
    vehicle = db.query(Vehicle).filter(Vehicle.plate_number == plate.upper()).first()
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    db.delete(vehicle)
    db.add(AuditLog(id=str(uuid.uuid4()), action="VEHICLE_DELETED", resource=plate.upper()))
    db.commit()
    return {"message": f"{plate} removed from registry"}

@app.get("/api/alerts")
def get_alerts(resolved: bool = False, db: Session = Depends(get_db)):
    alerts = db.query(Alert).filter(
        Alert.is_resolved == resolved
    ).order_by(desc(Alert.timestamp)).limit(50).all()
    return [{"id": a.id, "plate": a.plate_number, "type": a.alert_type,
             "severity": a.severity, "message": a.message,
             "timestamp": a.timestamp.isoformat(), "resolved": a.is_resolved} for a in alerts]

@app.patch("/api/alerts/{alert_id}/resolve")
def resolve_alert(alert_id: str, db: Session = Depends(get_db)):
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.is_resolved = True
    db.add(AuditLog(id=str(uuid.uuid4()), action="ALERT_RESOLVED", resource=alert.plate_number))
    db.commit()
    return {"message": "Alert resolved"}

@app.get("/api/audit")
def get_audit_logs(db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(desc(AuditLog.timestamp)).limit(100).all()
    return [{"id": l.id, "action": l.action, "resource": l.resource,
             "timestamp": l.timestamp.isoformat()} for l in logs]

@app.get("/api/analytics/hourly")
def hourly_detections(db: Session = Depends(get_db)):
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    detections = db.query(Detection).filter(Detection.timestamp >= today).all()
    hourly = {i: 0 for i in range(24)}
    for d in detections:
        hourly[d.timestamp.hour] += 1
    return [{"hour": h, "count": c} for h, c in hourly.items()]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
