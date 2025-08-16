from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import structlog
from contextlib import asynccontextmanager

from app.config import settings
from app.models import (
    EpisodeRequest, EpisodeResponse, 
    SearchRequest, SearchResponse,
    HealthResponse, StatsResponse
)
from app.utils import get_manager

logger = structlog.get_logger()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    try:
        # Startup
        logger.info("Starting Graphiti-Gemini application...")
        manager = get_manager()
        await manager.initialize_graphiti()
        logger.info("Application started successfully")
        yield
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down application...")

# Initialize FastAPI app
app = FastAPI(
    title="Graphiti with Gemini API",
    description="Knowledge graph API using Graphiti with Google Gemini LLM",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    try:
        manager = get_manager()
        services_status = await manager.health_check()
        
        overall_status = "healthy" if all(
            status == "healthy" for status in services_status.values()
        ) else "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            services=services_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")

@app.post("/episodes", response_model=EpisodeResponse)
async def add_episode(episode: EpisodeRequest):
    """Add a new episode to the knowledge graph"""
    try:
        manager = get_manager()
        graphiti = await manager.get_graphiti()
        
        await graphiti.add_episode(
            name=episode.name,
            episode_body=episode.episode_body,
            source_description=episode.source_description,
            reference_time=episode.reference_time
        )
        
        logger.info(f"Episode '{episode.name}' added successfully")
        
        return EpisodeResponse(
            success=True,
            message="Episode added successfully",
            episode_name=episode.name
        )
        
    except Exception as e:
        logger.error(f"Failed to add episode: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to add episode: {str(e)}"
        )

@app.post("/search", response_model=SearchResponse)
async def search_graph(search: SearchRequest):
    """Search the knowledge graph"""
    try:
        manager = get_manager()
        graphiti = await manager.get_graphiti()
        
        # Perform search
        if search.center_node_uuid:
            results = await graphiti.search(
                query=search.query,
                center_node_uuid=search.center_node_uuid,
                limit=search.limit
            )
        else:
            results = await graphiti.search(
                query=search.query,
                limit=search.limit
            )
        
        # Convert results to serializable format
        serializable_results = []
        for result in results:
            if hasattr(result, 'to_dict'):
                serializable_results.append(result.to_dict())
            else:
                serializable_results.append(str(result))
        
        logger.info(f"Search completed: {len(results)} results for query '{search.query}'")
        
        return SearchResponse(
            results=serializable_results,
            total_count=len(results),
            query=search.query
        )
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@app.get("/stats", response_model=StatsResponse)
async def get_graph_stats():
    """Get knowledge graph statistics"""
    try:
        manager = get_manager()
        graphiti = await manager.get_graphiti()
        
        # Get basic statistics (implement based on Graphiti's available methods)
        # This is a placeholder - adjust based on actual Graphiti API
        stats = {
            "nodes_count": 0,
            "edges_count": 0,
            "episodes_count": 0,
            "graph_status": "active"
        }
        
        return StatsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get statistics: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Graphiti with Gemini API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "add_episode": "/episodes",
            "search": "/search",
            "stats": "/stats"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.app_host,
        port=settings.app_port,
        log_config=None  # Use structlog instead
    )
