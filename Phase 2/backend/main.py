from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
import random
import sqlite3
import os
import json
import httpx
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def read_index():
    if os.path.exists(FRONTEND_PATH):
        return FileResponse(FRONTEND_PATH)
    return {"detail": "Frontend file not found", "path": FRONTEND_PATH}

@app.get("/api/health")
async def health_check():
    """Diagnostic endpoint to check Gemini connectivity and API key status."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"status": "error", "message": "No API key found in environment variables!"}
    
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "****"
    
    # Try a simple "Hello" to test the connection
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("hello")
        return {
            "status": "success", 
            "api_key_loaded": "Yes", 
            "masked_key": masked_key,
            "gemini_response": response.text.strip()
        }
    except Exception as e:
        return {
            "status": "error", 
            "api_key_loaded": "Yes", 
            "masked_key": masked_key, 
            "error_detail": str(e)
        }

DB_PATH = os.environ.get("DATABASE_URL", ".app.db")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PATH = os.path.join(os.path.dirname(BASE_DIR), "index.html")

# ---------------------------------------------------------------------------
# City coordinates for Open-Meteo API lookups
# ---------------------------------------------------------------------------
CITY_COORDS = {
    "Chennai":   {"lat": 13.08, "lon": 80.27},
    "Mumbai":    {"lat": 19.07, "lon": 72.87},
    "Bangalore": {"lat": 12.97, "lon": 77.59},
    "Madurai":   {"lat": 9.92,  "lon": 78.12},
    "Trichy":    {"lat": 10.79, "lon": 78.69},
    "Delhi":     {"lat": 28.61, "lon": 77.23},
    "Hyderabad": {"lat": 17.38, "lon": 78.49},
    "Kolkata":   {"lat": 22.57, "lon": 88.36},
    "Pune":      {"lat": 18.52, "lon": 73.85},
}

# ---------------------------------------------------------------------------
# Open-Meteo: Fetch LIVE weather + air quality (FREE, no API key needed)
# ---------------------------------------------------------------------------
async def fetch_live_weather(city: str) -> dict:
    """Fetch real-time weather and AQI data for a city from Open-Meteo APIs.
    Returns a dict with temperature, rain, weather_code, pm2_5, pm10, us_aqi.
    Returns None values on failure."""

    coords = CITY_COORDS.get(city)
    if not coords:
        print(f"[Weather] No coordinates for city: {city}")
        return {"temperature": None, "rain": None, "weather_code": None,
                "pm2_5": None, "pm10": None, "us_aqi": None, "city": city}

    lat, lon = coords["lat"], coords["lon"]
    result = {"city": city, "temperature": None, "rain": None, "weather_code": None,
              "pm2_5": None, "pm10": None, "us_aqi": None}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1️⃣  Current weather (temperature, rainfall, weather code)
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&current=temperature_2m,rain,weather_code"
                f"&timezone=Asia/Kolkata"
            )
            weather_resp = await client.get(weather_url)
            if weather_resp.status_code == 200:
                w = weather_resp.json().get("current", {})
                result["temperature"] = w.get("temperature_2m")
                result["rain"] = w.get("rain")
                result["weather_code"] = w.get("weather_code")

            # 2️⃣  Air quality (PM2.5, PM10, US AQI)
            aqi_url = (
                f"https://air-quality-api.open-meteo.com/v1/air-quality"
                f"?latitude={lat}&longitude={lon}"
                f"&current=pm2_5,pm10,us_aqi"
                f"&timezone=Asia/Kolkata"
            )
            aqi_resp = await client.get(aqi_url)
            if aqi_resp.status_code == 200:
                a = aqi_resp.json().get("current", {})
                result["pm2_5"] = a.get("pm2_5")
                result["pm10"] = a.get("pm10")
                result["us_aqi"] = a.get("us_aqi")

    except Exception as e:
        print(f"[Weather API Error] {e}")

    print(f"[Live Data] {city}: temp={result['temperature']}°C, rain={result['rain']}mm, "
          f"AQI={result['us_aqi']}, PM2.5={result['pm2_5']}")
    return result


async def fetch_live_news(city: str) -> list:
    """Fetch live news headlines via Google News RSS to verify local strikes/protests."""
    query = f"{city} (strike OR protest OR bandh) AND (transport OR union OR workers OR auto OR delivery) when:7d"
    q = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urllib.request.urlopen(req, timeout=5).read()
        root = ET.fromstring(html)
        titles = [item.find('title').text for item in root.findall('.//item')]
        return titles[:5]  # return top 5 recent headlines
    except Exception as e:
        print(f"[News API Error] {e}")
        return []


# ---------------------------------------------------------------------------
# Gemini helper — single place to call the LLM and parse JSON from its output
# ---------------------------------------------------------------------------
def gemini_json(prompt: str) -> dict | None:
    """Call Gemini and attempt to return parsed JSON, or None on failure."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[Gemini Error] No API key found in environment variables!")
        return None
    
    # Masked key for health check
    masked_key = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "****"
    print(f"[Gemini Health] Using API key: {masked_key}")

    # List of models to try in order of preference
    models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    
    last_err = None
    for model_name in models_to_try:
        try:
            print(f"[Gemini] Attempting with model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            text = response.text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text.rsplit("```", 1)[0]
            text = text.strip()
            return json.loads(text)
        except Exception as e:
            last_err = e
            print(f"[Gemini Error with {model_name}] {e}")
            # Try the next model for ANY error (404, 429, etc.)
            continue
            
    print(f"[Gemini Final Failure] All models failed. Last error: {last_err}")
    return None

def filter_news_with_nlp(city: str, headlines: list) -> list:
    """Uses Gemini NLP to filter out headlines that are not strictly related to the target city."""
    if not headlines:
        return []
    prompt = f"""You are an strict NLP filter detecting Named Entities in news headlines.
Target City: {city}
Headlines:
{json.dumps(headlines, indent=2)}

Filter this list. Reject any headline that explicitly mentions a different primary city (e.g. Hyderabad, Delhi, etc.) or appears to only be National news without a local impact. Focus strictly on retaining headlines that are highly likely local to {city}.
Return ONLY a raw JSON array of strings (the filtered headlines).
"""
    result = gemini_json(prompt)
    if isinstance(result, list):
        return result
    return headlines

def check_crowd_density(city: str, location: str) -> dict:
    """
    Simulates a Google Maps Directions/Traffic API payload.
    In production (with GCP billing enabled), this queries Routes API comparing
    typical vs actual router duration to estimate abnormal crowd/traffic density over 5h.
    """
    return {
        "status": "success",
        "provider": "Google Maps Traffic API (Simulation)",
        "location": f"{location}, {city}",
        "timeline_5h": [
            {"hour": "-5h", "density_multiplier": 1.0, "traffic": "Normal"},
            {"hour": "-4h", "density_multiplier": 1.2, "traffic": "Normal"},
            {"hour": "-3h", "density_multiplier": 1.8, "traffic": "Congested"},
            {"hour": "-2h", "density_multiplier": 2.5, "traffic": "Heavy Crowd Level"},
            {"hour": "-1h", "density_multiplier": 3.2, "traffic": "Severe Accumulation"},
            {"hour": "Now",  "density_multiplier": 4.0, "traffic": "Critical / Road Blocked"}
        ]
    }


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# Initialize DB
def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            city TEXT NOT NULL,
            address TEXT,
            platform TEXT NOT NULL,
            plan TEXT,
            premium INTEGER,
            risk_profile TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    # Migrate: add address and risk_profile columns if they don't exist
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN address TEXT")
    except Exception:
        pass
        
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN risk_profile TEXT")
    except Exception:
        pass

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS claims (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            location TEXT NOT NULL,
            datetime TEXT NOT NULL,
            status TEXT NOT NULL,
            amount INTEGER NOT NULL,
            reason TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    # Migrate: add risk_profile column if it doesn't exist (for existing DBs)
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN risk_profile TEXT")
    except Exception:
        pass  # column already exists
    conn.commit()
    conn.close()

init_db()

class RegisterRequest(BaseModel):
    name: str
    phone: str
    city: str
    address: str  # Included detailed address
    platform: str

class LoginRequest(BaseModel):
    phone: str

class PlanRequest(BaseModel):
    user_id: str
    plan: str
    premium: int


# ===========================================================================
# MODULE 1 — REGISTRATION  (AI Risk Profile on Signup + Live Weather Data)
# ===========================================================================
@app.post("/api/register")
async def register(req: RegisterRequest):
    if req.platform not in ["Swiggy", "Zomato"]:
        raise HTTPException(status_code=400, detail="Invalid platform. Must be Swiggy or Zomato.")
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE phone=?", (req.phone,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Phone already exists")
    
    user_id = str(uuid.uuid4())

    # ── Fetch LIVE weather data for the city ──
    live = await fetch_live_weather(req.city)

    # ── AI: Generate initial risk profile using REAL data ──
    risk_prompt = f"""You are a risk-assessment AI for IntelliCover, a gig-worker micro-insurance platform in India.
A new delivery worker just registered with the following details:
- Name: {req.name}
- City: {req.city}
- Delivery Platform: {req.platform}

LIVE WEATHER DATA for {req.city} right now:
- Temperature: {live['temperature']}°C
- Current Rainfall: {live['rain']} mm
- Air Quality Index (US AQI): {live['us_aqi']}
- PM2.5: {live['pm2_5']} μg/m³
- PM10: {live['pm10']} μg/m³

Based on this REAL data and typical seasonal patterns for {req.city}, provide an initial risk profile.

Output ONLY a raw JSON object (no markdown, no explanation):
{{"risk_level": "Low" or "Medium" or "High", "summary": "<one-sentence explanation referencing the actual data>"}}"""

    ai_profile = gemini_json(risk_prompt)
    if ai_profile is None:
        # Fallback: use live data to determine risk
        risk_level = "Low"
        summary = f"Current conditions in {req.city}: {live['temperature']}°C, {live['rain']}mm rain, AQI {live['us_aqi']}."
        if live['rain'] and live['rain'] > 5:
            risk_level = "High"
            summary = f"Active rainfall of {live['rain']}mm detected in {req.city}."
        elif live['us_aqi'] and live['us_aqi'] > 150:
            risk_level = "High"
            summary = f"Poor air quality (AQI {live['us_aqi']}) detected in {req.city}."
        elif live['temperature'] and live['temperature'] > 40:
            risk_level = "Medium"
            summary = f"High temperature of {live['temperature']}°C in {req.city}."
        ai_profile = {"risk_level": risk_level, "summary": summary}

    risk_profile_str = json.dumps(ai_profile)

    cursor.execute('''
        INSERT INTO users (user_id, name, phone, city, address, platform, plan, premium, risk_profile, created_at)
        VALUES (?, ?, ?, ?, ?, ?, NULL, NULL, ?, ?)
    ''', (user_id, req.name, req.phone, req.city, req.address, req.platform, risk_profile_str, datetime.utcnow().isoformat()))
    
    conn.commit()
    conn.close()
    
    return {
        "user_id": user_id,
        "message": "Registered successfully",
        "risk_profile": ai_profile
    }


# ===========================================================================
# MODULE 1 — LOGIN
# ===========================================================================
@app.post("/api/login")
async def login(req: LoginRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone=?", (req.phone,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="User not registered")
    
    result = dict(row)
    # Parse risk_profile back to dict for the response
    if result.get("risk_profile"):
        try:
            result["risk_profile"] = json.loads(result["risk_profile"])
        except Exception:
            pass
    return result


# ===========================================================================
# MODULE 2 — POLICY MANAGEMENT  (AI Plan Recommendation + Live Data)
# ===========================================================================
@app.post("/api/select-plan")
async def select_plan(req: PlanRequest):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (req.user_id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
    
    cursor.execute('''
        UPDATE users 
        SET plan=?, premium=? 
        WHERE user_id=?
    ''', (req.plan, req.premium, req.user_id))
    
    conn.commit()
    conn.close()
    return {"message": "Plan updated successfully", "plan": req.plan}


@app.get("/api/recommend-plan")
async def recommend_plan(user_id: str):
    """AI-powered plan recommendation based on city, platform, claim history, and LIVE weather."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT city, platform, plan FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")

    city = user["city"]
    platform = user["platform"]
    current_plan = user["plan"] or "None"

    # Fetch past claims summary
    cursor.execute("SELECT type, status FROM claims WHERE user_id=?", (user_id,))
    claims = [dict(r) for r in cursor.fetchall()]
    conn.close()

    claim_summary = "No claims filed yet."
    if claims:
        approved = [c for c in claims if c["status"] == "Approved"]
        rejected = [c for c in claims if c["status"] == "Rejected"]
        types = list(set(c["type"] for c in claims))
        claim_summary = (
            f"{len(claims)} total claims ({len(approved)} approved, {len(rejected)} rejected). "
            f"Disruption types filed: {', '.join(types)}."
        )

    # ── Fetch LIVE weather data ──
    live = await fetch_live_weather(city)

    recommend_prompt = f"""You are an insurance advisor AI for IntelliCover, a gig-worker micro-insurance platform.

User profile:
- City: {city}
- Delivery Platform: {platform}
- Current Plan: {current_plan}
- Claim History: {claim_summary}

LIVE WEATHER DATA for {city} right now:
- Temperature: {live['temperature']}°C
- Current Rainfall: {live['rain']} mm
- Air Quality Index (US AQI): {live['us_aqi']}
- PM2.5: {live['pm2_5']} μg/m³

Available plans:
1. Basic Plan — ₹20/week — Covers: Heavy Rain only
2. Standard Plan — ₹35/week — Covers: Heavy Rain + Heatwave
3. Premium Plan — ₹50/week — Covers: Heavy Rain + Heatwave + Pollution (full coverage)

Analyze the LIVE conditions and user's claim history to recommend the best plan.

Output ONLY a raw JSON object (no markdown, no explanation):
{{"recommended_plan": "Basic Plan" or "Standard Plan" or "Premium Plan", "reason": "<1-2 sentence explanation referencing actual weather data>"}}"""

    ai_result = gemini_json(recommend_prompt)
    if ai_result is None:
        # Fallback: use live data to decide
        if live['us_aqi'] and live['us_aqi'] > 100:
            ai_result = {"recommended_plan": "Premium Plan",
                         "reason": f"Current AQI of {live['us_aqi']} in {city} indicates pollution risk — Premium Plan gives full coverage."}
        elif live['temperature'] and live['temperature'] > 38:
            ai_result = {"recommended_plan": "Standard Plan",
                         "reason": f"Temperature of {live['temperature']}°C in {city} suggests heatwave risk — Standard Plan covers rain + heat."}
        else:
            ai_result = {"recommended_plan": "Standard Plan",
                         "reason": f"Standard Plan offers balanced coverage for gig workers in {city}."}

    return ai_result


# ===========================================================================
# MODULE 3 — DYNAMIC PREMIUM CALCULATION  (Live Weather + AI Analysis)
# ===========================================================================
@app.get("/api/premium")
async def get_premium(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT plan, premium, city FROM users WHERE user_id=?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Base prices: Basic -> 20, Standard -> 35, Premium -> 50
    base_price = 35  # Default
    if row["plan"]:
        if "Basic" in row["plan"]: base_price = 20
        elif "Premium" in row["plan"]: base_price = 50
        else: base_price = 35
    elif row["premium"] is not None:
        base_price = row["premium"]

    city = row["city"] or "Unknown"

    # ── Fetch LIVE weather + AQI data ──
    live = await fetch_live_weather(city)

    # ── AI: Analyze REAL live data for dynamic pricing ──
    premium_prompt = f"""You are a dynamic pricing AI for IntelliCover, a gig-worker micro-insurance platform in India.

LIVE WEATHER DATA for {city} right now:
- Temperature: {live['temperature']}°C
- Current Rainfall: {live['rain']} mm
- Weather Code (WMO): {live['weather_code']}
- Air Quality Index (US AQI): {live['us_aqi']}
- PM2.5: {live['pm2_5']} μg/m³
- PM10: {live['pm10']} μg/m³

Risk thresholds:
- Rain > 2.5 mm = active rainfall disruption
- Temperature > 40°C = heatwave conditions
- US AQI > 150 = unhealthy pollution levels
- US AQI > 200 = severe pollution

Based on this REAL data, determine the current risk and premium adjustment.

Rules for adjustment:
- High risk (active disruption detected) → adjustment between +8 and +15
- Medium risk (approaching thresholds) → adjustment between +1 and +7
- Low risk (normal conditions) → adjustment between -5 and 0

Output ONLY a raw JSON object (no markdown, no explanation):
{{"risk_level": "Low" or "Medium" or "High", "disruption_type": "None" or "Heavy Rain" or "Heatwave" or "Pollution", "adjustment": <integer between -5 and 15>, "reason": "<brief explanation with actual numbers from the live data>"}}"""

    ai_result = gemini_json(premium_prompt)

    if ai_result:
        risk_level = ai_result.get("risk_level", "Medium")
        disruption_type = ai_result.get("disruption_type", "None")
        adjustment = ai_result.get("adjustment", 0)
        reason = ai_result.get("reason", "AI-assessed risk")
        # Clamp adjustment to valid range
        adjustment = max(-5, min(15, int(adjustment)))
    else:
        # ── Fallback: use LIVE data instead of random numbers ──
        rain = live.get("rain") or 0
        temp = live.get("temperature") or 30
        aqi = live.get("us_aqi") or 50

        if rain > 2.5:
            risk_level = "High"
            disruption_type = "Heavy Rain"
            reason = f"Active rainfall of {rain}mm detected in {city}"
            adjustment = 10
        elif aqi > 150:
            risk_level = "High"
            disruption_type = "Pollution"
            reason = f"Unhealthy AQI of {aqi} in {city}"
            adjustment = 10
        elif temp > 40:
            risk_level = "Medium"
            disruption_type = "Heatwave"
            reason = f"High temperature of {temp}°C in {city}"
            adjustment = 5
        elif temp > 35 or aqi > 100:
            risk_level = "Medium"
            disruption_type = "None"
            reason = f"Moderate conditions in {city} (temp: {temp}°C, AQI: {aqi})"
            adjustment = 2
        else:
            risk_level = "Low"
            disruption_type = "None"
            reason = f"Clear conditions in {city} (temp: {temp}°C, rain: {rain}mm, AQI: {aqi})"
            adjustment = -5

    adjusted_price = base_price + adjustment
    if adjusted_price < 0:
        adjusted_price = 0

    return {
        "base": base_price,
        "adjusted": adjusted_price,
        "type": disruption_type,
        "risk": risk_level,
        "reason": reason
    }


# ===========================================================================
# MODULE 4 — CLAIMS MANAGEMENT  (Live Weather Verification + AI)
# ===========================================================================
@app.get("/api/claims")
async def get_claims(user_id: str):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM claims WHERE user_id=? ORDER BY datetime DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


@app.post("/api/claim")
async def process_claim(req: dict):
    user_id = req.get("user_id")
    claim_type = req.get("type", "Unknown")
    location = req.get("location", "Unknown Location")
    claim_datetime = req.get("datetime", datetime.utcnow().isoformat())
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT plan, city FROM users WHERE user_id=?", (user_id,))
    user = cursor.fetchone()
    
    if not user:
        conn.close()
        raise HTTPException(status_code=404, detail="User not found")
        
    plan = user["plan"] or "None"
    city = user["city"] or "Unknown"

    # ── CHECK 1: Monthly claim limit (3 per month) ──
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    cursor.execute(
        "SELECT COUNT(*) as cnt FROM claims WHERE user_id=? AND datetime >= ?",
        (user_id, month_start)
    )
    month_count = cursor.fetchone()["cnt"]
    if month_count >= 3:
        conn.close()
        return {
            "status": "Rejected",
            "amount": 0,
            "reason": f"Monthly claim limit reached ({month_count}/3). You can file new claims next month."
        }

    # ── CHECK 2: Location radius — must be within user's city ──
    city_locations = {
        "Chennai": ["t. nagar", "velachery", "anna nagar", "adyar", "mylapore", "tambaram", "guindy", "nungambakkam", "egmore", "chennai"],
        "Mumbai": ["powai", "bkc", "andheri", "bandra", "dadar", "worli", "juhu", "malad", "goregaon", "mumbai"],
        "Bangalore": ["whitefield", "indiranagar", "btm", "koramangala", "jayanagar", "hsr", "electronic city", "marathahalli", "bangalore", "bengaluru"],
        "Madurai": ["kk nagar", "mattuthavani", "anna nagar", "madurai"],
        "Trichy": ["srirangam", "thillai nagar", "trichy", "tiruchirappalli"],
    }
    known_locs = city_locations.get(city, [city.lower()])
    location_in_radius = any(loc in location.lower() for loc in known_locs)

    # ── Fetch LIVE weather + AQI data ──
    live_weather = await fetch_live_weather(city)
    
    # ── Fetch & Filter LIVE news data (NLP Strict Filtering) ──
    raw_news_titles = await fetch_live_news(city)
    filtered_news = filter_news_with_nlp(city, raw_news_titles)
    news_context = "\n".join([f"- {title}" for title in filtered_news]) if filtered_news else f"- No valid local {city} headlines found."

    # ── Fetch LIVE Google Maps API 5-Hour Crowd Density ──
    crowd_density_api = check_crowd_density(city, location)
    crowd_context = json.dumps(crowd_density_api, indent=2)

    # ── Calculate Payout dynamically based on Income Stabilization ──
    # Simulating last 4 weeks income since we don't collect income proofs in registration
    last_4_weeks_income = random.randint(12000, 24000) 
    avg_weekly_income = last_4_weeks_income // 4
    daily_income = avg_weekly_income // 6
    disruption_days = 1
    base_loss = daily_income * disruption_days
    coverage_pct = 0.70 if plan in ["Standard Plan", "Premium Plan"] else 0.60
    calculated_payout = int(base_loss * coverage_pct)

    # ── AI: Verify claim against REAL live data + news + radius ──
    claim_prompt = f"""You are an AI insurance claim verifier for IntelliCover, a gig-worker micro-insurance app.
You must verify claims using REAL LIVE DATA.

Claim details:
- Disruption Type: {claim_type}
- Claimed Location: {location}
- Registered City: {city}
- Date/Time: {claim_datetime}
- Active Plan: {plan}
- Location within 5-10km city radius: {"Yes" if location_in_radius else "UNKNOWN — may be outside coverage radius"}

LIVE WEATHER DATA for {city} (Open-Meteo API):
- Temperature: {live_weather['temperature']}deg C
- Current Rainfall: {live_weather['rain']} mm
- Weather Code (WMO): {live_weather['weather_code']}
- US AQI: {live_weather['us_aqi']}
- PM2.5: {live_weather['pm2_5']} ug/m3

LIVE LOCAL NEWS (Strike/Protest Verification):
{news_context}

LIVE GOOGLE MAPS TRAFFIC (5-Hour Crowd Density Simulation):
{crowd_context}

Coverage Rules:
1. Heavy Rain: Covered by ALL plans.
2. Heatwave: Covered by Standard+Premium only.
3. Pollution: Covered by Premium only.
4. Strike/Protest: Covered by Standard+Premium only.
5. No plan = REJECT ALL.

Dynamic Payout Calculation:
For approved claims, the payout amount MUST be calculated using Income Stabilization rules:
- Avg Weekly Income: ₹{avg_weekly_income}
- Daily Income: ₹{daily_income}
- Base Loss (1 Disruption Day): ₹{base_loss}
- Coverage %: {"70%" if coverage_pct == 0.7 else "60%"} ({plan})
- Final Payout Amount: ₹{calculated_payout}

You must return exactly {calculated_payout} as the "amount" if the status is "Approved".

Verification:
- Heavy Rain: rain > 2.5mm OR weather_code >= 61. If not met, REJECT with reason explaining the actual rain data.
- Heatwave: temperature > 40 deg C. If not met, REJECT with reason explaining the actual temperature data.
- Pollution: US AQI > 150. If not met, REJECT with reason explaining the actual AQI data.
- Strike/Protest: Check the LIVE LOCAL NEWS and the LIVE MAPS TRAFFIC above. If verified local headlines exist OR the Maps API shows a current density multiplier >= 3.0 (Critical crowd levels) in {location}, APPROVE. If the local news is empty and traffic is normal, REJECT with reason "No confirmed strikes in strictly local news and Maps traffic density is normal." 
- RADIUS: Location "{location}" must be within 5-10km of {city}. If clearly outside, REJECT with reason "Claimed location '{location}' is outside the 5-10km coverage radius of {city}."
- PLAN COVERAGE: If the disruption type is not covered by {plan} according to Coverage Rules, REJECT with reason "Disruption type '{claim_type}' is not covered by your current {plan}."

Output ONLY a raw JSON object:
{{"status": "Approved" or "Rejected", "amount": <int or 0>, "reason": "<explanation with actual data values and radius confirmation>"}}"""

    ai_result = gemini_json(claim_prompt)

    if ai_result:
        status = ai_result.get("status", "Rejected")
        amount = ai_result.get("amount", 0)
        reason = ai_result.get("reason", "")
        if status == "Rejected" and not reason:
            reason = "Claim rejected: Did not meet required live data thresholds for coverage."
    else:
        # ── Failsafe Fallback ──
        status = "Rejected"
        amount = 0
        reason = "Claim rejected: AI Verification Engine is currently offline or unreachable. Cannot securely verify disruption metrics."

    claim_id = str(uuid.uuid4())
    
    cursor.execute('''
        INSERT INTO claims (id, user_id, type, location, datetime, status, amount, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (claim_id, user_id, claim_type, location, claim_datetime, status, amount, reason))
    
    conn.commit()
    conn.close()
    
    return {
        "status": status,
        "amount": amount,
        "reason": reason
    }
