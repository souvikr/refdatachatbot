from fastmcp import FastMCP
import sqlite3
import pathlib
import os

# Initialize MCP Server
mcp = FastMCP("BondRefDataServer")

# Define the database file path relative to this script
DB_FILE = pathlib.Path(__file__).parent / "finance.db"

def get_db_connection():
    """
    Establishes a connection to the SQLite database.
    Uses generic read-only access where possible to avoid locking issues on Windows.
    """
    # Use URI format for read-only mode if supported, otherwise standard connect
    # Windows paths can be tricky with URIs, so we'll use standard connection 
    # but ensure we close it promptly in the context manager.
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

@mcp.tool()
def get_instrument_details(isin: str) -> str:
    """
    Get full bond details including issuer information.
    
    Args:
        isin: The International Securities Identification Number of the bond.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT i.isin, i.figi, i.maturity_date, i.coupon, i.currency,
                   iss.legal_name, iss.lei, iss.country, iss.sector
            FROM instruments i
            JOIN issuers iss ON i.issuer_id = iss.issuer_id
            WHERE i.isin = ?
        """
        
        cursor.execute(query, (isin,))
        row = cursor.fetchone()
        
        if row:
            # Convert Row object to dict for better serialization/formatting
            data = dict(row)
            return str(data)
        else:
            return f"ISIN {isin} not found."
            
    except Exception as e:
        return f"Error retrieving instrument details: {str(e)}"
    finally:
        if conn:
            conn.close()

@mcp.tool()
def get_bond_rating(isin: str) -> str:
    """
    Return the latest rating for a specific bond.
    
    Args:
        isin: The International Securities Identification Number of the bond.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get the most recent rating based on rating_date
        query = """
            SELECT agency, rating_value, rating_date
            FROM bond_ratings
            WHERE isin = ?
            ORDER BY rating_date DESC
            LIMIT 1
        """
        
        cursor.execute(query, (isin,))
        row = cursor.fetchone()
        
        if row:
            return f"Agency: {row['agency']}, Rating: {row['rating_value']}, Date: {row['rating_date']}"
        else:
            return f"No ratings found for ISIN {isin}."
            
    except Exception as e:
        return f"Error retrieving bond rating: {str(e)}"
    finally:
        if conn:
            conn.close()

@mcp.tool()
def search_issuer(name: str) -> str:
    """
    Search for issuers by name.
    
    Args:
        name: The name or partial name of the issuer to search for.
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Enhanced query to search both legal_name and lei
        query = """
            SELECT lei, legal_name, country, sector
            FROM issuers
            WHERE legal_name LIKE ? OR lei LIKE ?
        """
        
        # Add wildcards for partial match
        search_term = f"%{name}%"
        cursor.execute(query, (search_term, search_term))
        rows = cursor.fetchall()
        
        if rows:
            results = [dict(row) for row in rows]
            return str(results)
        else:
            return f"No issuers found matching '{name}'."
            
    except Exception as e:
        return f"Error searching for issuer: {str(e)}"
    finally:
        if conn:
            conn.close()
