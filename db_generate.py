import sqlite3
import pandas as pd
import os
import tempfile

class DBGenerator:
    def __init__(self, csv_path):
        self.csv_path = csv_path
        self.db_path = os.path.splitext(csv_path)[0] + '.db'
    
    def _create_temp_schema(self, df):
        """Creates a temporary schema file from DataFrame columns"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as temp_file:
            # Create table statement
            columns = []
            for col in df.columns:
                # Clean column name
                clean_col = col.lower().replace(' ', '_').replace('-', '_')
                clean_col = ''.join(c for c in clean_col if c.isalnum() or c == '_')
                if not clean_col:
                    clean_col = f"column_{len(columns)}"
                columns.append(f'"{clean_col}" TEXT')
            
            create_table = f"""
            CREATE TABLE IF NOT EXISTS "data" (
                {', '.join(columns)}
            );
            """
            temp_file.write(create_table)
            return temp_file.name

    def convert_csv_to_db(self):
        """Converts CSV to SQLite database with temporary schema handling"""
        try:
            df = pd.read_csv(self.csv_path)
            temp_schema = self._create_temp_schema(df)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            with open(temp_schema, 'r') as f:
                schema_sql = f.read()
            cursor.executescript(schema_sql)
            
            df.columns = [col.lower().replace(' ', '_').replace('-', '_') for col in df.columns]
            df.columns = [''.join(c for c in col if c.isalnum() or c == '_') for col in df.columns]
            
            df.to_sql('data', conn, if_exists='append', index=False)
            
            conn.commit()
            conn.close()
            os.unlink(temp_schema)
            
            print(f"Successfully converted {self.csv_path} to {self.db_path}")
            return True
            
        except Exception as e:
            print(f"Error converting CSV to database: {e}")
            if 'temp_schema' in locals():
                try:
                    os.unlink(temp_schema)
                except:
                    pass
            return False

def convert_csv_to_sqlite(csv_path):
    """
    Convert a CSV file to SQLite database.
    
    Args:
        csv_path (str): Path to the CSV file
        
    Returns:
        bool: True if conversion was successful, False otherwise
    """
    generator = DBGenerator(csv_path)
    return generator.convert_csv_to_db()

def execute_schema_from_file(schema_file, db_name):
    """
    Reads SQL schema from a file and executes it on the specified SQLite database.
    """
    try:
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()
        print(f"Successfully executed schema from {schema_file} on {db_name}")
        return True
    except Exception as e:
        print(f"Error executing schema: {e}")
        return False

if __name__ == "__main__":
    # Example usage
    csv_path = "EFI_seed_cleaned.csv"
    convert_csv_to_sqlite(csv_path)
