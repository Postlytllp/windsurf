"""
Chat module for the Clinical Trials & FDA Data Search App.
Handles chat requests using LangGraph for LLM-powered natural language queries.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import json
from app.models.user import User
from app.api.auth import get_current_user
from app.agents.chat_agent import create_chat_agent, process_chat_query

# Initialize router
chat_router = APIRouter()

class ChatMessage(BaseModel):
    """Chat message model for history."""
    role: str
    content: str
    sources: Optional[str] = None

class ChatRequest(BaseModel):
    """Chat request model."""
    query: str
    clinical_trials_data: Optional[List[Dict[str, Any]]] = None
    fda_data: Optional[List[Dict[str, Any]]] = None
    chat_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    sources: List[Dict[str, Any]] = []

@chat_router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Process a chat query using LangGraph and LLM.
    
    Args:
        request: Chat request containing the query and data context.
        current_user: The authenticated user.
        
    Returns:
        ChatResponse: LLM response and sources.
        
    Raises:
        HTTPException: If the chat processing fails.
    """
    try:
        # Log the incoming request for debugging
        print(f"Processing chat query: {request.query}")
        print(f"Clinical trials data: {len(request.clinical_trials_data) if request.clinical_trials_data else 0} items")
        print(f"FDA data: {len(request.fda_data) if request.fda_data else 0} items")
        
        # Process the chat query
        response, sources = await process_chat_query(
            query=request.query,
            clinical_trials_data=request.clinical_trials_data,
            fda_data=request.fda_data,
            chat_history=[{"role": message.role, "content": message.content, "sources": message.sources} for message in request.chat_history]
        )
        
        # Ensure response is a string
        if not isinstance(response, str):
            response = str(response)
        
        # Ensure sources is a list of dictionaries
        if not isinstance(sources, list):
            sources = []
        
        # Log the response for debugging
        print(f"Chat response generated. Length: {len(response)}, Sources: {len(sources)}")
        
        # Create a valid response object
        chat_response = ChatResponse(
            response=response,
            sources=sources
        )
        
        return chat_response
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Chat error: {str(e)}")
        print(f"Error trace: {error_trace}")
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )
