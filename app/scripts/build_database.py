# Import libraries needed for reading the CSV file, working with SQLite, and handling file paths
import pandas as pd
import sqlite3
from pathlib import Path

# Set file paths for the raw FEMA data and the SQLite database
csv_path = "data/raw/DisasterDeclarationsSummaries.csv"
db_path = "disasters.db"

# Read the FEMA CSV file into a pandas DataFrame
df = pd.read_csv(csv_path)

# Connect to the SQLite database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create database tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS states (
    state_id INTEGER PRIMARY KEY AUTOINCREMENT,
    state_code TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS incident_types (
    incident_type_id INTEGER PRIMARY KEY AUTOINCREMENT,
    incident_type TEXT UNIQUE
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS disasters (
    disaster_id INTEGER PRIMARY KEY,
    declaration_type TEXT,
    declaration_date TEXT,
    fy_declared INTEGER,
    declaration_title TEXT,
    state_id INTEGER,
    incident_type_id INTEGER,

    FOREIGN KEY(state_id) REFERENCES states(state_id),
    FOREIGN KEY(incident_type_id) REFERENCES incident_types(incident_type_id)
)
""")

# Insert unique state and jurisdiction codes
states = df["state"].dropna().unique()

for state in states:
    cursor.execute("""
    INSERT OR IGNORE INTO states (state_code)
    VALUES (?)
    """, (state,))

# Insert unique disaster incident types
incident_types = df["incidentType"].dropna().unique()

for incident in incident_types:
    cursor.execute("""
    INSERT OR IGNORE INTO incident_types (incident_type)
    VALUES (?)
    """, (incident,))

# Save state and incident type records before inserting disaster records
conn.commit()

# Insert disaster records
for _, row in df.iterrows():

    # Look up the matching state_id for this disaster record
    cursor.execute("""
    SELECT state_id FROM states
    WHERE state_code = ?
    """, (row["state"],))

    state_id = cursor.fetchone()[0]

    # Look up the matching incident_type_id for this disaster record
    cursor.execute("""
    SELECT incident_type_id FROM incident_types
    WHERE incident_type = ?
    """, (row["incidentType"],))

    incident_type_id = cursor.fetchone()[0]

    # Insert the disaster record using foreign keys instead of repeating text values
    cursor.execute("""
    INSERT OR IGNORE INTO disasters (
        disaster_id,
        declaration_type,
        declaration_date,
        fy_declared,
        declaration_title,
        state_id,
        incident_type_id
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        int(row["disasterNumber"]),
        row["declarationType"],
        row["declarationDate"],
        int(row["fyDeclared"]),
        row["declarationTitle"],
        state_id,
        incident_type_id
    ))

# Save all disaster records and close the database connection
conn.commit()
conn.close()

print("SQLite database created successfully.")
