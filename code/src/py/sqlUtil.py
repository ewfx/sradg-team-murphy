import sqlite3
import csv
from typing import Dict, List
import pandas as pd

class SQLiteDB:
    def __init__(self):
        """Initialize an in-memory SQLite database."""
        self.conn = sqlite3.connect(":memory:")  # In-memory DB
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        """Create the historical data table."""
        self.cursor.execute("""
        CREATE TABLE history (
            company_number TEXT, 
            account TEXT, 
            AU TEXT, 
            currency TEXT, 
            primary_account TEXT, 
            secondary_account TEXT, 
            gl_balance REAL, 
            ihb_balance REAL, 
            difference REAL, 
            match_status TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_number TEXT, account TEXT, AU TEXT, currency TEXT, 
            primary_account TEXT, secondary_account TEXT,
            gl_balance REAL, ihb_balance REAL, difference REAL, 
            match_status TEXT, result TEXT, category TEXT, explanation TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        self.conn.commit()

    def load_csv_data(self, csv_filepath):
        """Load historical data from a CSV file into the database."""
        with open(csv_filepath, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader)  # Skip header row
            data = [tuple(row) for row in reader]  # Convert rows to tuples
        
        self.cursor.executemany("""
        INSERT INTO history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, data)
        self.conn.commit()
        print(f"✅ Loaded {len(data)} records into the database.")

    def get_historical_data(self, new_data):
        """
        Retrieve historical data for a given group combination.
        
        :param new_data: Dictionary with new data fields.
        :return: List of matching historical records.
        """
        query = """
        SELECT * FROM history WHERE 
            company_number=? AND account=? AND AU=? AND currency=? 
            AND primary_account=? AND secondary_account=?
        """
        self.cursor.execute(query, (
            new_data["company_number"], new_data["account"], new_data["AU"],
            new_data["currency"], new_data["primary_account"], new_data["secondary_account"]
        ))
        records = self.cursor.fetchall()
        historical_data = [
            {
                "company_number": row[0],
                "account": row[1],
                "AU": row[2],
                "currency": row[3],
                "primary_account": row[4],
                "secondary_account": row[5],
                "gl_balance": float(row[6]),
                "ihb_balance": float(row[7]),
                "difference": float(row[8]),
                "match_status": row[9]
            }
            for row in records
        ]

        return historical_data

    def save_prediction(self, new_data, result, category, explanation):
        """
        Save new data, result, and explanation to the predictions table.
        :param new_data: Dictionary with new data fields.
        :param result: Prediction result (e.g., "Anomaly", "Not Anomaly").
        :param explanation: Explanation for the result.
        """
        query = """
            INSERT INTO predictions 
            (company_number, account, AU, currency, primary_account, secondary_account, 
            gl_balance, ihb_balance, difference, match_status, result, category, explanation) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        self.cursor.execute(query, (
            new_data["company_number"], new_data["account"], new_data["AU"],
            new_data["currency"], new_data["primary_account"], new_data["secondary_account"],
            new_data["gl_balance"], new_data["ihb_balance"], new_data["difference"],
            new_data["match_status"], result, category, explanation
        ))
        
        self.conn.commit()
        print("✅ Prediction saved successfully!")

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def get_predictions(self):
        self.cursor.execute("SELECT * FROM predictions ORDER BY timestamp DESC")
        return self.cursor.fetchall()
    
    def create_table_generic(self, table_name: str, columns: Dict[str, str]):
        """
        Creates a table dynamically based on the provided column names and types.
        Args:
            table_name (str): Name of the table to be created.
            columns (Dict[str, str]): Dictionary where keys are column names and values are SQL types.
        """
        columns_str = ", ".join([f"{col} {dtype}" for col, dtype in columns.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table_name} ({columns_str})"
        
        self.cursor.execute(query)
        self.conn.commit()

    def insert_data_generic(self, table_name: str, data: Dict[str, any]):
        """
        Inserts a row into a specified table.
        Args:
            table_name (str): Name of the table.
            data (Dict[str, any]): Dictionary of column-value pairs.
        """
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        values = tuple(data.values())

        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        self.cursor.execute(query, values)
        self.conn.commit()

    def fetch_data_generic(self, table_name: str, conditions: Dict[str, any] = None) -> List[Dict[str, any]]:
        """
        Fetches rows from a table with optional conditions.
        Args:
            table_name (str): Name of the table.
            conditions (Dict[str, any], optional): Dictionary of column-value pairs to filter results.
        Returns:
            List[Dict[str, any]]: List of row dictionaries.
        """
        if conditions:
            where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
            query = f"SELECT * FROM {table_name} WHERE {where_clause}"
            values = tuple(conditions.values())
        else:
            query = f"SELECT * FROM {table_name}"
            values = ()

        self.cursor.execute(query, values)
        columns = [desc[0] for desc in self.cursor.description]
        rows = self.cursor.fetchall()

        return [dict(zip(columns, row)) for row in rows]
    
    def load_csv_to_table_g(self, csv_path: str, table_name: str):
        """
        Loads data from a CSV file into the specified table.
        - The CSV headers should match the database column names.
        """
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            data = row.to_dict()
            self.insert_data(table_name, data)

        print(f"✅ Loaded {len(df)} records into {table_name}")

    def _create_metadata_table(self):
        """Creates metadata table if it doesn't exist"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    system_name TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    key_columns TEXT NOT NULL,
                    criteria_columns TEXT NOT NULL,
                    UNIQUE(system_name, table_name)  -- Prevent duplicate entries
                )
            """)
            conn.commit()