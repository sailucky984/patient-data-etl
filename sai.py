import logging
import psycopg
import os
import csv
from dotenv import load_dotenv
import time

# Step 1: Load database credentials from .env
load_dotenv()

logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Step 2: Connect to PostgreSQL
connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD")
)

print("Connected to the database!")
logging.info("Connected to the database!")

inserted_rows = 0
skipped_rows = 0
duplicate_rows = 0
start_time = time.time()
try:
    # Step 3: Create a cursor
    with connection.cursor() as cur:

        # Step 4: Create the table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS Patients (
                patient_id VARCHAR(50) PRIMARY KEY,
                patient_name VARCHAR(50),
                gender VARCHAR(10),
                date_of_birth DATE,
                city VARCHAR(50),
                state VARCHAR(50),
                region VARCHAR(50),
                primary_condition VARCHAR(100),
                payer_type VARCHAR(50)
            )
        """)


        # Step 5: Open the CSV file
        with open(
            r"C:\Users\sailu\Downloads\Patients.csv",
            "r",
            newline="",
            encoding="utf-8-sig"
        ) as f:

            reader = csv.DictReader(f)

            if not reader.fieldnames:
                raise ValueError("CSV file is empty or has no headers")

            required_columns = {
                "patient_id",
                "patient_name",
                "gender",
                "date_of_birth",
                "city",
                "state",
                "region",
                "primary_condition",
                "payer_type"
            }

            # if not required_columns.issubset(reader.fieldnames or []):
            #     raise ValueError("CSV is missing required columns")

            actual_columns = set(reader.fieldnames or [])
            missing_columns = required_columns - actual_columns

            if missing_columns:
                raise ValueError(f"Missing columns: {missing_columns}")

            # Step 6: Process each CSV row
            logging.info("Patient CSV import started")

            total_rows = 0

            for row in reader:
                total_rows += 1
                if (
                    not (row["patient_id"] or "").strip()
                    or not (row["patient_name"] or "").strip()
                ):  
                    skipped_rows += 1
                    logging.warning("Skipped row: patient ID or name is missing")
                    continue
                    skipped_rows += 1
                    logging.warning("Skipped rows: patient_id or patient_name is missing")
                    continue
                
                try:
                    # Step 7: Insert the record
                    cur.execute("""
                        INSERT INTO Patients (patient_id, patient_name, gender, date_of_birth, city, state, region, primary_condition, payer_type)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (patient_id) DO NOTHING
                    """, (row["patient_id"], row["patient_name"], row["gender"], row["date_of_birth"], row["city"], row["state"], row["region"], row["primary_condition"], row["payer_type"]))

                    # Step 8: Count inserted and duplicate rows
                    if cur.rowcount == 1:
                        inserted_rows += 1
                        # logging.info("Inserted:%s", row["patient_name"])
                    else:
                        duplicate_rows += 1
                        # logging.warning("Duplicate ID skipped: %s", row["patient_id"])

                except (ValueError, TypeError, KeyError) as e:
                    skipped_rows += 1
                    logging.error(f"Invalid row skipped: {row}. Error: {e}")

        # Step 9: Save all successful inserts
        logging.info("CSV file: Patients.csv")

        if total_rows == inserted_rows + duplicate_rows + skipped_rows:
            logging.info("Row count validation passed")
        else:
            logging.warning("Row count validation failed")

        # logging.info("Total rows processed: %s", total_rows)
        logging.info("ETL summary | Total: %d | Inserted: %d | Skipped: %d | Duplicates : %d",
            total_rows,
            inserted_rows,
            skipped_rows,
            duplicate_rows
        )

        print(f"\nETL summary | Total: {total_rows} |"
         f"Inserted: {inserted_rows} |"
         f"Skipped:{skipped_rows} |"
         f" Duplicates :{duplicate_rows}" 
        )

        connection.commit()
        # logging.info("Patient CSV import completed successfully")

        # print(f"\nInserted: {inserted_rows}")
        # print(f"Skipped: {skipped_rows}")

        # logging.info("\nInserted: %s", inserted_rows)
        # logging.info("Skipped: %s", skipped_rows)

        # Step 10: Verify the database records
        # cur.execute("SELECT * FROM patients ORDER BY id limit 5")
        # rows = cur.fetchall()

        # logging.info("\nPatient records:")

        cur.execute("SELECT * FROM patients ORDER BY id limit 10")
        rows = cur.fetchall()

        for row in rows:
            (
            print(row)
            )
        
        end_time = time.time()
        duration = end_time - start_time
        print(f"\nETL completed in {duration:.2f} seconds")
        logging.info("ETL duration: %.2f seconds", duration)

except Exception:
    connection.rollback()
    logging.exception("Patient data import failed")
    raise

finally:
    connection.close()
    print("\nDatabase connection closed!")