import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from app import Recorder, transcribe, format_document, main, SAMPLE_RATE


def test_format_document_empty_list():
    assert format_document([]) == "(empty)"


def test_format_document_single_entry():
    assert format_document(["hello world"]) == "1. hello world"


def test_format_document_multiple_entries():
    result = format_document(["first", "second", "third"])
    assert result == "1. first\n2. second\n3. third"


def test_recorder_stop_returns_empty_array_when_no_chunks():
    recorder = Recorder()
    result = recorder.stop()
    assert len(result) == 0
    assert result.dtype == np.float32


def test_recorder_stop_concatenates_chunks():
    recorder = Recorder()
    recorder._chunks = [np.array([0.1, 0.2], dtype="float32"),
                        np.array([0.3, 0.4], dtype="float32")]
    result = recorder.stop()
    np.testing.assert_array_almost_equal(result, [0.1, 0.2, 0.3, 0.4])


def test_recorder_start_creates_and_starts_stream():
    recorder = Recorder()
    with patch("app.sd.InputStream") as mock_cls:
        mock_stream = MagicMock()
        mock_cls.return_value = mock_stream
        recorder.start()
        mock_cls.assert_called_once_with(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype="float32",
            callback=recorder._callback,
        )
        mock_stream.start.assert_called_once()


def test_recorder_start_clears_previous_chunks():
    recorder = Recorder()
    recorder._chunks = [np.array([0.9], dtype="float32")]
    with patch("app.sd.InputStream"):
        recorder.start()
    assert recorder._chunks == []


def test_transcribe_returns_empty_string_for_empty_audio():
    mock_pipe = MagicMock()
    result = transcribe(mock_pipe, np.array([], dtype="float32"))
    mock_pipe.assert_not_called()
    assert result == ""


def test_transcribe_calls_pipeline_and_strips_whitespace():
    mock_pipe = MagicMock(return_value={"text": "  hello world  "})
    audio = np.array([0.1, 0.2, 0.3], dtype="float32")
    result = transcribe(mock_pipe, audio, sample_rate=16000)
    mock_pipe.assert_called_once_with({"array": audio, "sampling_rate": 16000})
    assert result == "hello world"


def test_transcribe_uses_default_sample_rate():
    mock_pipe = MagicMock(return_value={"text": "test"})
    audio = np.array([0.1], dtype="float32")
    transcribe(mock_pipe, audio)
    mock_pipe.assert_called_once_with({"array": audio, "sampling_rate": SAMPLE_RATE})


def test_main_exits_cleanly_on_eof():
    with patch("app.load_pipeline", return_value=MagicMock()), \
         patch("builtins.input", side_effect=EOFError), \
         patch("builtins.print") as mock_print:
        main()
    assert any("Goodbye." in str(call) for call in mock_print.call_args_list)
