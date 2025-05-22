from dotenv import load_dotenv
import os
import sqlite3
from sqlalchemy import create_engine, text
from langchain.chains import create_sql_query_chain
from langchain_community.llms import OpenAI
from langchain_community.utilities import SQLDatabase
import pandas as pd
from db_generate import convert_csv_to_sqlite

ADDITIONAL_INSTRUCTIONS = """Dont use any other columns except the ones provided in the database, 
dont limit the number of rows you return, return all rows"""

class Processor:
    def __init__(self, path):
        load_dotenv()
        temp_path = path.replace(".csv", ".db")
        if os.path.exists(temp_path):
            path = temp_path
        else:
            # convert csv to sqlite
            convert_csv_to_sqlite(path)
            path = temp_path

        self.openai_api_key = os.getenv("OPENAI_API_KEY")

        self.sqlite_db_path = path
        self.engine = create_engine(f"sqlite:///{self.sqlite_db_path}")
        self.db = SQLDatabase(self.engine)
        self.conn = sqlite3.connect(self.sqlite_db_path)
        # db agent
        self.llm = OpenAI(api_key=self.openai_api_key, temperature=0)
        self.db_agent = create_sql_query_chain(self.llm, self.db)
    
    def create_query(self, input_text):
        return self.db_agent.invoke({"question": f"{input_text} {ADDITIONAL_INSTRUCTIONS}"})
    
    def execute_query(self, query):
        return pd.read_sql_query(query, self.conn)
    

    
