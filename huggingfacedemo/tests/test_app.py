import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from app import Recorder, transcribe, format_document


def test_format_document_empty_list():
    assert format_document([]) == "(empty)"


def test_format_document_single_entry():
    assert format_document(["hello world"]) == "1. hello world"


def test_format_document_multiple_entries():
    result = format_document(["first", "second", "third"])
    assert result == "1. first\n2. second\n3. third"
