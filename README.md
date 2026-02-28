---

# rag-foundry-coderag

**AI-Powered Code & Document Intelligence**
*Query code repositories and documents like a developer assistant. Extracts functions, classes, and dependencies, performs graph-aware semantic search, and answers questions using LLMs. Perfect for demonstrating AI-assisted developer productivity in portfolios.*

---

## 🚀 Overview

`rag-foundry-coderag` extends the **RAG-Foundry** framework to provide **semantic retrieval and graph-aware querying** across both **codebases** and **documents**.

It enables you to:

* Navigate code repositories and dependencies
* Search documents and PDFs semantically
* Ask natural-language questions about code structure
* Combine deterministic graph analysis with LLM-powered reasoning

This system is ideal for building intelligent developer tools, knowledge assistants, or portfolio demos showcasing AI-enhanced software engineering.

---

## 🧩 Key Features

* **Unified Ingestion**: Supports Git repositories, text files, and PDFs
* **Deterministic Artifact Graph**: AST-based extraction ensures precise structure (modules, classes, functions, calls, imports)
* **Canonical Artifact Identity**: `(repo_id, canonical_id)` for reproducible queries
* **Vector Embeddings & RAG**: Semantic search over code and documents using configurable LLM providers
* **Graph-Aware Queries**: Multi-hop traversal for analyzing function calls, dependencies, or code/document relationships

---

## 📌 Why It Matters

Traditional document RAG systems handle unstructured text well, but **code requires structure**. This project combines:

* AST parsing and canonical IDs for structural precision
* Vector embeddings for semantic similarity
* Graph traversal for relational queries

Resulting in **intelligent, context-aware answers** across both code and documentation.

---

## 🛠️ Tech Stack

| Layer               | Technology                               |
| ------------------- | ---------------------------------------- |
| API / Orchestration | Python + FastAPI                         |
| Database            | PostgreSQL (with `pgvector` for vectors) |
| Code Parsing        | AST extraction (tree-sitter or similar)  |
| Embeddings          | Pluggable (Ollama, OpenAI, etc.)         |
| Vector Operations   | HTTP Vector Store Service                |
| UI                  | Gradio Web App                           |

---

## 📄 Current Capabilities

| Content Type | Ingestion Path                | Embedding | Graph Structure |
| ------------ | ----------------------------- | --------- | --------------- |
| Python code  | AST + canonical graph build   | ✅         | ✅               |
| Text files   | Standard chunking + embedding | ✅         | (flat)          |
| PDFs         | Extract → chunk → embed       | ✅         | (flat)          |

**Canonical IDs example**:

```
path/to/file.py
path/to/file.py#ClassName
path/to/file.py#function_name
```

---

## 💡 Getting Started

1. **Clone the repository**

```bash
git clone https://github.com/sankar-ramamoorthy/rag-foundry-coderag.git
cd rag-foundry-coderag
```

2. **Start services with Docker Compose**

```bash
docker compose up --build
```

3. **Run database migrations**

```bash
alembic upgrade head
```

4. **Ingest a Git repository**

```bash
curl -X POST http://localhost:8000/v1/ingest-repo \
     -F git_url=https://github.com/your/repo.git
```

5. **Ingest a text document**

```bash
curl -X POST http://localhost:8000/v1/ingest/file \
     -F file=@my_doc.txt
```

6. **Ingest a PDF**

```bash
curl -X POST http://localhost:8000/v1/ingest/file \
     -F file=@my_file.pdf
```

---

## 🤖 Architectural Decisions (ADRs)

Key design decisions are documented in:

```
docs/adr/
```

Notable ADRs:

* **ADR-030** — Unified Artifact Graph
* **ADR-031** — Canonical Identity Model
* **ADR-045** — Repository-aware Graph + RAG Query Semantics

These ensure design rationale is traceable and reproducible.

---

## 🔍 Multi-Hop Graph Queries

The system supports **graph traversal for complex code queries**:

* BFS traversal with depth limits and directionality
* Analyze function call chains (forward/backward)
* Identify authorization flows or data dependencies
* Detect test coverage gaps
* Deterministic queries ensure reproducibility; LLM invoked only after context assembly

Traversal relies on `document_nodes` and `document_relationships` tables.

---

## 📘 Portfolio / Recruiter Takeaways

* Demonstrates **AI-assisted developer tooling**
* Shows **structured code + document reasoning**
* Highlights **deterministic and reproducible pipelines**
* Includes **graph-aware semantic search** with LLM integration
* Suitable for **AI, RAG, or software engineering portfolios**

---

## 📄 License

MIT License

---

* advanced AI-assisted code and document intelligence!* 🚀

