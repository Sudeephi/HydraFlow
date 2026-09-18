import { useState, useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const API_BASE = 'http://127.0.0.1:8000';

function getColor(risk) {
  if (risk >= 0.7) return 'red';
  if (risk >= 0.4) return 'orange';
  return 'green';
}

function getOnsetWindow(risk) {
  if (risk >= 0.7) return '20–45 min';
  if (risk >= 0.4) return '45–90 min';
  return '2–3 hrs';
}


function FloodMap() {
  const [hour, setHour] = useState(0);
  const [selectedRoad, setSelectedRoad] = useState(null);
  const [roadsData, setRoadsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isReplaying, setIsReplaying] = useState(false);

  const [preloadedData, setPreloadedData] = useState(null);
  
  useEffect(() => {
  let isCurrent = true; // guards against stale responses

  setLoading(true);
  setError(null);
  fetch(`${API_BASE}/nowcast?hour=${hour}`)
    .then((res) => {
      if (!res.ok) throw new Error('Backend request failed');
      return res.json();
    })
    .then((data) => {
      if (isCurrent) {
        setRoadsData(data);
        setLoading(false);
      }
    })
    .catch((err) => {
      if (isCurrent) {
        console.error(err);
        setError('Could not connect to backend. Is it running?');
        setLoading(false);
      }
    });

  return () => {
    isCurrent = false; // runs when hour changes again before this fetch finishes
  };
}, [hour]);

 useEffect(() => {
  if (!isReplaying || !preloadedData) return;

  const interval = setInterval(() => {
    setHour((prevHour) => {
      const nextHour = prevHour + 1;
      if (nextHour > 3) {
        setIsReplaying(false);
        setPreloadedData(null);
        return prevHour;
      }
      setRoadsData(preloadedData[nextHour]); // instant swap, no fetch delay
      return nextHour;
    });
  }, 1500);

  return () => clearInterval(interval);
}, [isReplaying, preloadedData]);

 useEffect(() => {
  if (preloadedData) {
    setRoadsData(preloadedData[0]);
  }
}, [preloadedData]);

  if (loading && !roadsData) {
    return <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Loading roads...</div>;
  }

  if (error) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'red', flexDirection: 'column', gap: '8px' }}>
        <div>{error}</div>
        <div style={{ fontSize: '13px', color: '#666' }}>
          Make sure the backend is running: <code>python -m uvicorn main:app --reload</code>
        </div>
      </div>
    );
  }

  let highCount = 0, mediumCount = 0, lowCount = 0;
  roadsData.features.forEach((road) => {
    const risk = road.properties.risk;
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
          const roadId = road.properties.road_id;
          const risk = road.properties.risk;
          const name = road.properties.name || 'Unnamed Road';

          return (
            <Polyline
              key={`${roadId}-${hour}`}
              positions={coords}
              color={getColor(risk)}
              weight={4}
              eventHandlers={{
                click: () => setSelectedRoad({ roadId, name, risk, confidence: road.properties.confidence }),
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
        <button
          className="replay-btn"
          onClick={async () => {
            setIsReplaying(true);
            setHour(0);

            // Pre-fetch all 4 hours before starting the animation
          try {
            const results = await Promise.all(
              [0, 1, 2, 3].map((h) =>
                fetch(`${API_BASE}/nowcast?hour=${h}`).then((res) => res.json())
              )
            );
            setPreloadedData(results);
          } catch (err) {
            console.error('Preload failed', err);
            setIsReplaying(false);
          }
        }}
          disabled={isReplaying}
        >
          {isReplaying ? 'Replaying Storm...' : '▶ Replay Historical Storm'}
        </button>
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
            <b>{selectedRoad.confidence}%</b>
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