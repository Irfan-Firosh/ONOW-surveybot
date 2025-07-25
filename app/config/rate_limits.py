"""
Rate limiting configuration for the ONOW Survey Bot API
"""

# Rate limits for different endpoints
RATE_LIMITS = {
    # Core endpoints
    "root": "30/minute",
    "health": "60/minute",
    
    # Survey endpoints
    "query": "10/minute",  # More restrictive due to AI processing
    "survey_data": "30/minute",
    "survey_questions": "30/minute", 
    "survey_summary": "30/minute",
    "survey_refresh": "5/minute",  # Very restrictive due to API calls
}

# Rate limit descriptions
RATE_LIMIT_DESCRIPTIONS = {
    "root": "30 requests per minute for the root endpoint",
    "health": "60 requests per minute for health checks",
    "query": "10 requests per minute for natural language queries (AI processing)",
    "survey_data": "30 requests per minute for survey data information",
    "survey_questions": "30 requests per minute for survey questions",
    "survey_summary": "30 requests per minute for survey summaries",
    "survey_refresh": "5 requests per minute for data refresh (API intensive)",
}

def get_rate_limit(endpoint_name: str) -> str:
    """Get rate limit for a specific endpoint"""
    return RATE_LIMITS.get(endpoint_name, "30/minute")

def get_rate_limit_description(endpoint_name: str) -> str:
    """Get rate limit description for a specific endpoint"""
    return RATE_LIMIT_DESCRIPTIONS.get(endpoint_name, "30 requests per minute")