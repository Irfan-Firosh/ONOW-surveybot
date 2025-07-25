import os
import sqlite3
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from langchain_openai import OpenAI
from langchain_community.utilities import SQLDatabase
from langchain.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from .fetcher import get_data_from_api
from .graph import SmartVisualizationSystem

class SQLProcessor:
    def __init__(self, survey_id: int):
        """
        Initialize processor with survey data from API and set up database connections.
        """
        self.db_path, self.table_name = get_data_from_api(survey_id)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.db = SQLDatabase(self.engine)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
        self.llm = OpenAI(api_key=self.openai_api_key, temperature=0)
        
        self.query_prompt = PromptTemplate(
            input_variables=["question", "table_info"],
            template="""You are a SQL expert. Generate a SQLite query for this question.
        
Available tables and columns:
{table_info}

Question: {question}

Rules:
1. Use exact column names from the schema above
2. Use double quotes for column names: "column_name"
3. Use single quotes for string values: 'value'
4. Do not limit results unless specifically asked
5. Return ONLY the SQL query, nothing else
6. Start with SELECT or WITH
7. Ensure the query will return data

SQL Query:"""
        )
        
        self.preprocessing_prompt = PromptTemplate(
            input_variables=["query", "table_info"],
            template="""You are a SQL expert. Fix and validate this SQLite query to ensure it will return data.
        
Available tables and columns:
{table_info}

Original query:
{query}

Rules:
1. Keep the query's original intent
2. Ensure it follows SQLite syntax
3. Remove any LIMIT clauses unless specifically requested
4. Fix any column or table name issues
5. Ensure the query will return data
6. Return ONLY the fixed SQL query, nothing else

Fixed query:"""
        )
        self.visualization_system = SmartVisualizationSystem()

    def get_table_info(self) -> str:
        """
        Retrieves database schema information for query generation using pure SQL.
        """
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        table_info = []
        for table_row in tables:
            table_name = table_row[0]
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            column_names = [col[1] for col in columns]
            column_types = [f"{col[1]} ({col[2]})" for col in columns]
            
            table_info.append(f"Table '{table_name}' columns: {', '.join(column_types)}")
        
        return "\n".join(table_info)

    def get_sample_data(self, limit: int = 5) -> Dict[str, List[Dict]]:
        """
        Get sample data from all tables using pure SQL.
        """
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        sample_data = {}
        for table_row in tables:
            table_name = table_row[0]
            
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
                rows = cursor.fetchall()
                
                if rows:
                    columns = [description[0] for description in cursor.description]
                    sample_data[table_name] = [
                        dict(zip(columns, row)) for row in rows
                    ]
                else:
                    sample_data[table_name] = []
                    
            except Exception as e:
                sample_data[table_name] = {"error": str(e)}
                
        return sample_data

    def create_query(self, input_text: str) -> str:
        """
        Generates SQL query from natural language input using LLM.
        """
        if not input_text or len(input_text.strip()) == 0:
            raise ValueError("Empty query input")
            
        if "limit" not in input_text.lower():
            input_text += " (do not limit results unless specifically asked)"
        
        table_info = self.get_table_info()
        
        try:
            chain = self.query_prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "question": input_text,
                "table_info": table_info
            })
            
            sql_query = response.strip()
            
            if not sql_query:
                raise ValueError("Empty SQL query generated")
                
            if not sql_query.upper().startswith(('SELECT', 'WITH')):
                raise ValueError(f"Invalid SQL query. Must start with SELECT or WITH. Got: {sql_query[:20]}...")
            
            return self.preprocess_query(sql_query)
            
        except Exception as e:
            try:
                fallback_query = f'SELECT COUNT(*) as count FROM "{self.table_name}"'
                self.test_query_execution(fallback_query)
                return fallback_query
            except Exception:
                pass
            
            raise ValueError(f"Failed to generate valid SQL query: {str(e)}")

    def preprocess_query(self, query: str) -> str:
        """
        Validates and fixes SQL query to ensure proper execution.
        """
        table_info = self.get_table_info()
        
        try:
            chain = self.preprocessing_prompt | self.llm | StrOutputParser()
            response = chain.invoke({
                "query": query,
                "table_info": table_info
            })
            
            fixed_query = response.strip()
            
            if not fixed_query.upper().startswith(('SELECT', 'WITH')):
                raise ValueError("Fixed query doesn't start with SELECT or WITH")
            
            return fixed_query
            
        except Exception:
            return query

    def clean_sql_query(self, query: str) -> str:
        """
        Clean and format SQL query string.
        """
        query = query.strip()
        
        if query.startswith('```sql'):
            query = query.replace('```sql', '').replace('```', '').strip()
        elif query.startswith('```'):
            query = query.replace('```', '').strip()
        
        query = query.replace('""', '"')
        
        return query

    def test_query_execution(self, query: str) -> bool:
        """
        Test if a query can be executed without errors.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            cursor.fetchone()
            return True
        except Exception:
            return False

    def execute_query(self, query: str) -> Dict[str, Any]:
        """
        Executes SQL query and returns results with metadata using pure SQL.
        """
        try:
            query = self.clean_sql_query(query)
            query = self.preprocess_query(query)
            
            cursor = self.conn.cursor()
            cursor.execute(query)
            
            columns = [description[0] for description in cursor.description]
            
            rows = cursor.fetchall()
            
            data = [dict(zip(columns, row)) for row in rows]
            
            return {
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "success": True,
                "query_executed": query
            }
            
        except Exception as e:  
            try:
                cursor = self.conn.cursor()
                cursor.execute("SELECT 1")
                connection_error = False
            except Exception:
                connection_error = True
            
            error_msg = f"Database connection error: {str(e)}" if connection_error else f"Failed to execute query: {str(e)}"
            
            return {
                "data": [],
                "columns": [],
                "row_count": 0,
                "success": False,
                "error": error_msg,
                "query_executed": query
            }

    def get_aggregated_stats(self, table_name: str = None) -> Dict[str, Any]:
        """
        Get basic statistics about the database using SQL aggregations.
        """
        if not table_name:
            table_name = self.table_name
            
        cursor = self.conn.cursor()
        stats = {}
        
        try:
            cursor.execute(f"SELECT COUNT(*) as total_rows FROM {table_name}")
            stats["total_rows"] = cursor.fetchone()[0]
            
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns_info = cursor.fetchall()
            
            stats["columns"] = []
            for col_info in columns_info:
                col_name = col_info[1]
                col_type = col_info[2]
                
                col_stats = {
                    "name": col_name,
                    "type": col_type,
                    "null_count": 0,
                    "distinct_count": 0
                }
                
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table_name} WHERE "{col_name}" IS NULL')
                    col_stats["null_count"] = cursor.fetchone()[0]
                    
                    cursor.execute(f'SELECT COUNT(DISTINCT "{col_name}") FROM {table_name}')
                    col_stats["distinct_count"] = cursor.fetchone()[0]
                    
                except Exception as e:
                    col_stats["error"] = str(e)
                
                stats["columns"].append(col_stats)
                
        except Exception as e:
            stats["error"] = str(e)
            
        return stats

    def create_visualizations(self, query_result: Dict[str, Any], user_query: str) -> Dict[str, Any]:
        """
        Use SmartVisualizationSystem to generate visualization suggestions and chart configs.
        """
        if not query_result["success"] or not query_result["data"]:
            return {
                "charts": [],
                "reasoning": "No data available for visualization",
                "total_charts": 0,
                "suggestions": []
            }
        data = query_result["data"]
        columns = query_result["columns"]   
        result = self.visualization_system.create_visualizations(data, columns, user_query)
        return result

    def process_query_with_visualizations(self, user_query: str) -> Dict[str, Any]:
        """
        Complete pipeline: generates SQL, executes query, and analyzes for visualizations.
        """
        try:    
            sql_query = self.create_query(user_query)
            query_result = self.execute_query(sql_query)
            
            if not query_result["success"]:
                return {
                    "sql_query": sql_query,
                    "query_result": query_result,
                    "visualizations": {
                        "charts": [], 
                        "reasoning": f"Query execution failed: {query_result.get('error', 'Unknown error')}", 
                        "total_charts": 0
                    },
                    "success": False,
                    "error": query_result.get("error", "Query execution failed")
                }
            
            viz_result = self.create_visualizations(query_result, user_query)
            
            return {
                "sql_query": sql_query,
                "query_result": query_result,
                "visualizations": viz_result,
                "success": True,
                "stats": self.get_aggregated_stats()
            }
            
        except Exception as e:
            return {
                "sql_query": "",
                "query_result": {
                    "data": [],
                    "columns": [],
                    "row_count": 0,
                    "success": False,
                    "error": str(e)
                },
                "visualizations": {
                    "charts": [], 
                    "reasoning": f"Error: {str(e)}", 
                    "total_charts": 0
                },
                "success": False,
                "error": str(e)
            }

    def get_survey_questions(self) -> List[str]:
        """
        Get all questions for the survey from the database schema.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"PRAGMA table_info({self.table_name})")
            columns = cursor.fetchall()
            
            question_columns = []
            for col in columns:
                col_name = col[1]
                if col_name not in ['contact_id', 'name', 'is_anonymous']:
                    question_columns.append(col_name)
            
            return question_columns
        except Exception as e:
            print(f"Error getting survey questions: {e}")
            return []

    def get_survey_summary(self) -> Dict[str, Any]:
        """
        Get a summary of survey responses including response count and basic stats.
        """
        try:
            cursor = self.conn.cursor()
            
            cursor.execute(f"SELECT COUNT(*) as total_responses FROM {self.table_name}")
            total_responses = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) as anonymous_count FROM {self.table_name} WHERE is_anonymous = 1")
            anonymous_count = cursor.fetchone()[0]
            named_count = total_responses - anonymous_count
            
            questions = self.get_survey_questions()
            
            summary = {
                "total_responses": total_responses,
                "anonymous_responses": anonymous_count,
                "named_responses": named_count,
                "total_questions": len(questions),
                "questions": questions
            }
            
            return summary
        except Exception as e:
            print(f"Error getting survey summary: {e}")
            return {
                "error": str(e),
                "total_responses": 0,
                "anonymous_responses": 0,
                "named_responses": 0,
                "total_questions": 0,
                "questions": []
            }

    def __del__(self):
        """
        Clean up database connection on object destruction.
        """
        if hasattr(self, 'conn'):
            self.conn.close()


if __name__ == "__main__":
    import json
    processor = SQLProcessor(survey_id=3200079)
    
    result = processor.process_query_with_visualizations("Give me all the responses")
    
    if result["success"]:
        print(f"SQL Query: {result['sql_query']}")
        print(result['query_result']['data'])
        with open("result.json", "w") as f:
            json.dump(result['query_result'], f)
        print(f"Data rows: {result['query_result']['row_count']}")
        print(f"Columns: {result['query_result']['columns']}")
        print(f"Visualization suggestions: {result['visualizations']['total_charts']}")
        with open("visualizations.json", "w") as f:
            json.dump(result['visualizations'], f)
    else:
        print(f"Error: {result['error']}")