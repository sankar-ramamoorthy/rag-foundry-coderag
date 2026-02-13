## README.md
---

# rag-foundry-codebase

**Status:** 🚧 Active Development (Public WIP)
**Parent Lineage:** rag-foundry
**Focus:** Deterministic Codebase Knowledge Graph + RAG

---

## What Is This?

`rag-foundry-codebase` extends the RAG-Foundry architecture to support **codebase intelligence** using a **Unified Artifact Graph**.

This project turns a repository into a structured, deterministic knowledge graph that can power:

* Code navigation
* Dependency tracing
* Impact analysis
* Test coverage reasoning
* Multi-hop structural queries
* Retrieval-Augmented Generation (RAG) over code + documents

This is not just semantic search.

It is a structural + semantic system.

---

## Why This Exists

Traditional RAG systems:

* Chunk text
* Embed it
* Retrieve semantically similar content

That works for documents.

It does not work well for:

* Function call tracing
* Import resolution
* Class hierarchies
* Cross-module dependencies
* Test coverage gaps

This project introduces:

> A deterministic graph layer built from static analysis
> Combined with vector retrieval
> With LLM reasoning only at query time

---

## Core Design Principles

### 1. Deterministic Ingestion

* No LLM usage during ingestion
* AST-based extraction (Python first)
* Same input → same graph
* Rebuild-safe

---

### 2. Unified Artifact Graph

All artifacts are stored in the same graph model:

* Documents
* Python modules
* Classes
* Functions
* Methods
* Tests
* ADRs

No separate graph engines.
No parallel schema divergence.

---

### 3. Canonical Identity Model

Artifacts are identified by:

```
(repo_id, canonical_id)
```

Canonical ID format:

```
<relative_path>#<symbol_path>
```

Examples:

```
payments/stripe.py
payments/stripe.py#StripeClient
payments/stripe.py#StripeClient.charge
```

No UUID-based identity.
No ingestion-order dependency.

---

### 4. Repository Isolation

Artifacts are scoped by:

```
repo_id (UUID)
```

This enables indexing multiple repositories without identity collision.

---

### 5. Query-Time Semantics Only

Meaning is applied at query time.

The ingestion layer stores:

* Structure
* Relationships
* Provenance

LLMs are used only to assemble answers.

---

## Current Status

This repository is in active architectural development.

Completed:

* ADR-030: Unified Artifact Graph
* ADR-031: Canonical Identity Model
* Schema design for artifact_type + repo_id
* Milestone planning

In Progress:

* Python AST extractor
* Repository graph builder
* Deterministic identity utilities

Planned:

* Graph persistence layer
* Codebase ingestion API
* Multi-hop traversal queries
* RAG integration

---

## Milestones

The project is structured into 5–6 milestones with 4–6 issues per milestone.

Example milestone flow:

1. Schema & Architectural Foundation
2. Python AST Extraction
3. Repo Graph Builder
4. Persistence & Ingestion API
5. Multi-hop Queries
6. RAG Integration

All development is tracked via structured issue naming:

```
MS1-IS1-<description>
MS1-IS2-<description>
MS2-IS1-<description>
```

---

## Architecture Overview

High-level flow:

```
Repository
    ↓
AST Extraction (deterministic)
    ↓
Symbol Resolution
    ↓
Unified Artifact Graph
    ↓
Graph + Vector Retrieval
    ↓
LLM (query-time only)
```

---

## Tech Stack

* Python 3.10+
* FastAPI
* PostgreSQL
* pgvector
* Alembic (raw SQL migrations)
* tree-sitter (Python AST parsing)

---

## Development Setup

Clone the repository:

```bash
git clone https://github.com/sankar-ramamoorthy/rag-foundry-codebase.git
cd rag-foundry-codebase
```

Start services:

```bash
docker compose up --build
```

Run migrations:

```bash
alembic upgrade head
```

Test AST extraction:

```bash
python scripts/test_ast_extraction.py path/to/sample_repo
```

---

## Architectural Decision Records (ADRs)

This project uses ADRs to preserve architectural intent.

Location:

```
docs/adr/
```

Current ADRs:

* ADR-030 — Unified Artifact Graph
* ADR-031 — Canonical Identity Model

More will follow as the system evolves.

---

## Important Notes

* This repository is public.
* This is an evolving architecture.
* APIs may change during early milestones.
* Stability guarantees will be defined post-MVP.

---

## Long-Term Vision

The goal is to build:

* Deterministic code intelligence
* Multi-artifact reasoning
* Explainable RAG systems
* Cross-repository knowledge graphs

This project explores how far a unified artifact graph can go before needing specialized graph infrastructure.

If that boundary is reached, the learning itself becomes the product.

---

## Contributing

Contributions are welcome.

Please:

* Link every change to an issue
* Follow milestone structure
* Add or update ADRs when architectural decisions are made
* Keep ingestion deterministic

---

## License

MIT

---
