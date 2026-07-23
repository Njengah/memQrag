"""Document ingestion module boundary.

Planned responsibility, per docs/ARCHITECTURE.md: document intake, text
extraction, semantic chunking, chunk metadata assembly, and persistence
coordination into SQLite and ChromaDB.

Implemented so far (Phase 2 of docs/PRODUCT_TIMELINE.md):
- file intake contracts in `memQrag.ingestion.contracts` (`SupportedFileType`,
  `RawDocument`, `intake_document`);
- text extraction adapters in `memQrag.ingestion.extraction`
  (`extract_text`, `ExtractedDocument`, `ExtractedSegment`) for PDF, DOCX,
  TXT, and Markdown.

Semantic chunking and persistence do not exist yet.
"""
