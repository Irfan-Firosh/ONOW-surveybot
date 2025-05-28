from dotenv import load_dotenv
import os
import sqlite3
from sqlalchemy import create_engine, text
from langchain.chains import create_sql_query_chain
from langchain_community.llms import OpenAI
from langchain_community.utilities import SQLDatabase
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from Preprocessor.db_generate import convert_csv_to_sqlite

ADDITIONAL_INSTRUCTIONS = """Dont use any other columns except the ones provided in the database, 
dont limit the number of rows you return, return all rows"""

class Processor:
    def __init__(self, path):
        load_dotenv()
        temp_path = f'CleanedData/{path.replace(".csv", ".db")}'
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
    
    def get_graph(self, query):
        df = None
        if query is None:
            df = pd.read_sql_query("SELECT * FROM data", self.conn)
        else:
            df = pd.read_sql_query(query, self.conn)
        
        # Actually generate the graph
        if len(df.columns) == 1:
            # Single column - create a histogram
            fig = px.histogram(df, x=df.columns[0], title=f"Distribution of {df.columns[0]}")
        elif len(df.columns) == 2:
            # Two columns - create a scatter plot
            fig = px.scatter(df, x=df.columns[0], y=df.columns[1], 
                           title=f"{df.columns[1]} vs {df.columns[0]}")
        else:
            # Multiple columns - create a correlation heatmap
            numeric_df = df.select_dtypes(include=['float64', 'int64'])
            if not numeric_df.empty:
                corr_matrix = numeric_df.corr()
                fig = px.imshow(corr_matrix, 
                              title="Correlation Heatmap",
                              labels=dict(color="Correlation"))
            else:
                # If no numeric columns, create a bar chart of the first two columns
                fig = px.bar(df, x=df.columns[0], y=df.columns[1],
                           title=f"{df.columns[1]} by {df.columns[0]}")
        
        return fig