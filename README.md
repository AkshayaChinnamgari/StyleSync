# StyleSync - AI Wardrobe Companion

## 🚀 Quick Setup for Developers

### Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/StyleSync.git
cd StyleSync
```

### Automatic Setup (Recommended)

**Windows:**
```bash
./setup.bat
```

**macOS/Linux:**
```bash
chmod +x setup.sh
./setup.sh
```

### Manual Setup

See [SETUP_FOR_TEAMMATES.md](SETUP_FOR_TEAMMATES.md) for detailed instructions.

---

## 🎨 Project Overview

StyleSync is a full-stack AI-powered wardrobe companion application that helps users manage their clothing collections, get personalized outfit recommendations, and make smarter fashion choices. The application leverages computer vision and machine learning to analyze clothes and provide intelligent styling suggestions.

## ✨ Features

### User Wardrobe Management
- ✅ Upload pictures of clothing items
- ✅ Automatic image analysis (color detection, category classification)
- ✅ Organize items by category, style, and season
- ✅ Add custom descriptions and metadata

### AI-Powered Outfit Recommendations
- ✅ Get outfit suggestions for different occasions (casual, formal, professional, party)
- ✅ Weather-aware recommendations
- ✅ Color harmony analysis
- ✅ "What to wear today" based on current weather

### Search & Filter Functionality
- ✅ Advanced search by name, brand, or description
- ✅ Filter by category, color, style, and season
- ✅ Quick access to wardrobe items

### Style Analysis
- ✅ Color combination suggestions
- ✅ Personal style preferences tracking
- ✅ Outfit history with ratings

### Additional Features
- ✅ User authentication with JWT tokens
- ✅ Virtual outfit preview generation
- ✅ Weather integration via OpenWeatherMap API
- ✅ Responsive modern UI

## 🏗️ Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT (python-jose)
- **Image Processing**: PIL, rembg, TensorFlow/MobileNetV2
- **Weather API**: OpenWeatherMap
- **Server**: Uvicorn

### Frontend
- **Framework**: React 19.2.0
- **Routing**: React Router v6
- **HTTP Client**: Axios
- **Styling**: CSS3 with Gradients and Animations

## 📋 Project Structure

```
StyleSync/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── models.py               # SQLAlchemy models (User, Garment, OutfitHistory, etc.)
│   ├── database.py             # Database configuration
│   ├── crud.py                 # CRUD operations
│   ├── auth.py                 # Authentication & JWT
│   ├── requirements.txt         # Python dependencies
│   ├── utils/
│   │   ├── classify.py         # Garment classification using MobileNetV2
│   │   ├── image_utils.py      # Image processing & color extraction
│   │   ├── recommend.py        # Recommendation engine
│   │   └── virtual_tryon.py    # Outfit preview generation
│   ├── services/
│   │   └── weather.py          # Weather API integration
│   └── static/
│       └── uploads/            # Uploaded images
│
├── frontend/
│   ├── package.json
│   ├── src/
│   │   ├── App.js              # Main application component
│   │   ├── api.js              # API client configuration
│   │   ├── App.css             # Main styles (legacy)
│   │   ├── styles.css          # Updated comprehensive styles
│   │   ├── index.js
│   │   ├── pages/
│   │   │   ├── Login.jsx       # User login page
│   │   │   ├── Register.jsx    # User registration page
│   │   │   ├── Wardrobe.jsx    # Wardrobe management
│   │   │   ├── Recommendations.jsx  # Outfit recommendations
│   │   │   └── Search.jsx      # Search & filter
│   │   └── [other files]
│   └── public/
│
└── docs/
    └── requirements.md         # Feature requirements
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 14+ and npm
- Git

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the server**
   ```bash
   uvicorn main:app --reload
   ```
   The API will be available at `http://localhost:8000`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start the development server**
   ```bash
   npm start
   ```
   The app will open at `http://localhost:3000`

## 🔑 API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user info

### Wardrobe Management
- `POST /wardrobe/upload` - Upload clothing item
- `GET /wardrobe/items` - Get all wardrobe items
- `GET /wardrobe/items/{id}` - Get specific item
- `PUT /wardrobe/items/{id}` - Update item
- `DELETE /wardrobe/items/{id}` - Delete item
- `GET /wardrobe/search` - Search items
- `GET /wardrobe/filter` - Filter items by attributes
- `GET /wardrobe/by-category/{category}` - Get items by category

### Recommendations
- `POST /recommendations/outfit` - Get outfit recommendation
- `GET /recommendations/what-to-wear-today` - Get today's suggestion

