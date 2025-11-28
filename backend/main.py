from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

print("Starting AI Second Brain API...")

# base directory of the backend module
base_dir = os.path.dirname(os.path.abspath(__file__))

app = FastAPI(title="AI Second Brain API", version="1.0.0")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"message": "AI Second Brain API is running"}

print("Importing routes...")
try:
    from routes import ingest, search, system, advanced, analytics, chat_sessions
    
    # Register routes
    app.include_router(ingest.router, prefix="/api")
    app.include_router(search.router, prefix="/api")
    app.include_router(system.router, prefix="/api/system")
    app.include_router(advanced.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
    app.include_router(chat_sessions.router, prefix="/api")
    
    from routes import workflow
    app.include_router(workflow.router, prefix="/api")
    
    print("Routes imported and registered successfully.")
except Exception as e:
    print(f"Error importing routes: {e}")
    raise e

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount static files
app.mount("/static", StaticFiles(directory=os.path.join(base_dir, "static")), name="static")
app.mount("/assets", StaticFiles(directory=os.path.join(base_dir, "static", "assets")), name="assets")

# Mount frontend files for development
frontend_dir = os.path.join(os.path.dirname(base_dir), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/css", StaticFiles(directory=os.path.join(frontend_dir, "css")), name="css")
    app.mount("/js", StaticFiles(directory=os.path.join(frontend_dir, "js")), name="js")

@app.get("/")
async def read_index():
    # Serve development frontend directly
    frontend_index = os.path.join(os.path.dirname(base_dir), "frontend", "index.html")
    if os.path.exists(frontend_index):
        print(f"Serving frontend from: {frontend_index}")
        return FileResponse(frontend_index)
    # Fallback to built version
    static_index = os.path.join(base_dir, "static", "index.html")
    if os.path.exists(static_index):
        print(f"Serving static fallback from: {static_index}")
        return FileResponse(static_index)
    print("Frontend index not found!")
    return {"message": "Frontend not found. Please build frontend or check static files."}

if __name__ == "__main__":
    import uvicorn
    import logging
    
    # Suppress connection reset warnings
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    
    print("Starting Uvicorn server...")
    from config import SERVER_HOST, SERVER_PORT
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="info")