examine the following plan for a voice agent demo system and let me know what you think

Voice Agent Platform – Implementation TODO
Overview
Build a multi-tenant AI voice receptionist platform with the following components:

RAG ingestion pipeline
Vector database (ChromaDB)
RAG CLI for querying/testing without the agent
YAML-configured immutable agents
FastAPI agent gateway
Conversation state machine
vLLM inference service
Tool execution (calendar + email)
Dockerized microservices
System must allow multiple businesses to run independent agents with different personalities and RAG data.
Phase 1 — Repository Setup
Create Project Structure
voice-agent-platform/

services/
    agent_gateway/
    rag_loader/
    rag_cli/
    tools/

configs/
    tenants/

rag_data/

shared/
    embeddings/
    schemas/

scripts/

docker/

Setup Python Environment
Create requirements.txt
Required packages:

fastapi
uvicorn
chromadb
sentence-transformers
pydantic
pyyaml
redis
requests
python-dotenv
google-api-python-client
ics
typer
rich

Acceptance Criteria
Project installs dependencies
Python environment works
Project structure created
Phase 2 — ChromaDB Vector Database Service
Create standalone ChromaDB server container.

Directory
docker/chromadb/

Dockerfile
FROM python:3.11

RUN pip install chromadb

CMD ["chromadb", "run", "--host", "0.0.0.0", "--port", "8001"]

Expose port:

8001

Acceptance Criteria
curl http://localhost:8001/api/v2/heartbeat

returns healthy response.
Phase 3 — Embedding Module
Create shared embedding utilities.

File
shared/embeddings/embedding_model.py

Functions
Implement:

load_embedding_model()

embed_text(text)

embed_documents(list_of_text)

Use model:

sentence-transformers/all-MiniLM-L6-v2

Acceptance Criteria
Test script:

embed_text("Hello world")

returns vector embedding.
Phase 4 — RAG Data Layout
Define tenant-based document storage.

rag_data/

    silver_pine/
        faq.md
        hours.md

    smith_law/
        faq.md
        pricing.md

Rules:

Folder name = tenant_id
Vector collection name =
{tenant_id}_docs

Acceptance Criteria
Loader detects tenants automatically.
Phase 5 — Document Chunking
Create chunking module.

File
services/rag_loader/chunker.py

Function
chunk_document(text, chunk_size=500, overlap=50)

Requirements:

Prefer paragraph splits
Fallback to token size
Maintain overlap between chunks
Return structure:

[
  {
    chunk_id,
    text,
    metadata
  }
]

Metadata must include:

tenant_id
source_file
chunk_index

Acceptance Criteria
Chunking script prints valid chunks.
Phase 6 — RAG Loader Pipeline
Create ingestion service.

File
services/rag_loader/loader.py

Responsibilities
Read tenant folder
Load documents
Convert to text
Chunk documents
Generate embeddings
Store in ChromaDB
Pseudo flow:

for tenant in rag_data:

    collection = chroma.get_or_create_collection(tenant + "_docs")

    for document in tenant_folder:

        chunks = chunk(document)

        embeddings = embed(chunks)

        collection.add(
            ids,
            embeddings,
            documents,
            metadatas
        )

CLI Command
python loader.py --tenant silver_pine

Acceptance Criteria
Vector database contains document chunks.
Phase 7 — RAG CLI Tool
Create CLI tool to interact with the vector DB without the agent.

Directory
services/rag_cli/

Use typer for CLI.
Command: List Tenants
rag_cli list

Output example:

silver_pine_docs
smith_law_docs

Command: Query Vector DB
rag_cli query --tenant silver_pine --query "What are your hours?"

Output:

Top Results:

1.
Text: "We are open Monday-Friday 9am-6pm..."
Source: hours.md
Score: 0.82

2.
Text: ...

Command: Inspect Collection
rag_cli inspect --tenant silver_pine

Shows chunk metadata.
Command: Delete Tenant Collection
rag_cli delete --tenant silver_pine

Acceptance Criteria
RAG functionality works without running the agent.
Phase 8 — YAML Agent Configuration
Agents are configured with immutable YAML files.

Directory
configs/tenants/

Example:

silver_pine.yaml

Example Config
tenant_id: silver_pine

business_profile:
  name: "Silver Pine Wellness"
  industry: "Healthcare"

