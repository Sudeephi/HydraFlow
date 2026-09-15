import FloodMap from './FloodMap';
import './App.css';

function App() {
  return (
    <div className="app-container">
      <header className="app-header">
        <h1>🌊 HydraFlow</h1>
        <p>Urban Flood Nowcasting — Kukatpally-Hafeezpet, Hyderabad</p>
      </header>
      <FloodMap />
    </div>
  );
}

export default App;