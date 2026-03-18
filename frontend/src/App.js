import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Link, NavLink, useLocation, useNavigate } from 'react-router-dom';
import Login from './pages/Login';
import Register from './pages/Register';
import Wardrobe from './pages/Wardrobe';
import Recommendations from './pages/Recommendations';
import Search from './pages/Search';
import Profile from './pages/Profile';
import Analytics from './pages/Analytics';
import { outfitAPI, stylistAPI, wardrobeAPI, weatherAPI } from './api';
import './App.css';

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    totalItems: 0,
    categories: 0,
    outfitsGenerated: 0,
    dominantStyle: 'n/a',
    weather: null,
  });
  const [topCategories, setTopCategories] = useState([]);

  useEffect(() => {
    let active = true;
    const loadDashboard = async () => {
      try {
        const [itemsRes, categoriesRes, stylistRes, weatherRes] = await Promise.allSettled([
          wardrobeAPI.getItems(),
          wardrobeAPI.getCategories(),
          stylistAPI.getProfileSummary(),
          weatherAPI.getWeather('Hyderabad'),
        ]);

        if (!active) return;
        const items = itemsRes.status === 'fulfilled' ? itemsRes.value.data || [] : [];
        const categories = categoriesRes.status === 'fulfilled' ? categoriesRes.value.data : null;
        const stylist = stylistRes.status === 'fulfilled' ? stylistRes.value.data || {} : {};
        const weather = weatherRes.status === 'fulfilled' ? weatherRes.value.data || null : null;

        setStats({
          totalItems: items.length,
          categories: categories?.categories?.length || 0,
          outfitsGenerated: stylist?.outfits_count || 0,
          dominantStyle: stylist?.dominant_style || 'n/a',
          weather,
        });
        setTopCategories((stylist?.top_categories || []).slice(0, 4));
      } finally {
        if (active) setLoading(false);
      }
    };

    loadDashboard();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="page dashboard-page">
      <div className="container">
        <div style={{ marginTop: '2.5rem' }}>
          <div className="dashboard-hero">
            <div>
              <h1>Welcome back</h1>
              <p className="dashboard-subtitle">
                Plan outfits faster with AI-assisted organization and smart recommendations.
              </p>
            </div>
            <div className="button-group">
              <Link to="/recommendations?tab=occasions" className="suggest-btn" style={{ textDecoration: 'none' }}>Mix and Match</Link>
              <Link to="/recommendations?tab=color" className="color-suggest-btn" style={{ textDecoration: 'none' }}>Color Harmony</Link>
              <Link to="/recommendations?tab=today" className="weather-suggest-btn" style={{ textDecoration: 'none' }}>Weather Based</Link>
            </div>
          </div>

          <div className="dashboard-stats-grid">
            <div className="dashboard-stat">
              <div className="stat-label">Wardrobe Items</div>
              <div className="stat-value">{loading ? '...' : stats.totalItems}</div>
            </div>
            <div className="dashboard-stat">
              <div className="stat-label">Categories</div>
              <div className="stat-value">{loading ? '...' : stats.categories}</div>
            </div>
            <div className="dashboard-stat">
              <div className="stat-label">Outfits Saved</div>
              <div className="stat-value">{loading ? '...' : stats.outfitsGenerated}</div>
            </div>
            <div className="dashboard-stat">
              <div className="stat-label">Dominant Style</div>
              <div className="stat-value stat-text">{loading ? '...' : stats.dominantStyle}</div>
            </div>
          </div>

          <div className="grid-3" style={{ marginTop: '2rem' }}>
            <Link to="/wardrobe" style={{ textDecoration: 'none' }}>
              <div className="card dashboard-card" style={{ cursor: 'pointer' }}>
                <div className="dashboard-icon">W</div>
                <h2>My Wardrobe</h2>
                <p>Organize items, edit details, and manage categories.</p>
              </div>
            </Link>

            <Link to="/recommendations" style={{ textDecoration: 'none' }}>
              <div className="card dashboard-card" style={{ cursor: 'pointer' }}>
                <div className="dashboard-icon">AI</div>
                <h2>Recommendations</h2>
                <p>Get outfit ideas based on occasion and weather.</p>
              </div>
            </Link>

            <Link to="/search" style={{ textDecoration: 'none' }}>
              <div className="card dashboard-card" style={{ cursor: 'pointer' }}>
                <div className="dashboard-icon">F</div>
                <h2>Search and Filter</h2>
                <p>Find items quickly by color, season, or style.</p>
              </div>
            </Link>
          </div>

          <div className="dashboard-insights">
            <div className="card">
              <h3>Top Categories</h3>
              {loading ? (
                <p>Loading insights...</p>
              ) : topCategories.length ? (
                <div className="chip-row">
                  {topCategories.map((c) => (
                    <span className="insight-chip" key={c.category}>{c.category} ({c.count})</span>
                  ))}
                </div>
              ) : (
                <p>Add wardrobe items to unlock category insights.</p>
              )}
            </div>

            <div className="card">
              <h3>Weather Snapshot</h3>
              {stats.weather ? (
                <div className="weather-mini">
                  <div className="weather-mini-temp">{Math.round(stats.weather.temp)} C</div>
                  <div className="weather-mini-meta">{stats.weather.condition} | {stats.weather.city}</div>
                </div>
              ) : (
                <p>Weather unavailable.</p>
              )}
              <Link to="/recommendations?tab=today" className="btn btn-secondary" style={{ marginTop: '0.7rem', display: 'inline-block' }}>
                Plan Today Look
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function Navigation({ theme, onThemeChange }) {
  const navigate = useNavigate();
  const location = useLocation();
  const username = localStorage.getItem('username');
  const isLoggedIn = !!localStorage.getItem('token');

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userId');
    localStorage.removeItem('username');
    navigate('/login', { replace: true });
  };

  if (!isLoggedIn) return null;

  return (
    <nav>
      <div className="nav-container">
        <div className="nav-brand">StyleSync ✨</div>
        <ul className="nav-links">
          <li><NavLink to="/dashboard" className={location.pathname === '/dashboard' ? 'active' : ''}>Dashboard</NavLink></li>
          <li><NavLink to="/wardrobe" className={location.pathname === '/wardrobe' ? 'active' : ''}>Wardrobe</NavLink></li>
          <li><NavLink to="/recommendations" className={location.pathname === '/recommendations' ? 'active' : ''}>Recommendations</NavLink></li>
          <li><NavLink to="/search" className={location.pathname === '/search' ? 'active' : ''}>Search</NavLink></li>
          <li><NavLink to="/analytics" className={location.pathname === '/analytics' ? 'active' : ''}>Analytics</NavLink></li>
          <li><NavLink to="/profile" className={location.pathname === '/profile' ? 'active' : ''}>Profile</NavLink></li>
        </ul>
        <div className="nav-actions">
          <button 
            className={`theme-toggle ${theme === 'dark-mode' ? 'dark-mode' : ''}`}
            onClick={onThemeChange}
            title="Toggle theme"
          >
            <span></span>
          </button>
          <span className="nav-welcome">Welcome, {username}!</span>
          <button className="logout-btn" onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}

function ProtectedRoute({ children }) {
  const isLoggedIn = !!localStorage.getItem('token');
  return isLoggedIn ? children : <Navigate to="/login" replace />;
}

function PublicRoute({ children }) {
  const isLoggedIn = !!localStorage.getItem('token');
  return isLoggedIn ? <Navigate to="/dashboard" replace /> : children;
}

function AuthHistoryGuard() {
  const location = useLocation();

  useEffect(() => {
    const isLoggedIn = !!localStorage.getItem('token');
    const authPath = location.pathname === '/login' || location.pathname === '/register';
    const protectedPath = ['/dashboard', '/wardrobe', '/recommendations', '/search', '/profile'].includes(location.pathname);

    if (isLoggedIn && authPath) {
      window.history.replaceState(null, '', '/dashboard');
    }
    if (!isLoggedIn && protectedPath) {
      window.history.replaceState(null, '', '/login');
    }
  }, [location.pathname]);

  return null;
}

function App() {
  const [theme, setTheme] = useState('light');

  useEffect(() => {
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    document.documentElement.setAttribute('data-theme', savedTheme);
  }, []);

  const handleThemeChange = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    document.documentElement.setAttribute('data-theme', newTheme);
  };

  return (
    <Router>
      <div className="app">
        <AuthHistoryGuard />
        <Navigation theme={theme} onThemeChange={handleThemeChange} />
        <Routes>
          <Route
            path="/login"
            element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            }
          />
          <Route
            path="/register"
            element={
              <PublicRoute>
                <Register />
              </PublicRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/wardrobe"
            element={
              <ProtectedRoute>
                <Wardrobe />
              </ProtectedRoute>
            }
          />
          <Route
            path="/recommendations"
            element={
              <ProtectedRoute>
                <Recommendations />
              </ProtectedRoute>
            }
          />
          <Route
            path="/search"
            element={
              <ProtectedRoute>
                <Search />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/analytics"
            element={
              <ProtectedRoute>
                <Analytics />
              </ProtectedRoute>
            }
          />
          <Route
            path="/"
            element={
              localStorage.getItem('token')
                ? <Navigate to="/dashboard" replace />
                : <Navigate to="/login" replace />
            }
          />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
