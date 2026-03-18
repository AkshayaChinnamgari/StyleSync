import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { recommendationAPI, weatherAPI, wardrobeAPI, outfitAPI, stylistAPI, shoppingAPI, analyticsAPI, enhancedRecommendationAPI, styleProfileAPI } from '../api';
import '../styles.css';

const TOP_CATEGORIES = new Set(['shirt', 'cardigan', 'jacket', 'blazer', 'trench_coat', 'kurta']);
const BOTTOM_CATEGORIES = new Set(['pants', 'shorts', 'skirt']);

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

export default function Recommendations() {
  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const location = useLocation();
  const navigate = useNavigate();

  const [recommendations, setRecommendations] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [occasion, setOccasion] = useState('casual');
  const [city, setCity] = useState('');
  const [weather, setWeather] = useState(null);
  const [tab, setTab] = useState('occasions');

  const [wardrobeItems, setWardrobeItems] = useState([]);
  const [selectedGarmentId, setSelectedGarmentId] = useState('');
  const [colorMatches, setColorMatches] = useState(null);
  const [stylistSummary, setStylistSummary] = useState(null);

  const [recommendationSource, setRecommendationSource] = useState('');
  const [learningInfo, setLearningInfo] = useState(null);
  const [shoppingMatches, setShoppingMatches] = useState(null);
  const [shoppingLoading, setShoppingLoading] = useState(false);
  const [recommendationExplanation, setRecommendationExplanation] = useState(null);
  const [analyticsSummary, setAnalyticsSummary] = useState(null);

  const [tryOnSelectedIds, setTryOnSelectedIds] = useState([]);
  const [tryOnOccasion, setTryOnOccasion] = useState('virtual_tryon');
  const [tryOnResult, setTryOnResult] = useState(null);
  const [tryOnLoading, setTryOnLoading] = useState(false);

  const [enhancedExplanation, setEnhancedExplanation] = useState(null);
  const [personalStyleProfile, setPersonalStyleProfile] = useState(null);
  const [styleRecommendations, setStyleRecommendations] = useState(null);

  const selectedGarment = useMemo(
    () => wardrobeItems.find((w) => String(w.id) === String(selectedGarmentId)) || null,
    [wardrobeItems, selectedGarmentId]
  );

  const curatedShoppingSections = useMemo(() => {
    const links = shoppingMatches?.shopping_links || [];
    return {
      core: links.filter((link) => link.priority === 'core'),
      accessories: links.filter((link) => link.priority === 'accessory'),
    };
  }, [shoppingMatches]);

  const formatMatchScore = (confidence) => {
    const value = Math.round((confidence || 0) * 100);
    if (value >= 90) return `${value}% strong match`;
    if (value >= 75) return `${value}% good match`;
    return `${value}% match`;
  };

  const tryOnMeta = useMemo(() => {
    const selected = wardrobeItems.filter((w) => tryOnSelectedIds.includes(w.id));
    const hasTop = selected.some((s) => TOP_CATEGORIES.has((s.category || '').toLowerCase()));
    const hasBottom = selected.some((s) => BOTTOM_CATEGORIES.has((s.category || '').toLowerCase()));
    const validCount = selected.length === 2;
    const validPair = hasTop && hasBottom;
    let reason = '';

    if (!validCount) {
      reason = 'Select exactly 2 items.';
    } else if (!validPair) {
      reason = 'Select one top and one bottom.';
    }

    return { selected, valid: validCount && validPair, reason, hasTop, hasBottom };
  }, [tryOnSelectedIds, wardrobeItems]);

  const updateTab = useCallback((nextTab) => {
    setTab(nextTab);
    navigate(`/recommendations?tab=${nextTab}`, { replace: true });
  }, [navigate]);

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const tabParam = params.get('tab');
    if (tabParam) {
      setTab(tabParam);
    }
  }, [location.search]);

  const loadWardrobeItems = useCallback(async () => {
    try {
      const res = await wardrobeAPI.getItems();
      setWardrobeItems(res.data || []);
    } catch {
      setWardrobeItems([]);
    }
  }, []);



  useEffect(() => {
    setError('');

    if (tab !== 'occasions' && tab !== 'today') {
      setWeather(null);
      setLearningInfo(null);
      setRecommendationExplanation(null);
      setRecommendations([]);
      setRecommendationSource('');
    }

    if (tab !== 'color') {
      setColorMatches(null);
      setShoppingMatches(null);
      setSelectedGarmentId('');
    }

    if (tab !== 'tryon') {
      setTryOnSelectedIds([]);
      setTryOnResult(null);
    }



    if (tab === 'color' || tab === 'tryon') {
      loadWardrobeItems();
    }

  }, [tab, loadWardrobeItems]);

  const getRecommendations = async (e) => {
    e?.preventDefault?.();
    if (!occasion) return;

    setLoading(true);
    setError('');
    try {
      const response = await recommendationAPI.getOutfitRecommendation(occasion, city);
      setRecommendations(response.data.outfit || []);
      setLearningInfo(response.data.learning || null);
      setRecommendationExplanation(response.data.explanation || null);
      setRecommendationSource('occasions');

      if (city) {
        const weatherResponse = await weatherAPI.getWeather(city);
        setWeather(weatherResponse.data);
      }
    } catch {
      setError('Failed to get recommendations');
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const getWhatToWearToday = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await recommendationAPI.getWhatToWearToday(city);
      setRecommendations(response.data.outfit || []);
      setWeather(response.data.weather || null);
      setLearningInfo(response.data.learning || null);
      setRecommendationExplanation(response.data.explanation || null);
      setRecommendationSource('today');
    } catch {
      setError('Failed to get today recommendation');
      setRecommendations([]);
    } finally {
      setLoading(false);
    }
  };

  const getColorHarmony = async () => {
    if (!selectedGarmentId) return;
    setLoading(true);
    setError('');
    try {
      const response = await recommendationAPI.pairWith(selectedGarmentId);
      setColorMatches(response.data);
    } catch {
      setError('Failed to get color harmony suggestions');
      setColorMatches(null);
    } finally {
      setLoading(false);
    }
  };

  const getShoppingMatchesForSelected = async () => {
    if (!selectedGarmentId) return;
    setShoppingLoading(true);
    setError('');
    try {
      const response = await shoppingAPI.getComplementaryForGarment(selectedGarmentId);
      setShoppingMatches(response.data);
    } catch {
      setShoppingMatches(null);
      setError('Failed to load shopping recommendations');
    } finally {
      setShoppingLoading(false);
    }
  };

  const handleSelectedGarmentChange = (garmentId) => {
    const nextId = String(garmentId);
    if (nextId === String(selectedGarmentId)) {
      return;
    }
    setSelectedGarmentId(nextId);
    setColorMatches(null);
    setShoppingMatches(null);
    setError('');
  };

  const toggleTryOnSelection = (garmentId) => {
    setTryOnSelectedIds((prev) => {
      if (prev.includes(garmentId)) {
        return prev.filter((id) => id !== garmentId);
      }
      if (prev.length >= 2) {
        return prev;
      }
      return [...prev, garmentId];
    });
  };

  const generateVirtualTryOn = async () => {
    if (!tryOnMeta.valid) {
      setError(tryOnMeta.reason || 'Invalid try-on selection');
      return;
    }

    setTryOnLoading(true);
    setError('');
    try {
      const response = await outfitAPI.tryOn(tryOnSelectedIds, tryOnOccasion || 'virtual_tryon');
      setTryOnResult(response.data);
    } catch (err) {
      setTryOnResult(null);
      setError(err.response?.data?.detail || 'Failed to generate virtual try-on');
    } finally {
      setTryOnLoading(false);
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

  const tabButton = (value, label, className = 'btn btn-secondary') => (
    <button
      type="button"
      className={`${className} ${tab === value ? 'tab-cta-active' : ''}`}
      onClick={() => updateTab(value)}
    >
      {label}
    </button>
  );

  return (
    <div className="page recommendations-page">
      <div className="container">
        <h1>Outfit Recommendations</h1>

        <div className="button-group recommendation-tabs" style={{ marginBottom: '1rem' }}>
          {tabButton('occasions', 'Occasion Based', 'suggest-btn')}
          {tabButton('color', 'Find & Shop Matches', 'color-suggest-btn')}
          {tabButton('today', 'Weather Based', 'weather-suggest-btn')}
          {tabButton('tryon', 'Virtual Try-On', 'tryon-btn')}
        </div>

        {error && <div className="alert alert-error">{error}</div>}

        {tab === 'occasions' && (
          <div className="card">
            <div style={{ marginBottom: '2rem' }}>
              <h2 style={{ marginBottom: '0.5rem' }}>✨ Get Outfit Recommendation</h2>
              <p style={{ color: '#64748b', fontSize: '0.95rem' }}>Select an occasion and city to get personalized outfit suggestions based on weather and your preferences</p>
            </div>
            <form onSubmit={getRecommendations}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '1.5rem' }}>
                <div className="form-group">
                  <label>🎭 Occasion</label>
                  <select value={occasion} onChange={(e) => setOccasion(e.target.value)}>
                    <option value="casual">Casual</option>
                    <option value="formal">Formal</option>
                    <option value="professional">Professional</option>
                    <option value="party">Party</option>
                    <option value="weekend">Weekend</option>
                    <option value="interview">Interview</option>
                    <option value="travel">Travel</option>
                    <option value="date">Date Night</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>🌍 City (optional for weather)</label>
                  <input
                    type="text"
                    placeholder="e.g., Hyderabad, London, Dubai"
                    value={city}
                    onChange={(e) => setCity(e.target.value)}
                  />
                </div>
              </div>
              <button type="submit" className="btn btn-primary" disabled={loading} style={{ marginTop: '1rem', width: '100%' }}>
                {loading ? '⏳ Getting recommendations...' : '🎯 Get Outfit'}
              </button>
            </form>
            {learningInfo && (
              <div className="card" style={{ marginTop: '1.5rem', padding: '1.2rem', background: 'linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(56,189,248,0.1) 100%)', border: '1px solid rgba(102,126,234,0.2)' }}>
                <strong style={{ color: '#667eea' }}>🧠 Personalization:</strong> <span style={{ color: '#64748b' }}>{learningInfo.applied ? '✓ Learning from your outfit history is active.' : '○ No history yet; using base preferences.'}</span>
              </div>
            )}
          </div>
        )}

        {tab === 'today' && (
          <div className="card">
            <div style={{ marginBottom: '2rem' }}>
              <h2 style={{ marginBottom: '0.5rem' }}>☀️ What Should I Wear Today?</h2>
              <p style={{ color: '#64748b', fontSize: '0.95rem' }}>Get a personalized outfit suggestion based on today's weather and your style preferences</p>
            </div>
            <div className="form-group">
              <label>🌍 Your City</label>
              <input
                type="text"
                placeholder="e.g., Hyderabad, London, Dubai"
                value={city}
                onChange={(e) => setCity(e.target.value)}
              />
            </div>
            <button className="btn btn-primary" onClick={getWhatToWearToday} disabled={loading} style={{ width: '100%' }}>
              {loading ? '⏳ Getting outfit...' : '🎯 Suggest Outfit for Today'}
            </button>
            {learningInfo && recommendationSource === 'today' && (
              <div className="card" style={{ marginTop: '1.5rem', padding: '1.2rem', background: 'linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(56,189,248,0.1) 100%)', border: '1px solid rgba(102,126,234,0.2)' }}>
                <strong style={{ color: '#667eea' }}>🧠 Personalization:</strong> <span style={{ color: '#64748b' }}>{learningInfo.applied ? '✓ Today suggestion is adapted from your past outfit behavior.' : '○ No history yet; using weather + base preferences.'}</span>
              </div>
            )}
          </div>
        )}

        {tab === 'color' && (
          <div className="card">
            <h2>Color Harmony and Matching Shopping</h2>
            <p style={{ color: '#666', marginBottom: '1rem' }}>
              Select one wardrobe item to get matching in-closet options and external shopping links.
            </p>

            <div className="grid-4" style={{ marginTop: '1rem' }}>
              {wardrobeItems.map((item) => (
                <div
                  key={item.id}
                  className="garment-item"
                  onClick={() => handleSelectedGarmentChange(item.id)}
                  style={{
                    border: String(item.id) === String(selectedGarmentId) ? '3px solid #667eea' : '1px solid #e5e7eb',
                    boxShadow: String(item.id) === String(selectedGarmentId) ? '0 0 20px rgba(102,126,234,0.35)' : undefined
                  }}
                >
                  <img
                    src={`/image/${item.filename}`}
                    alt={item.category}
                    className="garment-image"
                    onError={(e) => (e.target.src = 'https://via.placeholder.com/200x200?text=No+Image')}
                  />
                  <div className="garment-info">
                    <div className="garment-category">{item.category}</div>
                    <div className="garment-color">
                      <div className="color-swatch" style={{ backgroundColor: item.color }} />
                      <span>{getColorName(item.color)}</span>
                    </div>
                    {!['watch', 'necklace', 'bracelet', 'earrings', 'hat', 'gloves', 'scarf', 'belt', 'bag'].includes(item.category.toLowerCase()) ? (
                      <small style={{ color: '#999' }}>{item.style} | {item.season}</small>
                    ) : (
                      <small style={{ color: '#999' }}>{item.style}</small>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {selectedGarment && (
              <div className="card" style={{ marginTop: '1rem', padding: '1rem' }}>
                <strong>Selected:</strong> {selectedGarment.category} • {selectedGarment.style}
                <div style={{ marginTop: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.9rem', color: '#64748b' }}>Color:</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.4rem 0.8rem', background: '#f0f4f8', borderRadius: '6px' }}>
                    <div style={{ width: '20px', height: '20px', borderRadius: '4px', backgroundColor: selectedGarment.color || '#ccc', border: '1px solid #ddd' }} />
                    <span style={{ fontWeight: '600', color: '#333' }}>{getColorName(selectedGarment.color)}</span>
                  </div>
                </div>
              </div>
            )}

            <div style={{ marginTop: '1rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap' }}>
              <button type="button" className="btn btn-primary" disabled={!selectedGarmentId || loading} onClick={getColorHarmony}>
                {loading ? 'Analyzing...' : 'Get Color Harmony'}
              </button>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={!selectedGarmentId || shoppingLoading}
                onClick={getShoppingMatchesForSelected}
              >
                {shoppingLoading ? 'Finding stores...' : 'Buy Matching Items + Accessories'}
              </button>
              {!selectedGarmentId && <small style={{ color: '#999' }}>Select an item to continue</small>}
            </div>

            {colorMatches && (
              <div style={{ marginTop: '1.5rem' }}>
                <h3>Best Matching Items</h3>
                <p style={{ color: '#666', marginBottom: '0.75rem' }}>{colorMatches.message}</p>
                <div className="grid-4" style={{ marginTop: '1rem' }}>
                  {(colorMatches.suggestions || []).map((garment) => (
                    <div key={garment.id} className="garment-item">
                      <img
                        src={`/image/${garment.filename}`}
                        alt={garment.category}
                        className="garment-image"
                        onError={(e) => (e.target.src = 'https://via.placeholder.com/200x200?text=No+Image')}
                      />
                      <div className="garment-info">
                        <div className="garment-category">{garment.category}</div>
                        <div className="garment-color">
                          <div className="color-swatch" style={{ backgroundColor: garment.color }} />
                          <span>{getColorName(garment.color)}</span>
                        </div>
                        {!['watch', 'necklace', 'bracelet', 'earrings', 'hat', 'gloves', 'scarf', 'belt', 'bag'].includes(garment.category.toLowerCase()) ? (
                          <small style={{ color: '#999' }}>{garment.style} | {garment.season}</small>
                        ) : (
                          <small style={{ color: '#999' }}>{garment.style}</small>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {shoppingMatches && (
              <div style={{ marginTop: '1.5rem' }}>
                <h3>Shopping Recommendations</h3>
                {shoppingMatches.compatibility_note && (
                  <p style={{ color: '#666' }}>{shoppingMatches.compatibility_note}</p>
                )}

                {shoppingMatches.shopping_links?.length > 0 ? (
                  <div style={{ marginTop: '0.75rem' }}>
                    {curatedShoppingSections.core.length > 0 && (
                      <div style={{ marginBottom: '1.25rem' }}>
                        <h4 style={{ marginBottom: '0.75rem' }}>Core Clothing Picks</h4>
                        <div className="grid-4">
                          {curatedShoppingSections.core.map((link, idx) => (
                            <div key={`${link.store}-${link.category}-${idx}`} className="card" style={{ padding: '0.9rem' }}>
                              <div style={{ fontWeight: 700 }}>{link.category}</div>
                              <div style={{ color: '#666', fontSize: '0.9rem', marginBottom: '0.35rem' }}>{link.intent}</div>
                              <div style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: '0.6rem' }}>
                                {link.store} | {link.target_color} | {formatMatchScore(link.confidence)}
                              </div>
                              <a href={link.url} target="_blank" rel="noreferrer" className="btn btn-primary" style={{ display: 'inline-block' }}>
                                View Item
                              </a>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {curatedShoppingSections.accessories.length > 0 && (
                      <div>
                        <h4 style={{ marginBottom: '0.75rem' }}>Accessory Picks</h4>
                        <div className="grid-4">
                          {curatedShoppingSections.accessories.map((link, idx) => (
                            <div key={`${link.store}-${link.category}-${idx}`} className="card" style={{ padding: '0.9rem' }}>
                              <div style={{ fontWeight: 700 }}>{link.category}</div>
                              <div style={{ color: '#666', fontSize: '0.9rem', marginBottom: '0.35rem' }}>{link.intent}</div>
                              <div style={{ color: '#64748b', fontSize: '0.85rem', marginBottom: '0.6rem' }}>
                                {link.store} | {link.target_color} | {formatMatchScore(link.confidence)}
                              </div>
                              <a href={link.url} target="_blank" rel="noreferrer" className="btn btn-secondary" style={{ display: 'inline-block' }}>
                                View Item
                              </a>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    {shoppingMatches.shopping_plan && (
                      <div className="card" style={{ marginTop: '1rem', padding: '0.9rem' }}>
                        <strong>Shopping plan:</strong> Core {`(${(shoppingMatches.shopping_plan.core_focus || []).join(', ') || 'n/a'})`}
                        {' '}and accessories {`(${(shoppingMatches.shopping_plan.accessory_focus || []).join(', ') || 'n/a'})`}.
                      </div>
                    )}
                  </div>
                ) : (
                  <p style={{ color: '#666' }}>No shopping links generated for this item.</p>
                )}
              </div>
            )}
          </div>
        )}



        {tab === 'tryon' && (
          <div className="card">
            <h2>Virtual Try-On</h2>
            <p style={{ color: '#666', marginBottom: '1rem' }}>
              Select exactly 2 garments: one top and one bottom.
            </p>

            <div className="form-group">
              <label>Occasion Tag (optional)</label>
              <input
                type="text"
                value={tryOnOccasion}
                onChange={(e) => setTryOnOccasion(e.target.value)}
                placeholder="virtual_tryon"
              />
            </div>

            <div style={{ marginBottom: '0.75rem', color: tryOnMeta.valid ? '#15803d' : '#b45309' }}>
              {tryOnMeta.valid ? 'Selection valid: ready to generate.' : (tryOnMeta.reason || 'Select compatible garments.')}
            </div>

            <div className="grid-4" style={{ marginTop: '1rem' }}>
              {wardrobeItems.map((item) => (
                <div
                  key={item.id}
                  className="garment-item"
                  onClick={() => toggleTryOnSelection(item.id)}
                  style={{
                    border: tryOnSelectedIds.includes(item.id) ? '3px solid #10b981' : '1px solid #e5e7eb',
                    boxShadow: tryOnSelectedIds.includes(item.id) ? '0 0 16px rgba(16,185,129,0.35)' : undefined
                  }}
                >
                  <img
                    src={`/image/${item.filename}`}
                    alt={item.category}
                    className="garment-image"
                    onError={(e) => (e.target.src = 'https://via.placeholder.com/200x200?text=No+Image')}
                  />
                  <div className="garment-info">
                    <div className="garment-category">{item.category}</div>
                    {!['watch', 'necklace', 'bracelet', 'earrings', 'hat', 'gloves', 'scarf', 'belt', 'bag'].includes(item.category.toLowerCase()) ? (
                      <small style={{ color: '#999' }}>{item.style} | {item.season}</small>
                    ) : (
                      <small style={{ color: '#999' }}>{item.style}</small>
                    )}
                  </div>
                </div>
              ))}
            </div>

            <div style={{ marginTop: '1rem', display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={generateVirtualTryOn}
                disabled={tryOnLoading || !tryOnMeta.valid}
              >
                {tryOnLoading ? 'Generating...' : `Generate Try-On (${tryOnSelectedIds.length} selected)`}
              </button>
              {!tryOnMeta.valid && <small style={{ color: '#999' }}>Pick one top and one bottom.</small>}
            </div>

            {tryOnResult && (
              <div style={{ marginTop: '1.5rem' }}>
                <h3>Try-On Preview</h3>
                <img
                  src={`${API_BASE}${tryOnResult.preview_url}`}
                  alt="Virtual try-on preview"
                  style={{
                    width: '100%',
                    maxWidth: '720px',
                    borderRadius: '12px',
                    border: '1px solid #ddd',
                    background: '#fff'
                  }}
                />
                <div style={{ marginTop: '0.75rem' }}>
                  <small style={{ color: '#666', display: 'block', marginBottom: '0.5rem' }}>
                    Used {tryOnResult.used_count} of {tryOnResult.selected_count} selected items.
                  </small>
                  <a href={`${API_BASE}${tryOnResult.preview_url}`} target="_blank" rel="noreferrer" className="btn btn-secondary">
                    Open Full Preview
                  </a>
                </div>
              </div>
            )}
          </div>
        )}

        {weather && (tab === 'occasions' || tab === 'today') && (
          <div className="weather-card" style={{ marginBottom: '2rem', animation: 'fadeUp 0.5s ease both' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '3rem', flexWrap: 'wrap', justifyContent: 'center' }}>
              <div className="weather-info">
                <div className="weather-condition">
                  {weather.condition === 'Clear' && '☀️ Clear'}
                  {weather.condition === 'Cloudy' && '☁️ Cloudy'}
                  {weather.condition === 'Sunny' && '🌞 Sunny'}
                  {weather.condition === 'Rain' && '🌧️ Rainy'}
                  {!['Clear', 'Cloudy', 'Sunny', 'Rain'].includes(weather.condition) && weather.condition}
                </div>
                <div className="weather-temp">{weather.temp}°C</div>
                <small style={{ color: '#e0e7ff', fontSize: '0.85rem' }}>in {weather.city}</small>
              </div>
              <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap' }}>
                {weather.feels_like && weather.feels_like !== weather.temp && (
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '0.85rem', color: '#cbd5e1', letterSpacing: '0.5px', textTransform: 'uppercase' }}>Feels Like</div>
                    <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#ffffff' }}>{weather.feels_like}°C</div>
                  </div>
                )}
                {weather.humidity && (
                  <div style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: '0.85rem', color: '#cbd5e1', letterSpacing: '0.5px', textTransform: 'uppercase' }}>Humidity</div>
                    <div style={{ fontSize: '1.8rem', fontWeight: 700, color: '#ffffff' }}>{weather.humidity}%</div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {recommendations.length > 0 && recommendationSource === tab && (tab === 'occasions' || tab === 'today') && (
          <div className="card">
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ marginBottom: '0.5rem' }}>👗 Your Recommended Outfit</h2>
              {recommendationExplanation?.summary?.[0] && (
                <p style={{ color: '#64748b', fontSize: '0.95rem', margin: 0 }}>💡 {recommendationExplanation.summary[0]}</p>
              )}
            </div>
            <div className="outfit-preview">
              {recommendations.map((item) => (
                <div key={item.id} className="outfit-item">
                  <img
                    src={`/image/${item.filename}`}
                    alt={item.category}
                    className="outfit-item-image"
                    onError={(e) => (e.target.src = 'https://via.placeholder.com/150x150?text=No+Image')}
                  />
                  <div className="outfit-item-label">{item.category}</div>
                  <small style={{ color: '#64748b', fontSize: '0.85rem' }}>{getColorName(item.color)}</small>
                  {item.fabric && <small style={{ color: '#94a3b8', fontSize: '0.8rem', display: 'block' }}>🧵 {item.fabric}</small>}
                </div>
              ))}
            </div>
          </div>
        )}

        {!loading && recommendations.length === 0 && !error && tab === 'occasions' && (
          <div className="card">
            <div className="empty-state">
              <div style={{ fontSize: '3.5rem', marginBottom: '1rem' }}>📦</div>
              <div className="empty-title">No recommendations yet</div>
              <p className="empty-description">Pick an occasion above and enter a city, then click Get Outfit to see personalized recommendations!</p>
              <div style={{ marginTop: '1.5rem', padding: '1.2rem', background: 'linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(56,189,248,0.1) 100%)', borderRadius: '12px', border: '1px solid rgba(102,126,234,0.2)' }}>
                <p style={{ margin: '0.5rem 0', fontSize: '0.9rem', color: '#475569' }}>
                  💡 <strong>Tip:</strong> Try cities like Dubai (hot), London (cold), or your local city to see how temperature affects your outfit!
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
