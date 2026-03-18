import React, { useState } from 'react';
import { wardrobeAPI } from '../api';
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
    '#000000': 'Black', '#8B4513': 'Brown', '#A52A2A': 'Maroon', '#A0522D': 'Sienna', '#D2691E': 'Chocolate',
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

// Helper function to convert hex to RGB (robust version)
const hexToRgb = (hexColor) => {
  try {
    let hex = String(hexColor).trim().replace('#', '').toUpperCase();
    if (hex.length === 3) {
      hex = hex.split('').map(x => x + x).join('');
    }
    if (hex.length !== 6) return [128, 128, 128];
    return [
      parseInt(hex.substring(0, 2), 16),
      parseInt(hex.substring(2, 4), 16),
      parseInt(hex.substring(4, 6), 16),
    ];
  } catch (err) {
    return [128, 128, 128];
  }
};

// Convert RGB to HSL for better color classification
const rgbToHsl = (r, g, b) => {
  r /= 255;
  g /= 255;
  b /= 255;
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0, s = 0;
  const l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
    switch (max) {
      case r: h = ((g - b) / d + (g < b ? 6 : 0)) / 6; break;
      case g: h = ((b - r) / d + 2) / 6; break;
      case b: h = ((r - g) / d + 4) / 6; break;
    }
  }
  return [Math.round(h * 360), Math.round(s * 100), Math.round(l * 100)];
};

// Classify color by hue (more accurate than RGB distance for human perception)
const classifyColorByHue = (hexColor) => {
  const [r, g, b] = hexToRgb(hexColor);
  const [h, s, l] = rgbToHsl(r, g, b);
  
  // Handle grayscale
  if (s < 10) {
    return l < 30 ? '#000000' : l > 85 ? '#FFFFFF' : '#808080';
  }
  
  // Classify by hue
  if (h < 15 || h >= 345) return '#FF0000';     // Red
  if (h < 45) return '#FFA500';                  // Orange
  if (h < 65) return '#FFFF00';                  // Yellow
  if (h < 150) return '#00FF00';                 // Green
  if (h < 200) return '#00FFFF';                 // Cyan
  if (h < 260) return '#0000FF';                 // Blue
  if (h < 290) return '#800080';                 // Purple
  if (h < 330) return '#FFC0CB';                 // Pink
  return '#FF0000';                              // Default to Red
};

// Get the nearest palette color using hue-based classification
const getNearestPaletteColor = (garmentColor, paletteColors) => {
  if (!garmentColor) return '#808080';
  
  try {
    const classifiedColor = classifyColorByHue(garmentColor);
    return classifiedColor || '#808080';
  } catch (err) {
    return '#808080';
  }
};

