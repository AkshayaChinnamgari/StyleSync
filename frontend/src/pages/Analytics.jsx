import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { stylistAPI, analyticsAPI, styleProfileAPI, enhancedRecommendationAPI, recommendationAPI } from '../api';
import '../styles.css';

// Helper function to convert hex to readable color name
const getColorName = (hexColor) => {
  if (!hexColor) return 'Unknown';
  
  const colorNames = {
    '#FF0000': 'Red', '#FF5733': 'Red-Orange', '#FF8C00': 'Orange', '#FFC000': 'Gold',
    '#FFFF00': 'Yellow', '#808000': 'Olive', '#00FF00': 'Green', '#00CC66': 'Sea Green',
    '#008000': 'Dark Green', '#00FFFF': 'Cyan', '#0099CC': 'Sky Blue', '#0000FF': 'Blue',
    '#000080': 'Navy', '#4B0082': 'Indigo', '#9400D3': 'Purple', '#FF1493': 'Deep Pink',
    '#FF69B4': 'Hot Pink', '#FFB6C1': 'Light Pink', '#FFC0CB': 'Pink', '#FFFFFF': 'White',
    '#F5F5F5': 'Off-White', '#D3D3D3': 'Light Gray', '#808080': 'Gray', '#A9A9A9': 'Dark Gray',
    '#000000': 'Black', '#8B4513': 'Brown', '#A0522D': 'Sienna', '#D2691E': 'Chocolate',
    '#CD853F': 'Peru', '#DEB887': 'Burlywood', '#F4A460': 'Sandy Brown', '#DAA520': 'Goldenrod',
  };
  
  const upper = hexColor.toUpperCase();
  if (colorNames[upper]) return colorNames[upper];
  
  // Simple HSL-based estimation if not in predefined list
  const r = parseInt(upper.slice(1, 3), 16) / 255;
  const g = parseInt(upper.slice(3, 5), 16) / 255;
  const b = parseInt(upper.slice(5, 7), 16) / 255;
  
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  
  if (max === min) h = 0;
  else if (max === r) h = ((g - b) / (max - min) + (g < b ? 6 : 0)) / 6;
  else if (max === g) h = ((b - r) / (max - min) + 2) / 6;
  else h = ((r - g) / (max - min) + 4) / 6;
  
  const l = (max + min) / 2;
  const s = l > 0.5 ? (max - min) / (2 - max - min) : (max - min) / (max + min);
  
  const hue = Math.round(h * 360);
  
  if (s < 0.1) return l < 0.5 ? 'Black' : 'White';
  if (l < 0.2) return 'Very Dark';
  if (hue < 15 || hue > 345) return 'Red';
  if (hue < 45) return 'Orange';
  if (hue < 65) return 'Yellow';
  if (hue < 150) return 'Green';
  if (hue < 200) return 'Cyan';
  if (hue < 260) return 'Blue';
  if (hue < 290) return 'Purple';
  if (hue < 330) return 'Pink';
  return 'Red';
};

