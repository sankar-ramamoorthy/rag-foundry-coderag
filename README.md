# rag-foundry-docgraph 🚀

**Production-Ready RAG Platform** with **Document Intelligence**: Automatic chunking, **Tesseract OCR**, LLM-powered summaries, and full provenance tracking.

## 🎯 What It Does

Transform **any document** (PDFs, images, TXT) into an intelligent knowledge base:

```
📄 Upload PDF/TXT/Image → Tesseract OCR → Auto-chunk → Embed → LLM Summary → RAG Query
                                   ↓
                       "What are the main themes?" → Instant answer + sources
```

**Key features:**
- **Tesseract OCR** - Extracts text from images/PDF scans
- **Automatic LLM summaries** stored per document
- **Full provenance** - trace every answer to exact source chunks/documents
- **Production Docker stack** - ingestion + OCR + vector store + LLM + RAG orchestrator
- **Swagger UI** - interactive API docs at `localhost:8001/docs`
- **Gradio UI** - chat interface at `localhost:7860`

## ✅ What's Working

| Feature | Status |
|---------|--------|
| **OCR Text Extraction** | ✅ Live |
| **Document Ingestion** | ✅ Live |
| **LLM Summaries** | ✅ Live |
| **RAG Retrieval** | ✅ Live |
| **Docker Multi-Service** | ✅ Live |
| **Gradio Chat UI** | ✅ Live (`localhost:7860`) |
| **Swagger API Docs** | ✅ Live (`localhost:8001/docs`) |

## 🏗️ Architecture

```
Files/Images → Ingestion Service (OCR) → Vector Store + Document Nodes → RAG Orchestrator → LLM Answers
                  ↗️ Tesseract OCR          ↗️ Document Summaries         ↗️ Provenance Tracking
```

## 💻 System Requirements

**Tested on:**
- **Processor**: Intel(R) Core(TM) i7-8565U CPU @ 1.80GHz (1.99 GHz)
- **RAM**: 8.00 GB (7.79 GB usable) 
- **OS**: Windows 11
- **Docker**: Required
- **Ollama**: Required on host at `http://host.docker.internal:11434`
- **Architecture**: CPU-only (no GPU required)

## 🚀 Quick Start

```bash
# 1. Ensure Ollama running on host (port 11434)
# 2. Build fresh Docker images  
docker compose build --no-cache

# 3. Start all services
docker compose up

# 4. Run database migrations  
docker compose exec ingestion_service uv run alembic upgrade head
```

**~5 minutes → Full RAG + OCR stack running!**

## 🎮 How to Use

### **Gradio UI (Recommended)**
```
1. Open: http://localhost:7860
2. Upload PDF/TXT/IMAGE → OCR extracts text → "Ingestion accepted" 
3. Wait ~30-60s → Status: "completed"
4. Ask: "What are the main themes?" → Instant answer + sources!
```

### **Direct API**
```bash
# Upload scanned image/PDF (OCR auto-enabled)
curl -X POST http://localhost:8001/v1/ingest/file \
  -F "file=@scanned_receipt.jpg" -F 'metadata="{}"'

# Check status
curl http://localhost:8001/v1/ingest/<ingestion_id>

# RAG query
curl -X POST http://localhost:8004/v1/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "main themes?", "top_k": 3}'
```

## 📊 Example Results

**Uploaded:** Dolomites climbing story (Marcus + Lucius)  
**OCR/Summary:** *"Marcus mentors Lucius... resilience and growth"*  
**RAG Query:** *"Dolomites story themes?"* → **Perfect retrieval + answer**

## 🔧 Tech Stack

```
🗃️ Postgres + pgvector    Vector storage + metadata
🖼️ Tesseract OCR         Image/PDF text extraction
🐳 Docker Compose         Multi-service production stack
⚡ FastAPI                All APIs
🎨 Gradio                 Chat UI
📊 Swagger/OpenAPI        Interactive docs
🤖 Ollama (CPU)           Local LLM inference
```

## 📈 Production Features

- ✅ **OCR-first** - Scanned documents work automatically
- ✅ **Document intelligence** - Auto-summaries + provenance  
- ✅ **Full traceability** - Every answer links to source chunks
- ✅ **Docker production** - No dependency hell
- ✅ **Laptop-optimized** - Runs on 8GB CPU-only systems

## 🔍 Testing Status

**✅ Extensively tested on target hardware** (i7-8565U, 8GB RAM, Windows 11)
**🔄 Ongoing validation** - Additional edge cases in progress

## 🤝 Contributing

Docs and edge-case testing welcome!

## 📄 License

MIT - Free for commercial use

***

**RAG + OCR that actually works on real hardware.** Production-ready today.


refer to 
DOCS\detailed_architecture_20260207.md