import os
import sqlite3
import json
import time
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from typing import Literal, List, Optional, Dict, Any, Union
from langchain_openai import OpenAI
from langchain.prompts import PromptTemplate
from langchain.output_parsers import PydanticOutputParser


openai_api_key = os.getenv("OPENAI_API_KEY")

class ChartJSDataset(BaseModel):
    label: str
    data: List[Union[int, float]]
    backgroundColor: Optional[Union[str, List[str]]] = None
    borderColor: Optional[Union[str, List[str]]] = None
    borderWidth: Optional[int] = 1

class ChartJSData(BaseModel):
    labels: List[str]
    datasets: List[ChartJSDataset]

class ChartJSOptions(BaseModel):
    responsive: bool = True
    plugins: Optional[Dict[str, Any]] = None
    scales: Optional[Dict[str, Any]] = None

class BarChart(BaseModel):
    chart_type: Literal["bar"] = "bar"
    x_column: str = Field(description="Column name for x-axis")
    y_column: Optional[str] = Field(description="Column name for y-axis (if needed)")
    title: str = Field(description="Chart title")
    color_column: Optional[str] = Field(description="Column for color grouping")
    
    def to_chartjs_config(self, data: List[Dict]) -> Dict[str, Any]:
        if self.y_column:
            # Grouped bar chart
            labels = [str(row[self.x_column]) for row in data]
            values = [row[self.y_column] for row in data]
            
            dataset = ChartJSDataset(
                label=self.y_column,
                data=values,
                backgroundColor='rgba(54, 162, 235, 0.6)',
                borderColor='rgba(54, 162, 235, 1)'
            )
        else:
            # Count-based bar chart
            value_counts = {}
            for row in data:
                key = str(row[self.x_column])
                value_counts[key] = value_counts.get(key, 0) + 1
            
            labels = list(value_counts.keys())
            values = list(value_counts.values())
            
            dataset = ChartJSDataset(
                label="Count",
                data=values,
                backgroundColor='rgba(54, 162, 235, 0.6)',
                borderColor='rgba(54, 162, 235, 1)'
            )
        
        return {
            "type": "bar",
            "data": ChartJSData(labels=labels, datasets=[dataset]).dict(),
            "options": ChartJSOptions(
                plugins={"title": {"display": True, "text": self.title}}
            ).dict()
        }

class LineChart(BaseModel):
    chart_type: Literal["line"] = "line"
    x_column: str = Field(description="Column name for x-axis")
    y_column: str = Field(description="Column name for y-axis")
    title: str = Field(description="Chart title")
    color_column: Optional[str] = Field(description="Column for line grouping")
    
    def to_chartjs_config(self, data: List[Dict]) -> Dict[str, Any]:
        if self.color_column:
            groups = {}
            for row in data:
                group_key = str(row[self.color_column])
                if group_key not in groups:
                    groups[group_key] = {"x": [], "y": []}
                groups[group_key]["x"].append(str(row[self.x_column]))
                groups[group_key]["y"].append(row[self.y_column])
            
            datasets = []
            colors = ['rgba(255, 99, 132, 0.6)', 'rgba(54, 162, 235, 0.6)', 'rgba(255, 206, 86, 0.6)']
            for i, (group, values) in enumerate(groups.items()):
                datasets.append(ChartJSDataset(
                    label=group,
                    data=values["y"],
                    backgroundColor=colors[i % len(colors)],
                    borderColor=colors[i % len(colors)].replace('0.6', '1'),
                    fill=False
                ))
            
            labels = list(set(str(row[self.x_column]) for row in data))
            labels.sort()
        else:
            labels = [str(row[self.x_column]) for row in data]
            values = [row[self.y_column] for row in data]
            
            datasets = [ChartJSDataset(
                label=self.y_column,
                data=values,
                backgroundColor='rgba(75, 192, 192, 0.6)',
                borderColor='rgba(75, 192, 192, 1)',
                fill=False
            )]
        
        return {
            "type": "line",
            "data": ChartJSData(labels=labels, datasets=datasets).dict(),
            "options": ChartJSOptions(
                plugins={"title": {"display": True, "text": self.title}}
            ).dict()
        }

