import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestRegressor, RandomForestClassifier
from geopy.distance import geodesic
import random

class FraudSentinel:
    def __init__(self):
        self._generate_synthetic_data()
        self._train_models()

    def _generate_synthetic_data(self):
        """Generate a realistic dataset for training the ML models."""
        # 500 rows of user behavior data
        np.random.seed(42)
        n_samples = 500
        
        # Features for Anomaly Detection (Isolation Forest)
        # 1. Distance_from_Home_km
        # 2. Time_Since_Last_Claim_hrs
        # 3. Claims_in_last_30_days
        # Normal behavior
        dist_normal = np.random.normal(loc=3.0, scale=1.5, size=n_samples)
        dist_normal = np.clip(dist_normal, 0, 12)
        
        time_normal = np.random.normal(loc=120, scale=50, size=n_samples) # hours
        time_normal = np.clip(time_normal, 24, 720)
        
        claims_normal = np.random.poisson(lam=1.5, size=n_samples)
        
        self.X_anomaly = np.column_stack((dist_normal, time_normal, claims_normal))
        
        # Inject some anomalies (fraud patterns)
        for i in range(20):
            self.X_anomaly[i] = [
                np.random.uniform(15, 50), # Unrealistic distance
                np.random.uniform(0.5, 5), # Unrealistic time between claims
                np.random.randint(5, 15)   # Too many claims
            ]
            
        # Features for Credibility Regressor
        # Inputs: Successful_Orders_Week, Avg_Rating (0-5), Years_Active
        # Outputs: Credibility Score (0-100)
        orders = np.random.randint(20, 150, size=n_samples)
        ratings = np.random.uniform(3.5, 5.0, size=n_samples)
        years = np.random.uniform(0.1, 4.0, size=n_samples)
        
        self.X_cred = np.column_stack((orders, ratings, years))
        # Simple heuristic to act as the target variable for the training
        self.y_cred = (orders/150 * 40) + ((ratings-3.5)/1.5 * 40) + (years/4 * 20)
        self.y_cred = np.clip(self.y_cred, 0, 100)
        
    def _train_models(self):
        # 1. Anomaly Model
        self.anomaly_model = IsolationForest(contamination=0.05, random_state=42)
        self.anomaly_model.fit(self.X_anomaly)
        
        # 2. Credibility Regressor
        self.credibility_model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
        self.credibility_model.fit(self.X_cred, self.y_cred)
        print("[ML Engine] Fraud Sentinel Models Trained Successfully.")

    def calculate_distance(self, loc1_str, loc2_str):
        """Calculate Haversine distance between two sets of lat/lon coordinates if possible."""
        try:
            # We assume string is something like "13.08, 80.27" or we mock it for the hackathon
            return 3.5 # MOCKED baseline for the text-based generic locations in hackathon
        except:
            return 0.0

    def get_fraud_score(self, distance_km: float, time_since_last_claim_hrs: float, claims_last_30d: int) -> dict:
        """
        Evaluate a claim against the Isolation Forest to get an Anomaly Risk Score.
        Returns High, Medium, or Low Risk.
        """
        X_test = np.array([[distance_km, time_since_last_claim_hrs, claims_last_30d]])
        
        # Predict returns 1 for inliers, -1 for anomalies
        prediction = self.anomaly_model.predict(X_test)[0]
        # Decision function gives continuous score (lower = more abnormal)
        score = self.anomaly_model.decision_function(X_test)[0]
        
        # Convert to 0-100 Risk Probability
        # Sigmoid-ish scaling just for display logic
        risk_probability = max(0, min(100, int((0.1 - score) * 500)))

        if prediction == -1 or risk_probability > 80:
            classification = "High"
        elif risk_probability > 50:
            classification = "Medium"
        else:
            classification = "Low"
            
        return {
            "risk_classification": classification,
            "risk_score": risk_probability,
            "is_anomaly": bool(prediction == -1)
        }

    def predict_credibility(self, orders_week=80, rating=4.5, years_active=1.5):
        """Predict the user's honor score using the random forest regressor."""
        X_test = np.array([[orders_week, rating, years_active]])
        pred = self.credibility_model.predict(X_test)[0]
        return int(max(0, min(100, pred)))

# Instantiate the global sentinel service
sentinel = FraudSentinel()

# --- HELPER IP CHECKER ---
import requests
def verify_ip_location(ip_address=""):
    """
    Simulates calling an IP Geolocation API to check where the user's internet is routing from.
    Used for multi-signal verification against GPS constraints.
    """
    try:
        if not ip_address:
            # Mock success for Chennai if no IP provided
            return {"status": "success", "city": "Chennai", "lat": 13.08, "lon": 80.27}
        # In a real environment, we would use an API like ip-api.com
        res = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=2)
        return res.json()
    except Exception:
         return {"status": "error", "city": "Unknown", "message": "IP Geo Lookup Failed"}
