"""File intake contracts for memQrag document ingestion.

Defines the supported file types and the validation contract that later
ingestion PRs (text extraction, chunking, persistence) build on. This module
intentionally contains no text extraction, chunking, or persistence logic;
see docs/PRODUCT_TIMELINE.md (Phase 2) for what each following PR adds.

File type detection is extension-based, not content-sniffing. This is a
deliberate scope choice for the intake contract; see docs/DECISIONS.md
("File Intake Contract Design").
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SupportedFileType(str, Enum):
    """File types memQrag can ingest, per docs/PROJECT_BLUEPRINT.md."""

    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MARKDOWN = "markdown"


# Maps recognized filename extensions (lowercase, without the leading dot) to
# a SupportedFileType. Both "md" and "markdown" map to MARKDOWN.
_EXTENSION_TO_FILE_TYPE: dict[str, SupportedFileType] = {
    "pdf": SupportedFileType.PDF,
    "docx": SupportedFileType.DOCX,
    "txt": SupportedFileType.TXT,
    "md": SupportedFileType.MARKDOWN,
    "markdown": SupportedFileType.MARKDOWN,
}


class UnsupportedFileTypeError(ValueError):
    """Raised when a file's extension is not one of SupportedFileType."""

    def __init__(self, filename: str) -> None:
        self.filename = filename
        supported = ", ".join(sorted(_EXTENSION_TO_FILE_TYPE))
        super().__init__(
            f"Unsupported file type for '{filename}'. Supported extensions: {supported}."
        )


@dataclass(frozen=True)
class RawDocument:
    """A validated, not-yet-extracted document accepted for ingestion.

    This is the intake contract's output: it only carries what was needed to
    prove the file is supported. Text extraction (Phase 2 PR 2) consumes
    this and produces the actual extracted content and metadata.
    """

    filename: str
    content: bytes
    file_type: SupportedFileType


def detect_file_type(filename: str) -> SupportedFileType:
    """Return the SupportedFileType matching filename's extension.

    Raises UnsupportedFileTypeError if filename has no extension or the
    extension is not one memQrag supports.
    """
    if "." not in filename:
        raise UnsupportedFileTypeError(filename)

    suffix = filename.rsplit(".", 1)[-1].lower()
    try:
        return _EXTENSION_TO_FILE_TYPE[suffix]
    except KeyError as exc:
        raise UnsupportedFileTypeError(filename) from exc


def intake_document(filename: str, content: bytes) -> RawDocument:
    """Validate and construct the intake contract for an uploaded file.

    This is the single entry point later ingestion steps consume; it
    performs no extraction, parsing, chunking, or persistence itself.
    """
    if not filename.strip():
        raise ValueError("filename must not be empty.")
    if not content:
        raise ValueError(f"'{filename}' has no content to ingest.")

    file_type = detect_file_type(filename)
    return RawDocument(filename=filename, content=content, file_type=file_type)
