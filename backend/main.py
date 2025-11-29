from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import sys

print("Starting LivingOS AI...")

# base directory of the backend module
base_dir = os.path.dirname(os.path.abspath(__file__))

# Ensure backend directory is in sys.path for imports
if base_dir not in sys.path:
    sys.path.append(base_dir)

app = FastAPI(title="LivingOS AI API", version="1.0.0")

# CORS Setup - Production ready
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    status = {"message": "LivingOS AI is running", "services": {}}
    
    # Check Qdrant connection
    try:
        from database import qdrant_manager
        health_check = qdrant_manager.health_check()
        status["services"]["qdrant"] = health_check["status"]
    except Exception as e:
        status["services"]["qdrant"] = "unavailable"
    
    # Check R2 storage
    try:
        from r2_storage import r2_storage
        status["services"]["r2_storage"] = "enabled" if r2_storage.enabled else "disabled"
    except Exception as e:
        status["services"]["r2_storage"] = "unavailable"
    
    # Check AI clients
    try:
        from groq_client import groq_client
        status["services"]["groq"] = "enabled" if groq_client.client else "disabled"
    except Exception as e:
        status["services"]["groq"] = "unavailable"
    
    return status

print("Importing routes...")
try:
    from routes import ingest, system, chat_sessions, workflow, smart_notes
    
    # Register essential routes only
    app.include_router(ingest.router, prefix="/api")
    app.include_router(system.router, prefix="/api/system")
    app.include_router(chat_sessions.router, prefix="/api")
    app.include_router(workflow.router, prefix="/api")
    app.include_router(smart_notes.router, prefix="/api")
    
    print("Routes imported and registered successfully.")
except Exception as e:
    print(f"Error importing routes: {e}")
    print("Server will start with limited functionality")
    # Add basic health check even if routes fail
    @app.get("/api/status")
    async def status():
        return {"status": "limited", "message": "Some features may be unavailable"} 

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")

# Mount frontend files
frontend_dir = os.path.join(os.path.dirname(base_dir), "frontend")
if os.path.exists(frontend_dir):
    js_dir = os.path.join(frontend_dir, "js")
    css_dir = os.path.join(frontend_dir, "css")
    assets_dir = os.path.join(frontend_dir, "assets")
    
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

@app.get("/")
async def read_index():
    os_layout = os.path.join(os.path.dirname(base_dir), "frontend", "os_layout.html")
    if os.path.exists(os_layout):
        return FileResponse(os_layout)
    return {"message": "LivingOS AI Frontend not found"}

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # Suppress connection reset warnings
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    
    print("Starting Uvicorn server...")
    from config import SERVER_HOST, SERVER_PORT
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="info", access_log=False)