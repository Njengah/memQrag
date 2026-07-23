"""Smoke tests for the memQrag package scaffold.

These tests only confirm that the placeholder module boundaries defined in
docs/ARCHITECTURE.md exist and are importable. They intentionally do not
test behavior, because no behavior has been implemented in this scaffold.
"""

import importlib

import pytest

EXPECTED_SUBMODULES = [
    "memQrag.ingestion",
    "memQrag.retrieval",
    "memQrag.memory",
    "memQrag.agent",
    "memQrag.api",
]


def test_top_level_package_imports_and_has_version():
    package = importlib.import_module("memQrag")
    assert package.__version__ == "0.1.0"


@pytest.mark.parametrize("module_name", EXPECTED_SUBMODULES)
def test_submodule_imports_and_is_documented(module_name):
    module = importlib.import_module(module_name)
    assert module.__doc__, f"{module_name} must document its planned responsibility"
