from flask import Flask, request, jsonify
import psycopg2
from datetime import datetime

app = Flask(__name__)

# Connect to your PostgreSQL database
conn = psycopg2.connect(
    dbname="fire_sensor_db",
    user="postgres",
    password="postgres",
    host="172.22.0.3",
    port="5432"
)
cursor = conn.cursor()

# Create the table if it doesn't exist
cursor.execute("""
    CREATE TABLE IF NOT EXISTS smoke_logs (
        id SERIAL PRIMARY KEY,
        smoke_value INTEGER NOT NULL,
        timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

@app.route('/log', methods=['POST'])
def log_data():
    data = request.get_json()
    smoke = data.get('smoke')

    if smoke is None:
        return jsonify({"error": "Missing smoke value"}), 400

    try:
        cursor.execute("INSERT INTO smoke_logs (smoke_value) VALUES (%s)", (smoke,))
        conn.commit()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        print("Error inserting:", e)
        return jsonify({"error": "Failed to insert"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)

