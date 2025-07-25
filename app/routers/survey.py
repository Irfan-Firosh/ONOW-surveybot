from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
from helpers.processor import SQLProcessor
from helpers.fetcher import get_data_from_api
from slowapi import Limiter
from slowapi.util import get_remote_address

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    survey_id: Optional[int] = 3200079

class SurveyDataRequest(BaseModel):
    survey_id: int

class QueryResponse(BaseModel):
    success: bool
    sql_query: Optional[str] = None
    query_result: Optional[Dict[str, Any]] = None
    visualizations: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/query", response_model=QueryResponse)
@limiter.limit("10/minute")
async def process_query(request: Request, query_request: QueryRequest):
    """
    Process a natural language query and return SQL results with visualizations
    """
    try:
        processor = SQLProcessor(survey_id=query_request.survey_id)
        result = processor.process_query_with_visualizations(query_request.query)
        
        return QueryResponse(
            success=result["success"],
            sql_query=result.get("sql_query"),
            query_result=result.get("query_result"),
            visualizations=result.get("visualizations"),
            error=result.get("error")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@router.get("/surveys/{survey_id}/data")
@limiter.limit("30/minute")
async def get_survey_data(request: Request, survey_id: int):
    """
    Get survey data for a specific survey ID
    """
    try:
        db_path, table_name = get_data_from_api(survey_id)
        if db_path and table_name:
            return {
                "success": True,
                "survey_id": survey_id,
                "database_path": db_path,
                "table_name": table_name
            }
        else:
            raise HTTPException(status_code=404, detail="Survey data not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching survey data: {str(e)}")

@router.get("/surveys/{survey_id}/questions")
@limiter.limit("30/minute")
async def get_survey_questions(request: Request, survey_id: int):
    """
    Get all questions for a specific survey
    """
    try:
        processor = SQLProcessor(survey_id=survey_id)
        questions = processor.get_survey_questions()
        return {
            "success": True,
            "survey_id": survey_id,
            "questions": questions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching questions: {str(e)}")

@router.get("/surveys/{survey_id}/summary")
@limiter.limit("30/minute")
async def get_survey_summary(request: Request, survey_id: int):
    """
    Get a summary of survey responses
    """
    try:
        processor = SQLProcessor(survey_id=survey_id)
        summary = processor.get_survey_summary()
        return {
            "success": True,
            "survey_id": survey_id,
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching summary: {str(e)}")

@router.post("/surveys/{survey_id}/refresh")
@limiter.limit("5/minute")
async def refresh_survey_data(request: Request, survey_id: int, background_tasks: BackgroundTasks):
    """
    Refresh survey data from the API
    """
    try:
        background_tasks.add_task(get_data_from_api, survey_id)
        return {
            "success": True,
            "message": f"Survey {survey_id} data refresh initiated",
            "survey_id": survey_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing data: {str(e)}") 