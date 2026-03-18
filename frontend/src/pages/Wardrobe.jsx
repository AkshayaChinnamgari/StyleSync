import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { wardrobeAPI, recommendationAPI, profileAPI } from '../api';
import '../styles.css';

export default function Wardrobe() {
  const navigate = useNavigate();
  const [garments, setGarments] = useState([]);
  const [filteredGarments, setFilteredGarments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [categories, setCategories] = useState(null);
  const [pairingModal, setPairingModal] = useState(null);
  const [pairingLoading, setPairingLoading] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [previewData, setPreviewData] = useState(null);
  const [editedCategory, setEditedCategory] = useState('');
  const [selectedItems, setSelectedItems] = useState([]);
  const [pendingFiles, setPendingFiles] = useState([]);
  const [pendingIndex, setPendingIndex] = useState(0);
  const username = localStorage.getItem('username');
  const [avatarUrl, setAvatarUrl] = useState('');

  useEffect(() => {
    fetchGarments();
    fetchCategories();
    profileAPI.getProfile().then((res) => setAvatarUrl(res.data.avatar_url || '')).catch(() => {});
  }, []);

  useEffect(() => {
    // Filter garments based on selected category
    if (selectedCategory === 'all') {
      setFilteredGarments(garments);
    } else {
      setFilteredGarments(garments.filter(g => g.category === selectedCategory));
    }
  }, [selectedCategory, garments]);

  // Keyboard shortcut to clear selections
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setSelectedItems([]);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Multi-select functions
  const toggleSelect = (id) => {
    setSelectedItems(prev =>
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  const selectAllItems = () => {
    if (selectedItems.length === filteredGarments.length) {
      setSelectedItems([]);
    } else {
      const allIds = filteredGarments.map(g => g.id);
      setSelectedItems(allIds);
    }
  };

  const deleteSelected = async () => {
    if (selectedItems.length === 0) {
      alert("No items selected");
      return;
    }

    if (!window.confirm(`Delete ${selectedItems.length} selected item(s)?`)) return;

    try {
      await Promise.all(selectedItems.map(id => wardrobeAPI.deleteItem(id)));
      setSelectedItems([]);
      await fetchGarments();
      await fetchCategories();
    } catch (err) {
      setError('Bulk delete failed');
      console.error(err);
    }
  };

  const fetchGarments = async () => {
    try {
      const response = await wardrobeAPI.getItems();
      setGarments(response.data);
      setError('');
    } catch (err) {
      setError('Failed to load wardrobe');
    } finally {
      setLoading(false);
    }
  };

  const fetchCategories = async () => {
    try {
      const response = await wardrobeAPI.getCategories();
      setCategories(response.data);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const startPreviewForFile = async (file) => {
    const response = await wardrobeAPI.detectGarment(file);
    setPreviewData({
      file,
      fileUrl: URL.createObjectURL(file),
      category: response.data.category,
      style: response.data.style,
      season: response.data.season,
      fabric: response.data.fabric,
      color: response.data.color
    });
    setEditedCategory(response.data.category);
    setShowPreview(true);
  };

  const handleCreateOutfit = async (garmentId) => {
    setPairingLoading(true);
    try {
      const response = await recommendationAPI.pairWith(garmentId);
      setPairingModal(response.data);
    } catch (err) {
      setError('Failed to generate outfit suggestions');
      console.error(err);
    } finally {
      setPairingLoading(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFiles.length) return;

    setUploading(true);
    setError('');
    try {
      if (selectedFiles.length >= 1) {
        // Queue files for sequential preview
        setPendingFiles(selectedFiles);
        setPendingIndex(0);
        await startPreviewForFile(selectedFiles[0]);
      }
    } catch (err) {
      console.error('Detection error:', err);
      setError(err.response?.data?.detail || 'Detection failed');
    } finally {
      setUploading(false);
    }
  };

  const handleConfirmUpload = async () => {
    setUploading(true);
    try {
      // Step 2: Save to wardrobe with final category
      const formData = new FormData();
      formData.append('file', previewData.file);
      formData.append('category', editedCategory);
      
      await wardrobeAPI.uploadGarmentWithCategory(formData);
      
      // Reset and refresh
      setShowPreview(false);
      setPreviewData(null);
      setEditedCategory('');
      setError('');
      await fetchGarments();
      await fetchCategories();

      const nextIndex = pendingIndex + 1;
      if (pendingFiles.length && nextIndex < pendingFiles.length) {
        setPendingIndex(nextIndex);
        await startPreviewForFile(pendingFiles[nextIndex]);
      } else {
        setSelectedFiles([]);
        setPendingFiles([]);
        setPendingIndex(0);
        document.querySelector('input[type="file"]').value = '';
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleCancelPreview = () => {
    setShowPreview(false);
    setPreviewData(null);
    setEditedCategory('');
    setSelectedFiles([]);
    setPendingFiles([]);
    setPendingIndex(0);
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this garment?')) return;
    try {
      await wardrobeAPI.deleteItem(id);
      await fetchGarments();
    } catch (err) {
      setError('Delete failed');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length) {
      setSelectedFiles(Array.from(e.dataTransfer.files));
    }
  };

  return (
    <div className="wardrobe-page">
      <div className="container wardrobe-container">
        {/* Header with Profile Avatar */}
        <div className="wardrobe-header">
          <div className="header-left">
            <div className="header-avatar-ring" onClick={() => navigate('/profile')} title="View Profile">
              <div className="header-profile">
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt="avatar"
                    style={{ width: '100%', height: '100%', borderRadius: '50%', objectFit: 'cover' }}
                  />
                ) : (
                  username ? username[0].toUpperCase() : '👤'
                )}
              </div>
            </div>
            <h1>My Wardrobe</h1>
          </div>
          
          <div className="button-group">
            <button className="suggest-btn" onClick={() => navigate('/recommendations?tab=occasions')}>
              Mix & Match
            </button>
            <button className="color-suggest-btn" onClick={() => navigate('/recommendations?tab=color')}>
              Color Harmony
            </button>
            <button className="weather-suggest-btn" onClick={() => navigate('/recommendations?tab=today')}>
              Weather-Based
            </button>
            <button className="btn btn-secondary" onClick={() => navigate('/dashboard')}>
              ← Dashboard
            </button>
          </div>
        </div>

      <div className="card upload-card">
        <h2>Upload New Item</h2>
        {error && <div className="alert alert-error">{error}</div>}

        <form onSubmit={handleUpload}>
          <div
            className={`upload-bar ${dragOver ? 'drag-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
          >
            <label className="file-label" htmlFor="wardrobe-file-input">
              📁 Browse Files
              <input
                id="wardrobe-file-input"
                type="file"
                accept="image/*"
                multiple
                onChange={(e) => setSelectedFiles(Array.from(e.target.files || []))}
              />
            </label>

            <span className="file-name">
              {selectedFiles.length
                ? `${selectedFiles.length} file(s) selected`
                : 'Drag & drop images here or browse'}
            </span>

            <button
              type="submit"
              className="upload-btn"
              disabled={!selectedFiles.length || uploading}
            >
              {uploading ? '⏳ Processing...' : selectedFiles.length > 1 ? '⬆ Upload All' : '🔍 Analyze'}
            </button>
          </div>
        </form>
      </div>

      <div className="card items-card">
        <h2>Wardrobe Items ({filteredGarments.length})</h2>

        {/* Category Filter */}
        {categories && categories.categories && (
          <div className="category-filter">
            <button
              className={`filter-btn ${selectedCategory === 'all' ? 'active' : ''}`}
              onClick={() => setSelectedCategory('all')}
            >
              All ({categories.total_items || garments.length})
            </button>
            {categories.categories.map((cat) => (
              <button
                key={cat.name}
                className={`filter-btn ${selectedCategory === cat.name ? 'active' : ''}`}
                onClick={() => setSelectedCategory(cat.name)}
              >
                {cat.name} ({cat.count})
              </button>
            ))}
          </div>
        )}

        {/* Select All and Delete Selected Controls */}
        {filteredGarments.length > 0 && (
          <div className="select-all-container">
            <button className="select-all-btn" onClick={selectAllItems}>
              {selectedItems.length === filteredGarments.length ? 'Unselect All' : 'Select All'}
            </button>
            {selectedItems.length > 0 && (
              <button className="delete-selected-btn" onClick={deleteSelected}>
                🗑 Delete Selected ({selectedItems.length})
              </button>
            )}
          </div>
        )}

        {loading ? (
          <div className="spinner"></div>
        ) : filteredGarments.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">👕</div>
            <div className="empty-title">No items in this category</div>
            <p className="empty-description">Try selecting a different category or upload new items</p>
          </div>
        ) : (
          <div className="items-grid">
            {filteredGarments.map((garment) => (
              <div key={garment.id} className="item">
                <input
                  type="checkbox"
                  className="select-box"
                  checked={selectedItems.includes(garment.id)}
                  onChange={() => toggleSelect(garment.id)}
                />
                <img
                  src={`/image/${garment.filename}`}
                  alt={garment.filename}
                  onError={(e) => (e.target.src = 'https://via.placeholder.com/200x200?text=No+Image')}
                />
                <p><strong>{garment.category}</strong></p>
                <div className="color-row">
                  <div className="color-circle" style={{ backgroundColor: garment.color }}></div>
                  <p>{garment.color}</p>
                </div>
                {!['watch', 'necklace', 'bracelet', 'earrings', 'hat', 'gloves', 'scarf', 'belt', 'bag'].includes(garment.category.toLowerCase()) ? (
                  <small style={{ color: '#777', display: 'block', marginTop: '4px' }}>
                    Style: {garment.style} • Season: {garment.season} • Fabric: {garment.fabric || 'unknown'}
                  </small>
                ) : (
                  <small style={{ color: '#777', display: 'block', marginTop: '4px' }}>
                    Style: {garment.style}
                  </small>
                )}
                <button className="suggest-btn" onClick={() => handleCreateOutfit(garment.id)}>
                  🎨 Create Outfit
                </button>
                <button className="delete-btn" onClick={() => handleDelete(garment.id)}>
                  🗑 Delete
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pairing Modal */}
      {pairingModal && (
        <div className="modal-overlay" onClick={() => setPairingModal(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setPairingModal(null)}>✕</button>
            
            <h2>🎨 Outfit Suggestions</h2>
            
            {/* Base Garment */}
            <div style={{ marginBottom: '2rem' }}>
              <h3>Selected Item:</h3>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <img
                  src={`/image/${pairingModal.base_garment.filename}`}
                  alt="base"
                  style={{
                    width: '100px',
                    height: '120px',
                    objectFit: 'contain',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '8px'
                  }}
                />
                <div>
                  <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>
                    {pairingModal.base_garment.category.toUpperCase()}
                  </div>
                  <div style={{ color: '#666', fontSize: '0.9rem' }}>
                    Style: {pairingModal.base_garment.style} • Season: {pairingModal.base_garment.season}
                  </div>
                  <div style={{ color: '#999', fontSize: '0.85rem', marginTop: '0.5rem' }}>
                    Color: {pairingModal.base_garment.color} • Fabric: {pairingModal.base_garment.fabric || 'unknown'}
                  </div>
                </div>
              </div>
            </div>

            {/* Suggestions */}
            <div>
              <h3>{pairingModal.message}</h3>
              {pairingLoading ? (
                <div className="spinner"></div>
              ) : pairingModal.suggestions && pairingModal.suggestions.length > 0 ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(100px, 1fr))', gap: '1rem' }}>
                  {pairingModal.suggestions.map((garment) => (
                    <div key={garment.id} style={{ textAlign: 'center' }}>
                      <img
                        src={`/image/${garment.filename}`}
                        alt={garment.category}
                        style={{
                          width: '100%',
                          height: '120px',
                          objectFit: 'contain',
                          backgroundColor: '#f5f5f5',
                          borderRadius: '8px',
                          marginBottom: '0.5rem'
                        }}
                      />
                      <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>
                        {garment.category}
                      </div>
                      <small style={{ color: '#666', display: 'block' }}>
                        {garment.style}
                      </small>
                    </div>
                  ))}
                </div>
              ) : (
                <p style={{ color: '#999' }}>No matching items found. Try adding more garments!</p>
              )}
            </div>

            <button 
              className="btn btn-primary" 
              onClick={() => setPairingModal(null)}
              style={{ marginTop: '2rem', width: '100%' }}
            >
              Close
            </button>
          </div>
        </div>
      )}

      {/* Preview & Edit Modal */}
      {showPreview && previewData && (
        <div className="modal-overlay" onClick={handleCancelPreview}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '500px' }}>
            <button className="modal-close" onClick={handleCancelPreview}>✕</button>
            
            <h2>🔍 Review Detected Item</h2>
            
            <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
              <img
                src={previewData.fileUrl}
                alt="Preview"
                style={{
                  maxWidth: '100%',
                  height: '250px',
                  objectFit: 'contain',
                  backgroundColor: '#f5f5f5',
                  borderRadius: '8px',
                  padding: '1rem'
                }}
              />
            </div>

            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600', fontSize: '1.1rem' }}>
                Category <span style={{ color: '#667eea' }}>(edit if incorrect)</span>:
              </label>
              <select
                value={editedCategory}
                onChange={(e) => setEditedCategory(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.75rem',
                  border: '2px solid #667eea',
                  borderRadius: '8px',
                  fontSize: '1rem',
                  fontWeight: '600'
                }}
              >
                <optgroup label="👕 Tops">
                  <option value="shirt">Shirt / T-shirt / Top</option>
                  <option value="cardigan">Cardigan / Sweater</option>
                  <option value="jacket">Jacket</option>
                  <option value="blazer">Blazer</option>
                </optgroup>
                <optgroup label="👖 Bottoms">
                  <option value="pants">Pants / Jeans / Trousers</option>
                  <option value="shorts">Shorts</option>
                  <option value="skirt">Skirt</option>
                </optgroup>
                <optgroup label="👗 Full Body">
                  <option value="dress">Dress</option>
                  <option value="kurta">Kurta / Kurti</option>
                </optgroup>
                <optgroup label="🧥 Outerwear">
                  <option value="trench_coat">Trench Coat</option>
                </optgroup>
                <optgroup label="👞 Footwear">
                  <option value="shoes">Shoes</option>
                  <option value="boots">Boots</option>
                  <option value="sandals">Sandals</option>
                </optgroup>
                <optgroup label="💍 Accessories">
                  <option value="necklace">Necklace</option>
                  <option value="bracelet">Bracelet</option>
                  <option value="earrings">Earrings</option>
                  <option value="watch">Watch</option>
                  <option value="hat">Hat</option>
                  <option value="scarf">Scarf</option>
                  <option value="belt">Belt</option>
                  <option value="bag">Bag</option>
                </optgroup>
              </select>
            </div>

            <div style={{ fontSize: '0.9rem', color: '#666', marginBottom: '1.5rem', padding: '1rem', backgroundColor: '#f8f9fa', borderRadius: '8px' }}>
              <div><strong>Detected:</strong> {previewData.category}</div>
              <div><strong>Style:</strong> {previewData.style}</div>
              <div><strong>Season:</strong> {previewData.season}</div>
              <div><strong>Fabric:</strong> {previewData.fabric || 'unknown'}</div>
              <div><strong>Color:</strong> <span style={{ display: 'inline-block', width: '20px', height: '20px', backgroundColor: previewData.color, border: '1px solid #ddd', borderRadius: '3px', verticalAlign: 'middle', marginLeft: '5px' }}></span> {previewData.color}</div>
            </div>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button 
                className="btn btn-secondary" 
                onClick={handleCancelPreview}
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <button 
                className="btn btn-primary" 
                onClick={handleConfirmUpload}
                disabled={uploading}
                style={{ flex: 1 }}
              >
                {uploading ? '⏳ Saving...' : '✅ Save to Wardrobe'}
              </button>
            </div>
          </div>
        </div>
      )}
      </div>
    </div>
  );
}
