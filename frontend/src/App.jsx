import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/Navbar';
import PopmeltBadge from './components/PopmeltBadge';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Favorites from './pages/Favorites';
import Watchlist from './pages/Watchlist';
import Recommendations from './pages/Recommendations';
import BasedOn from './pages/BasedOn';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="min-h-screen bg-background">
          <Navbar />
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/favorites" element={<Favorites />} />
            <Route path="/watchlist" element={<Watchlist />} />
            <Route path="/recommendations" element={<Recommendations />} />
            <Route path="/based-on" element={<BasedOn />} />
          </Routes>
          <PopmeltBadge />
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;