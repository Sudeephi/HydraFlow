import { MapContainer, TileLayer, Polyline, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import roadsData from './data/roads.json';

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
        const coords = road.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
        return (
          <Polyline
            key={road.properties.road_id}
            positions={coords}
            color={getColor(road.properties.risk)}
            weight={5}
          >
            <Popup>
              <b>{road.properties.name}</b><br />
              Risk: {(road.properties.risk * 100).toFixed(0)}%
            </Popup>
          </Polyline>
        );
      })}
    </MapContainer>
  );
}

export default FloodMap;