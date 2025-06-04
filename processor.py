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
from ydata_profiling import ProfileReport
from Graph.main import Graph
import json
import re

ADDITIONAL_INSTRUCTIONS = """Dont use any other columns except the ones provided in the database, 
dont limit the number of rows you return, return all rows, if you are selecting the entire table, just use
SELECT * FROM [name of table]"""

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
        string = self.db_agent.invoke({"question": f"{input_text} {ADDITIONAL_INSTRUCTIONS}"})
        sql_query = self.filter_query(string)
        
        return sql_query
    
    def execute_query(self, query):
        query = query.replace('""', '"')
        return pd.read_sql_query(query, self.conn)
    
    def get_graph(self, query):
        df = None
        if query is None:
            df = pd.read_sql_query("SELECT * FROM data", self.conn)
        else:
            df = pd.read_sql_query(query, self.conn)

        # Limit the number of rows for profiling if dataset is large
        if len(df) > 1000:
            df_sample = df.sample(n=1000, random_state=42)
        else:
            df_sample = df

        # Create a minimal profile with only essential statistics
        profile = ProfileReport(
            df_sample,
            minimal=True,
            correlations=None,
            interactions=None,
            samples=None,
            duplicates=None,
            missing_diagrams=None,
            progress_bar=True
        )
        
        json_data = profile.to_json()
        json_dict = json.loads(json_data)
        graph = Graph(json_dict, df_sample, correlation_threshold=0.5)
        top_graphs = graph.suggest_top_graphs()
        
        figures = []
        for graph_info in top_graphs:
            try:
                if graph_info['plotly_type'] == 'px.histogram':
                    fig = px.histogram(df, x=graph_info["x"], title=f"Distribution of {graph_info['variable']}")
                    figures.append(fig)
                elif graph_info['plotly_type'] == 'px.bar':
                    fig = px.bar(df, x=graph_info["x"], y=graph_info["y"], title=f"Distribution of {graph_info['variable']}")
                    figures.append(fig)
                elif graph_info['plotly_type'] == 'px.treemap':
                    fig = px.treemap(df, path=[graph_info["labels"]], values=graph_info["values"], title=f"Distribution of {graph_info['variable']}")
                    figures.append(fig)
                elif graph_info['plotly_type'] == 'px.scatter':
                    title = f"Scatter Plot: {graph_info['x']} vs {graph_info['y']}"
                    fig = px.scatter(df, x=graph_info["x"], y=graph_info["y"], title=title)
                    figures.append(fig)
            except Exception as e:
                print(f"Error creating graph: {str(e)}")
                continue
        
        return figures

    def get_profile_report(self, df=None):
        """Generate and return a pandas profiling report for the given DataFrame or entire dataset"""
        if df is None:
            df = pd.read_sql_query("SELECT * FROM data", self.conn)
        profile = ProfileReport(df, title="Dataset Profiling Report")
        return profile.to_html()
    

    def filter_query(self, query):
        query = query.replace('""', '"')
        query = query.replace('"', '')
        query = query.replace("'", "")
        query = query.replace("`", "")
        
        sql_keywords = {
            'SELECT', 'FROM', 'WHERE', 'GROUP', 'BY', 'ORDER', 'HAVING', 
            'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON', 'AND', 'OR', 
            'AS', 'DISTINCT', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN', 'LIMIT',
            'OFFSET', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER',
            'TABLE', 'INDEX', 'VIEW', 'INTO', 'VALUES', 'SET', 'NULL', 'NOT',
            'IN', 'LIKE', 'BETWEEN', 'EXISTS', 'CASE', 'WHEN', 'THEN', 'ELSE',
            'END', 'IS', 'ASC', 'DESC', 'UNION', 'ALL'
        }
    
        def quote_column_names(match):
            word = match.group(0)
        
            if word.upper() in sql_keywords:
                return word
        
            if word.replace('.', '').replace('-', '').isdigit():
                return word
        
            if '(' in word or ')' in word:
                return word
        
            if '"' in word or "'" in word or '`' in word:
                return word
        
            return f'"{word}"'
 
        pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'

        result = re.sub(pattern, quote_column_names, query)
    
        return result
    

