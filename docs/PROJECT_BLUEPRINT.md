# Project Blueprint

## One-Line Idea

memQrag is a production RAG system that improves answers over time by using persistent retrieval memory, explicit confidence, staleness alerts, and contradiction surfacing.

## Problem

Stateless RAG systems often retrieve the same poor sources repeatedly, hide uncertainty, and allow the language model to silently pick between conflicting documents. Teams need a RAG system that remembers what worked, shows what changed retrieval quality, and gives humans clear review signals when sources are stale or contradictory.

## First User

A technical founder, AI engineer, or internal tools team building a trustworthy document QA demo for policy-heavy knowledge bases.

## Goals

- Build a local, production-shaped RAG system with document ingestion, retrieval, memory, agent orchestration, API, and demo UI.
- Make persistent retrieval memory the clear differentiator.
- Show standard RAG and memQrag answers side by side for the same query.
- Surface confidence, citations, stale sources, and contradictions explicitly.
- Keep the architecture modular enough for future model, vector store, and reranker swaps.

## Non-Goals

- Multi-tenant hosted SaaS.
- User accounts, billing, authorization, or admin dashboards.
- Replacing human review for stale or contradictory policy content.
- Silent automated edits to source documents.
- Building unsupported file types before PDF, DOCX, TXT, and Markdown are complete.
- Optimizing for massive distributed scale before the local MVP is correct.

## MVP

The smallest useful version should let the first user:

1. start the full stack locally with one command;
2. ingest the included fictional policy documents;
3. ask questions through the demo UI;
4. compare standard RAG and memQrag answers in a split panel;
5. inspect cited chunks, confidence, memory notes, staleness alerts, and contradiction warnings;
6. understand known limitations without reading source code.

## Core Workflows

- Ingest documents: upload supported files, extract chunks and metadata, store vectors in ChromaDB, and store metadata in SQLite.
- Ask a question: classify the query, retrieve with hybrid search, apply memory boosts, rerank, answer with citations, and persist session feedback.
- Compare retrieval modes: run the same question through standard RAG and memQrag, then show both answers side by side.
- Review memory: inspect session memory and long-term memory records.
- Review risk signals: list stale frequently retrieved documents and detected contradictions.

## Trust And Safety Boundaries

- The product may store uploaded fictional or user-provided documents, extracted chunks, embeddings, metadata, query text, query embeddings, retrieval history, and usefulness feedback.
- The product must not silently transmit private documents to external services unless the configured embedding, reranking, or LLM provider requires it and the README documents that behavior.
- The product must not modify source documents automatically.
- Low-confidence answers must say they are low confidence.
- Conflicting factual claims must be shown as conflicts instead of hidden inside a synthesized answer.
- Any future use of real company data requires explicit user consent and documented storage behavior.

## Success Criteria

- `docker compose up --build` starts the API, UI, ChromaDB integration, and SQLite-backed memory store.
- The sample fictional policy set triggers at least one staleness alert and one contradiction alert during the demo walkthrough.
- A side-by-side query shows a concrete difference between standard RAG and memQrag output.
- Every answer includes source document name, chunk reference, excerpt, and confidence level.
- Tests cover semantic chunking boundaries, reciprocal rank fusion, confidence scoring, memory decay, stale document detection, contradiction flagging, and API response shapes.
