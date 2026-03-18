import React, { useMemo, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api';
import '../styles.css';

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const passwordStrength = useMemo(() => {
    const checks = [password.length >= 8, /[A-Z]/.test(password), /[0-9]/.test(password), /[^A-Za-z0-9]/.test(password)];
    const score = checks.filter(Boolean).length;
    if (!password) return { label: 'Not set', score: 0 };
    if (score <= 1) return { label: 'Weak', score: 1 };
    if (score <= 2) return { label: 'Fair', score: 2 };
    if (score === 3) return { label: 'Good', score: 3 };
    return { label: 'Strong', score: 4 };
  }, [password]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);

    try {
      const response = await authAPI.register(username, email, password);
      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('userId', response.data.user_id);
      localStorage.setItem('username', response.data.username);
      navigate('/dashboard', { replace: true });
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-shell">
        <div className="auth-visual auth-visual-register">
          <div className="auth-visual-content">
            <span className="auth-pill">Create Profile</span>
            <h1>Start your personal virtual stylist</h1>
            <p>Upload wardrobe items, track outfit history, and get personalized suggestions every day.</p>

            <div className="auth-points">
              <div className="auth-point">Smart category and style management</div>
              <div className="auth-point">Color harmony with matching outfit ideas</div>
              <div className="auth-point">Try-on preview for realistic combinations</div>
            </div>

            <div className="auth-metrics">
              <div className="auth-metric">
                <strong>Fast</strong>
                <span>Onboarding</span>
              </div>
              <div className="auth-metric">
                <strong>Secure</strong>
                <span>Login flow</span>
              </div>
              <div className="auth-metric">
                <strong>Personal</strong>
                <span>Styling profile</span>
              </div>
            </div>
          </div>
        </div>

        <div className="auth-panel">
          <div className="auth-card">
            <div className="auth-brand">StyleSync</div>
            <h2>Create Account</h2>
            <p className="auth-caption">Set up your account and open your smart wardrobe.</p>

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
                  placeholder="Choose a username"
                />
              </div>

              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={loading}
                  placeholder="name@example.com"
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
                  placeholder="Create password"
                />
                <div className="password-strength">
                  <div className="strength-track">
                    <div className={`strength-fill level-${passwordStrength.score}`} />
                  </div>
                  <span>{passwordStrength.label}</span>
                </div>
              </div>

              <div className="form-group">
                <label>Confirm Password</label>
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={loading}
                  placeholder="Re-enter password"
                />
              </div>

              <button type="submit" className="btn btn-primary auth-submit" disabled={loading}>
                {loading ? 'Creating account...' : 'Create Account'}
              </button>
            </form>

            <div className="auth-link">
              Already have an account? <Link to="/login">Login here</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
