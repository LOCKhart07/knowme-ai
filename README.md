# LangChain FastAPI Boilerplate

A modern FastAPI application with LangChain integration for building AI-powered applications.

## Features

- FastAPI web framework
- LangChain integration with OpenAI
- CORS middleware enabled
- Environment variable configuration
- Basic query endpoint

## Setup

1. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
```
Edit `.env` and add your OpenAI API key.

## Running the Application

Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /`: Welcome message
- `POST /query`: Process a query using LangChain

## API Documentation

Once the server is running, you can access:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
