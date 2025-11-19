import psycopg2
import time
import random

conn = psycopg2.connect(
    dbname="postgres",
    user="postgres", 
    password="1234",
    host="localhost",
    port=5432
)
conn.autocommit = True
cur = conn.cursor()

try:
    cur.execute("CREATE DATABASE elk")
    print("Database Created")
except:
    print("Database Already Exists")

conn.close()
conn = psycopg2.connect(
    dbname="elk",
    user="postgres",
    password="1234", 
    host="localhost",
    port=5432
)
conn.autocommit = True
cur = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        first_name TEXT,
        last_name TEXT
    )
""")
print("Table ready")

first_names = ["John", "Jane", "Bob", "Alice", "Mike", "Sarah", "Tom", "Emma"]
last_names = ["Smith", "Johnson", "Brown", "Davis", "Wilson", "Miller", "Moore"]

while True:
    first = random.choice(first_names)
    last = random.choice(last_names)
    
    cur.execute(
        "INSERT INTO users (first_name, last_name) VALUES (%s, %s)",
        (first, last)
    )
    
    print(f"Inserted: {first} {last}")
    time.sleep(5)
