import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard, Datasets, Judges, ScoringConfig } from './pages';
import { TourProvider, Tour } from './components/tour';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <TourProvider>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/datasets" element={<Datasets />} />
          <Route path="/judges" element={<Judges />} />
          <Route path="/scoring-config" element={<ScoringConfig />} />
        </Routes>
        <Tour />
      </TourProvider>
    </BrowserRouter>
  );
}

export default App;