personality:
  tone: "empathetic"
  pace: "calm"
  formality: "professional"

agent_behavior:
  greeting: "Thank you for calling Silver Pine Wellness. How can I help you tonight?"

  rules:
    - "Never give medical advice"
    - "Confirm caller phone number before ending call"

rag:
  collection: "silver_pine_docs"
  top_k: 5

integrations:
  calendar:
    provider: google

  email:
    provider: gmail

Phase 9 — YAML Schema Validation
Create Pydantic schemas.

File
shared/schemas/agent_config.py

Models:

AgentConfig
BusinessProfile
Personality
AgentBehavior
Integrations
RAGConfig

Requirements
Validate YAML at startup
Fail if invalid
Acceptance Criteria
Invalid config stops application.
Phase 10 — Agent Context Builder
Create runtime configuration object.

File
services/agent_gateway/context_builder.py

Purpose:
Convert YAML config → immutable runtime context.
Example:

AgentContext(
    tenant_id
    business_name
    greeting
    rules
    personality
    rag_collection
)

Acceptance Criteria
Context loads once at service startup.
Phase 11 — Conversation State Machine
Create conversation state system.

File
services/agent_gateway/state_machine.py

Define stages:

GREETING
INTENT_DETECTION
ANSWER_QUESTION
COLLECT_NAME
COLLECT_PHONE
COLLECT_TIME
CONFIRM_DETAILS
BOOK_CALLBACK
END

Session state structure:

SessionState
    session_id
    stage
    name
    phone
    requested_time
    history

Store session state in:

Redis

Acceptance Criteria
State persists between conversation turns.
Phase 12 — RAG Retrieval Service
Create module:

services/agent_gateway/rag_service.py

Function:

retrieve_context(query, tenant_id, top_k=5)

Steps:

Embed query
Query ChromaDB
Return top results
Acceptance Criteria
Returns relevant business context.
Phase 13 — Prompt Builder
Create structured prompt builder.

File
services/agent_gateway/prompt_builder.py

Inputs:

AgentContext
SessionState
RAG results
User transcript

Output:

LLM messages JSON

Structure:

system instructions
rules
rag context
conversation history
user message

Acceptance Criteria
Prompt generation deterministic.
Phase 14 — vLLM Client
Create client module.

File
services/agent_gateway/llm_client.py

Call endpoint:

POST /v1/chat/completions

Support:

streaming responses

Acceptance Criteria
Test script generates LLM completion.
Phase 15 — Tool Execution Layer
Create tools for agent actions.

Directory
services/tools/

Tools:

schedule_callback
Creates calendar event.

send_confirmation_email
Sends Gmail email with ICS attachment.
Modules:

calendar_tool.py
email_tool.py

Acceptance Criteria
Standalone tests succeed.
Phase 16 — FastAPI Agent Gateway
Create main service.

File
services/agent_gateway/main.py

Endpoints:

POST /call/start
POST /call/turn
POST /call/end

Call flow:

receive transcript
load session state
run state machine
retrieve rag context
build prompt
call vllm
update state
return response

Acceptance Criteria
Agent responds to simulated conversations.
Phase 17 — Docker Compose
Create orchestration.

File
docker/docker-compose.yml

Services:

agent_gateway
chromadb
vllm
redis

GPU assignment:

vllm → 3080ti
chromadb → 980ti

Acceptance Criteria
docker compose up

starts system.
Phase 18 — Local Agent Testing Script
Create script to simulate calls.

scripts/test_agent.py

Example interaction:

user: what are your hours
agent: ...

user: can someone call me tomorrow
agent: ...

Acceptance Criteria
Agent works without VAPI.
Phase 19 — VAPI Integration
Configure webhook endpoint.
VAPI sends transcript to:

POST /call/turn

Agent returns text response.
VAPI handles:

TTS
audio playback

Acceptance Criteria
Phone call successfully interacts with agent.
Final System Requirements
The finished system must support:

Multi-tenant RAG
YAML configured agents
Independent vector DB testing
Conversation state machine
Callback scheduling
Gmail confirmation emails with iCal
Dockerized microservices
GPU accelerated vLLM inference
If you'd like, I can also generate a much stronger RAG ingestion system next (about 3× more capable) that adds:

