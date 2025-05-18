import psycopg2
from datetime import datetime, timedelta
import random

# === Database connection details ===
DB_HOST = '172.22.0.3'
DB_PORT = '5432'
DB_NAME = 'fire_sensor_db'
DB_USER = 'postgres'
DB_PASSWORD = 'postgres'

# === Generate smoke sensor data ===
def generate_sensor_data():
    data = []
    start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(720):  # 720 points for 2-minute intervals over 24 hours
        timestamp = start_time + timedelta(minutes=2*i)

        # Simulate realistic smoke levels
        if 6 <= timestamp.hour < 9:  # Morning rise
            value = random.randint(100, 300)
        elif 9 <= timestamp.hour < 17:  # Midday activity
            value = random.randint(200, 600)
        elif 17 <= timestamp.hour < 20:  # Evening peak
            value = random.randint(500, 1023)
        else:  # Night low
            value = random.randint(50, 200)

        data.append((timestamp, value))
    return data

# === Create and populate the PostgreSQL table ===
def load_data_to_postgres(data):
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()

        # Create table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sensor_data (
                id SERIAL PRIMARY KEY,
                timestamp TIMESTAMP NOT NULL,
                smoke_value INTEGER NOT NULL
            );
        """)
        conn.commit()

        # Insert data
        cursor.executemany("""
            INSERT INTO sensor_data (timestamp, smoke_value)
            VALUES (%s, %s);
        """, data)
        conn.commit()

        print(f"{len(data)} records inserted successfully into sensor_data table.")
        cursor.close()
        conn.close()

    except Exception as e:
        print("Error:", e)

# === Main ===
if __name__ == "__main__":
    sensor_data = generate_sensor_data()
    load_data_to_postgres(sensor_data)