class PieChart(BaseModel):
    chart_type: Literal["pie"] = "pie"
    values_column: str = Field(description="Column name for values")
    names_column: str = Field(description="Column name for labels")
    title: str = Field(description="Chart title")
    
    def to_chartjs_config(self, data: List[Dict]) -> Dict[str, Any]:
        labels = [str(row[self.names_column]) for row in data]
        values = [row[self.values_column] for row in data]
        
        colors = [
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 206, 86, 0.6)',
            'rgba(75, 192, 192, 0.6)',
            'rgba(153, 102, 255, 0.6)',
            'rgba(255, 159, 64, 0.6)'
        ]
        
        dataset = ChartJSDataset(
            label=self.title,
            data=values,
            backgroundColor=colors[:len(values)]
        )
        
        return {
            "type": "pie",
            "data": ChartJSData(labels=labels, datasets=[dataset]).dict(),
            "options": ChartJSOptions(
                plugins={"title": {"display": True, "text": self.title}}
            ).dict()
        }

class DoughnutChart(BaseModel):
    chart_type: Literal["doughnut"] = "doughnut"
    values_column: str = Field(description="Column name for values")
    names_column: str = Field(description="Column name for labels")
    title: str = Field(description="Chart title")
    
    def to_chartjs_config(self, data: List[Dict]) -> Dict[str, Any]:
        labels = [str(row[self.names_column]) for row in data]
        values = [row[self.values_column] for row in data]
        
        colors = [
            'rgba(255, 99, 132, 0.6)',
            'rgba(54, 162, 235, 0.6)',
            'rgba(255, 206, 86, 0.6)',
            'rgba(75, 192, 192, 0.6)',
            'rgba(153, 102, 255, 0.6)',
            'rgba(255, 159, 64, 0.6)'
        ]
        
        dataset = ChartJSDataset(
            label=self.title,
            data=values,
            backgroundColor=colors[:len(values)]
        )
        
        return {
            "type": "doughnut",
            "data": ChartJSData(labels=labels, datasets=[dataset]).dict(),
            "options": ChartJSOptions(
                plugins={"title": {"display": True, "text": self.title}}
            ).dict()
        }

class ScatterChart(BaseModel):
    chart_type: Literal["scatter"] = "scatter"
    x_column: str = Field(description="Column name for x-axis")
    y_column: str = Field(description="Column name for y-axis")
    title: str = Field(description="Chart title")
    color_column: Optional[str] = Field(description="Column for color grouping")
    
    def to_chartjs_config(self, data: List[Dict]) -> Dict[str, Any]:
        if self.color_column:
            groups = {}
            for row in data:
                group_key = str(row[self.color_column])
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append({
                    "x": row[self.x_column],
                    "y": row[self.y_column]
                })
            
            datasets = []
            colors = ['rgba(255, 99, 132, 0.6)', 'rgba(54, 162, 235, 0.6)', 'rgba(255, 206, 86, 0.6)']
            for i, (group, points) in enumerate(groups.items()):
                datasets.append({
                    "label": group,
                    "data": points,
                    "backgroundColor": colors[i % len(colors)],
                    "borderColor": colors[i % len(colors)].replace('0.6', '1')
                })
        else:
            points = [{"x": row[self.x_column], "y": row[self.y_column]} for row in data]
            datasets = [{
                "label": f"{self.x_column} vs {self.y_column}",
                "data": points,
                "backgroundColor": 'rgba(75, 192, 192, 0.6)',
                "borderColor": 'rgba(75, 192, 192, 1)'
            }]
        
        return {
            "type": "scatter",
            "data": {"datasets": datasets},
            "options": {
                "responsive": True,
                "plugins": {"title": {"display": True, "text": self.title}},
                "scales": {
                    "x": {"title": {"display": True, "text": self.x_column}},
                    "y": {"title": {"display": True, "text": self.y_column}}
                }
            }
        }

ChartConfig = Union[BarChart, LineChart, PieChart, DoughnutChart, ScatterChart]

class VisualizationRecommendation(BaseModel):
    """Recommended visualizations for the given data and query"""
    recommendations: List[ChartConfig] = Field(description="List of recommended chart configurations")
    reasoning: str = Field(description="Explanation of why these charts were recommended")

