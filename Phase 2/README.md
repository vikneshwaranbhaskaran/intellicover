# IntelliCover - Social Security for Gig Workers

IntelliCover is an AI-powered micro-insurance platform designed specifically for the Indian gig economy. It provides on-demand protection against weather-related disruptions (heavy rain, heatwaves), strike-related protests, and severe pollution, enabling income stabilization for delivery partners and gig workers.

## Key Features

- **🛡️ Real-Time Protection Status**: Active monitoring of coverage based on live API metrics.
- **🌤️ AI Disruption Verification**: Uses Gemini AI to match claims with local weather (Open-Meteo), news (Google RSS), and traffic (G-Maps Traffic) APIs.
- **⚡ Dynamic Pricing**: Premiums adjust based on live city-level risk profiles.
- **📍 GPS Precision**: Claims are verified within a 5-10km radius of the user's location.
- **💰 Income Stabilization**: Automated payout calculations based on typical daily earnings for a seamless experience.

## Tech Stack

- **Frontend**: Static HTML5, CSS3, Vanilla JavaScript (Fast, minimal, and mobile-responsive).
- **Backend**: FastAPI (Python), uvicorn, SQLite for persistence.
- **AI Engine**: Google Gemini 1.5 Flash (via `google-generativeai`).
- **External APIs**: Open-Meteo (Weather), Google News RSS, Maps Traffic Simulation.

## Setup Instructions

### 1. Prerequisite
Ensure Python 3.9+ is installed and configured in your path.

### 2. Backend Setup
1. Navigate to the `backend/` folder.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file from the example:
   ```
   GEMINI_API_KEY=YOUR_GEMINI_API_KEY
   ```
5. Start the backend:
   ```bash
   uvicorn main:app --reload --port 8000
   ```

### 3. Frontend Setup
1. Navigate to the `Phase 2/` root directory.
2. Start a simple web server:
   ```bash
   python -m http.server 8080
   ```
3. Open `http://localhost:8080` in your browser.

## Project Structure

```text
Phase 2/
├── index.html        # Main Application UI
├── .gitignore        # Git exclusion rules
├── README.md         # This documentation
└── backend/          # FastAPI Implementation
    ├── main.py       # Core Logic (AI, Database, APIs)
    ├── .env          # API Keys (Excluded from Git)
    └── app.db        # SQLite Database (Excluded from Git)
```

---
*Created for the 45-Day Problem Statement Challenge. Built with AI-Integration for Social Good.*
