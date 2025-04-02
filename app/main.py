from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
import logging
import traceback
from typing import Dict, Any
from .models import (
    QueryRequest,
    PongResponse,
    QueryResponse,
    StreamingResponse as StreamingResponseModel,
)
from .services.llm_service import LLMService

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create router for chat endpoints
chat_router = APIRouter(prefix="/knowme-ai/api")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        title="KnowMe AI",
        description="A customizable chatbot powered by an LLM that dynamically answers questions about a user's career, skills, and background. Designed for seamless integration with various data sources to generate personalized responses.",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://portfolio.lockhart.in",
            "https://portfolio-jenslee.netlify.app",
            "http://localhost:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()

# Initialize services
llm_service = LLMService()


@app.get("/ping", response_model=PongResponse, tags=["Health"])
async def ping() -> PongResponse:
    """
    Health check endpoint.

    Returns:
        PongResponse: Simple response to verify the service is running
    """
    return PongResponse(message="pong")


@chat_router.post("/chat/complete", response_model=QueryResponse, tags=["Chat"])
async def process_query_complete(query_request: QueryRequest) -> QueryResponse:
    """
    Process a chat query and return the complete response.

    Args:
        query_request (QueryRequest): The chat query request containing the user's message and chat history

    Returns:
        QueryResponse: The AI's response and updated chat history

    Raises:
        HTTPException: If there's an error processing the query
    """
    try:
        response, history, message_id = await llm_service.process_query(
            query_request.query, query_request.history
        )
        return QueryResponse(response=response, history=history, message_id=message_id)
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)},
        )


@chat_router.post("/chat/stream", response_model=StreamingResponseModel, tags=["Chat"])
async def process_query_stream(query_request: QueryRequest):
    """
    Process a chat query and stream the response chunks.

    Args:
        query_request (QueryRequest): The chat query request containing the user's message and chat history

    Returns:
        StreamingResponse: A stream of response chunks

    Raises:
        HTTPException: If there's an error processing the query
    """
    try:

        async def generate():
            async for chunk, message_id in llm_service.process_query_stream(
                query_request.query, query_request.history
            ):
                yield StreamingResponseModel(
                    chunk=chunk, is_final=False, message_id=message_id
                ).model_dump_json() + "\n"
            yield StreamingResponseModel(
                chunk="", is_final=True, message_id=message_id
            ).model_dump_json() + "\n"

        return StreamingResponse(
            generate(),
            media_type="application/x-ndjson",
            headers={"X-Accel-Buffering": "no"},
        )
    except Exception as e:
        logger.error(f"Error processing streaming query: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail={"error": "Internal server error", "message": str(e)},
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled exceptions.

    Args:
        request: The request that caused the exception
        exc (Exception): The unhandled exception

    Returns:
        JSONResponse: A formatted error response
    """
    logger.error(f"Unhandled exception: {str(exc)}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred",
        },
    )


# Include routers after all route definitions
app.include_router(chat_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7000, log_level="info")
