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
  return (
    <MapContainer center={[17.4933, 78.3900]} zoom={13} style={{ height: '100vh', width: '100%' }}>
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
  );
}

export default FloodMap;