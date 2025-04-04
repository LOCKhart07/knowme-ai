[![Docker Image CI/CD](https://github.com/LOCKhart07/knowme-ai/actions/workflows/backend-build-push-deploy.yaml/badge.svg)](https://github.com/LOCKhart07/knowme-ai/actions/workflows/backend-build-push-deploy.yaml)
# KnowMe AI

A customizable chatbot powered by Google's Gemini LLM that dynamically answers questions about a user's career, skills, and background. The system uses DatoCMS for content management and Redis for caching to provide fast, personalized responses.

## Features

- 🤖 Powered by Google's Gemini LLM
- 📝 Dynamic resume information retrieval
- 💬 Interactive chat interface
- 🔄 Redis caching for improved performance
- 📊 DatoCMS integration for content management
- 🔒 Secure API key management with automatic balancing
- 📚 Comprehensive API documentation
- 🌐 CORS enabled for cross-origin requests
- 🐳 Docker support for easy deployment
- 📈 LangSmith integration for monitoring and tracing

## Tech Stack

- **Backend Framework**: FastAPI
- **LLM**: Google Gemini
- **Content Management**: DatoCMS
- **Caching**: Redis
- **API Documentation**: OpenAPI (Swagger/ReDoc)

## Prerequisites

- Python 3.8+
- Redis server
- Google API key
- DatoCMS API token
- Docker (optional, for containerized deployment)

## Setup

1. Clone the repository:
```bash
git clone https://github.com/LOCKhart07/knowme-ai.git
cd knowme-ai
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
Create a `.env` file in the root directory with the following variables:
```env
GOOGLE_API_KEYS=your_google_api_keys  # Comma-separated list of API keys
DATOCMS_API_TOKEN=your_dato_cms_token
GEMINI_MODEL=your_gemini_model_name  # Optional, defaults to "gemini-2.0-flash-lite"

# Redis Configuration
REDIS_HOST=your_redis_host
REDIS_PORT=your_redis_port
REDIS_DB=0
REDIS_USERNAME=your_redis_username
REDIS_PASSWORD=your_redis_password

# LangSmith Configuration (Optional)
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=your_langsmith_endpoint
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=your_langsmith_project
```

## Running the Application

### Local Development
Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:7000`

### Docker Deployment
Build and run using Docker Compose:
```bash
docker-compose up --build
```

## API Endpoints

- `GET /ping`: Health check endpoint
- `POST /knowme-ai/api/chat/complete`: Process a chat query and get complete AI response
- `POST /knowme-ai/api/chat/stream`: Process a chat query and get streaming AI response chunks

## API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:7000/docs`
- ReDoc: `http://localhost:7000/redoc`

## Project Structure

```
knowme-ai/
├── app/
│   ├── models.py          # Data models and schemas
│   ├── main.py           # FastAPI application and routes
│   ├── prompts/          # LLM prompt templates
│   ├── utils/            # Utility functions and helpers
│   └── services/         # Business logic
│       ├── llm_service.py    # Gemini LLM integration
│       ├── info_service.py   # Resume info and DatoCMS service
│       ├── redis_service.py  # Redis caching service
│       └── api_key_balancer.py  # API key load balancing service
├── requirements.txt      # Python dependencies
├── docker-compose.yaml   # Docker Compose configuration
├── Dockerfile           # Docker build configuration
├── playground.ipynb     # Development and testing notebook
└── .env                 # Environment variables
```

## Dependencies

Main project dependencies:
- fastapi==0.115.12
- uvicorn==0.34.0
- redis==5.2.1
- langchain==0.3.22
- langchain-community==0.3.20
- langchain-google-genai==2.1.2
- pydantic>=2.5.2
- python-dotenv==1.0.0
- requests==2.31.0

## Features in Detail

### Resume Information
The system dynamically fetches and caches various aspects of your resume:
- Full name
- Professional summary
- Skills
- Languages
- Work experience
- Projects
- Education
- Certifications
- Contact details

### Caching
- Redis caching for improved performance
- Configurable cache expiration
- Automatic cache invalidation
- Fallback mechanisms for cache failures

### Chat Interface
- Maintains conversation history
- Context-aware responses
- Personalized information delivery
- Error handling and logging
- Streaming response support for real-time updates
- Two response modes:
  - Complete response: Get the full AI response at once
  - Streaming response: Receive response chunks in real-time for better user experience

### Development Tools
- `playground.ipynb`: Jupyter notebook for development, testing, and experimentation
- Docker support for containerized deployment
- Comprehensive API documentation

### API Key Management
- Automatic load balancing across multiple API keys
- Rate limit monitoring and management
- Fallback mechanisms for API key failures
- Configurable key rotation strategies

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
