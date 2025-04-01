# KnowMe AI

A customizable chatbot powered by Google's Gemini LLM that dynamically answers questions about a user's career, skills, and background. The system uses DatoCMS for content management and Redis for caching to provide fast, personalized responses.

## Features

- 🤖 Powered by Google's Gemini LLM
- 📝 Dynamic resume information retrieval
- 💬 Interactive chat interface
- 🔄 Redis caching for improved performance
- 📊 DatoCMS integration for content management
- 🔒 Secure API key management
- 📚 Comprehensive API documentation
- 🌐 CORS enabled for cross-origin requests

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

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
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
GOOGLE_API_KEY=your_google_api_key
DATOCMS_API_TOKEN=your_dato_cms_token

# Redis Configuration
REDIS_HOST=your_redis_host
REDIS_PORT=your_redis_port
REDIS_DB=0
REDIS_USERNAME=your_redis_username
REDIS_PASSWORD=your_redis_password
```

## Running the Application

Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /ping`: Health check endpoint
- `POST /chat`: Process a chat query and get AI response

## API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
knowme-ai/
├── app/
│   ├── models.py          # Data models
│   ├── main.py           # FastAPI application
│   ├── prompts/          # LLM prompts
│   └── services/         # Business logic
│       ├── llm_service.py    # LLM integration
│       ├── info_service.py   # Resume info service
│       └── redis_service.py  # Redis caching
├── requirements.txt      # Python dependencies
└── .env                 # Environment variables
```

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

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
