# 🏎️ AutoValuate Pro — Enterprise Automotive Valuation & Market Intelligence                                    
  
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python)](https://www.python.org/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Scikit--Learn-F7931E?style=flat-square&logo=scikit-learn)](https://scikit-learn.org/) 
[![Vercel](https://img.shields.io/badge/Deploy-Vercel-000000?style=flat-square&logo=vercel)](https://vercel.com)

**AutoValuate Pro** is a commercial-grade vehicle valuation engine and automotive market analytics platform. It provides real-time resale price predictions in Indian Rupees (₹ Lakhs & Crores) and USD, 5-year depreciation schedules, side-by-side vehicle comparisons, and exportable official valuation certificates.

---

## 🔥 Key Features

- **🇮🇳 Indian Rupee Valuation**: Formatted in standard Indian notation (`₹ 11.90 Lakh`, `₹ 24.50 Lakh`, `₹ 1.25 Cr`) & full Rupees (`₹ 11,89,875`).
- **🌐 Global Multi-Currency Switcher**: Toggle between **🇮🇳 ₹ INR (Lakhs)** and **🇺🇸 $ USD** dynamically.
- **📊 3-Way Valuation Matrix**:
  - Ex-Showroom New Car Tag
  - Private Resale Market Value
  - Instant Dealer Cash Trade-in Payout
- **🏎️ Dynamic 3D Vehicle Category Visualizer**: High-resolution renders for Sedans, Hatchbacks, Convertibles, Wagons/SUVs, and Coupes.
- **⚔️ Side-by-Side Car Comparison**: Compare two vehicle configurations side-by-side with visual cards and price variance summaries.
- **📈 5-Year Depreciation Schedule**: Track retained vehicle value across 1, 2, 3, and 5-year ownership horizons.
- **📜 1-Click Printable Valuation Certificate**: Export official valuation report documents formatted for PDF/Print.
- **🎨 Glassmorphic Dark Theme**: Modern dark mode UI (`#070913`) built with CSS blur cards and glowing metric accents.

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, CSS3 Glassmorphic Styling, JavaScript (ES6+), Chart.js
- **Backend API**: FastAPI, Uvicorn, Pydantic
- **Machine Learning Engine**: Scikit-Learn (Random Forest, Gradient Boosting, XGBoost), Pandas, NumPy, Joblib
- **Deployment**: Vercel Serverless Functions / Python Runtime

---

## ⚡ Quick Start

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/YOUR_USERNAME/AutoValuate-Pro.git
cd AutoValuate-Pro
pip install -r requirements.txt
```

### 2. Train Model Pipeline (Optional)
```bash
python train_model.py
```

### 3. Run Application Server
```bash
python -m uvicorn app:app --reload --port 8000
```
Open **`http://127.0.0.1:8000`** in your browser.
