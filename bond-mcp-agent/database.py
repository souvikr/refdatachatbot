import sqlite3
import pathlib
from datetime import date

# Define the database file path relative to this script
DB_FILE = pathlib.Path(__file__).parent / "finance.db"

def init_db():
    """Initialize the database with the required schema."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Enable foreign key constraint enforcement
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Create issuers table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS issuers (
        issuer_id INTEGER PRIMARY KEY AUTOINCREMENT,
        lei TEXT UNIQUE,
        legal_name TEXT NOT NULL,
        country TEXT,
        sector TEXT
    );
    """)

    # Create instruments table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS instruments (
        isin TEXT PRIMARY KEY,
        figi TEXT UNIQUE,
        issuer_id INTEGER,
        maturity_date TEXT,
        coupon REAL,
        currency TEXT,
        FOREIGN KEY (issuer_id) REFERENCES issuers (issuer_id)
    );
    """)

    # Create bond_ratings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bond_ratings (
        rating_id INTEGER PRIMARY KEY AUTOINCREMENT,
        isin TEXT,
        agency TEXT,
        rating_value TEXT,
        rating_date TEXT,
        FOREIGN KEY (isin) REFERENCES instruments (isin)
    );
    """)

    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_FILE}")

def seed_data():
    """Populate the database with diverse financial seed data."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Check if data already exists to avoid duplication
    cursor.execute("SELECT COUNT(*) FROM issuers")
    if cursor.fetchone()[0] > 0:
        print("Database already seeded. Skipping seed data.")
        conn.close()
        return

    # Seed Issuers
    # US Treasury, Apple, Microsoft, Petrobras (Emerging Market), and a generic bank
    issuers = [
        ("5493006MNBPLPEVJEJ08", "US Treasury", "USA", "Government"),
        ("549300F299002598R715", "Apple Inc.", "USA", "Technology"),
        ("INR123456789", "Reliance Industries Ltd", "IN", "Energy"),
        ("5493001R1363646N5762", "European Investment Bank", "LU", "Supranational"),
        ("JPSK01239102", "Japan Government", "JP", "Government")
    ]
    
    cursor.executemany("""
        INSERT INTO issuers (lei, legal_name, country, sector) 
        VALUES (?, ?, ?, ?)
    """, issuers)

    # Get generated issuer IDs
    cursor.execute("SELECT issuer_id, legal_name FROM issuers")
    issuer_map = {name: iid for iid, name in cursor.fetchall()}

    # Seed Instruments (Bonds)
    # Mapping to correct issuer_ids
    instruments = [
        # US Treasury Bond
        ("US912810TS08", "BBG000DQQNJ8", issuer_map["US Treasury"], "2030-05-15", 0.625, "USD"),
        # Apple Corporate Bond
        ("US037833AS99", "BBG005P7Q8K7", issuer_map["Apple Inc."], "2025-05-06", 3.25, "USD"),
        # Reliance Bond
        ("IN0020220011", "BBG003ABC123", issuer_map["Reliance Industries Ltd"], "2028-09-01", 7.50, "INR"),
        # EIB Green Bond
        ("XS2345678901", "BBG001XYZ987", issuer_map["European Investment Bank"], "2031-11-15", 0.50, "EUR"),
        # JGB
        ("JP1200021F77", "BBG002JGB456", issuer_map["Japan Government"], "2040-03-20", 1.8, "JPY")
    ]

    cursor.executemany("""
        INSERT INTO instruments (isin, figi, issuer_id, maturity_date, coupon, currency)
        VALUES (?, ?, ?, ?, ?, ?)
    """, instruments)
    
    # Seed Ratings
    ratings = [
        ("US912810TS08", "Moody's", "Aaa", "2023-01-15"),
        ("US912810TS08", "S&P", "AA+", "2023-01-15"),
        ("US037833AS99", "Moody's", "Aa1", "2023-02-10"),
        ("IN0020220011", "S&P", "BBB+", "2023-06-20"),
        ("XS2345678901", "Fitch", "AAA", "2023-03-05"),
        ("JP1200021F77", "S&P", "A+", "2023-07-01")
    ]

    cursor.executemany("""
        INSERT INTO bond_ratings (isin, agency, rating_value, rating_date)
        VALUES (?, ?, ?, ?)
    """, ratings)

    conn.commit()
    conn.close()
    print("Seed data inserted successfully.")

if __name__ == "__main__":
    init_db()
    seed_data()
