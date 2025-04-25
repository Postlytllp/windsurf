from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from app.api.auth import auth_router, get_current_user
from app.api.search import search_router
from app.api.chat import chat_router

app = FastAPI(title="Clinical Trials & FDA Data Search App")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(search_router, prefix="/api/search", tags=["Search"], dependencies=[Depends(get_current_user)])
app.include_router(chat_router, prefix="/api/chat", tags=["Chat"], dependencies=[Depends(get_current_user)])

# Mount static files for frontend
app.mount("/", StaticFiles(directory="app/frontend", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
