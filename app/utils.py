import asyncio
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import Any, Optional
import google.generativeai as genai
from graphiti import LLMConfig

logger = structlog.get_logger()

class GraphitiGeminiManager:
    def __init__(self, settings):
        self.settings = settings
        self._graphiti = None
        self._setup_logging()
        self._setup_gemini()
    
    def _setup_logging(self):
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    def _setup_gemini(self):
        """Configure Gemini API"""
        genai.configure(api_key=self.settings.google_api_key)
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def initialize_graphiti(self):
        """Initialize Graphiti with Gemini configuration"""
        if self._graphiti is not None:
            return self._graphiti
        
        try:
            from graphiti import Graphiti
            
            # Configure LLM for Gemini
            llm_config = LLMConfig(
                provider="gemini",
                model=self.settings.gemini_model,
                temperature=self.settings.gemini_temperature,
                max_tokens=self.settings.gemini_max_tokens,
            )
            
            # Initialize Graphiti
            self._graphiti = Graphiti(
                neo4j_uri=self.settings.neo4j_uri,
                neo4j_user=self.settings.neo4j_user,
                neo4j_password=self.settings.neo4j_password,
                llm_config=llm_config
            )
            
            # Build indices
            await self._graphiti.build_indices()
            
            logger.info("Graphiti initialized successfully with Gemini")
            return self._graphiti
            
        except Exception as e:
            logger.error(f"Failed to initialize Graphiti: {str(e)}")
            raise
    
    async def get_graphiti(self):
        """Get or create Graphiti instance"""
        if self._graphiti is None:
            await self.initialize_graphiti()
        return self._graphiti
    
    async def health_check(self) -> dict:
        """Perform health check on all services"""
        health_status = {
            "graphiti": "unknown",
            "neo4j": "unknown",
            "gemini": "unknown"
        }
        
        try:
            # Check Gemini
            model = genai.GenerativeModel(self.settings.gemini_model)
            response = await model.generate_content_async("Hello")
            health_status["gemini"] = "healthy" if response else "unhealthy"
        except Exception as e:
            logger.error(f"Gemini health check failed: {e}")
            health_status["gemini"] = "unhealthy"
        
        try:
            # Check Neo4j and Graphiti
            graphiti = await self.get_graphiti()
            # Simple query to test connection
            await graphiti.search("health_check", limit=1)
            health_status["graphiti"] = "healthy"
            health_status["neo4j"] = "healthy"
        except Exception as e:
            logger.error(f"Graphiti/Neo4j health check failed: {e}")
            health_status["graphiti"] = "unhealthy"
            health_status["neo4j"] = "unhealthy"
        
        return health_status

# Global instance
graphiti_manager: Optional[GraphitiGeminiManager] = None

def get_manager() -> GraphitiGeminiManager:
    global graphiti_manager
    if graphiti_manager is None:
        from app.config import settings
        graphiti_manager = GraphitiGeminiManager(settings)
    return graphiti_manager
