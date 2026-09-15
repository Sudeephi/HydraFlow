import { MapContainer, TileLayer, Polyline, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import roadsData from './data/overpass-roads.json';

// Temporary: assign a realistic-looking risk score per road.
// This simulates our future XGBoost model output until it's trained.
function getFakeRisk(roadId) {
  // Use the road_id to generate a consistent (not random-every-render) fake risk
  let hash = 0;
  for (let i = 0; i < roadId.length; i++) {
    hash = (hash * 31 + roadId.charCodeAt(i)) % 100;
  }
  return hash / 100;
}

function getColor(risk) {
  if (risk >= 0.7) return 'red';
  if (risk >= 0.4) return 'orange';
  return 'green';
}

function FloodMap() {
  // Calculate risk counts for the summary panel
  let highCount = 0, mediumCount = 0, lowCount = 0;

  roadsData.features.forEach((road) => {
    if (!road.geometry || road.geometry.type !== 'LineString') return;
    const roadId = String(road.id || road.properties.id || Math.random());
    const risk = getFakeRisk(roadId);
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
          const risk = getFakeRisk(roadId);
          const name = road.properties.name || 'Unnamed Road';

          return (
            <Polyline
              key={roadId}
              positions={coords}
              color={getColor(risk)}
              weight={4}
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
    </div>
  );
}

export default FloodMap;