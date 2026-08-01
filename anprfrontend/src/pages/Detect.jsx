import { useState } from "react";
import { API } from "../App";

export default function Detect() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [manualPlate, setManualPlate] = useState("");
  const [manualCamera, setManualCamera] = useState("CAM-1");
  const [preview, setPreview] = useState(null);
  const [message, setMessage] = useState("");

  const handleImageUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setPreview(URL.createObjectURL(file));
    setLoading(true);
    setMessage("");
    const formData = new FormData();
    formData.append("file", file);
    formData.append("camera_id", manualCamera);
    try {
      const res = await fetch(`${API}/api/detect/upload`, { method: "POST", body: formData });
      if (!res.ok) throw new Error("Detection request failed");
      const data = await res.json();
      setResults(data.detections || []);
      if (data.count === 0) setMessage("No plates detected. Try a clearer image.");
    } catch (e) {
      setMessage(e.message || "Error connecting to backend.");
    } finally {
      setLoading(false);
    }
  };

  const handleManualDetect = async () => {
    if (!manualPlate.trim()) return;
    setLoading(true);
    setMessage("");
    try {
      const res = await fetch(`${API}/api/detect/manual`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ plate_number: manualPlate.toUpperCase(), camera_id: manualCamera, confidence: 95.0 }),
      });
      if (!res.ok) {
        const error = await res.json();
        throw new Error(error.detail || "Detection request failed");
      }
      const data = await res.json();
      setMessage(`✓ Plate ${manualPlate.toUpperCase()} logged. Action: ${JSON.stringify(data.action)}`);
      setManualPlate("");
    } catch (e) {
      setMessage(e.message || "Error connecting to backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page">
      <div className="page-header"><h1>Vehicle Detection</h1></div>
      <div className="detect-grid">
        <div className="card">
          <h2 className="card-title">📷 Upload Vehicle Image</h2>
          <p className="muted">Upload a photo to detect number plate automatically.</p>
          <div className="upload-zone">
            <input type="file" accept="image/*" onChange={handleImageUpload} id="img-upload" style={{ display: "none" }} />
            <label htmlFor="img-upload" className="upload-btn">
              {loading ? "⏳ Detecting..." : "📁 Choose Image"}
            </label>
          </div>
          <div className="camera-select">
            <label>Camera:</label>
            <select value={manualCamera} onChange={e => setManualCamera(e.target.value)}>
              <option>CAM-1</option>
              <option>CAM-2</option>
              <option>CAM-SERVICE</option>
            </select>
          </div>
          {preview && <img src={preview} alt="preview" className="preview-img" />}
          {results.length > 0 && (
            <div className="results-list">
              <h3>Results:</h3>
              {results.map((r, i) => (
                <div key={i} className="result-item">
                  <span className="plate-number">{r.plate}</span>
                  <span className="conf-badge">{r.confidence}%</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="card-title">⌨️ Manual Plate Entry</h2>
          <p className="muted">Manually enter a plate number for testing or manual logging.</p>
          <div className="manual-form">
            <input
              type="text"
              placeholder="e.g. MH12AB1234"
              value={manualPlate}
              onChange={e => setManualPlate(e.target.value.toUpperCase())}
              className="plate-input"
              maxLength={11}
            />
            <select value={manualCamera} onChange={e => setManualCamera(e.target.value)}>
              <option>CAM-1</option>
              <option>CAM-2</option>
              <option>CAM-SERVICE</option>
            </select>
            <button onClick={handleManualDetect} disabled={loading || !manualPlate.trim()} className="btn-primary">
              {loading ? "Processing..." : "Log Detection"}
            </button>
          </div>
          {message && <div className={`message ${message.startsWith("✓") ? "success" : "error"}`}>{message}</div>}
          <div className="tips">
            <h3>Indian Plate Formats:</h3>
            <ul>
              <li>Standard: <code>MH12AB1234</code></li>
              <li>Odisha: <code>OD02AB1234</code></li>
              <li>BH Series: <code>BH01AB1234</code></li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
