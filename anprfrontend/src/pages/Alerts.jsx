import { useState, useEffect, useCallback } from "react";
import { API } from "../App";

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [showResolved, setShowResolved] = useState(false);

  const fetchAlerts = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/alerts?resolved=${showResolved}`);
      setAlerts(await res.json());
    } catch (e) {
      console.error(e);
    }
  }, [showResolved]);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 5000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const resolveAlert = async (id) => {
    await fetch(`${API}/api/alerts/${id}/resolve`, { method: "PATCH" });
    fetchAlerts();
  };

  const SEVERITY_COLOR = { CRITICAL: "#ff4444", HIGH: "#ff8800", MEDIUM: "#ffcc00" };
  const TYPE_ICON = { BLACKLIST: "🚫", AFTER_HOURS: "🌙", EXTENDED_STAY: "⏰" };
  const criticalAlerts = alerts.filter(a => a.severity === "CRITICAL");

  return (
    <div className="page">
      <div className="page-header">
        <h1 style={{ color: "#ff4444" }}>🚨 Security Alerts</h1>
        <label className="toggle-label">
          <input type="checkbox" checked={showResolved} onChange={e => setShowResolved(e.target.checked)} />
          Show Resolved
        </label>
      </div>

      {criticalAlerts.length > 0 && !showResolved && (
        <div className="critical-banner">
          🚨 {criticalAlerts.length} CRITICAL ALERT{criticalAlerts.length > 1 ? "S" : ""} — IMMEDIATE ACTION REQUIRED
        </div>
      )}

      <div className="card">
        <h2 className="card-title">
          {showResolved ? "Resolved Alerts" : "Open Alerts"}
          <span className="count-badge">{alerts.length}</span>
        </h2>
        {alerts.length === 0 ? (
          <p className="muted">✓ No {showResolved ? "resolved" : "open"} alerts.</p>
        ) : (
          <div className="alert-list">
            {alerts.map(a => (
              <div key={a.id} className="alert-item" style={{ borderLeft: `4px solid ${SEVERITY_COLOR[a.severity] || "#888"}` }}>
                <div className="alert-left">
                  <span className="alert-icon">{TYPE_ICON[a.type] || "⚠️"}</span>
                  <div>
                    <div className="alert-plate">{a.plate}</div>
                    <div className="alert-message">{a.message}</div>
                    <div className="alert-time">{new Date(a.timestamp).toLocaleString()}</div>
                  </div>
                </div>
                <div className="alert-right">
                  <span className="severity-badge" style={{ background: SEVERITY_COLOR[a.severity] || "#888" }}>
                    {a.severity}
                  </span>
                  {!a.resolved && (
                    <button onClick={() => resolveAlert(a.id)} className="btn-resolve">RESOLVE</button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
