# ONOW Survey Bot API

A FastAPI-based REST API for processing and analyzing survey data using natural language queries and AI-powered visualizations.

## Features

- **Natural Language Query Processing**: Convert natural language questions into SQL queries
- **AI-Powered Visualizations**: Automatically generate chart suggestions based on query results
- **Survey Data Management**: Fetch and manage survey data from external APIs
- **Real-time Processing**: Process queries and generate visualizations in real-time
- **RESTful API**: Clean, documented API endpoints

## Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key
- Survey API credentials

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ONOW-surveybot
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your actual credentials
   ```

5. **Run the application**
   ```bash
   python run.py
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## API Endpoints

### Core Endpoints

#### `GET /`
**Health check endpoint**

Returns a simple message indicating the API is running.

**Response:**
```json
{
  "message": "ONOW Survey Bot API is running"
}
```

---

### Survey Endpoints

#### `POST /api/surveybot/query`
**Process natural language queries**

Converts natural language questions into SQL queries, executes them, and generates visualization suggestions.

**Request Body:**
```json
{
  "query": "Show me all responses where people answered yes",
  "survey_id": 3200079
}
```

**Parameters:**
- `query` (string, required): Natural language question
- `survey_id` (integer, optional): Survey ID (default: 3200079)

**Response:**
```json
{
  "success": true,
  "sql_query": "SELECT * FROM survey_3200079 WHERE \"do_you_agree\" = 'yes'",
  "query_result": {
    "data": [
      {
        "contact_id": "12345",
        "name": "John Doe",
        "is_anonymous": false,
        "do_you_agree": "yes"
      }
    ],
    "columns": ["contact_id", "name", "is_anonymous", "do_you_agree"],
    "row_count": 1,
    "success": true
  },
  "visualizations": {
    "charts": [
      {
        "type": "bar",
        "title": "Responses by Agreement",
        "config": {
          "x": "do_you_agree",
          "y": "count"
        }
      }
    ],
    "total_charts": 1,
    "reasoning": "Bar chart shows distribution of agreement responses"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Processing error: Invalid query syntax",
  "sql_query": null,
  "query_result": null,
  "visualizations": null
}
```

---

#### `GET /api/surveybot/surveys/{survey_id}/data`
**Get survey data information**

Retrieves information about the survey data including database path and table name.

**Parameters:**
- `survey_id` (integer, required): Survey ID

**Response:**
```json
{
  "success": true,
  "survey_id": 3200079,
  "database_path": "survey_data.db",
  "table_name": "survey_3200079"
}
```

**Error Response:**
```json
{
  "detail": "Survey data not found"
}
```

---

#### `GET /api/surveybot/surveys/{survey_id}/questions`
**Get all questions for a specific survey**

Retrieves all question columns from the survey database schema.

**Parameters:**
- `survey_id` (integer, required): Survey ID

**Response:**
```json
{
  "success": true,
  "survey_id": 3200079,
  "questions": [
    "what_is_your_age",
    "do_you_agree",
    "how_likely_are_you_to_recommend",
    "what_is_your_favorite_color"
  ]
}
```

**Error Response:**
```json
{
  "detail": "Error fetching questions: Database connection failed"
}
```

---

#### `GET /api/surveybot/surveys/{survey_id}/summary`
**Get a summary of survey responses**

Provides comprehensive statistics about the survey including response counts and question information.

**Parameters:**
- `survey_id` (integer, required): Survey ID

**Response:**
```json
{
  "success": true,
  "survey_id": 3200079,
  "summary": {
    "total_responses": 150,
    "anonymous_responses": 45,
    "named_responses": 105,
    "total_questions": 4,
    "questions": [
      "what_is_your_age",
      "do_you_agree", 
      "how_likely_are_you_to_recommend",
      "what_is_your_favorite_color"
    ]
  }
}
```

**Error Response:**
```json
{
  "detail": "Error fetching summary: Survey not found"
}
```

