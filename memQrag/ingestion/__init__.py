"""Document ingestion module boundary.

Planned responsibility, per docs/ARCHITECTURE.md: document intake, text
extraction, semantic chunking, chunk metadata assembly, and persistence
coordination into SQLite and ChromaDB.

Implemented so far (Phase 2 of docs/PRODUCT_TIMELINE.md):
- file intake contracts in `memQrag.ingestion.contracts` (`SupportedFileType`,
  `RawDocument`, `intake_document`);
- text extraction adapters in `memQrag.ingestion.extraction`
  (`extract_text`, `ExtractedDocument`, `ExtractedSegment`) for PDF, DOCX,
  TXT, and Markdown;
- semantic chunking in `memQrag.ingestion.chunking` (`chunk_document`,
  `Chunk`), backed by sentence embeddings from
  `memQrag.ingestion.embeddings.embed_sentences`;
- SQLite persistence in `memQrag.ingestion.storage` (`persist_ingested_document`,
  `get_document_by_filename`, `get_chunks_for_document`) for document and
  chunk metadata.

Persistence into ChromaDB does not exist yet.
"""
