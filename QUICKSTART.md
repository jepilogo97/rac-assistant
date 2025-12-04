# RAC Assistant - Quick Start Guide

## 🚀 Quick Start (5 minutes)

### Prerequisites Check

```bash
# Check Python version (need 3.10+)
python --version

# Check Node.js version (need 18+)
node --version
```

### Step 1: Install Dependencies

```bash
# Install backend dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..
```

### Step 2: Configure API Key

1. Get your Google Gemini API Key from: https://makersuite.google.com/app/apikey
2. You'll configure it in the web interface (no need to set it now)

### Step 3: Start Backend

```bash
# From project root
python -m uvicorn main:app --reload
```

✅ Backend running at: http://localhost:8000  
📚 API Docs at: http://localhost:8000/api/docs

### Step 4: Start Frontend

Open a **new terminal** window:

```bash
cd frontend
npm run dev
```

✅ Frontend running at: http://localhost:5173

### Step 5: Open Application

1. Open your browser to: http://localhost:5173
2. Click "Configurar API Key" in the header
3. Paste your Google Gemini API Key
4. Click "Guardar"

### Step 6: Upload a File

1. Go to "Carga de Datos" tab
2. Drag and drop an Excel file or click to select
3. Wait for validation
4. Explore the data preview

## 🎯 What's Working

✅ **Fully Functional:**
- File upload with drag & drop
- Data validation
- API key configuration
- Theme toggle (light/dark)
- Responsive layout

🚧 **In Development:**
- BPMN visualization
- Lean classification
- Activity segmentation
- TO-BE proposals
- KPIs dashboard

## 📁 Example Files

Example Excel files are in the `files-example/` directory. Use these to test the application.

## 🔧 Troubleshooting

### Port Already in Use

**Backend:**
```bash
python -m uvicorn main:app --reload --port 8001
```

**Frontend:**
```bash
npm run dev -- --port 3000
```

Then update `frontend/.env`:
```
VITE_API_URL=http://localhost:8001
```

### Module Not Found

```bash
# Backend
pip install -r requirements.txt --force-reinstall

# Frontend
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### CORS Error

Make sure both backend and frontend are running on the correct ports:
- Backend: http://localhost:8000
- Frontend: http://localhost:5173

## 📚 Next Steps

1. **Read the Documentation:**
   - [Installation Guide](INSTALLATION.md)
   - [Migration Summary](MIGRATION_SUMMARY.md)
   - [Walkthrough](walkthrough.md)

2. **Explore the Code:**
   - Backend API: `api/routes/`
   - Frontend Components: `frontend/src/components/`
   - Pages: `frontend/src/pages/`

3. **Contribute:**
   - Implement remaining pages
   - Add tests
   - Improve documentation

## 🆘 Need Help?

- Check the [Installation Guide](INSTALLATION.md)
- Review the [Walkthrough](walkthrough.md)
- Open an issue on GitHub

---

**Happy Coding! 🚀**
