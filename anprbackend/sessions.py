from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import VehicleSession, Vehicle, Alert, Detection
import uuid

DUPLICATE_WINDOW_SECONDS = 30
EXTENDED_STAY_HOURS = 8
OPERATIONAL_START = 6
OPERATIONAL_END = 22

def handle_detection(plate: str, camera_id: str, confidence: float, db: Session):
    now = datetime.now()
    actions = []

    recent = db.query(Detection).filter(
        Detection.plate_number == plate,
        Detection.timestamp >= now - timedelta(seconds=DUPLICATE_WINDOW_SECONDS)
    ).first()

    if recent:
        return {"action": "DUPLICATE_SUPPRESSED", "plate": plate}

    detection = Detection(
        id=str(uuid.uuid4()),
        plate_number=plate,
        camera_id=camera_id,
        confidence=confidence,
        timestamp=now
    )
    db.add(detection)

    active_session = db.query(VehicleSession).filter(
        VehicleSession.plate_number == plate,
        VehicleSession.status == "ACTIVE"
    ).first()

    if not active_session:
        session = VehicleSession(
            id=str(uuid.uuid4()),
            plate_number=plate,
            entry_time=now,
            status="ACTIVE",
            camera_id=camera_id
        )
        db.add(session)
        actions.append("SESSION_CREATED")
    else:
        actions.append("SESSION_UPDATED")

    anomalies = check_anomalies(plate, camera_id, now, db)
    actions.extend(anomalies)

    db.commit()
    return {"action": actions, "plate": plate}

def check_anomalies(plate: str, camera_id: str, now: datetime, db: Session) -> list:
    anomalies = []

    vehicle = db.query(Vehicle).filter(Vehicle.plate_number == plate).first()
    if vehicle and vehicle.is_blacklisted:
        recent_alert = db.query(Alert).filter(
            Alert.plate_number == plate,
            Alert.alert_type == "BLACKLIST",
            Alert.timestamp >= now - timedelta(minutes=30)
        ).first()
        if not recent_alert:
            alert = Alert(
                id=str(uuid.uuid4()),
                plate_number=plate,
                alert_type="BLACKLIST",
                severity="CRITICAL",
                message=f"BLACKLISTED VEHICLE {plate} detected at {camera_id}",
                timestamp=now
            )
            db.add(alert)
            anomalies.append("BLACKLIST_ALERT")

    if now.hour < OPERATIONAL_START or now.hour >= OPERATIONAL_END:
        recent_alert = db.query(Alert).filter(
            Alert.plate_number == plate,
            Alert.alert_type == "AFTER_HOURS",
            Alert.timestamp >= now - timedelta(hours=1)
        ).first()
        if not recent_alert:
            alert = Alert(
                id=str(uuid.uuid4()),
                plate_number=plate,
                alert_type="AFTER_HOURS",
                severity="HIGH",
                message=f"After-hours entry: {plate} at {now.strftime('%H:%M')}",
                timestamp=now
            )
            db.add(alert)
            anomalies.append("AFTER_HOURS_ALERT")

    active_session = db.query(VehicleSession).filter(
        VehicleSession.plate_number == plate,
        VehicleSession.status == "ACTIVE"
    ).first()
    if active_session:
        hours_inside = (now - active_session.entry_time).total_seconds() / 3600
        if hours_inside > EXTENDED_STAY_HOURS:
            recent_alert = db.query(Alert).filter(
                Alert.plate_number == plate,
                Alert.alert_type == "EXTENDED_STAY",
                Alert.timestamp >= now - timedelta(hours=2)
            ).first()
            if not recent_alert:
                alert = Alert(
                    id=str(uuid.uuid4()),
                    plate_number=plate,
                    alert_type="EXTENDED_STAY",
                    severity="MEDIUM",
                    message=f"Extended stay: {plate} inside for {hours_inside:.1f} hours",
                    timestamp=now
                )
                db.add(alert)
                anomalies.append("EXTENDED_STAY_ALERT")

    return anomalies

def expire_old_sessions(db: Session, now: datetime):
    """Retained for API compatibility.

    A missing detection is not proof that a vehicle left the site. Sessions are
    therefore closed only by the explicit exit action until exit-camera logic is
    added.
    """
    return None

def get_session_stats(db: Session) -> dict:
    now = datetime.now()
    total_detections = db.query(Detection).count()
    today_detections = db.query(Detection).filter(
        Detection.timestamp >= now.replace(hour=0, minute=0, second=0)
    ).count()
    active_vehicles = db.query(VehicleSession).filter(
        VehicleSession.status == "ACTIVE"
    ).count()
    open_alerts = db.query(Alert).filter(Alert.is_resolved == False).count()
    return {
        "total_detections": total_detections,
        "today_detections": today_detections,
        "active_vehicles": active_vehicles,
        "open_alerts": open_alerts
    }
