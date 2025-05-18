import pandas as pd
from sqlalchemy import create_engine
from datetime import timedelta


# Create PostgreSQL Engine
def create_postgres_engine(user, password, host, port, database):
    db_uri = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return create_engine(db_uri)


# Load a Table from PostgreSQl
def load_table(engine, table_name):
    with engine.connect() as conn:
        return pd.read_sql(f"SELECT * FROM {table_name}", conn)


# Match sensor data to MODIS data within ±
def match_sensor_to_modis(sensor_df, modis_df):
    sensor_df["timestamp"] = pd.to_datetime(sensor_df["timestamp"])
    modis_df["modis_timestamp"] = pd.to_datetime(modis_df["modis_timestamp"])

    matched_rows = []

    for _, sensor_row in sensor_df.iterrows():
        sensor_time = sensor_row["timestamp"]
        window_start = sensor_time - timedelta(minutes=2)
        window_end = sensor_time + timedelta(minutes=2)

        candidates = modis_df[
            (modis_df["modis_timestamp"] >= window_start)
            & (modis_df["modis_timestamp"] <= window_end)
        ].copy()

        if not candidates.empty:
            candidates["time_diff"] = (
                (candidates["modis_timestamp"] - sensor_time).abs().dt.total_seconds()
            )
            best_match = candidates.sort_values("time_diff").iloc[0]

            matched_rows.append(
                {
                    "timestamp": sensor_time,
                    "modis_timestamp": best_match["modis_timestamp"],
                    "smoke_value": sensor_row["smoke_value"],
                    "fire_lat": best_match["fire_lat"],
                    "fire_long": best_match["fire_long"],
                    "bright_ti4": best_match["bright_ti4"],
                    "confidence": best_match["confidence"],
                    "fire_radiative_power": best_match["fire_radiative_power"],
                    "daynight": best_match["daynight"],
                    "fire_detected": int(
                        best_match["fire_radiative_power"] > 2
                        or sensor_row["smoke_value"] > 300
                    ),
                }
            )

    return pd.DataFrame(matched_rows)


# Write Data to Postgrsql
def write_to_postgres(engine, df, table_name):
    with engine.begin() as conn:
        df.to_sql(table_name, conn, index=False, if_exists="replace")


# Main Function
def main():
    # DB connection info
    user = "postgres"
    password = "postgres"
    host = "172.22.0.2"
    port = 5432
    database = "fire_sensor_db"

    # Table names
    sensor_table = "sensor_data"
    modis_table = "modis_data"
    output_table = "prediction_data"

    # Connect and load
    engine = create_postgres_engine(user, password, host, port, database)
    sensor_df = load_table(engine, sensor_table)
    modis_df = load_table(engine, modis_table)

    # Process
    result_df = match_sensor_to_modis(sensor_df, modis_df)

    # Write back
    write_to_postgres(engine, result_df, output_table)

    print(f"{len(result_df)} rows written to table '{output_table}'.")


if __name__ == "__main__":
    main()
