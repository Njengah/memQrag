"""Tests for memQrag.ingestion.extraction (text extraction, Phase 2 PR 2).

Fixtures are built in-memory (a minimal hand-assembled PDF and a python-docx
document) rather than checked-in binary files, so the test suite stays
plain-text and self-contained.
"""

from datetime import datetime, timezone
from io import BytesIO

from docx import Document as DocxDocument

from memQrag.ingestion.contracts import intake_document
from memQrag.ingestion.extraction import extract_text


def _build_minimal_pdf(page_texts: list[str], with_dates: bool = False) -> bytes:
    """Assemble a minimal, valid single- or multi-page PDF with real text.

    Byte offsets are computed dynamically so this stays correct regardless of
    object body lengths.
    """
    object_count = 3 + 2 * len(page_texts)  # catalog, pages, font, then per-page content+page
    page_object_ids = [4 + 2 * i for i in range(len(page_texts))]
    content_object_ids = [5 + 2 * i for i in range(len(page_texts))]

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids ["
        + " ".join(f"{page_id} 0 R" for page_id in page_object_ids).encode("ascii")
        + b"] /Count "
        + str(len(page_texts)).encode("ascii")
        + b" >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    for page_id, content_id, text in zip(page_object_ids, content_object_ids, page_texts):
        objects.append(
            b"<< /Type /Page /Parent 2 0 R /Resources << /Font << /F1 3 0 R >> >> "
            b"/MediaBox [0 0 612 792] /Contents " + str(content_id).encode("ascii") + b" 0 R >>"
        )
        content_stream = f"BT /F1 24 Tf 20 700 Td ({text}) Tj ET".encode("latin-1")
        objects.append(
            b"<< /Length "
            + str(len(content_stream)).encode("ascii")
            + b" >>\nstream\n"
            + content_stream
            + b"\nendstream"
        )

    info_object_id = None
    if with_dates:
        info_object_id = object_count + 1
        objects.append(
            b"<< /CreationDate (D:20240102030405+00'00') /ModDate (D:20240506070809+00'00') >>"
        )

    buffer = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(len(buffer))
        buffer += f"{index} 0 obj\n".encode("ascii") + body + b"\nendobj\n"

    xref_offset = len(buffer)
    total_objects = len(objects) + 1
    buffer += f"xref\n0 {total_objects}\n".encode("ascii")
    buffer += b"0000000000 65535 f \n"
    for offset in offsets[1:]:
        buffer += f"{offset:010d} 00000 n \n".encode("ascii")

    info_ref = f" /Info {info_object_id} 0 R" if info_object_id else ""
    buffer += (
        f"trailer\n<< /Size {total_objects} /Root 1 0 R{info_ref} >>\n"
        f"startxref\n{xref_offset}\n%%EOF"
    ).encode("ascii")

    return bytes(buffer)


def _build_minimal_docx(
    paragraphs: list[tuple[str, str | None]],
    created: datetime | None = None,
    modified: datetime | None = None,
) -> bytes:
    document = DocxDocument()
    for text, style in paragraphs:
        document.add_paragraph(text, style=style)
    if created is not None:
        document.core_properties.created = created
    if modified is not None:
        document.core_properties.modified = modified

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


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
