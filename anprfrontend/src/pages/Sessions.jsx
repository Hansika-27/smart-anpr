import { useState, useEffect, useCallback } from "react";
import { API } from "../App";

export default function Sessions() {
  const [tab, setTab] = useState("ACTIVE");
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchSessions = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/sessions?status=${tab}`);
      if (!res.ok) throw new Error("Could not load sessions");
      setSessions(await res.json());
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    setLoading(true);
    fetchSessions();
    const interval = setInterval(fetchSessions, 5000);
    return () => clearInterval(interval);
  }, [fetchSessions]);

  const markExited = async (id) => {
    try {
      const res = await fetch(`${API}/api/sessions/${id}/exit`, { method: "PATCH" });
      if (!res.ok) throw new Error("Could not mark the session as exited");
      fetchSessions();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <h1>Vehicle Sessions</h1>
        <button onClick={() => window.open(`${API}/api/sessions/export`, "_blank")} className="btn-export">
          📥 Export XLSX
        </button>
      </div>

      <div className="tab-bar">
        <button className={tab === "ACTIVE" ? "tab active" : "tab"} onClick={() => setTab("ACTIVE")}>Active Vehicles</button>
        <button className={tab === "EXITED" ? "tab active" : "tab"} onClick={() => setTab("EXITED")}>Exited Vehicles</button>
      </div>

      <div className="card">
        {loading ? (
          <p className="muted">Loading...</p>
        ) : sessions.length === 0 ? (
          <p className="muted">No {tab.toLowerCase()} sessions found.</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Plate</th>
                <th>Entry Time</th>
                <th>Exit Time</th>
                <th>Duration</th>
                <th>Camera</th>
                <th>Status</th>
                {tab === "ACTIVE" && <th>Action</th>}
              </tr>
            </thead>
            <tbody>
              {sessions.map(s => (
                <tr key={s.id}>
                  <td><span className="plate-number-sm">{s.plate}</span></td>
                  <td>{new Date(s.entry_time).toLocaleString()}</td>
                  <td>{s.exit_time ? new Date(s.exit_time).toLocaleString() : <span className="muted">Still inside</span>}</td>
                  <td>{s.duration_minutes ? `${s.duration_minutes} min` : "—"}</td>
                  <td>{s.camera}</td>
                  <td>
                    <span className={`status-badge ${s.status === "ACTIVE" ? "badge-green" : "badge-gray"}`}>
                      {s.status}
                    </span>
                  </td>
                  {tab === "ACTIVE" && (
                    <td><button onClick={() => markExited(s.id)} className="btn-small">Mark Exited</button></td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
