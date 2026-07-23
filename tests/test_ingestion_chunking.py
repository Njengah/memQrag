"""Tests for memQrag.ingestion.chunking (semantic chunking, Phase 2 PR 3).

Uses a small deterministic fake embedding function instead of the real
fastembed-backed embedder, so these tests are fast and network-free; see
docs/DECISIONS.md ("Semantic Chunking Algorithm").
"""

from memQrag.ingestion.chunking import (
    MAX_CHUNK_TOKENS,
    MIN_CHUNK_TOKENS,
    Chunk,
    chunk_document,
    estimate_token_count,
    split_sentences,
)
from memQrag.ingestion.contracts import SupportedFileType
from memQrag.ingestion.extraction import ExtractedDocument, ExtractedSegment


def _topic_embed(sentences):
    """Return a one-hot-ish vector per sentence based on keyword topic.

    Sentences sharing a topic keyword get identical vectors (cosine
    similarity 1.0); sentences with different topics are orthogonal
    (similarity 0.0). This makes semantic grouping fully predictable.
    """
    vectors = []
    for sentence in sentences:
        lower = sentence.lower()
        vectors.append(
            [
                1.0 if "cat" in lower else 0.0,
                1.0 if "car" in lower else 0.0,
                1.0 if "moon" in lower else 0.0,
            ]
        )
    return vectors


def _document(segments: list[ExtractedSegment]) -> ExtractedDocument:
    return ExtractedDocument(
        source_document="fixture.txt",
        file_type=SupportedFileType.TXT,
        created_date=None,
        last_modified_date=None,
        segments=segments,
    )


def _words(word: str, count: int) -> str:
    """Build a single "sentence" of `count` repetitions of `word`.

    Capitalized so the punctuation-based sentence splitter recognizes the
    following text (if any) as a new sentence, matching real prose where
    sentences start with a capital letter.
    """
    words = [word.capitalize()] + [word] * (count - 1)
    return " ".join(words) + "."


def test_estimate_token_count_counts_whitespace_separated_words():
    assert estimate_token_count("one two three") == 3
    assert estimate_token_count("") == 0


def test_split_sentences_splits_on_terminal_punctuation():
    text = "Hello world. This is great! Are you sure? Yes."
    assert split_sentences(text) == [
        "Hello world.",
        "This is great!",
        "Are you sure?",
        "Yes.",
    ]


def test_split_sentences_returns_empty_list_for_blank_text():
    assert split_sentences("   \n  ") == []


def test_chunk_document_groups_sentences_by_semantic_similarity():
    # Each sentence is well over MIN_CHUNK_TOKENS on its own so the
    # merge/split passes are no-ops, isolating the similarity grouping.
    cat_sentence = _words("cat", 250)
    car_sentence = _words("car", 250)
    text = f"{cat_sentence} {car_sentence}"
    document = _document([ExtractedSegment(text=text)])

    chunks = chunk_document(document, embed=_topic_embed)

    assert len(chunks) == 2
    assert "cat" in chunks[0].text
    assert "car" not in chunks[0].text
    assert "car" in chunks[1].text
    assert "cat" not in chunks[1].text


def test_chunk_document_merges_undersized_groups_across_topic_breaks():
    # Alternating topics force separate similarity groups, but each is far
    # below MIN_CHUNK_TOKENS, so the merge pass must combine them anyway.
    sentences = [_words("cat", 5), _words("car", 5), _words("moon", 5)]
    document = _document([ExtractedSegment(text=" ".join(sentences))])

    chunks = chunk_document(document, embed=_topic_embed)

    assert len(chunks) == 1
    assert chunks[0].token_count < MIN_CHUNK_TOKENS
    assert "cat" in chunks[0].text
    assert "car" in chunks[0].text
    assert "moon" in chunks[0].text


def test_chunk_document_merges_trailing_undersized_group_backward():
    # First group is large enough alone; second (last) group is a runt and
    # has nothing after it to absorb into, so it must merge backward.
    sentences = [_words("cat", 250), _words("car", 5)]
    document = _document([ExtractedSegment(text=" ".join(sentences))])

    chunks = chunk_document(document, embed=_topic_embed)

    assert len(chunks) == 1
    assert "cat" in chunks[0].text
    assert "car" in chunks[0].text


def test_chunk_document_splits_oversized_group():
    # All sentences share one topic so similarity grouping keeps them
    # together; the combined group is over MAX_CHUNK_TOKENS and must split.
    sentences = [_words("cat", 150) for _ in range(8)]  # ~1200 tokens total
    document = _document([ExtractedSegment(text=" ".join(sentences))])

    chunks = chunk_document(document, embed=_topic_embed)

    assert len(chunks) > 1
    for chunk in chunks:
        assert chunk.token_count <= MAX_CHUNK_TOKENS
    # No sentence content is lost across the split.
    combined_word_count = sum(chunk.token_count for chunk in chunks)
    assert combined_word_count == estimate_token_count(" ".join(sentences))


def test_chunk_document_preserves_per_segment_metadata_and_never_spans_segments():
    segment_one = ExtractedSegment(text=_words("cat", 5), page_number=1, section_heading="Intro")
    segment_two = ExtractedSegment(text=_words("car", 5), page_number=2, section_heading="Body")
    document = _document([segment_one, segment_two])

    chunks = chunk_document(document, embed=_topic_embed)

    assert len(chunks) == 2
    assert chunks[0].page_number == 1
    assert chunks[0].section_heading == "Intro"
    assert "cat" in chunks[0].text
    assert chunks[1].page_number == 2
    assert chunks[1].section_heading == "Body"
    assert "car" in chunks[1].text


def test_chunk_document_returns_empty_list_for_document_with_no_segments():
    document = _document([])

    assert chunk_document(document, embed=_topic_embed) == []


def test_chunk_document_skips_embedding_for_single_sentence_segment():
    calls = []

    def counting_embed(sentences):
        calls.append(sentences)
        return _topic_embed(sentences)

    document = _document([ExtractedSegment(text=_words("cat", 5))])

    chunks = chunk_document(document, embed=counting_embed)

    assert len(chunks) == 1
    assert calls == []  # a single sentence never needs an embedding call


def test_chunk_carries_source_document_name():
    document = _document([ExtractedSegment(text=_words("cat", 250))])

    chunks = chunk_document(document, embed=_topic_embed)

    assert all(isinstance(chunk, Chunk) for chunk in chunks)
    assert all(chunk.source_document == "fixture.txt" for chunk in chunks)
