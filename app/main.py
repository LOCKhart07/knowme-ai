from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import traceback
from .models import QueryRequest, PongResponse, QueryResponse
from .services.llm_service import LLMService

# Load environment variables
load_dotenv()

app = FastAPI(
    title="KnowMe AI",
    description="A customizable chatbot powered by an LLM that dynamically answers questions about a user's career, skills, and background. Designed for seamless integration with various data sources to generate personalized responses.",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
llm_service = LLMService()


@app.get("/ping", response_model=PongResponse)
def ping():
    return PongResponse(message="pong")


@app.post("/query", response_model=QueryResponse)
async def process_query(query_request: QueryRequest):
    try:
        response, history = await llm_service.process_query(
            query_request.query, query_request.history
        )
        return QueryResponse(response=response, history=history)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7000)