### Weather
- `GET /weather/{city}` - Get weather information
- `GET /weather-clothing/{city}` - Get clothing recommendations for weather

### Color Analysis
- `GET /colors/harmony/{garment_id}` - Get color-harmonious items

### Outfit Management
- `POST /outfit/create-preview` - Create outfit preview
- `GET /outfit/history` - Get outfit history
- `PUT /outfit/{id}/rate` - Rate an outfit

### User Preferences
- `GET /preferences` - Get user preferences
- `PUT /preferences` - Update preferences

## 🔐 Authentication

The application uses JWT (JSON Web Tokens) for authentication:

1. User registers/logs in and receives a token
2. Token is stored in browser's localStorage
3. All API requests include the token in the Authorization header
4. Token is valid for 30 minutes

## 💾 Database Models

### User
- id, username, email, hashed_password, created_at
- Relationships: garments, outfit_history, preferences

### Garment
- id, user_id, filename, color, category, style, season, size, brand, description
- Relationships: owner (User), outfit_items

### OutfitHistory
- id, user_id, occasion, date, rating, notes
- Relationships: user, outfit_items

### OutfitItem
- id, outfit_id, garment_id
- Junction table for outfit-garment relationship

### UserPreferences
- id, user_id, preferred_colors, preferred_styles, body_type, skin_tone, budget_range

## 🎯 Recommendation Algorithm

The recommendation engine uses:

1. **Occasion-based Filtering**: Different item categories for different occasions
2. **Weather Integration**: Real-time weather data affects recommendations
3. **Color Harmony**: Uses HSV color space to find complementary and analogous colors
4. **User Preferences**: Learns from outfit ratings and history

## 🖼️ Image Processing

1. **Color Extraction**: Removes background using rembg, calculates dominant color
2. **Classification**: Uses pre-trained MobileNetV2 to classify garment type
3. **Virtual Preview**: Generates outfit collages from selected items

## 🌐 Weather Integration

- **API**: OpenWeatherMap (free tier)
- **Updates**: Real-time weather data
- **Recommendations**: Temperature and condition-based clothing suggestions

## 📱 Frontend Features

### Pages
1. **Login/Register** - Authentication
2. **Dashboard** - Home with feature overview
3. **Wardrobe** - Upload and manage items
4. **Recommendations** - Get outfit suggestions
5. **Search** - Search and filter wardrobe

### UI Components
- Responsive grid layouts
- Card-based design
- Form validation
- Error handling
- Loading states
- Empty state placeholders

## 🚀 Future Enhancements

1. **Virtual Try-On**: AR/VR integration for trying outfits
2. **Shopping Integration**: Direct links to buy recommended items
3. **Trend Analysis**: Fashion trend integration
4. **Social Features**: Share outfits with friends
5. **Sustainability**: Track eco-friendly items and suggestions
6. **Conversational AI**: Chat-based styling assistant
7. **Mobile App**: Native iOS/Android applications
8. **Advanced Analytics**: Wardrobe usage statistics

## 🐛 Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Change the port
uvicorn main:app --reload --port 8001
```

**Database errors:**
```bash
# Reset the database
rm stylesync.db
# Restart the server
```

**Image processing issues:**
```bash
# Reinstall image libraries
pip install --upgrade tensorflow pillow rembg
```

### Frontend Issues

**Port 3000 already in use:**
```bash
# Use a different port
PORT=3001 npm start
```

**API connection issues:**
- Ensure backend is running on http://localhost:8000
- Check CORS settings in main.py

## 📝 Configuration

### Backend Configuration
Edit in `main.py`:
- `SECRET_KEY` - Change for production
- `DATABASE_URL` - Change database location
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

### Frontend Configuration
Create `.env` file:
```
REACT_APP_API_URL=http://localhost:8000
```

## 📊 Performance Tips

1. **Image Optimization**: Compress images before uploading
2. **Database**: Add indexes for frequently queried columns
3. **Caching**: Implement Redis for session storage
4. **CDN**: Serve static files via CDN in production

## 🔒 Security Considerations

1. Change `SECRET_KEY` in production
2. Use HTTPS in production
3. Implement rate limiting
4. Validate all user inputs
5. Use environment variables for sensitive data
6. Implement CSRF protection

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

Contributions are welcome! Please follow these steps:
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation
3. Check GitHub issues

## 🎓 Learning Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [SQLAlchemy Tutorial](https://docs.sqlalchemy.org/)
- [MobileNetV2 Paper](https://arxiv.org/abs/1801.04381)

---

**Made with ❤️ for fashion enthusiasts and developers**
