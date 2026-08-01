from sqlalchemy import create_engine, Column, String, Float, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import uuid

SQLALCHEMY_DATABASE_URL = "sqlite:///./smart_anpr.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Detection(Base):
    __tablename__ = "detections"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plate_number = Column(String, index=True)
    camera_id = Column(String, default="CAM-1")
    confidence = Column(Float)
    timestamp = Column(DateTime, default=datetime.now)

class VehicleSession(Base):
    __tablename__ = "vehicle_sessions"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plate_number = Column(String, index=True)
    entry_time = Column(DateTime, default=datetime.now)
    exit_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Float, nullable=True)
    status = Column(String, default="ACTIVE")
    camera_id = Column(String, default="CAM-1")

class Vehicle(Base):
    __tablename__ = "vehicles"
    plate_number = Column(String, primary_key=True)
    owner_name = Column(String, nullable=True)
    vehicle_type = Column(String, nullable=True)
    is_blacklisted = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=datetime.now)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    plate_number = Column(String)
    alert_type = Column(String)
    severity = Column(String, default="CRITICAL")
    message = Column(String)
    timestamp = Column(DateTime, default=datetime.now)
    is_resolved = Column(Boolean, default=False)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(String)
    resource = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.now)

Base.metadata.create_all(bind=engine)