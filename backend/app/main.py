"""
FastAPI main application for Mutual Fund Anomaly Dashboard.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from .routes import router
from .simulator import simulate_stream, manager

# Create FastAPI app
app = FastAPI(
    title="Fund Anomaly API",
    description="Mutual Fund Anomaly Monitoring Dashboard API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Fund Anomaly Monitoring API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "funds": "/api/funds",
            "overview": "/api/overview",
            "signals": "/api/signals",
            "heatmap": "/api/heatmap",
            "websocket": "/ws/stream",
        }
    }


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket):
    """
    WebSocket endpoint for real-time data streaming.
    Simulates live NAV updates and anomaly events.
    """
    await simulate_stream(websocket)


@app.websocket("/ws/subscribe/{scheme_code}")
async def websocket_fund_stream(websocket: WebSocket, scheme_code: str):
    """
    WebSocket endpoint for subscribing to a specific fund's updates.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Wait for client messages (keepalive or unsubscribe)
            data = await websocket.receive_text()
            if data == "unsubscribe":
                break
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    print("🚀 Fund Anomaly API starting up...")
    print("📊 Data will be loaded on first request (lazy loading for fast startup)")
    print("🎯 API ready at http://localhost:8000")
    print("📖 Docs available at http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("👋 Fund Anomaly API shutting down...")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