export default function Analytics() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  const [stylistSummary, setStylistSummary] = useState(null);
  const [analyticsSummary, setAnalyticsSummary] = useState(null);
  const [personalStyleProfile, setPersonalStyleProfile] = useState(null);
  const [styleRecommendations, setStyleRecommendations] = useState(null);
  const [enhancedExplanation, setEnhancedExplanation] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [occasion, setOccasion] = useState('casual');

  useEffect(() => {
    if (!localStorage.getItem('token')) {
      navigate('/login', { replace: true });
      return;
    }
    loadAnalytics();
  }, [navigate]);

  const loadAnalytics = async () => {
    try {
      const [stylistRes, analyticsRes] = await Promise.allSettled([
        stylistAPI.getProfileSummary(),
        analyticsAPI.getWardrobeSummary()
      ]);

      if (stylistRes.status === 'fulfilled') {
        setStylistSummary(stylistRes.value.data);
      }
      if (analyticsRes.status === 'fulfilled') {
        setAnalyticsSummary(analyticsRes.value.data);
      }
    } catch (err) {
      console.error('Analytics error:', err);
      setError('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const loadPersonalStyleProfile = useCallback(async () => {
    try {
      const response = await styleProfileAPI.getPersonalProfile();
      setPersonalStyleProfile(response.data);
    } catch {
      setPersonalStyleProfile(null);
    }
  }, []);

  const loadStyleRecommendations = useCallback(async () => {
    try {
      const response = await styleProfileAPI.getStyleRecommendations();
      setStyleRecommendations(response.data);
    } catch {
      setStyleRecommendations(null);
    }
  }, []);

  const loadEnhancedExplanation = useCallback(async () => {
    if (recommendations.length === 0) return;
    
    try {
      const garmentIds = recommendations.map(r => r.id);
      const response = await enhancedRecommendationAPI.getEnhancedExplanation(garmentIds, occasion);
      setEnhancedExplanation(response.data);
    } catch {
      setEnhancedExplanation(null);
    }
  }, [recommendations, occasion]);

  if (loading) {
    return (
      <div className="page">
        <div className="container">
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <div className="loading-skeleton"></div>
            <p>Loading your style insights...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="container">
        {error && <div className="error-message" style={{ marginBottom: '1rem' }}>{error}</div>}

        <div className="dashboard-hero" style={{ marginBottom: '2rem' }}>
          <div>
            <h1>✨ Style Analytics Dashboard</h1>
            <p className="dashboard-subtitle">Explore your wardrobe insights and personal style</p>
          </div>
        </div>

        {/* Wardrobe Analysis Section */}
        <div className="card">
          <h2>📊 Wardrobe Analysis</h2>
          {!stylistSummary ? (
            <p style={{ color: '#666' }}>Unable to load wardrobe profile.</p>
          ) : (
            <div>
              <p><strong>Total items:</strong> {stylistSummary.total_items}</p>
              <p><strong>Dominant style:</strong> {stylistSummary.dominant_style || 'n/a'}</p>
              <p><strong>Dominant season:</strong> {stylistSummary.dominant_season || 'n/a'}</p>
              <p><strong>Dominant fabric:</strong> {stylistSummary.dominant_fabric || 'n/a'}</p>
              <h3 style={{ marginTop: '1rem' }}>Top Categories</h3>
              <div style={{ color: '#666' }}>
                {(stylistSummary.top_categories || []).map((c) => `${c.category} (${c.count})`).join(' | ') || 'n/a'}
              </div>
              <h3 style={{ marginTop: '1rem' }}>Color Palette</h3>
              <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                {(stylistSummary.palette || []).map((p) => (
                  <div key={p.color} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0.8rem', background: '#f0f4f8', borderRadius: '6px' }}>
                    <span style={{ width: '16px', height: '16px', borderRadius: '3px', background: p.color, border: '1px solid #ddd' }} />
                    <small><strong>{getColorName(p.color)}</strong> ({p.count})</small>
                  </div>
                ))}
              </div>

              {analyticsSummary && (
                <div className="card insight-panel" style={{ marginTop: '1rem' }}>
                  <h3>Research Insights</h3>
                  <div className="insight-metrics-grid">
                    <div className="insight-metric-card">
                      <span>Balance</span>
                      <strong>{Math.round(analyticsSummary.scores?.wardrobe_balance || 0)}%</strong>
                    </div>
                    <div className="insight-metric-card">
                      <span>Versatility</span>
                      <strong>{Math.round(analyticsSummary.scores?.versatility || 0)}%</strong>
                    </div>
                    <div className="insight-metric-card">
                      <span>Seasonal Coverage</span>
                      <strong>{Math.round(analyticsSummary.scores?.seasonal_coverage || 0)}%</strong>
                    </div>
                    <div className="insight-metric-card">
                      <span>Usage Coverage</span>
                      <strong>{Math.round(analyticsSummary.usage?.usage_coverage || 0)}%</strong>
                    </div>
                  </div>

                  <div className="insight-summary-list">
                    {(analyticsSummary.insights || []).map((line, index) => (
                      <p key={`${line}-${index}`}>{line}</p>
                    ))}
                  </div>

                  <h3 style={{ marginTop: '1rem' }}>Occasion Readiness</h3>
                  <div className="insight-breakdown-grid">
                    {(analyticsSummary.readiness || []).slice(0, 6).map((item) => (
                      <div key={item.occasion} className="insight-breakdown-card">
                        <div className="insight-breakdown-head">
                          <strong>{item.occasion}</strong>
                          <span>{Math.round(item.score)}%</span>
                        </div>
                        <div className="insight-tags">
                          {(item.missing_categories || []).length
                            ? item.missing_categories.map((missing) => <span className="insight-tag" key={`${item.occasion}-${missing}`}>Missing: {missing}</span>)
                            : <span className="insight-tag">Ready</span>}
                        </div>
                      </div>
                    ))}
                  </div>

                  <h3 style={{ marginTop: '1rem' }}>Wardrobe Gaps</h3>
                  {(analyticsSummary.gaps || []).length ? (
                    <div className="insight-breakdown-grid">
                      {analyticsSummary.gaps.map((gap) => (
                        <div key={gap.area} className="insight-breakdown-card">
                          <div className="insight-breakdown-head">
                            <strong>{gap.area}</strong>
                            <span>{gap.current}/{gap.target}</span>
                          </div>
                          <div className="insight-breakdown-meta">{gap.recommendation}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p style={{ color: '#666' }}>No critical wardrobe gaps detected.</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Style Insights Section */}
        <div className="card" style={{ marginTop: '2rem' }}>
          <h2>✨ Your Personal Style Insights</h2>
          
          <button 
            type="button" 
            className="btn btn-primary" 
            onClick={() => {
              loadPersonalStyleProfile();
              loadStyleRecommendations();
              if (recommendations.length > 0) {
                loadEnhancedExplanation();
              }
            }}
            style={{ marginBottom: '1rem' }}
          >
            Load My Style Profile
          </button>

          {personalStyleProfile && (
            <div style={{ marginTop: '1.5rem' }}>
              <div className="ai-insights-section" style={{
                padding: '1.5rem',
                background: 'linear-gradient(135deg, var(--accent-light) 0%, var(--accent-pale) 100%)',
                borderRadius: '12px',
                marginBottom: '1.5rem'
              }}>
                <h3 style={{ marginBottom: '0.5rem' }}>{personalStyleProfile.style_type}</h3>
                <p style={{ fontSize: '1.1rem', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
                  {personalStyleProfile.personality}
                </p>
              </div>

              <div className="style-profile-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
                <div className="stat-box">
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Style Type</div>
                  <strong style={{ fontSize: '1.3rem' }}>{personalStyleProfile.style_type}</strong>
                </div>
                <div className="stat-box">
                  <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Versatility Score</div>
                  <strong style={{ fontSize: '1.3rem' }}>{personalStyleProfile.versatility_score}<span style={{ fontSize: '0.8rem' }}>/100</span></strong>
                </div>
                {personalStyleProfile.characteristics && (
                  <div className="stat-box">
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Characteristics</div>
                    <div>{personalStyleProfile.characteristics.slice(0, 2).join(', ')}</div>
                  </div>
                )}
              </div>

              {personalStyleProfile.color_palette && personalStyleProfile.color_palette.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4>Your Color Palette</h4>
                  <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginTop: '0.75rem' }}>
                    {personalStyleProfile.color_palette.map((color) => (
                      <div 
                        key={color} 
                        style={{
                          display: 'flex',
                          alignItems: 'center',
                          gap: '0.5rem',
                          padding: '0.5rem 0.75rem',
                          background: 'var(--bg-secondary)',
                          borderRadius: '8px',
                          fontSize: '0.9rem'
                        }}
                      >
                        <span 
                          style={{
                            width: '20px',
                            height: '20px',
                            borderRadius: '4px',
                            background: color,
                            border: '1px solid var(--border-color)'
                          }}
                        />
                        <strong>{getColorName(color)}</strong>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {personalStyleProfile.style_strengths && personalStyleProfile.style_strengths.length > 0 && (
                <div style={{ marginBottom: '1.5rem' }}>
                  <h4>Your Strengths</h4>
                  <ul style={{ listStyle: 'none', padding: 0 }}>
                    {personalStyleProfile.style_strengths.map((strength, idx) => (
                      <li key={idx} style={{ padding: '0.5rem 0', color: 'var(--text-secondary)' }}>
                        ✓ {strength}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {styleRecommendations && (
            <div style={{ marginTop: '1.5rem' }}>
              <h3>Personalized Recommendations</h3>
              <div style={{ 
                display: 'grid', 
                gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
                gap: '1rem',
                marginTop: '1rem'
              }}>
                {styleRecommendations.personalized_recommendations && styleRecommendations.personalized_recommendations.map((rec, idx) => (
                  <div 
                    key={idx} 
                    className="ai-recommendation-card"
                    style={{
                      padding: '1rem',
                      background: 'var(--bg-secondary)',
                      borderRadius: '8px',
                      border: '1px solid var(--border-color)',
                      transition: 'all 0.3s ease'
                    }}
                  >
                    <div style={{ fontSize: '0.95rem', lineHeight: '1.5', color: 'var(--text-secondary)' }}>
                      💡 {rec}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {enhancedExplanation && (
            <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'var(--bg-secondary)', borderRadius: '8px' }}>
              <h3>Current Outfit Analysis</h3>
              {enhancedExplanation.explanation && (
                <div>
                  {enhancedExplanation.explanation.summary && enhancedExplanation.explanation.summary.length > 0 && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong>Why This Outfit:</strong>
                      {enhancedExplanation.explanation.summary.map((summary, idx) => (
                        <p key={idx} style={{ margin: '0.5rem 0', color: 'var(--text-secondary)' }}>
                          {summary}
                        </p>
                      ))}
                    </div>
                  )}
                  
                  {enhancedExplanation.explanation.color_theory && (
                    <div style={{ marginBottom: '1rem' }}>
                      <strong>Color Theory:</strong>
                      <p style={{ margin: '0.5rem 0', color: 'var(--text-secondary)' }}>
                        {enhancedExplanation.explanation.color_theory}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {enhancedExplanation.styling_tips && enhancedExplanation.styling_tips.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <strong>Styling Tips:</strong>
                  <ul style={{ listStyle: 'none', padding: '0.5rem 0 0 0', margin: 0 }}>
                    {enhancedExplanation.styling_tips.map((tip, idx) => (
                      <li key={idx} style={{ padding: '0.4rem 0', color: 'var(--text-secondary)' }}>
                        ✨ {tip}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {!personalStyleProfile && !styleRecommendations && !enhancedExplanation && (
            <p style={{ color: '#999', textAlign: 'center', padding: '2rem' }}>
              Click "Load My Style Profile" to discover your personalized style insights
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
