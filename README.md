# 🛡️ ScamGuard AI — Tourist Price Scam Prevention System

An AI-powered Django web platform that helps tourists detect overpricing, tourist scams, fake products, inflated taxi fares, fake tour guides, manipulated restaurant bills, and suspicious vendors using **AI (Groq/LangChain)**, **OCR**, **geospatial intelligence**, **community reporting**, and **analytics dashboards**.

---

## 🚀 Quick Start

### 1. Clone & Setup Environment
```bash
cd tourist-scam-prevention
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
copy .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### 4. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Admin User
```bash
python manage.py createsuperuser
```

### 6. Run Development Server
```bash
python manage.py runserver
```

Visit **http://127.0.0.1:8000** — you'll see the landing page.

---

## 🏗️ Project Structure

```
tourist-scam-prevention/
├── scamguard/              # Django project settings
│   ├── settings.py         # Configuration
│   ├── urls.py             # Root URL routing
│   ├── wsgi.py / asgi.py   # Deployment
├── accounts/               # User auth, profiles, travel history
├── scams/                  # Scam reports, bills, OCR, price check
├── vendors/                # Trusted vendor listings & reviews
├── ai_engine/              # Groq AI, LangChain, OCR, assistant
├── analytics/              # Analytics dashboard & charts
├── alerts/                 # Real-time scam alerts
├── templates/              # All HTML templates
├── static/                 # CSS, JS, images
├── media/                  # User uploads
├── requirements.txt
├── Procfile                # Render/Railway deployment
└── manage.py
```

---

## ✨ Features

| Feature | Description |
|---------|------------|
| **AI Price Verification** | Verify any price against local market rates using Groq AI |
| **OCR Bill Analyzer** | Upload bills/receipts, AI extracts text and detects suspicious charges |
| **Scam Reporting** | Community-powered scam reports with AI classification |
| **Trusted Vendors** | Verified vendor listings with trust scores and reviews |
| **AI Tourist Assistant** | Chat with AI about safety, prices, and local tips |
| **Scam Heatmaps** | Interactive Leaflet.js maps showing scam hotspots |
| **Real-time Alerts** | Get notified about active scams in your area |
| **Admin Dashboard** | Comprehensive analytics with Chart.js visualizations |
| **User Profiles** | Badges, trust scores, travel history |

---

## 🤖 AI Integration

- **Groq API** — LLaMA 3.3 70B for scam analysis, price verification, and chat
- **LangChain** — AI orchestration framework
- **OCR (Pytesseract)** — Bill text extraction
- **SentenceTransformers** — Semantic duplicate report detection

### Setup Groq API
1. Get your API key from [console.groq.com](https://console.groq.com)
2. Add to `.env`: `GROQ_API_KEY=your-key-here`

---

## 🗺️ Maps Integration

- **Leaflet.js** + **OpenStreetMap** for scam heatmaps and vendor maps
- Dark CARTO basemap tiles
- Color-coded severity markers

---

## 🚀 Deployment (Render/Railway)

1. Push to GitHub
2. Connect to Render/Railway
3. Set environment variables:
   - `SECRET_KEY` — Generate a secure key
   - `GROQ_API_KEY` — Your Groq API key
   - `DATABASE_URL` — PostgreSQL URL (provided by platform)
   - `DEBUG` — `False`
   - `ALLOWED_HOSTS` — Your domain

---

## 📊 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 4.2+ |
| Frontend | Django Templates, Bootstrap 5, Custom CSS |
| Database | SQLite (dev) / PostgreSQL (prod) |
| AI | Groq API, LangChain, Pytesseract, SentenceTransformers |
| Maps | Leaflet.js, OpenStreetMap, CARTO tiles |
| Charts | Chart.js |
| Auth | Django Authentication |
| Deployment | Render/Railway, Gunicorn, WhiteNoise |

---

## 📝 License

Built for educational and demonstration purposes.

## Added Trip Planner Feature