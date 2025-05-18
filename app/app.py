import os
import joblib
import pandas as pd
from flask import Flask, request, jsonify, render_template
from sklearn.ensemble import RandomForestClassifier


# Get base directory (one level up from app/)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Load model and encoders
model_path = os.path.join(BASE_DIR, "models", "random_forest_model.pkl")
confidence_encoder_path = os.path.join(BASE_DIR, "encoders", "confidence_encoder.pkl")
daynight_encoder_path = os.path.join(BASE_DIR, "encoders", "daynight_encoder.pkl")

model = joblib.load(model_path)
confidence_encoder = joblib.load(confidence_encoder_path)
daynight_encoder = joblib.load(daynight_encoder_path)


# Helper function to safely encode
def safe_label_encode(encoder, value):
    if value not in encoder.classes_:
        return encoder.transform([encoder.classes_[0]])[0]
    return encoder.transform([value])[0]


# Create the Flask app
app = Flask(__name__)


# Home route - direct access to the application
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()

    try:
        # Extract fields
        df = pd.DataFrame(
            [
                {
                    "smoke_value": data["smoke_value"],
                    "fire_lat": data["fire_lat"],
                    "fire_long": data["fire_long"],
                    "bright_ti4": data["bright_ti4"],
                    "fire_radiative_power": data["fire_radiative_power"],
                    "sensor_hour": pd.to_datetime(data["sensor_timestamp"]).hour,
                    "sensor_dayofweek": pd.to_datetime(
                        data["sensor_timestamp"]
                    ).dayofweek,
                    "sensor_day": pd.to_datetime(data["sensor_timestamp"]).day,
                    "modis_hour": pd.to_datetime(data["modis_timestamp"]).hour,
                    "modis_dayofweek": pd.to_datetime(
                        data["modis_timestamp"]
                    ).dayofweek,
                    "modis_day": pd.to_datetime(data["modis_timestamp"]).day,
                    "timestamp_diff": (
                        pd.to_datetime(data["sensor_timestamp"])
                        - pd.to_datetime(data["modis_timestamp"])
                    ).total_seconds()
                    / 60,
                    "confidence_encoded": safe_label_encode(
                        confidence_encoder, data["confidence"]
                    ),
                    "daynight_encoded": safe_label_encode(
                        daynight_encoder, data["daynight"]
                    ),
                }
            ]
        )

        # Predict
        prediction = model.predict(df)[0]
        prediction_proba = model.predict_proba(df)[0][1]

        return jsonify(
            {
                "fire_detected": int(prediction),
                "probability": round(float(prediction_proba), 4),
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(debug=True)
