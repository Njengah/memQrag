"""Shared in-memory fixture builders for ingestion tests.

Fixtures are built in-memory (a minimal hand-assembled PDF and a
python-docx document) rather than checked-in binary files, so the test
suite stays plain-text and self-contained; see docs/DECISIONS.md ("Text
Extraction Adapter Behavior"). Shared here so both the per-adapter tests
(tests/test_ingestion_extraction.py) and the end-to-end pipeline tests
(tests/test_ingestion_pipeline.py) build fixtures the same way.
"""

from datetime import datetime
from io import BytesIO

from docx import Document as DocxDocument


def build_minimal_pdf(page_texts: list[str], with_dates: bool = False) -> bytes:
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


def build_minimal_docx(
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
