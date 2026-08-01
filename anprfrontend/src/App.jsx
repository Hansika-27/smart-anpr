import { useState, useEffect } from "react";
import { BrowserRouter as Router, Routes, Route, NavLink } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import Detect from "./pages/Detect";
import Sessions from "./pages/Sessions";
import Alerts from "./pages/Alerts";
import Registry from "./pages/Registry";
import "./App.css";

const API = "http://localhost:8000";
export { API };

function Clock() {
  const [time, setTime] = useState(new Date());
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(t);
  }, []);
  return <span>{time.toLocaleTimeString()}</span>;
}

export default function App() {
  const [openAlerts, setOpenAlerts] = useState(0);

  useEffect(() => {
    const fetch_alerts = () => {
      fetch(`${API}/api/alerts?resolved=false`)
        .then(r => r.json())
        .then(data => setOpenAlerts(data.length))
        .catch(() => {});
    };
    fetch_alerts();
    const interval = setInterval(fetch_alerts, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Router>
      <div className="app">
        <header className="header">
          <div className="header-left">
            <div className="logo">⚡ CIL</div>
            <div>
              <span className="title-main">SMART ANPR SYSTEM</span>
              <span className="title-sub">Coal India Limited — MCL Lakhanpur</span>
            </div>
          </div>
          <div className="header-right">
            <span className="system-status">
              <span className="status-dot"></span> SYSTEM ACTIVE
            </span>
            <span className="live-clock"><Clock /></span>
          </div>
        </header>

        <div className="layout">
          <nav className="sidebar">
            <NavLink to="/" end className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              📊 Dashboard
            </NavLink>
            <NavLink to="/detect" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              📷 Detect
            </NavLink>
            <NavLink to="/sessions" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              🚗 Sessions
            </NavLink>
            <NavLink to="/alerts" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              🚨 Alerts {openAlerts > 0 && <span className="badge">{openAlerts}</span>}
            </NavLink>
            <NavLink to="/registry" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
              📋 Registry
            </NavLink>
          </nav>

          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/detect" element={<Detect />} />
              <Route path="/sessions" element={<Sessions />} />
              <Route path="/alerts" element={<Alerts />} />
              <Route path="/registry" element={<Registry />} />
            </Routes>
          </main>
        </div>
      </div>
    </Router>
  );
}