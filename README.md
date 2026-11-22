# AI Document Assistant

An AI-powered backend application for document ingestion, conversational Retrieval-Augmented Generation (RAG), and interview booking.

## Tech Stack

- **Backend:** FastAPI, Python
- **Database:** PostgreSQL, SQLAlchemy
- **Vector Database:** Qdrant
- **Cache & Chat Memory:** Redis
- **AI:** OpenAI API
- **Migrations:** Alembic
- **Containerization:** Docker Compose

## Features

- Upload PDF and TXT documents.
- Extract and chunk document content using different strategies.
- Generate embeddings and store them in Qdrant.
- Ask questions about uploaded documents using RAG.
- Maintain conversational context using Redis.
- Collect and store interview booking details.

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd ai-document-assistant
```

### 2. Create and activate a virtual environment

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root and configure the required database URLs and API keys.

### 5. Start the services

```bash
docker compose up -d
```

### 6. Run database migrations

```bash
alembic upgrade head
```

### 7. Start the application

```bash
uvicorn app.main:app --reload
```

## License

This project is developed as a learning and portfolio project.