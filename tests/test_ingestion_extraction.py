"""Tests for memQrag.ingestion.extraction (text extraction, Phase 2 PR 2).

Fixtures are built in-memory (a minimal hand-assembled PDF and a python-docx
document, via tests/fixtures.py) rather than checked-in binary files, so the
test suite stays plain-text and self-contained.
"""

from datetime import datetime, timezone

from fixtures import build_minimal_docx as _build_minimal_docx
from fixtures import build_minimal_pdf as _build_minimal_pdf

from memQrag.ingestion.contracts import intake_document
from memQrag.ingestion.extraction import extract_text


def test_extract_txt_returns_single_segment_with_no_structural_metadata():
    document = intake_document("notes.txt", "Line one.\nLine two.".encode())

    extracted = extract_text(document)

    assert extracted.source_document == "notes.txt"
    assert extracted.created_date is None
    assert extracted.last_modified_date is None
    assert len(extracted.segments) == 1
    assert extracted.segments[0].text == "Line one.\nLine two."
    assert extracted.segments[0].page_number is None
    assert extracted.segments[0].section_heading is None


def test_extract_txt_skips_blank_content_after_stripping():
    document = intake_document("blank.txt", b"   \n  ")

    extracted = extract_text(document)

    assert extracted.segments == []


def test_extract_markdown_splits_on_atx_headings():
    markdown = (
        "Intro paragraph before any heading.\n\n"
        "# First Section\n"
        "Body of first section.\n\n"
        "## Nested Section\n"
        "Body of nested section.\n"
    )
    document = intake_document("guide.md", markdown.encode())

    extracted = extract_text(document)

    assert [segment.section_heading for segment in extracted.segments] == [
        None,
        "First Section",
        "Nested Section",
    ]
    assert "Intro paragraph" in extracted.segments[0].text
    assert "Body of first section." in extracted.segments[1].text
    assert "Body of nested section." in extracted.segments[2].text
    assert all(segment.page_number is None for segment in extracted.segments)


def test_extract_markdown_alias_extension_uses_same_adapter():
    document = intake_document("guide.markdown", b"# Heading\nBody text.")

    extracted = extract_text(document)

    assert extracted.segments[0].section_heading == "Heading"


def test_extract_docx_groups_paragraphs_by_heading_style():
    docx_bytes = _build_minimal_docx(
        [
            ("Untitled intro.", None),
            ("Overview", "Heading 1"),
            ("Overview body text.", None),
            ("Details", "Heading 2"),
            ("Details body text.", None),
        ]
    )
    document = intake_document("handbook.docx", docx_bytes)

    extracted = extract_text(document)

    assert [segment.section_heading for segment in extracted.segments] == [
        None,
        "Overview",
        "Details",
    ]
    assert extracted.segments[0].text == "Untitled intro."
    assert extracted.segments[1].text == "Overview body text."
    assert extracted.segments[2].text == "Details body text."
    assert all(segment.page_number is None for segment in extracted.segments)


def test_extract_docx_captures_core_property_dates():
    created = datetime(2023, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
    modified = datetime(2023, 6, 15, 14, 30, 0, tzinfo=timezone.utc)
    docx_bytes = _build_minimal_docx([("Body text.", None)], created=created, modified=modified)
    document = intake_document("policy.docx", docx_bytes)

    extracted = extract_text(document)

    assert extracted.created_date == created
    assert extracted.last_modified_date == modified


def test_extract_pdf_returns_one_segment_per_page():
    pdf_bytes = _build_minimal_pdf(["Page one text", "Page two text"])
    document = intake_document("report.pdf", pdf_bytes)

    extracted = extract_text(document)

    assert [segment.page_number for segment in extracted.segments] == [1, 2]
    assert "Page one text" in extracted.segments[0].text
    assert "Page two text" in extracted.segments[1].text
    assert all(segment.section_heading is None for segment in extracted.segments)


def test_extract_pdf_without_info_dictionary_has_no_dates():
    pdf_bytes = _build_minimal_pdf(["Only page"], with_dates=False)
    document = intake_document("undated.pdf", pdf_bytes)

    extracted = extract_text(document)

    assert extracted.created_date is None
    assert extracted.last_modified_date is None


def test_extract_pdf_captures_info_dictionary_dates():
    pdf_bytes = _build_minimal_pdf(["Only page"], with_dates=True)
    document = intake_document("dated.pdf", pdf_bytes)

    extracted = extract_text(document)

    assert extracted.created_date is not None
    assert extracted.created_date.year == 2024
    assert extracted.created_date.month == 1
    assert extracted.last_modified_date is not None
    assert extracted.last_modified_date.month == 5