# --- Replace SQLiteAnalyzer with DataAnalyzer ---
class DataAnalyzer:
    def __init__(self):
        self.llm = OpenAI(api_key=openai_api_key, temperature=0)
        self.parser = PydanticOutputParser(pydantic_object=VisualizationRecommendation)
        self.prompt = PromptTemplate(
            template="""
Data visualization expert: Recommend 1-2 best Chart.js compatible charts for this query and data.

QUERY: {user_query}
DATA SIZE: {data_size}

COLUMNS & TYPES:
{column_info}

AVAILABLE CHART TYPES:
- bar: categorical data distributions 
- line: trends over time/ordered data
- pie/doughnut: categorical proportions
- scatter: two numerical relationships

Use exact column names from above. For Chart.js compatibility, ensure proper data structure.

For the explanation, explain why the data insight is important, not why the graph style was chosen.

{format_instructions}
""",
            input_variables=["user_query", "data_size", "column_info"],
            partial_variables={"format_instructions": self.parser.get_format_instructions()}
        )

    def analyze_data(self, data: list, columns: list) -> dict:
        column_types = {}
        if data:
            sample_row = data[0]
            for col in columns:
                value = sample_row.get(col, None)
                if isinstance(value, (int, float)):
                    column_types[col] = 'numerical'
                else:
                    column_types[col] = 'categorical'
        return {
            "data": data,
            "columns": columns,
            "data_size": f"{len(data)} rows × {len(columns)} columns",
            "numerical_columns": [col for col, typ in column_types.items() if typ == 'numerical'],
            "categorical_columns": [col for col, typ in column_types.items() if typ == 'categorical'],
            "column_types": column_types
        }

    def recommend_visualizations(self, data: list, columns: list, user_query: str) -> tuple[VisualizationRecommendation, list]:
        data_info = self.analyze_data(data, columns)
        column_info = ", ".join([f"{col}({typ})" for col, typ in data_info["column_types"].items()])
        formatted_prompt = self.prompt.format(
            user_query=user_query,
            data_size=data_info["data_size"],
            column_info=column_info
        )
        response = self.llm(formatted_prompt)
        try:
            recommendations = self.parser.parse(response)
            return recommendations, data_info["data"]
        except Exception as e:
            return self._fallback_recommendations(data_info), data_info["data"]

    def _fallback_recommendations(self, data_info: dict) -> VisualizationRecommendation:
        recommendations = []
        numerical_cols = data_info["numerical_columns"]
        categorical_cols = data_info["categorical_columns"]
        if len(numerical_cols) >= 2:
            recommendations.append(ScatterChart(
                x_column=numerical_cols[0],
                y_column=numerical_cols[1],
                title=f"{numerical_cols[0]} vs {numerical_cols[1]}"
            ))
        if len(categorical_cols) >= 1:
            recommendations.append(BarChart(
                x_column=categorical_cols[0],
                title=f"Distribution of {categorical_cols[0]}"
            ))
        return VisualizationRecommendation(
            recommendations=recommendations,
            reasoning="Fallback recommendations based on data types"
        )

class ChartJSGenerator:
    
    @staticmethod
    def generate_chart_config(data: List[Dict], config: ChartConfig) -> Dict[str, Any]:
        """Generate Chart.js configuration from data and chart config"""
        try:
            return config.to_chartjs_config(data)
        except Exception as e:
            return None

# --- Refactor SmartVisualizationSystem ---
class SmartVisualizationSystem:
    def __init__(self):
        self.analyzer = DataAnalyzer()
        self.generator = ChartJSGenerator()

    def create_visualizations(self, data: list, columns: list, user_query: str) -> dict:
        try:
            recommendations, data_rows = self.analyzer.recommend_visualizations(data, columns, user_query)
            if not recommendations.recommendations:
                return {
                    "charts": [],
                    "reasoning": "No suitable visualizations could be generated for the given data and query",
                    "total_charts": 0,
                    "data_size": len(data_rows) if data_rows else 0
                }
            charts = []
            for i, config in enumerate(recommendations.recommendations):
                chart_config = self.generator.generate_chart_config(data_rows, config)
                if chart_config:
                    charts.append({
                        "config": chart_config,
                        "chart_type": config.chart_type,
                        "title": config.title
                    })
            return {
                "charts": charts,
                "reasoning": recommendations.reasoning,
                "total_charts": len(charts),
                "data_size": len(data_rows) if data_rows else 0
            }
        except Exception as e: 
            return {
                "charts": [],
                "reasoning": f"Error generating visualizations: {str(e)}",
                "total_charts": 0,
                "data_size": 0
            }

# --- Refactor generate_smart_visualizations ---
def generate_smart_visualizations(data: list, columns: list, user_query: str) -> list:
    system = SmartVisualizationSystem()
    result = system.create_visualizations(data, columns, user_query)
    if not result["charts"]:
        return []   
    return [chart_data["config"] for chart_data in result["charts"]]

if __name__ == "__main__":
    db_path = "/Users/irfanfirosh/Desktop/ONOW/ONOW-surveybot/survey_data.db"  # Path to your SQLite database
    test_query = "How many responses are there?"
    
    custom_sql = "SELECT * FROM survey_3200079"
    
    system = SmartVisualizationSystem()
    result = system.create_visualizations(data, columns, user_query)

    for i, chart_data in enumerate(result['charts']):
        print(json.dumps(chart_data['config'], indent=2))