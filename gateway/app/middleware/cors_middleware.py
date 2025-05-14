from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import CORS_ORIGINS

def setup_cors(app):
    """
    Thiết lập CORS middleware cho FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ) 