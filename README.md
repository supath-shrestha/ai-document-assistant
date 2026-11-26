# AI Document Assistant

An AI-powered backend application that allows users to upload documents, ask questions about their content using Retrieval-Augmented Generation (RAG), and schedule interviews through a conversational API.

## Features

- **Document Ingestion:** Upload PDF and TXT documents.
- **Text Chunking:** Supports fixed-size and recursive text chunking strategies.
- **Vector Search:** Generates embeddings and stores document vectors in Qdrant.
- **Conversational RAG:** Answers questions using retrieved document context.
- **Conversation Memory:** Maintains conversation history using Redis.
- **Interview Booking:** Collects candidate information through a conversational workflow and stores bookings in PostgreSQL.

## Tech Stack

| Category | Technologies |
|---|---|
| Backend | Python, FastAPI |
| Database | PostgreSQL, SQLAlchemy |
| Vector Database | Qdrant |
| Cache & Conversation Memory | Redis |
| LLM | Ollama, Qwen3 4B |
| Embeddings | Nomic Embed Text |
| Migrations | Alembic |
| Containerization | Docker Compose |

## Project Structure

```text
ai-document-assistant/
├── app/
│   ├── api/
│   │   └── routes/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── repositories/
│   └── main.py
├── migrations/
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.11+
- Docker and Docker Compose
- Ollama

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/supath-shrestha/ai-document-assistant.git
cd ai-document-assistant
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file using the provided example:

```powershell
Copy-Item .env.example .env
```

Update the environment variables according to your local configuration.

### 5. Start infrastructure services

```bash
docker compose up -d
```

This starts PostgreSQL, Redis, and Qdrant.

### 6. Pull Ollama models

```bash
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

Make sure the Ollama service is running.

### 7. Run database migrations

```bash
alembic upgrade head
```

### 8. Start the application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

Interactive API documentation:

```text
http://localhost:8000/docs
```

## API Modules

- **Document API:** Document upload and ingestion.
- **Chat API:** Conversational question answering using RAG.
- **Booking API:** Conversational interview booking.

Refer to the Swagger documentation at `/docs` for available endpoints and request schemas.

## Notes

- The application uses locally hosted Ollama models for chat generation and embeddings.
- PostgreSQL stores relational application data.
- Qdrant stores document embeddings for semantic retrieval.
- Redis manages conversational history and booking workflow state.