---

#### `POST /api/surveybot/surveys/{survey_id}/refresh`
**Refresh survey data from the API**

Initiates a background task to fetch fresh data from the survey API.

**Parameters:**
- `survey_id` (integer, required): Survey ID

**Response:**
```json
{
  "success": true,
  "message": "Survey 3200079 data refresh initiated",
  "survey_id": 3200079
}
```

**Error Response:**
```json
{
  "detail": "Error refreshing data: API authentication failed"
}
```

**Note:** This endpoint runs the refresh in the background and returns immediately. The actual data fetching happens asynchronously.

## API Reference

### Base URL
```
http://localhost:8000
```

### Authentication
Currently, the API does not require authentication. All endpoints are publicly accessible.

### Response Format
All API responses follow a consistent JSON format:

**Success Response:**
```json
{
  "success": true,
  "data": {...},
  "message": "Optional success message"
}
```

**Error Response:**
```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes
- `200 OK` - Request successful
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Rate Limiting
The API implements rate limiting to prevent abuse and ensure fair usage:

| Endpoint | Rate Limit | Description |
|----------|------------|-------------|
| `GET /` | 30/minute | Root endpoint |
| `GET /health` | 60/minute | Health checks |
| `POST /api/surveybot/query` | 10/minute | Natural language queries (AI processing) |
| `GET /api/surveybot/surveys/{id}/data` | 30/minute | Survey data information |
| `GET /api/surveybot/surveys/{id}/questions` | 30/minute | Survey questions |
| `GET /api/surveybot/surveys/{id}/summary` | 30/minute | Survey summaries |
| `POST /api/surveybot/surveys/{id}/refresh` | 5/minute | Data refresh (API intensive) |

**Rate Limit Headers:**
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time when the rate limit resets

**Rate Limit Exceeded Response:**
```json
{
  "detail": "Rate limit exceeded: 10 per 1 minute"
}
```

## Usage Examples

### Process a Natural Language Query

```bash
curl -X POST "http://localhost:8000/api/surveybot/query" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Show me all responses where people answered yes",
       "survey_id": 3200079
     }'
```

### Get Survey Summary

```bash
curl "http://localhost:8000/api/surveybot/surveys/3200079/summary"
```

### Get Survey Questions

```bash
curl "http://localhost:8000/api/surveybot/surveys/3200079/questions"
```

### Get Survey Data Information

```bash
curl "http://localhost:8000/api/surveybot/surveys/3200079/data"
```

### Refresh Survey Data

```bash
curl -X POST "http://localhost:8000/api/surveybot/surveys/3200079/refresh"
```

### Health Check

```bash
curl "http://localhost:8000/"
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `8000` |
| `RELOAD` | Enable auto-reload | `true` |
| `DB_PATH` | Database file path | `survey_data.db` |
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `SURVEY_API_USERNAME` | Survey API username | Required |
| `SURVEY_API_PASSWORD` | Survey API password | Required |
| `DEFAULT_SURVEY_ID` | Default survey ID | `3200079` |

## Development

### Project Structure

```
ONOW-surveybot/
├── main.py              # FastAPI application entry point
├── run.py               # Development server script
├── requirements.txt     # Python dependencies
├── env.example          # Environment variables template
├── routers/             # API route definitions
│   └── survey.py        # Survey-related endpoints
├── helpers/             # Core processing modules
│   ├── fetcher.py       # Data fetching from external APIs
│   ├── processor.py     # SQL query processing
│   └── graph.py         # Visualization generation
└── survey_data.db       # SQLite database
```

### Running in Development

```bash
# With auto-reload
python run.py

# Or directly with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running in Production

```bash
# Using uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Using gunicorn (install with: pip install gunicorn)
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Docker Support

### Build and Run with Docker

```bash
# Build the image
docker build -t onow-surveybot .

# Run the container
docker run -p 8000:8000 --env-file .env onow-surveybot
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license information here] 