export default function Search() {
  const [garments, setGarments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterStyle, setFilterStyle] = useState('');
  const [filterSeason, setFilterSeason] = useState('');
  const [filterColor, setFilterColor] = useState('');
  const [filterFabric, setFilterFabric] = useState('');
  const [filterOccasion, setFilterOccasion] = useState('');
  const [error, setError] = useState('');
  const [expandFilters, setExpandFilters] = useState(true);

  const commonColors = [
    '#000000', '#FFFFFF', '#808080', '#FF0000', '#00FF00', '#0000FF',
    '#FFFF00', '#FFC0CB', '#A52A2A', '#FFA500', '#800080', '#008080'
  ];

  const occasions = ['Casual', 'Formal', 'Professional', 'Party', 'Weekend', 'Interview', 'Travel', 'Date'];

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const response = await wardrobeAPI.searchItems(searchQuery);
      setGarments(response.data);
      setError('');
    } catch (err) {
      setError('Search failed');
      setGarments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleFilter = async () => {
    setLoading(true);
    try {
      const response = await wardrobeAPI.filterItems(
        filterCategory || null,
        filterColor || null,
        filterStyle || null,
        filterSeason || null,
        filterFabric || null
      );
      setGarments(response.data);
      setError('');
    } catch (err) {
      setError('Filter failed');
      setGarments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleClearFilters = () => {
    setFilterCategory('');
    setFilterStyle('');
    setFilterSeason('');
    setFilterColor('');
    setFilterFabric('');
    setFilterOccasion('');
    setSearchQuery('');
    setGarments([]);
  };

  const applyQuickFilter = (preset) => {
    handleClearFilters();
    switch (preset) {
      case 'casual-weekend':
        setFilterStyle('casual');
        setFilterOccasion('Weekend');
        break;
      case 'professional':
        setFilterStyle('professional');
        setFilterOccasion('Professional');
        break;
      case 'formal-party':
        setFilterStyle('formal');
        setFilterOccasion('Party');
        break;
      case 'spring-summer':
        setFilterSeason('spring');
        break;
      case 'fall-winter':
        setFilterSeason('fall');
        break;
      default:
        break;
    }
  };

  return (
    <div className="page search-page">
      <div className="container">
        <h1>🔍 Search & Filter</h1>

      {error && <div className="alert alert-error">{error}</div>}

      <div className="card">
        <h2>Search Wardrobe</h2>
        <form onSubmit={handleSearch}>
          <div className="search-bar">
            <input
              type="text"
              placeholder="Search by name, brand, or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            <button type="submit" disabled={loading}>
              {loading ? '⏳' : '🔍'}
            </button>
          </div>
        </form>
      </div>

      <div className="card">
        <h2>Filter Items</h2>

        {/* Quick Filter Presets */}
        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '0.9rem', fontWeight: '600', marginBottom: '0.75rem', color: 'var(--text-secondary)' }}>
            Quick Filters
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => { applyQuickFilter('casual-weekend'); handleFilter(); }}
              style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
            >
              👕 Casual
            </button>
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => { applyQuickFilter('professional'); handleFilter(); }}
              style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
            >
              💼 Professional
            </button>
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => { applyQuickFilter('formal-party'); handleFilter(); }}
              style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
            >
              🎭 Formal
            </button>
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => { applyQuickFilter('spring-summer'); handleFilter(); }}
              style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
            >
              ☀️ Spring/Summer
            </button>
            <button 
              type="button" 
              className="btn btn-secondary"
              onClick={() => { applyQuickFilter('fall-winter'); handleFilter(); }}
              style={{ fontSize: '0.9rem', padding: '0.5rem 1rem' }}
            >
              ❄️ Fall/Winter
            </button>
          </div>
        </div>

        {/* Advanced Filters */}
        <div style={{
          padding: '1rem',
          background: 'var(--bg-primary)',
          borderRadius: '8px',
          marginBottom: '1.5rem'
        }}>
          <button
            type="button"
            onClick={() => setExpandFilters(!expandFilters)}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '1rem',
              fontWeight: '600',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: 'var(--text-primary)',
              width: '100%'
            }}
          >
            {expandFilters ? '▼' : '▶'} Advanced Filters
          </button>

          {expandFilters && (
            <div style={{ marginTop: '1rem' }}>
              {/* Color Palette Picker */}
              <div style={{ marginBottom: '1.5rem' }}>
                <label style={{ display: 'block', marginBottom: '0.75rem', fontWeight: '600' }}>
                  Color Palette {filterColor && `- ${getColorName(filterColor)}`}
                </label>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
                  {commonColors.map((color) => (
                    <button
                      key={color}
                      type="button"
                      onClick={() => setFilterColor(color)}
                      style={{
                        display: 'flex',
                        flexDirection: 'column',
                        alignItems: 'center',
                        gap: '0.5rem',
                        background: 'none',
                        border: 'none',
                        cursor: 'pointer',
                        transition: 'all 0.2s'
                      }}
                      title={getColorName(color)}
                    >
                      <div
                        style={{
                          width: '48px',
                          height: '48px',
                          borderRadius: '8px',
                          background: color,
                          border: filterColor === color ? '3px solid #667eea' : '2px solid #ddd',
                          transition: 'all 0.2s',
                          boxShadow: filterColor === color ? '0 2px 8px rgba(102, 126, 234, 0.3)' : 'none'
                        }}
                      />
                      <span style={{ fontSize: '0.75rem', fontWeight: '500', textAlign: 'center', color: 'var(--text-primary)' }}>
                        {getColorName(color)}
                      </span>
                    </button>
                  ))}
                </div>
                {filterColor && (
                  <div style={{ 
                    padding: '0.75rem', 
                    background: '#f0f4ff', 
                    borderRadius: '4px', 
                    marginBottom: '0.5rem',
                    textAlign: 'center',
                    fontWeight: '500',
                    color: '#667eea'
                  }}>
                    ✓ Selected: {getColorName(filterColor)}
                  </div>
                )}
              </div>

              {/* Grid of filter selects */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '1rem',
                marginBottom: '1rem'
              }}>
                <div className="form-group">
                  <label>Category</label>
                  <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
                    <option value="">All Categories</option>
                    <option value="shirt">Shirt</option>
                    <option value="pants">Pants</option>
                    <option value="dress">Dress</option>
                    <option value="shoes">Shoes</option>
                    <option value="cardigan">Cardigan</option>
                    <option value="trench_coat">Coat</option>
                    <option value="jacket">Jacket</option>
                    <option value="blazer">Blazer</option>
                    <option value="skirt">Skirt</option>
                    <option value="shorts">Shorts</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Style</label>
                  <select value={filterStyle} onChange={(e) => setFilterStyle(e.target.value)}>
                    <option value="">All Styles</option>
                    <option value="casual">Casual</option>
                    <option value="formal">Formal</option>
                    <option value="professional">Professional</option>
                    <option value="trendy">Trendy</option>
                    <option value="bohemian">Bohemian</option>
                    <option value="minimal">Minimal</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Season</label>
                  <select value={filterSeason} onChange={(e) => setFilterSeason(e.target.value)}>
                    <option value="">All Seasons</option>
                    <option value="spring">Spring</option>
                    <option value="summer">Summer</option>
                    <option value="fall">Fall</option>
                    <option value="winter">Winter</option>
                    <option value="all-season">All-Season</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Fabric</label>
                  <select value={filterFabric} onChange={(e) => setFilterFabric(e.target.value)}>
                    <option value="">All Fabrics</option>
                    <option value="cotton">Cotton</option>
                    <option value="denim">Denim</option>
                    <option value="knit">Knit</option>
                    <option value="wool">Wool</option>
                    <option value="linen">Linen</option>
                    <option value="silk">Silk</option>
                    <option value="synthetic">Synthetic</option>
                    <option value="leather">Leather</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>Occasion</label>
                  <select value={filterOccasion} onChange={(e) => setFilterOccasion(e.target.value)}>
                    <option value="">All Occasions</option>
                    {occasions.map((occ) => (
                      <option key={occ} value={occ}>{occ}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <button className="btn btn-primary" onClick={handleFilter} disabled={loading}>
            {loading ? 'Filtering...' : '🔍 Apply Filters'}
          </button>
          <button className="btn btn-secondary" onClick={handleClearFilters}>
            ✕ Clear All
          </button>
        </div>
      </div>

      {loading && <div className="spinner"></div>}

      {garments.length > 0 && (
        <div className="card">
          <h2>Results ({garments.length})</h2>
          <div className="grid-4">
            {garments.map((garment) => {
              const nearestColor = getNearestPaletteColor(garment.color, commonColors);
              // Non-clothing items that shouldn't show style/season
              const nonClothingCategories = ['watch', 'shoes', 'accessory', 'bag', 'jewelry', 'hat', 'scarf', 'belt', 'sunglasses'];
              const isClothing = !nonClothingCategories.includes(garment.category?.toLowerCase());
              
              return (
                <div key={garment.id} className="garment-item">
                  <img
                    src={`/image/${garment.filename}`}
                    alt={garment.filename}
                    className="garment-image"
                    onError={(e) => (e.target.src = 'https://via.placeholder.com/200x200?text=No+Image')}
                  />
                  <div className="garment-info">
                    <div className="garment-category">{garment.category}</div>
                    <div className="garment-color">
                      <div
                        className="color-swatch"
                        style={{ backgroundColor: garment.color }}
                      ></div>
                      {getColorName(garment.color)}
                    </div>
                    {isClothing && (
                      <small style={{ color: '#999' }}>
                        {garment.style} • {garment.season} • {garment.fabric || 'unknown fabric'}
                      </small>
                    )}
                    {!isClothing && (
                      <small style={{ color: '#999' }}>
                        {garment.fabric || 'accessory'}
                      </small>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {!loading && garments.length === 0 && (searchQuery || filterCategory || filterStyle || filterSeason || filterColor || filterFabric) && (
        <div className="card">
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <div className="empty-title">No items found</div>
            <p className="empty-description">Try adjusting your filters or search query</p>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
