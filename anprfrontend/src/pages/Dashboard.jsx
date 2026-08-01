import { useState, useEffect } from "react";
import { API } from "../App";

export default function Dashboard() {
  const [stats, setStats] = useState({ total_detections: 0, today_detections: 0, active_vehicles: 0, open_alerts: 0 });
  const [detections, setDetections] = useState([]);
  const [hourly, setHourly] = useState([]);

  const fetchAll = async () => {
    try {
      const [statsRes, detectRes, hourlyRes] = await Promise.all([
        fetch(`${API}/api/stats`),
        fetch(`${API}/api/detections?limit=12`),
        fetch(`${API}/api/analytics/hourly`)
      ]);
      setStats(await statsRes.json());
      setDetections(await detectRes.json());
      setHourly(await hourlyRes.json());
    } catch (e) {
      console.error("API error", e);
    }
  };

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 5000);
    return () => clearInterval(interval);
  }, []);

  const maxHourly = Math.max(...hourly.map(h => h.count), 1);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Dashboard</h1>
        <span className="refresh-badge">Auto-refresh: 5s</span>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card kpi-teal">
          <div className="kpi-icon">🔍</div>
          <div className="kpi-value">{stats.total_detections}</div>
          <div className="kpi-label">Total Detections</div>
        </div>
        <div className="kpi-card kpi-green">
          <div className="kpi-icon">📅</div>
          <div className="kpi-value">{stats.today_detections}</div>
          <div className="kpi-label">Today</div>
        </div>
        <div className="kpi-card kpi-amber">
          <div className="kpi-icon">🚗</div>
          <div className="kpi-value">{stats.active_vehicles}</div>
          <div className="kpi-label">Active Vehicles</div>
        </div>
        <div className="kpi-card kpi-red">
          <div className="kpi-icon">🚨</div>
          <div className="kpi-value">{stats.open_alerts}</div>
          <div className="kpi-label">Open Alerts</div>
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">24-Hour Detection Activity</h2>
        <div className="bar-chart">
          {hourly.map(h => (
            <div key={h.hour} className="bar-col">
              <div className="bar" style={{ height: `${(h.count / maxHourly) * 100}%` }} title={`${h.count} detections`} />
              <span className="bar-label">{h.hour}h</span>
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <h2 className="card-title">Recent Detections</h2>
        {detections.length === 0 ? (
          <p className="muted">No detections yet. Go to Detect page to start.</p>
        ) : (
          <div className="detection-grid">
            {detections.map(d => (
              <div key={d.id} className="detection-card">
                <div className="plate-number">{d.plate}</div>
                <div className="detection-meta">
                  <span className="conf-badge">{d.confidence}%</span>
                  <span className="camera-badge">{d.camera}</span>
                </div>
                <div className="detection-time">{new Date(d.timestamp).toLocaleTimeString()}</div>
                <div className="anpr-verified">✓ ANPR VERIFIED</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}