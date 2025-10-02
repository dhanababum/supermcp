import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from mcp_tools.connectors import get_all_connectors, get_connector_schema

app = FastAPI(title="MCP Tools API", description="API for MCP Tools", version="0.1.0")

# Add CORS middleware to allow requests from React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(
    prefix="/api",
)


@router.get("/")
def read_root():
    return {"message": "Hello, World!"}


@router.get("/connectors")
def get_connectors() -> list:
    return get_all_connectors()


@router.get("/connector-schema/{connector_name}")
def get_connector_schema_endpoint(connector_name: str) -> dict:
    return get_connector_schema(connector_name)


app.include_router(router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)
