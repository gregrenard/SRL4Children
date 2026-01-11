import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Dashboard, Datasets } from './pages';
import './index.css';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/datasets" element={<Datasets />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
