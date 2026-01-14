import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard, Datasets, Judges } from './pages';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/datasets" element={<Datasets />} />
        <Route path="/judges" element={<Judges />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
