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
