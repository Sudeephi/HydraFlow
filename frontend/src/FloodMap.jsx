import { useState } from 'react';
import { MapContainer, TileLayer, Polyline, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import roadsData from './data/overpass-roads.json';

function getBaseFakeRisk(roadId) {
  let hash = 0;
  for (let i = 0; i < roadId.length; i++) {
    hash = (hash * 31 + roadId.charCodeAt(i)) % 100;
  }
  return hash / 100;
}

function getRiskAtHour(baseRisk, hour) {
  const growthFactor = 1 + (hour * 0.15) * baseRisk;
  return Math.min(baseRisk * growthFactor, 1);
}

function getColor(risk) {
  if (risk >= 0.7) return 'red';
  if (risk >= 0.4) return 'orange';
  return 'green';
}

// Fake onset window + confidence, derived consistently from risk
function getOnsetWindow(risk) {
  if (risk >= 0.7) return '20–45 min';
  if (risk >= 0.4) return '45–90 min';
  return '2–3 hrs';
}

function getConfidence(roadId) {
  let hash = 0;
  for (let i = 0; i < roadId.length; i++) {
    hash = (hash * 17 + roadId.charCodeAt(i)) % 100;
  }
  return 60 + (hash % 35); // fake range 60-94%
}

function FloodMap() {
  const [hour, setHour] = useState(0);
  const [selectedRoad, setSelectedRoad] = useState(null);

  let highCount = 0, mediumCount = 0, lowCount = 0;

  roadsData.features.forEach((road) => {
    if (!road.geometry || road.geometry.type !== 'LineString') return;
    const roadId = String(road.id || road.properties.id || Math.random());
    const risk = getRiskAtHour(getBaseFakeRisk(roadId), hour);
    if (risk >= 0.7) highCount++;
    else if (risk >= 0.4) mediumCount++;
    else lowCount++;
  });

  return (
    <div style={{ position: 'relative', flex: 1, display: 'flex' }}>
      <div className="summary-panel">
        <div className="summary-item high">
          <span className="summary-count">{highCount}</span>
          <span className="summary-label">High Risk</span>
        </div>
        <div className="summary-item medium">
          <span className="summary-count">{mediumCount}</span>
          <span className="summary-label">Medium Risk</span>
        </div>
        <div className="summary-item low">
          <span className="summary-count">{lowCount}</span>
          <span className="summary-label">Low Risk</span>
        </div>
      </div>

      <MapContainer center={[17.4933, 78.3900]} zoom={13} style={{ flex: 1, width: '100%' }}>
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; OpenStreetMap contributors'
        />
        {roadsData.features.map((road) => {
          if (!road.geometry || road.geometry.type !== 'LineString') return null;

          const coords = road.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
          const roadId = String(road.id || road.properties.id || Math.random());
          const risk = getRiskAtHour(getBaseFakeRisk(roadId), hour);
          const name = road.properties.name || 'Unnamed Road';

          return (
            <Polyline
              key={roadId}
              positions={coords}
              color={getColor(risk)}
              weight={4}
              eventHandlers={{
                click: () => setSelectedRoad({ roadId, name, risk }),
              }}
            >
              <Popup>
                <b>{name}</b><br />
                Risk: {(risk * 100).toFixed(0)}%
              </Popup>
            </Polyline>
          );
        })}
      </MapContainer>

      <div className="legend">
        <h4>Flood Risk</h4>
        <div><span className="dot red"></span> High (70%+)</div>
        <div><span className="dot orange"></span> Medium (40–69%)</div>
        <div><span className="dot green"></span> Low (&lt;40%)</div>
      </div>

      <div className="timeline-panel">
        <div className="timeline-label">
          Nowcast: <b>+{hour} hour{hour !== 1 ? 's' : ''}</b>
        </div>
        <input
          type="range"
          min="0"
          max="3"
          step="1"
          value={hour}
          onChange={(e) => setHour(Number(e.target.value))}
          className="timeline-slider"
        />
        <div className="timeline-ticks">
          <span>Now</span>
          <span>+1h</span>
          <span>+2h</span>
          <span>+3h</span>
        </div>
      </div>

      {selectedRoad && (
        <div className="detail-panel">
          <button className="close-btn" onClick={() => setSelectedRoad(null)}>×</button>
          <h3>{selectedRoad.name}</h3>
          <div className="detail-risk" style={{ color: getColor(selectedRoad.risk) }}>
            {(selectedRoad.risk * 100).toFixed(0)}% Flood Probability
          </div>
          <div className="detail-row">
            <span>Onset Window</span>
            <b>{getOnsetWindow(selectedRoad.risk)}</b>
          </div>
          <div className="detail-row">
            <span>Confidence</span>
            <b>{getConfidence(selectedRoad.roadId)}%</b>
          </div>
          <div className="detail-row">
            <span>Risk Level</span>
            <b style={{ color: getColor(selectedRoad.risk), textTransform: 'capitalize' }}>
              {selectedRoad.risk >= 0.7 ? 'High' : selectedRoad.risk >= 0.4 ? 'Medium' : 'Low'}
            </b>
          </div>
        </div>
      )}
    </div>
  );
}

export default FloodMap;