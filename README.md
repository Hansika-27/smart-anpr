# Smart ANPR System — Coal India Limited (MCL)

AI-Powered Vehicle Surveillance & Gate Management Platform built during industrial training at MCL, Lakhanpur Area, Coal India Limited.

## Tech Stack
- **AI/CV**: YOLOv8n + EasyOCR
- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: React + Vite
- **Export**: OpenPyXL (Excel)

## Features
- Real-time vehicle + number plate detection from images
- Automatic session tracking (entry/exit/duration)
- 3 Anomaly detection rules: Blacklist, After-Hours, Extended Stay
- Vehicle registry with blacklist management
- Excel export for all sessions
- Audit log for all actions
- Dark-themed MCL-branded dashboard

## How to Run

### Backend
```bash
cd anprbackend
venv\Scripts\activate
uvicorn main:app --reload --port 8000
```

### Frontend
```bash
cd anprfrontend
npm run dev
```

Open: http://localhost:5173

## Project Structure

smart-anpr/
├── anprbackend/
│ ├── main.py # FastAPI endpoints
│ ├── models.py # Database tables
│ ├── detection.py # YOLOv8 + EasyOCR pipeline
│ └── sessions.py # Session + anomaly logic
└── anprfrontend/
└── src/
├── pages/ # Dashboard, Detect, Sessions, Alerts, Registry
└── App.jsx
