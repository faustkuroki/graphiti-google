from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class EpisodeRequest(BaseModel):
    name: str = Field(..., description="Episode name/identifier")
    episode_body: str = Field(..., description="Episode content")
    source_description: Optional[str] = Field(None, description="Source description")
    reference_time: Optional[str] = Field(None, description="Reference timestamp")

class EpisodeResponse(BaseModel):
    success: bool
    message: str
    episode_name: str

class SearchRequest(BaseModel):
    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, ge=1, le=100, description="Number of results")
    center_node_uuid: Optional[str] = Field(None, description="Center node for reranking")

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total_count: int
    query: str

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, str]
    version: str = "1.0.0"

class StatsResponse(BaseModel):
    nodes_count: int
    edges_count: int
    episodes_count: int
    graph_status: str
