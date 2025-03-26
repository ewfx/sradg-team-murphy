from tinydb import TinyDB, Query
import pandas as pd
import os

class TinyDBManager:
    def __init__(self, db_path="tinydb.json"):
        """Initialize TinyDB and create metadata table if not exists."""
        self.db = TinyDB(db_path)
        self.metadata_table = self.db.table("metadata")

    def register_system(self, system_name, key_columns, criteria_columns):
        """Register a system in metadata. Table name is derived from system_name."""
        table_name = f"{system_name}_data"
        query = Query()

        # Check if system already exists
        if not self.metadata_table.search(query.system_name == system_name):
            self.metadata_table.insert({
                "system_name": system_name,
                "table_name": table_name,
                "key_columns": key_columns,
                "criteria_columns": criteria_columns
            })
            print(f"✅ Registered system: {system_name}, Table: {table_name}")
        else:
            print(f"⚠️ System '{system_name}' already registered.")

    def create_system_table(self, system_name):
        """Create (or get) the system-specific table."""
        table_name = f"{system_name}_data"
        return self.db.table(table_name)

    def load_csv_to_system(self, system_name, csv_path):
        """Load CSV data into the corresponding system table."""
        if not os.path.exists(csv_path):
            print("❌ CSV file not found!")
            return
        
        table = self.create_system_table(system_name)
        df = pd.read_csv(csv_path)
        records = df.to_dict(orient="records")
        table.insert_multiple(records)

        print(f"✅ Loaded {len(records)} records into {system_name}_data")

    def get_historical_data(self, system_name, filters={}):
        """Retrieve historical data for a given system based on filters."""
        table_name = f"{system_name}_data"
        table = self.db.table(table_name)
        query = Query()

        print(table_name)
        print(table)
        print(filters)

        if filters:
            results = table.search(query.fragment(filters))
        else:
            results = table.all()

        return results

# 🌟 Initialize DB on startup
db_manager = TinyDBManager()
