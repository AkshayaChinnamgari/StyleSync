# StyleSync - Setup Guide for Developers

## 🚀 Quick Start (Windows)

### Prerequisites
- Python 3.8+ installed
- Node.js 14+ installed
- Git installed

### Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# On Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Start backend server (runs on http://localhost:8000)
python main.py
```

### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Start frontend development server (runs on http://localhost:3000)
npm start
```

## 📁 Project Structure

```
StyleSync/
├── backend/              # FastAPI application
│   ├── main.py          # Main API file
│   ├── models.py        # Database models
│   ├── auth.py          # Authentication
│   ├── crud.py          # Database operations
│   ├── config.py        # Configuration
│   ├── utils/           # Utility functions
│   ├── services/        # External services
│   └── requirements.txt  # Python dependencies
│
├── frontend/            # React application
│   ├── public/
│   ├── src/
│   │   ├── App.js       # Main component
│   │   ├── api.js       # API client
│   │   ├── pages/       # Page components
│   │   └── styles.css   # Global styles
│   ├── package.json     # Node dependencies
│   └── README.md
│
├── data/                # Data files
├── static/              # Static assets
├── stylesync.db         # SQLite database
└── README.md
```

## 🔑 Key Features

✅ User Authentication (JWT)  
✅ Wardrobe Management  
✅ AI-Powered Garment Classification  
✅ Outfit Recommendations  
✅ Weather-Based Suggestions  
✅ Color Harmony Analysis  
✅ User Analytics & Insights  
✅ Virtual Try-On  

## 🧪 Testing the Application

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### Test Workflow

1. Register a new user at http://localhost:3000
2. Upload clothing items to your wardrobe
3. Navigate to Recommendations to get outfit suggestions
4. Use Search to filter items by color, style, season
5. Check Analytics for wardrobe insights

## 📋 Environment Variables

No `.env` file needed for development! The app uses defaults:

| Variable | Default | Purpose |
|----------|---------|---------|
| SECRET_KEY | dev-only-change-me | JWT signing |
| OPENWEATHER_API_KEY | (optional) | Weather API |
| CORS_ALLOW_ORIGINS | http://localhost:3000 | Frontend URL |

## 🐛 Troubleshooting

### Backend Issues

**Issue**: `No module named 'tensorflow'`  
**Solution**: Run `pip install -r requirements.txt` in the backend directory

**Issue**: `Port 8000 already in use`  
**Solution**: Kill the process using port 8000 or change the port in `main.py`

### Frontend Issues

**Issue**: `npm: command not found`  
**Solution**: Install Node.js from https://nodejs.org/

**Issue**: `Cannot find module 'react'`  
**Solution**: Run `npm install` in the frontend directory

**Issue**: `Port 3000 already in use`  
**Solution**: Kill the process using port 3000 or use `PORT=3001 npm start`

## 📝 Development Workflow

1. Create a new branch for features:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Commit with clear messages:
   ```bash
   git commit -m "Add feature description"
   ```

4. Push and create a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

## 🔗 API Endpoints (Quick Reference)

### Authentication
- `POST /auth/register` - Register user
- `POST /auth/login` - Login user
- `GET /auth/me` - Get current user

### Wardrobe
- `POST /wardrobe/upload` - Upload garment
- `GET /wardrobe/items` - Get all items
- `DELETE /wardrobe/items/{id}` - Delete item

### Recommendations
- `POST /recommendations/outfit` - Get outfit recommendation
- `GET /recommendations/what-to-wear-today` - Daily suggestion

### Analytics
- `GET /analytics/wardrobe-summary` - Wardrobe stats
- `GET /analytics/style-profile` - Style analysis
- `GET /style/profile` - Personal profile

Full API docs: http://localhost:8000/docs

## 💡 Tips

- Keep the backend running while developing frontend
- Use React DevTools browser extension for easier debugging
- Check API documentation at `/docs` endpoint
- Database is auto-created on first run

## 🤝 Contributing

1. Always work on feature branches
2. Update requirements.txt if adding Python packages
3. Update package.json if adding Node packages
4. Test your changes before pushing
5. Write clear commit messages

## 📞 Need Help?

Check the documentation or reach out to the team!

---

**Happy coding! 🚀**