website crawling
pdf parsing
google docs ingestion
automatic re-indexing
which makes onboarding real businesses dramatically easier.
yes we need pdf parsing
Perfect — we can extend your RAG ingestion pipeline to handle PDFs (and eventually other document types) while keeping the multi-tenant structure intact. Below is a detailed plan for updating your RAG tooling with PDF parsing, chunking, and embedding.
PDF Parsing for Multi-Tenant RAG
1. Dependencies
Add the following packages:


pip install pdfplumber PyMuPDF

pdfplumber → reliable text extraction from structured PDFs (tables, multi-column)
PyMuPDF / fitz → faster, lower-level extraction if needed
Optional: tika if you want highly robust but heavier parsing.
2. Update Document Loader
Create a generic load_document(path) function in your loader:


from pathlib import Path
import pdfplumber

def load_document(path: Path) -> str:
    if path.suffix.lower() in [".md", ".txt"]:
        return path.read_text(encoding="utf-8")
    elif path.suffix.lower() == ".pdf":
        return load_pdf(path)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")

def load_pdf(path: Path) -> str:
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

Notes:
Extracts all pages
Preserves paragraph separation
Returns a single string for chunking
3. Update Chunker
Your existing chunker works on text. No change needed, but you may want page-aware metadata:


def chunk_document(text, chunk_size=500, overlap=50, tenant_id=None, source_file=None):
    # Split text into chunks (paragraph-aware)
    chunks = []
    paragraphs = text.split("\n\n")
    current_chunk = ""
    chunk_index = 0

    for para in paragraphs:
        if len(current_chunk) + len(para) > chunk_size:
            chunks.append({
                "chunk_id": f"{source_file}_{chunk_index}",
                "text": current_chunk.strip(),
                "metadata": {
                    "tenant_id": tenant_id,
                    "source_file": source_file,
                    "chunk_index": chunk_index,
                }
            })
            chunk_index += 1
            current_chunk = para + "\n\n"
        else:
            current_chunk += para + "\n\n"

    if current_chunk.strip():
        chunks.append({
            "chunk_id": f"{source_file}_{chunk_index}",
            "text": current_chunk.strip(),
            "metadata": {
                "tenant_id": tenant_id,
                "source_file": source_file,
                "chunk_index": chunk_index,
            }
        })

    return chunks

4. Multi-Tenant Loader
Update your loader script to support PDFs:


from pathlib import Path

tenant_folder = Path(f"rag_data/{tenant_id}")

for file in tenant_folder.glob("*"):
    text = load_document(file)
    chunks = chunk_document(
        text,
        chunk_size=500,
        overlap=50,
        tenant_id=tenant_id,
        source_file=file.name
    )
    embeddings = embed_documents([c["text"] for c in chunks])
    collection.add(
        ids=[c["chunk_id"] for c in chunks],
        embeddings=embeddings,
        documents=[c["text"] for c in chunks],
        metadatas=[c["metadata"] for c in chunks]
    )

Acceptance Criteria:
Loader works for .md, .txt, and .pdf
Each PDF page is chunked properly
Metadata includes tenant_id and source_file
Chroma collection is populated
5. CLI Testing
Add CLI commands for testing PDF ingestion:


rag_cli ingest --tenant silver_pine
rag_cli query --tenant silver_pine --query "What are your business hours?"

PDF content should appear in top results.
Verify chunks contain source_file = hours.pdf or whatever PDF was used.
6. Optional Enhancements
Table-aware extraction: If your PDFs contain tables (pricing, schedules), pdfplumber lets you extract tables as JSON.
OCR for scanned PDFs: Integrate pytesseract if PDFs are scanned images.
Automatic re-indexing: Watch tenant folders and trigger ingestion when a new PDF is added.
Document type tagging: Store "type": "pdf" in metadata for downstream agent reasoning.
7. Updated RAG Pipeline Flow
Tenant folder (rag_data/<tenant_id>)
   ├── faq.md
   ├── hours.pdf
   └── services.md

   ↓ load_document (detect type, parse)
   ↓ chunk_document (500 token chunks, overlap 50)
   ↓ embed_documents (sentence-transformers)
   ↓ chroma.add (ids, embeddings, documents, metadatas)

This allows querying PDFs directly without involving the agent.
