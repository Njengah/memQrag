"""Tests for memQrag.ingestion.contracts (file intake, Phase 2 PR 1).

These tests only cover the intake contract: file type detection and
`RawDocument` construction. They intentionally do not test extraction,
chunking, or persistence, since none of that exists yet.
"""

import pytest

from memQrag.ingestion.contracts import (
    RawDocument,
    SupportedFileType,
    UnsupportedFileTypeError,
    detect_file_type,
    intake_document,
)


@pytest.mark.parametrize(
    ("filename", "expected_type"),
    [
        ("policy.pdf", SupportedFileType.PDF),
        ("Policy.PDF", SupportedFileType.PDF),
        ("handbook.docx", SupportedFileType.DOCX),
        ("notes.txt", SupportedFileType.TXT),
        ("readme.md", SupportedFileType.MARKDOWN),
        ("readme.markdown", SupportedFileType.MARKDOWN),
    ],
)
def test_detect_file_type_recognizes_supported_extensions(filename, expected_type):
    assert detect_file_type(filename) is expected_type


@pytest.mark.parametrize("filename", ["image.png", "archive.zip", "no-extension"])
def test_detect_file_type_rejects_unsupported_extensions(filename):
    with pytest.raises(UnsupportedFileTypeError):
        detect_file_type(filename)


def test_unsupported_file_type_error_message_lists_supported_extensions():
    with pytest.raises(UnsupportedFileTypeError) as exc_info:
        detect_file_type("data.csv")

    message = str(exc_info.value)
    assert "data.csv" in message
    for extension in ("pdf", "docx", "txt", "md", "markdown"):
        assert extension in message


def test_intake_document_returns_raw_document_for_supported_file():
    document = intake_document("policy.pdf", b"%PDF-1.4 fake content")

    assert isinstance(document, RawDocument)
    assert document.filename == "policy.pdf"
    assert document.content == b"%PDF-1.4 fake content"
    assert document.file_type is SupportedFileType.PDF


def test_intake_document_raises_for_unsupported_file_type():
    with pytest.raises(UnsupportedFileTypeError):
        intake_document("malware.exe", b"content")


def test_intake_document_raises_for_empty_content():
    with pytest.raises(ValueError, match="no content"):
        intake_document("empty.txt", b"")


def test_intake_document_raises_for_empty_filename():
    with pytest.raises(ValueError, match="filename must not be empty"):
        intake_document("   ", b"content")


def test_raw_document_is_immutable():
    document = intake_document("notes.txt", b"hello")

    with pytest.raises(AttributeError):
        document.filename = "renamed.txt"
