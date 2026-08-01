import { useState, useEffect } from "react";
import { API } from "../App";

export default function Registry() {
  const [vehicles, setVehicles] = useState([]);
  const [form, setForm] = useState({ plate_number: "", owner_name: "", vehicle_type: "", is_blacklisted: false });
  const [filter, setFilter] = useState("");
  const [message, setMessage] = useState("");

  const fetchVehicles = async () => {
    const res = await fetch(`${API}/api/vehicles`);
    if (!res.ok) throw new Error("Could not load vehicles");
    setVehicles(await res.json());
  };

  useEffect(() => { fetchVehicles(); }, []);

  const handleSubmit = async () => {
    if (!form.plate_number.trim()) return;
    const res = await fetch(`${API}/api/vehicles`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, plate_number: form.plate_number.toUpperCase() }),
    });
    if (!res.ok) {
      const error = await res.json();
      setMessage(error.detail || "Could not register vehicle");
      return;
    }
    const data = await res.json();
    setMessage(`✓ ${data.message}`);
    setForm({ plate_number: "", owner_name: "", vehicle_type: "", is_blacklisted: false });
    fetchVehicles();
    setTimeout(() => setMessage(""), 3000);
  };

  const toggleBlacklist = async (plate) => {
    const res = await fetch(`${API}/api/vehicles/${plate}/blacklist`, { method: "PATCH" });
    if (res.ok) fetchVehicles();
  };

  const deleteVehicle = async (plate) => {
    if (!window.confirm(`Remove ${plate}?`)) return;
    const res = await fetch(`${API}/api/vehicles/${plate}`, { method: "DELETE" });
    if (res.ok) fetchVehicles();
  };

  const filtered = vehicles.filter(v =>
    v.plate.toLowerCase().includes(filter.toLowerCase()) ||
    (v.owner && v.owner.toLowerCase().includes(filter.toLowerCase()))
  );

  return (
    <div className="page">
      <div className="page-header"><h1>Vehicle Registry</h1></div>
      <div className="registry-grid">
        <div className="card">
          <h2 className="card-title">➕ Register Vehicle</h2>
          <div className="form-group">
            <label>Plate Number *</label>
            <input type="text" placeholder="e.g. OD02AB1234" value={form.plate_number}
              onChange={e => setForm({ ...form, plate_number: e.target.value.toUpperCase() })} className="form-input" />
          </div>
          <div className="form-group">
            <label>Owner Name</label>
            <input type="text" placeholder="Owner name" value={form.owner_name}
              onChange={e => setForm({ ...form, owner_name: e.target.value })} className="form-input" />
          </div>
          <div className="form-group">
            <label>Vehicle Type</label>
            <select value={form.vehicle_type} onChange={e => setForm({ ...form, vehicle_type: e.target.value })} className="form-input">
              <option value="">Select type</option>
              <option>Car</option>
              <option>Truck</option>
              <option>Dumper</option>
              <option>Tipper</option>
              <option>Bus</option>
              <option>Motorcycle</option>
            </select>
          </div>
          <div className="form-group checkbox-group">
            <input type="checkbox" id="blacklist" checked={form.is_blacklisted}
              onChange={e => setForm({ ...form, is_blacklisted: e.target.checked })} />
            <label htmlFor="blacklist" style={{ color: form.is_blacklisted ? "#ff4444" : "inherit" }}>
              🚫 Add to Blacklist
            </label>
          </div>
          <button onClick={handleSubmit} className="btn-primary" style={{ width: "100%" }}>Register Vehicle</button>
          {message && <div className="message success">{message}</div>}
        </div>

        <div className="card">
          <h2 className="card-title">Registered Vehicles <span className="count-badge">{vehicles.length}</span></h2>
          <input type="text" placeholder="Search by plate or owner..." value={filter}
            onChange={e => setFilter(e.target.value)} className="search-input" />
          {filtered.length === 0 ? (
            <p className="muted">No vehicles found.</p>
          ) : (
            <div className="vehicle-list">
              {filtered.map(v => (
                <div key={v.plate} className={`vehicle-item ${v.blacklisted ? "blacklisted" : ""}`}>
                  <div className="vehicle-left">
                    <span className="plate-number-sm">{v.plate}</span>
                    {v.blacklisted && <span className="blacklist-tag">🚫 BLACKLISTED</span>}
                    <div className="vehicle-meta">
                      {v.owner && <span>{v.owner}</span>}
                      {v.type && <span>• {v.type}</span>}
                    </div>
                  </div>
                  <div className="vehicle-actions">
                    <button onClick={() => toggleBlacklist(v.plate)} className={v.blacklisted ? "btn-unblacklist" : "btn-blacklist"}>
                      {v.blacklisted ? "Unblacklist" : "Blacklist"}
                    </button>
                    <button onClick={() => deleteVehicle(v.plate)} className="btn-delete">🗑</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
