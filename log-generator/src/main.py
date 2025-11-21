import psycopg2
import time
import random
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "dbname": os.getenv("POSTGRES_DB"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "host": os.getenv("POSTGRES_HOST"),
    "port": 5432,
}

conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute("CREATE DATABASE elk")
    print("Database Created")
except:
    print("Database Already Exists")

conn.close()
conn = psycopg2.connect(**DB_CONFIG)
conn.autocommit = True
cur = conn.cursor()

cur.execute(
    """
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        first_name TEXT,
        last_name TEXT
    )
"""
)
print("Table ready")

first_names = ["John", "Jane", "Bob", "Alice", "Mike", "Sarah", "Tom", "Emma"]
last_names = ["Smith", "Johnson", "Brown", "Davis", "Wilson", "Miller", "Moore"]

while True:
    first = random.choice(first_names)
    last = random.choice(last_names)

    cur.execute(
        "INSERT INTO users (first_name, last_name) VALUES (%s, %s)", (first, last)
    )

    print(f"Inserted: {first} {last}")
    time.sleep(5)
