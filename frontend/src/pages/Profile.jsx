import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { profileAPI, preferencesAPI } from "../api";
import "../styles.css";

export default function Profile() {
  const navigate = useNavigate();

  const [user, setUser] = useState({
    username: "",
    email: "",
  });

  const [profileExtras, setProfileExtras] = useState({
    gender: "",
    age: "",
  });
  const [editMode, setEditMode] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState('');
  const [avatarFile, setAvatarFile] = useState(null);
  const [preferences, setPreferences] = useState({
    preferred_colors: "",
    preferred_styles: "",
    preferred_brands: "",
    budget_range: "",
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/login', { replace: true });
      return;
    }
    const storedExtras = JSON.parse(localStorage.getItem('profileExtras') || '{}');
    setProfileExtras({
      gender: storedExtras.gender || "",
      age: storedExtras.age || "",
    });
    fetchProfile();
    fetchPreferences();
  }, [navigate]);

  const fetchPreferences = async () => {
    try {
      const res = await preferencesAPI.getPreferences();
      const data = res.data || {};
      setPreferences({
        preferred_colors: (data.preferred_colors || []).join(", "),
        preferred_styles: (data.preferred_styles || []).join(", "),
        preferred_brands: (data.preferred_brands || []).join(", "),
        budget_range: data.budget_range || "",
      });
    } catch (err) {
      console.error("Preferences fetch error:", err);
    }
  };

  const fetchProfile = async () => {
    try {
      const res = await profileAPI.getProfile();
      setUser({ username: res.data.username, email: res.data.email });
      setAvatarUrl(res.data.avatar_url || '');
      setProfileExtras({
        gender: res.data.gender || "",
        age: res.data.age || "",
      });
      setLoading(false);
    } catch (err) {
      console.error("Profile fetch error:", err);
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    localStorage.removeItem('userId');
    navigate('/login', { replace: true });
  };

  const handleSaveProfile = async () => {
    try {
      const formData = new FormData();
      formData.append('gender', profileExtras.gender || '');
      formData.append('age', profileExtras.age || '');
      if (avatarFile) formData.append('file', avatarFile);
      const res = await profileAPI.updateProfile(formData);
      setAvatarUrl(res.data.avatar_url || '');
      await preferencesAPI.updatePreferences({
        preferred_colors: preferences.preferred_colors
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        preferred_styles: preferences.preferred_styles
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        preferred_brands: preferences.preferred_brands
          .split(",")
          .map((v) => v.trim())
          .filter(Boolean),
        budget_range: preferences.budget_range || null,
      });
      setAvatarFile(null);
      setEditMode(false);
    } catch (err) {
      console.error('Profile update error:', err);
    }
  };

  if (loading) {
    return (
      <div className="container">
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <div className="spinner"></div>
          <p style={{ marginTop: '1rem' }}>Loading profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="container">
      <button 
        className="btn btn-secondary" 
        onClick={() => navigate('/dashboard', { replace: true })}
        style={{ marginBottom: '2rem' }}
      >
        ← Back to Dashboard
      </button>

      <div className="card profile-card" style={{ 
        maxWidth: '500px', 
        margin: '0 auto',
        background: 'linear-gradient(135deg, rgba(102,126,234,0.05) 0%, rgba(118,75,162,0.05) 100%)',
        border: '2px solid rgba(102,126,234,0.2)'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          {/* Animated Avatar Ring */}
          <div style={{
            position: 'relative',
            width: '150px',
            height: '150px',
            margin: '0 auto 1.5rem',
          }}>
            <div style={{
              position: 'absolute',
              width: '150px',
              height: '150px',
              borderRadius: '50%',
              background: 'conic-gradient(from 0deg, #667eea, #764ba2, #f472b6, #667eea)',
              animation: 'spin 4s linear infinite',
              filter: 'blur(8px)'
            }} />
            <div style={{
              position: 'absolute',
              top: '10px',
              left: '10px',
              width: '130px',
              height: '130px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '4rem',
              color: 'white',
              fontWeight: 'bold',
              boxShadow: '0 10px 30px rgba(102,126,234,0.4)'
            }}>
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt="avatar"
                  style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }}
                />
              ) : (
                user.username ? user.username[0].toUpperCase() : '👤'
              )}
            </div>
          </div>

          {editMode && (
            <div style={{ marginBottom: '1rem' }}>
              <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
                📷 Upload Profile Picture
                <input
                  type="file"
                  accept="image/*"
                  hidden
                  onChange={(e) => setAvatarFile(e.target.files?.[0] || null)}
                />
              </label>
              {avatarFile && (
                <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
                  Selected: {avatarFile.name}
                </div>
              )}
            </div>
          )}
          
          <h2 className="profile-name">
            {user.username}
          </h2>
          <p className="profile-email">{user.email}</p>
        </div>

        <div style={{ 
          padding: '2rem', 
          background: 'white', 
          borderRadius: '12px',
          marginBottom: '1.5rem',
          boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
        }}>
          <div style={{ 
            marginBottom: '1.5rem',
            paddingBottom: '1.5rem',
            borderBottom: '1px solid #e5e7eb'
          }}>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.75rem',
              marginBottom: '0.5rem'
            }}>
              <span style={{ fontSize: '1.5rem' }}>👤</span>
              <strong style={{ fontSize: '0.9rem', color: '#667eea' }}>USERNAME</strong>
            </div>
            <div style={{ fontSize: '1.1rem', paddingLeft: '2.25rem' }}>
              {user.username}
            </div>
          </div>
          
          <div>
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: '0.75rem',
              marginBottom: '0.5rem'
            }}>
              <span style={{ fontSize: '1.5rem' }}>📧</span>
              <strong style={{ fontSize: '0.9rem', color: '#667eea' }}>EMAIL</strong>
            </div>
            <div style={{ fontSize: '1.1rem', paddingLeft: '2.25rem' }}>
              {user.email}
            </div>
          </div>

          <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #e5e7eb' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>🧾</span>
              <strong style={{ fontSize: '0.9rem', color: '#667eea' }}>PROFILE DETAILS</strong>
            </div>
            <div style={{ display: 'grid', gap: '0.75rem', paddingLeft: '2.25rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Gender</label>
                <input
                  type="text"
                  value={profileExtras.gender}
                  onChange={(e) => setProfileExtras({ ...profileExtras, gender: e.target.value })}
                  disabled={!editMode}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    background: editMode ? 'white' : '#f9fafb'
                  }}
                  placeholder="Enter gender"
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Age</label>
                <input
                  type="number"
                  min="1"
                  max="120"
                  value={profileExtras.age}
                  onChange={(e) => setProfileExtras({ ...profileExtras, age: e.target.value })}
                  disabled={!editMode}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    background: editMode ? 'white' : '#f9fafb'
                  }}
                  placeholder="Enter age"
                />
              </div>
            </div>
          </div>

          <div style={{ marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #e5e7eb' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
              <span style={{ fontSize: '1.5rem' }}>🎯</span>
              <strong style={{ fontSize: '0.9rem', color: '#667eea' }}>STYLE PREFERENCES</strong>
            </div>
            <div style={{ display: 'grid', gap: '0.75rem', paddingLeft: '2.25rem' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Preferred Colors (comma-separated)</label>
                <input
                  type="text"
                  value={preferences.preferred_colors}
                  onChange={(e) => setPreferences({ ...preferences, preferred_colors: e.target.value })}
                  disabled={!editMode}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    background: editMode ? 'white' : '#f9fafb'
                  }}
                  placeholder="#000000, #ffffff"
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Preferred Styles (comma-separated)</label>
                <input
                  type="text"
                  value={preferences.preferred_styles}
                  onChange={(e) => setPreferences({ ...preferences, preferred_styles: e.target.value })}
                  disabled={!editMode}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    background: editMode ? 'white' : '#f9fafb'
                  }}
                  placeholder="casual, formal"
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Preferred Brands (comma-separated)</label>
                <input
                  type="text"
                  value={preferences.preferred_brands}
                  onChange={(e) => setPreferences({ ...preferences, preferred_brands: e.target.value })}
                  disabled={!editMode}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    background: editMode ? 'white' : '#f9fafb'
                  }}
                  placeholder="Zara, Uniqlo"
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '0.85rem', color: '#666', marginBottom: '0.25rem' }}>Budget Range</label>
                <input
                  type="text"
                  value={preferences.budget_range}
                  onChange={(e) => setPreferences({ ...preferences, budget_range: e.target.value })}
                  disabled={!editMode}
                  style={{
                    width: '100%',
                    padding: '0.6rem 0.75rem',
                    borderRadius: '8px',
                    border: '1px solid #e5e7eb',
                    background: editMode ? 'white' : '#f9fafb'
                  }}
                  placeholder="$50-$150"
                />
              </div>
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <button
            className="btn btn-secondary"
            onClick={() => navigate('/wardrobe')}
            style={{ flex: 1 }}
          >
            👗 My Wardrobe
          </button>
          {!editMode ? (
            <button
              className="btn btn-primary"
              onClick={() => setEditMode(true)}
              style={{ flex: 1 }}
            >
              ✏️ Edit Profile
            </button>
          ) : (
            <button
              className="btn btn-primary"
              onClick={handleSaveProfile}
              style={{ flex: 1 }}
            >
              ✅ Save Changes
            </button>
          )}
          <button 
            className="btn btn-danger" 
            onClick={handleLogout}
            style={{ flex: 1 }}
          >
            🚪 Logout
          </button>
        </div>
      </div>

      {/* Add spinning animation */}
      <style>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
      `}</style>
      </div>
    </div>
  );
}
