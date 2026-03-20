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
 * 	Frontend: Flutter 
 *  Backend: FastAPI (Python) + PostgreSQL
 * 	AI/ML: Isolation Forest/Regressor + random forest
 *  Integrations: OpenWeatherMap API + Goople Places API
 *  Payments:  Razorpay 

Development plan :
 *  Days 1–7: Project setup (Flutter + Python+ PostgreSQL), onboarding screens, user registration & basic dashboard. 
 *  Days 8–14: OpenWeatherMap API integration, simple AI risk profiling (Python/scikit-learn), dynamic premium calculation, policy purchase (Razorpay test/mock). 
 *  Days 15–23: Background service for hourly trigger checks, parametric triggers logic (rain/heat/strike )
 *  Days 24–31: Auto-claim + instant payout simulation, claim history & dashboard polish, basic fraud checks (GPS + rules). 
 *  Days 32–38: Refine ML model (Chennai weather data), full testing, bug fixes, edge cases. 
 *  Days 39–45: UI polish, README + screenshots, record/upload 2-min demo video,  submission prep.

##  Adversarial Defense & Anti-Spoofing Strategy(Market Crash Scenario):

We implement a **multi-layered AI-driven fraud detection and prevention system** that ensures only legitimate claims are processed.

---

 1. Service Radius Enforcement

* Each user defines a **primary location (home/base)** during registration.
* The system dynamically assigns a **service radius** based on:

  * Historical activity
  * Order density in the region

 Benefit:

Prevents unrealistic location jumps and restricts claims to the user’s normal working area.

---

 2. Location Change Cooldown

* Users can update their working location.
* However, **insurance claims are disabled for 24 hours** after a location change.

 Benefit:

Prevents users from instantly switching to high-risk zones to exploit payouts.

---

 3. Credibility factor System

Each user is assigned a dynamic **Credibility factor  (0–100)** based on behavior.

Score Increases:

* Consistent work within service radius
* Stable activity patterns

Score Decreases:

* Frequent location switching
* Suspicious disruption claims
* Unrealistic movement patterns

 Impact:

* Low score → Higher premiums, reduced coverage
* High score → Lower premiums, faster payouts

---

 4. Multi-Signal Location Verification

We do not rely solely on GPS data.

### Signals Used:

* GPS coordinates
* IP address location
* Device/network metadata

Detection Logic:

If multiple signals conflict, the system flags the claim as suspicious.

---

 5. AI-Based Behavioral Analysis

We use machine learning models to detect anomalies in user activity.

### Detects:

* Sudden drops in activity only during disruptions
* Unrealistic travel speeds
* Abnormal work patterns

 Models:

* Isolation Forest
* Time-series anomaly detection

---

 6. Group Fraud Detection

To prevent coordinated attacks:

* Detect clusters of users claiming from the same region simultaneously
* Identify synchronized behavior patterns

 Example:

If hundreds of users suddenly appear in the same disaster zone → flagged as high-risk cluster.

---

 7. Movement Validation

The system validates whether user movement is physically possible.

 Example:

* Sudden long-distance travel in a short time
  → flagged as impossible → claim rejected

---

8. Activity Verification

We cross-check actual work activity:

* Delivery logs
* App usage
* Movement consistency

 Detection:

No activity during disruption periods → suspicious claim

---

9. Risk-Based Payout Processing

Claims are processed based on risk level:

| Risk Level | Action                        |
| ---------- | ----------------------------- |
| Low        | Instant payout                |
| Medium     | Delayed processing            |
| High       | Manual/AI review or rejection |

---

## 🔁 Fraud Detection Workflow

```
Claim Triggered
      ↓
Service Radius Check
      ↓
Location Verification (GPS + IP)
      ↓
Movement Validation
      ↓
Behavioral Analysis (AI)
      ↓
Group Fraud Detection
      ↓
Honor Score Evaluation
      ↓
Risk Classification
      ↓
Approve / Delay / Reject
```

---





