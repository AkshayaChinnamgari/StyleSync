import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api';
import '../styles.css';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.login(username, password);
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userId', response.data.user_id);
      localStorage.setItem('username', response.data.username);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid username or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-shell">
        <div className="auth-visual">
          <div className="auth-visual-content">
            <span className="auth-pill">StyleSync</span>
            <h1>Plan better outfits in minutes</h1>
            <p>Organize wardrobe items, create stronger combinations, and stay weather-ready every day.</p>

            <div className="auth-points">
              <div className="auth-point">AI outfit suggestions by occasion</div>
              <div className="auth-point">Virtual try-on for selected top and bottom</div>
              <div className="auth-point">Shopping links for matching pieces</div>
            </div>

            <div className="auth-metrics">
              <div className="auth-metric">
                <strong>5+</strong>
                <span>Feature tabs</span>
              </div>
              <div className="auth-metric">
                <strong>24x7</strong>
                <span>Wardrobe access</span>
              </div>
              <div className="auth-metric">
                <strong>1-click</strong>
                <span>Outfit generation</span>
              </div>
            </div>
          </div>
        </div>

        <div className="auth-panel">
          <div className="auth-card">
            <div className="auth-brand">StyleSync</div>
            <h2>Login</h2>
            <p className="auth-caption">Welcome back. Continue your style planning.</p>

            {error && <div className="alert alert-error">{error}</div>}

            <form onSubmit={handleSubmit}>
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                  disabled={loading}
                  placeholder="Enter username"
                />
              </div>

              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={loading}
                  placeholder="Enter password"
                />
              </div>

              <button type="submit" className="btn btn-primary auth-submit" disabled={loading}>
                {loading ? 'Signing in...' : 'Sign in to Dashboard'}
              </button>
            </form>

            <div className="auth-link">
              Do not have an account? <Link to="/register">Create one</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
