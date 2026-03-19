# intellicover
Description

IntelliCover is an AI-powered parametric insurance platform designed for food delivery partners. It uses real-time environmental data and automated triggers to protect gig workers from income loss caused by external disruptions such as extreme weather conditions.
⚠️ Problem Statement
Delivery partners working on platforms like Zomato and Swiggy often face income loss due to factors beyond their control, such as:
Heavy rainfall and floods
Extreme temperatures
Industry-wide disruptions
These events can reduce monthly earnings by 20–30%, with no financial protection available.

💡 Solution Overview
IntelliCover offers a mobile-first parametric insurance system tailored for gig workers.
Key Features:
AI-based disruption detection
Real-time weather integration via OpenWeatherMap API
Automatic claim processing
Instant compensation payouts

How It Works:
The system monitors external conditions (e.g., weather data)
If predefined thresholds are met → payout is triggered automatically
No manual claims or verification required

Coverage Model:
Based only on objective external events

No coverage for:
Personal issues (health, family)
Vehicle damage or accidents
Individual work decisions

 AI & Machine Learning Used

This system integrates both **supervised** and **unsupervised learning models**.

1. Random Forest (Supervised Learning)

 Random Forest Classifier

* Used for **disruption detection**
* Predicts whether a disruption has occurred based on:

  * Rainfall level
  * Traffic conditions
  * User inactivity
  * Duration

1. Random Forest Regressor

* Used for **risk prediction and premium calculation**
* Inputs:

  * Weekly income
  * Working hours
  * Consistency
  * Past claims
  * Location risk

2. Isolation Forest (Unsupervised Learning)

* Used for **fraud detection**
* Detects abnormal behavior such as:

  * Fake inactivity
  * Suspicious claim patterns
  * Unusual activity

Parametric Triggers (Chennai-centric, expandable)
1.	Heavy Rainfall / Flood Risk – Rainfall exceeding 50 mm in a 24-hour period (sourced from Weather API)
2.	Extreme Heat – Sustained temperatures above 38°C for at least 4 peak hours (Weather API)
3.	Industry Strike / Zone Disruption – Verified sudden local strike or market/zone closure

Technology Platform Developed as a cross-platform mobile application using Flutter for optimal performance, intuitive UX, reliable background processing .
Tech Stack
•	Frontend: Flutter 
•	Backend: FastAPI (Python) + PostgreSQL
•	AI/ML: Isolation Forest/Regressor + random forest
•	Integrations: OpenWeatherMap API + Goople Places API
•	Payments:  Razorpay 

Development plan :
•  Days 1–7: Project setup (Flutter + Python+ PostgreSQL), onboarding screens, user registration & basic dashboard. 
•  Days 8–14: OpenWeatherMap API integration, simple AI risk profiling (Python/scikit-learn), dynamic premium calculation, policy purchase (Razorpay test/mock). 
•  Days 15–23: Background service for hourly trigger checks, parametric triggers logic (rain/heat/strike )
•  Days 24–31: Auto-claim + instant payout simulation, claim history & dashboard polish, basic fraud checks (GPS + rules). 
•  Days 32–38: Refine ML model (Chennai weather data), full testing, bug fixes, edge cases. 
•  Days 39–45: UI polish, README + screenshots, record/upload 2-min demo video,  submission prep.

