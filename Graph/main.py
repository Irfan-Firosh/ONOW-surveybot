import json
import pandas as pd

class Graph:
    def __init__(self, json_data, df=None, correlation_threshold=0.7):
        """
        Initialize Graph with JSON data and optionally a DataFrame for type analysis
        Args:
            json_data: Dictionary containing JSON data
            df: Optional pandas DataFrame for type analysis
            correlation_threshold: Minimum correlation coefficient to suggest scatter plot (default: 0.7)
        """
        self.json_data = json_data
        self.variables = json_data.get("variables", {})
        self.correlation_threshold = correlation_threshold
        self.correlations = {}
        
        # If DataFrame is provided, update column types based on DataFrame analysis
        if df is not None:
            self._update_column_types(df)
            self._calculate_correlations(df)
            
        self.graph_suggestions = []

    def _calculate_correlations(self, df):
        """Calculate correlations between numeric columns"""
        numeric_cols = [col for col in df.columns if self.variables.get(col, {}).get("type") == "Numeric"]
        if len(numeric_cols) >= 2:
            corr_matrix = df[numeric_cols].corr()
            self.correlations = corr_matrix.to_dict()

    def _update_column_types(self, df):
        """Update column types based on DataFrame analysis while preserving other JSON data"""
        for col in df.columns:
            if col in self.variables:
                # Get basic column info
                n_unique = df[col].nunique()
                
                # Determine column type
                col_type = "Unsupported"
                
                # Check for datetime
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    col_type = "DateTime"
                # Check for numeric
                elif pd.api.types.is_numeric_dtype(df[col]):
                    col_type = "Numeric"
                # Check for boolean
                elif pd.api.types.is_bool_dtype(df[col]):
                    col_type = "Categorical"
                # Check for categorical (low cardinality)
                elif n_unique < len(df) * 0.05 or n_unique < 10:  # Less than 5% unique values or less than 10 unique values
                    col_type = "Categorical"
                # Check for text
                elif pd.api.types.is_string_dtype(df[col]):
                    # Check if it's actually categorical with string values
                    if n_unique < len(df) * 0.05 or n_unique < 10:
                        col_type = "Categorical"
                    else:
                        col_type = "Text"
                
                # Update only the type in the existing variable info
                self.variables[col]["type"] = col_type
                
                # Update type-specific information if needed
                if col_type == "Numeric" and "mean" not in self.variables[col]:
                    self.variables[col].update({
                        "mean": df[col].mean(),
                        "std": df[col].std(),
                        "min": df[col].min(),
                        "max": df[col].max()
                    })
                elif col_type == "Categorical" and "value_counts_without_nan" not in self.variables[col]:
                    self.variables[col]["value_counts_without_nan"] = df[col].value_counts().to_dict()
                elif col_type == "Text" and "word_counts" not in self.variables[col]:
                    word_counts = {}
                    for text in df[col].dropna():
                        words = str(text).lower().split()
                        for word in words:
                            word_counts[word] = word_counts.get(word, 0) + 1
                    self.variables[col]["word_counts"] = word_counts

    def get_graph(self):
        return self.json_data

    def write_json_to_file(self, file_path):
        with open(file_path, 'w') as f:
            json.dump(self.json_data, f)

    def _score_variable(self, var_data):
        type_priority = {
            "Numeric": 3,
            "Categorical": 1,
            "Text": 0,
            "Unsupported": -1
        }
        score = 0
        score += type_priority.get(var_data.get("type", "Unsupported"), -1) * 10
        score -= var_data.get("p_missing", 1) * 10
        score += var_data.get("p_distinct", 0)
        return score

    def suggest_top_graphs(self, top_n=10):
        scored_vars = []
        numeric_vars = []
        
        # First pass: collect numeric variables and score all variables
        for var_name, var_data in self.variables.items():
            var_type = var_data.get("type", "Unsupported")
            if var_type == "Numeric":
                numeric_vars.append((var_name, var_data))
            score = self._score_variable(var_data)
            scored_vars.append((score, var_name, var_data))

        # Sort variables by score
        top_vars = sorted(scored_vars, reverse=True)[:top_n]
        suggestions = []

        # Add scatterplot suggestions for highly correlated numeric variables
        if len(numeric_vars) >= 2 and self.correlations:
            for i in range(len(numeric_vars)):
                for j in range(i + 1, len(numeric_vars)):
                    var1_name, var1_data = numeric_vars[i]
                    var2_name, var2_data = numeric_vars[j]
                    
                    # Get correlation coefficient
                    corr = abs(self.correlations.get(var1_name, {}).get(var2_name, 0))
                    
                    # Only suggest scatter plot if correlation is above threshold
                    if corr >= self.correlation_threshold:
                        scatter_info = {
                            "plotly_type": "px.scatter",
                            "x": var1_name,
                            "y": var2_name,
                            "type": "Scatter",
                            "variables": [var1_name, var2_name],
                            "correlation": corr
                        }
                        suggestions.append(scatter_info)

        # Add individual variable suggestions
        for _, var_name, var_data in top_vars:
            var_type = var_data.get("type", "Unsupported")
            if var_type == "DateTime":  # Skip datetime variables
                continue
                
            graph_info = {"variable": var_name, "type": var_type}

            if var_type == "Numeric":
                graph_info["plotly_type"] = "px.histogram"
                graph_info["x"] = var_name
            elif var_type == "Categorical":
                graph_info["plotly_type"] = "px.bar"
                graph_info["x"] = list(var_data.get("value_counts_without_nan", {}).keys())
                graph_info["y"] = list(var_data.get("value_counts_without_nan", {}).values())
            elif var_type == "Text":
                graph_info["plotly_type"] = "px.bar"
                counts = var_data.get("word_counts", {})
                if len(counts) < 20:
                    graph_info["x"] = list(counts.keys())
                    graph_info["y"] = list(counts.values())
                else:
                    graph_info["plotly_type"] = "px.treemap"
                    graph_info["labels"] = list(counts.keys())
                    graph_info["values"] = list(counts.values())
            else:
                graph_info["plotly_type"] = "Unsupported"

            suggestions.append(graph_info)

        self.graph_suggestions = suggestions
        return suggestions

    def get_graph_suggestions(self):
        return self.graph_suggestions

    def suggest_graphs_from_dataframe(self, df, top_n=10):
        """Analyze DataFrame and suggest graphs based on direct analysis"""
        self.analyze_dataframe(df)
        return self.suggest_top_graphs(top_n)
