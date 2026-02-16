## 📘 **README.md** — *Updated for Codebase + Document Ingestion* 
# date 20260216

```markdown
# rag-foundry-codebase

**Status:** Active Development (Public WIP)  
**Parent Project:** rag-foundry  
**Focus:** Unified Ingestion & RAG for Codebases + Documents

---

## 🚀 What Is This?

`rag-foundry-codebase` extends the **RAG-Foundry** architecture to support *semantic retrieval* across both **codebases** and **documents**.

This system turns code repositories, text files, and PDFs into structured vectors and a canonical artifact graph suitable for:

- Semantic code search
- Cross-artifact retrieval (code ↔ docs)
- Repository navigation + dependency reasoning
- Querying code and content using LLMs

It combines a **deterministic artifact graph** with vector retrieval for powerful RAG experiences.

---

## 🧠 Why This Exists

Traditional RAG systems simply:

1. Chunk text
2. Embed it
3. Retrieve based on similarity

That works well for prose, but **code demands structure**:

- Function and method boundaries
- Import graphs and symbol paths
- Cross-module references

This project bridges that gap by combining:

- **Deterministic graph extraction** (AST & canonical IDs)
- **Vector embeddings + retrieval**
- **RAG over both code and text content**

---

## 📌 Key Highlights

### ✅ Unified Ingestion

This system now correctly ingests:

✔ Git repositories containing **Python code**  
✔ Regular **text documents**  
✔ **PDFs** (via text extraction + embedding)

Each artifact is processed *appropriately* based on type:

- Text/PDF → chunked & embedded by text content
- Code → AST-derived artifacts embedded with structural context

---

## 🧩 Core Design Principles

### 1️⃣ **Deterministic Ingestion**
- No extraneous randomness during ingestion
- Same input = same artifact identity
- AST extraction for code artifacts ensures structural precision

### 2️⃣ **Unified Artifact Identity**
Artifacts are uniquely and deterministically identified using:

```

(repo_id, canonical_id)

```

Where:
- `repo_id` is a UUID per repository ingestion
- `canonical_id` is computed from file paths and symbol names

This prevents collisions across ingestions and supports repeatable graph builds.

---

## 🧱 Architectural Overview

```

Repository/Document Sources
│
▼
AST Extraction & Text Parsing
│
Canonical Artifact Model
│
Database Persistence
│
Vector Embedding & Storage
│
RAG Queries (LLM + Retrieval)

```

This layered pipeline ensures *structural context* is preserved before embedding.

---

## ✔ Canonical Identity Format

A typical `canonical_id` looks like:

```

path/to/file.py
path/to/file.py#ClassName
path/to/file.py#function_name

````

**Artifacts are scoped by a deterministic `(repo_id, canonical_id)` identity.**  
No ephemeral UUIDs — stable identity per artifact across runs.

---

## 🛠️ Current Feature Set

✔ Git repository ingestion (Python AST extraction)  
✔ Regular document ingestion (text + PDF)  
✔ Vector embeddings via configurable provider  
✔ Vector store integration (pgvector, etc.)  
✔ Code navigation + retrieval foundations

---

## ▶ Supported Content Types

| Content Type     | Ingestion Path              | Embedding? | Graph Structure? |
|------------------|-----------------------------|------------|------------------|
| Python code      | AST + canonical graph build | ✅         | ✅               |
| Text files       | Standard chunk/embedding    | ✅         | (flat)           |
| PDFs             | Extract → chunk → embed     | ✅         | (flat)           |

---

## 💡 Getting Started

1. **Clone repository**
```bash
git clone https://github.com/sankar-ramamoorthy/rag-foundry-codebase.git
cd rag-foundry-codebase
````

2. **Start Services**

```bash
docker compose up --build
```

3. **Run Migrations**

```bash
alembic upgrade head
```

4. **Ingest a Git Repository**

```bash
curl -X POST http://localhost:8000/v1/codebase/ingest-repo \
     -F git_url=https://github.com/your/repo.git
```

5. **Ingest a Text Document**

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

## 🤖 Architectural Decision Records (ADRs)

This repository uses ADRs to document architectural choices.
Find them under:

```
docs/adr/
```

Example ADRs:

* ADR-030 — Unified Artifact Graph
* ADR-031 — Canonical Identity Model
* ADR-042 — Document ID Consistency / Vector Linking (recent) *(proposed)*

These ensure design intent is preserved and decisions are traceable.

---

## 🧬 Tech Stack

| Layer               | Technology                       |
| ------------------- | -------------------------------- |
| API / Orchestration | Python + FastAPI                 |
| Vector Storage      | PostgreSQL + pgvector            |
| Database            | PostgreSQL                       |
| Migrations          | Alembic                          |
| Code Parsing        | tree-sitter (AST extraction)     |
| Embeddings          | Pluggable (Ollama, OpenAI, etc.) |
| Vector Operations   | HTTP Vector Store Service        |

---

## 🔗 Projects & Lineage

This project builds on **rag-foundry**, an opinionated RAG framework for structured knowledge ingestion, and extends it to support *code + document ingestion* with structural context and query time semantics.

---

## 🚧 Contribution Notes

* Link every change to a GitHub issue
* Follow milestone naming in issue templates
* Add/update ADRs for significant design decisions
* Keep ingestion deterministic

---

## 📄 License

MIT License

---

*Ready for codebase + document RAG ingestion with structural intelligence!* 🚀

