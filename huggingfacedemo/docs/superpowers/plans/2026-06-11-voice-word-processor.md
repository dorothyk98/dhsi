# Voice-to-Text Word Processor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a single-file terminal app that records mic audio on Enter keypress and transcribes it with Whisper, accumulating entries into a printed document.

**Architecture:** A `Recorder` class wraps `sounddevice.InputStream` for mic capture; a `transcribe()` function passes the captured numpy array to a HF `transformers` pipeline; a `format_document()` helper renders accumulated entries; `main()` wires them together in a blocking input loop.

**Tech Stack:** Python 3.10+, `transformers`, `sounddevice`, `numpy`, `torch`, `portaudio` (Homebrew)

---

## File Structure

| File | Responsibility |
|---|---|
| `app.py` | All application code: `Recorder`, `load_pipeline`, `transcribe`, `format_document`, `main` |
| `requirements.txt` | Runtime dependencies |
| `tests/test_app.py` | Unit tests for `Recorder`, `transcribe`, `format_document` |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `app.py`
- Create: `tests/__init__.py`
- Create: `tests/test_app.py`

- [ ] **Step 1: Create `requirements.txt`**

```
torch
transformers
sounddevice
numpy
```

- [ ] **Step 2: Create `app.py` skeleton**

```python
import sys
import numpy as np
import sounddevice as sd
from transformers import pipeline

SAMPLE_RATE = 16000
MODEL_ID = "openai/whisper-large-v3-turbo"


class Recorder:
    pass


def load_pipeline():
    pass


def transcribe(pipe, audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
    pass


def format_document(entries: list[str]) -> str:
    pass


def main():
    pass


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Create `tests/__init__.py`** (empty file)

- [ ] **Step 4: Create `tests/test_app.py` skeleton**

```python
import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from app import Recorder, transcribe, format_document
```

- [ ] **Step 5: Install dependencies**

```bash
brew install portaudio
pip install torch transformers sounddevice numpy pytest
```

- [ ] **Step 6: Verify imports**

```bash
python -c "import sounddevice, transformers, numpy, torch; print('OK')"
```

Expected output: `OK`

- [ ] **Step 7: Commit**

```bash
git add app.py requirements.txt tests/__init__.py tests/test_app.py
git commit -m "feat: scaffold voice-to-text app"
```

---

## Task 2: Document Formatter (TDD)

**Files:**
- Modify: `app.py` — implement `format_document`
- Modify: `tests/test_app.py` — add tests

- [ ] **Step 1: Write failing tests**

Add to `tests/test_app.py`:

```python
def test_format_document_empty_list():
    assert format_document([]) == "(empty)"


def test_format_document_single_entry():
    assert format_document(["hello world"]) == "1. hello world"


def test_format_document_multiple_entries():
    result = format_document(["first", "second", "third"])
    assert result == "1. first\n2. second\n3. third"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_app.py -v -k "format_document"
```

Expected: 3 FAILs — `TypeError` or `AssertionError` (function returns `None`)

- [ ] **Step 3: Implement `format_document` in `app.py`**

Replace the `pass` stub:

```python
def format_document(entries: list[str]) -> str:
    if not entries:
        return "(empty)"
    return "\n".join(f"{i + 1}. {entry}" for i, entry in enumerate(entries))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_app.py -v -k "format_document"
```

Expected: 3 PASSes

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat: implement format_document"
```

---

## Task 3: Recorder Class (TDD)

**Files:**
- Modify: `app.py` — implement `Recorder`
- Modify: `tests/test_app.py` — add tests

- [ ] **Step 1: Write failing tests**

Add to `tests/test_app.py`:

```python
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
```

Add the missing import at the top of `tests/test_app.py`:

```python
from app import Recorder, transcribe, format_document, SAMPLE_RATE
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_app.py -v -k "recorder"
```

Expected: 4 FAILs

- [ ] **Step 3: Implement `Recorder` in `app.py`**

Replace the `class Recorder: pass` stub:

```python
class Recorder:
    def __init__(self, sample_rate: int = SAMPLE_RATE):
        self._sample_rate = sample_rate
        self._chunks: list[np.ndarray] = []
        self._stream: sd.InputStream | None = None

    def _callback(self, indata: np.ndarray, frames: int, time, status) -> None:
        self._chunks.append(indata.copy().flatten())

    def start(self) -> None:
        self._chunks = []
        self._stream = sd.InputStream(
            samplerate=self._sample_rate,
            channels=1,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()

    def stop(self) -> np.ndarray:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        if not self._chunks:
            return np.array([], dtype="float32")
        return np.concatenate(self._chunks)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_app.py -v -k "recorder"
```

Expected: 4 PASSes

- [ ] **Step 5: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat: implement Recorder class"
```

---

## Task 4: Transcription Wrapper (TDD)

**Files:**
- Modify: `app.py` — implement `load_pipeline` and `transcribe`
- Modify: `tests/test_app.py` — add tests

- [ ] **Step 1: Write failing tests**

Add to `tests/test_app.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_app.py -v -k "transcribe"
```

Expected: 3 FAILs

- [ ] **Step 3: Implement `load_pipeline` and `transcribe` in `app.py`**

Replace the two stubs:

```python
def load_pipeline():
    return pipeline("automatic-speech-recognition", model=MODEL_ID)


def transcribe(pipe, audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
    if len(audio) == 0:
        return ""
    result = pipe({"array": audio, "sampling_rate": sample_rate})
    return result["text"].strip()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
pytest tests/test_app.py -v -k "transcribe"
```

Expected: 3 PASSes

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/test_app.py -v
```

Expected: all 10 tests pass

- [ ] **Step 6: Commit**

```bash
git add app.py tests/test_app.py
git commit -m "feat: implement load_pipeline and transcribe"
```

---

## Task 5: Main Loop

**Files:**
- Modify: `app.py` — implement `main`

- [ ] **Step 1: Implement `main` in `app.py`**

Replace the `def main(): pass` stub:

```python
def main():
    print("Loading model... (first run downloads ~800MB)")
    try:
        pipe = load_pipeline()
    except Exception as e:
        print(f"Failed to load model: {e}")
        sys.exit(1)

    print("Ready. Press Enter to start recording, Ctrl+C to quit.\n")
    document: list[str] = []
    recorder = Recorder()

    while True:
        try:
            input()
        except KeyboardInterrupt:
            print("\nGoodbye.")
            break

        try:
            recorder.start()
        except sd.PortAudioError as e:
            print(f"Mic error: {e}")
            print("Check available devices: python -m sounddevice")
            sys.exit(1)

        print("Recording... Press Enter to stop.")
        try:
            input()
        except KeyboardInterrupt:
            recorder.stop()
            print("\nGoodbye.")
            break

        audio = recorder.stop()

        if len(audio) == 0:
            print("(nothing recorded)\n")
            print("Press Enter to start recording, Ctrl+C to quit.\n")
            continue

        print("Transcribing...")
        try:
            text = transcribe(pipe, audio)
        except Exception as e:
            print(f"Transcription error: {e}\n")
            print("Press Enter to start recording, Ctrl+C to quit.\n")
            continue

        if not text:
            print("(no speech detected)\n")
            print("Press Enter to start recording, Ctrl+C to quit.\n")
            continue

        document.append(text)
        print(f'\n> "{text}"\n')
        print("--- Document so far ---")
        print(format_document(document))
        print("-----------------------\n")
        print("Press Enter to start recording, Ctrl+C to quit.\n")
```

- [ ] **Step 2: Run full test suite to confirm nothing broke**

```bash
pytest tests/test_app.py -v
```

Expected: all 10 tests pass

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: implement main loop"
```

---

## Task 6: Integration Smoke Test

**Files:** none — manual test only

- [ ] **Step 1: Run the app**

```bash
python app.py
```

Expected on first run: model downloads to `~/.cache/huggingface/hub/` (~800MB), then:
```
Loading model... (first run downloads ~800MB)
Ready. Press Enter to start recording, Ctrl+C to quit.
```

- [ ] **Step 2: Record a short phrase**

1. Press Enter
2. Say "the quick brown fox"
3. Press Enter

Expected:
```
Recording... Press Enter to stop.
Transcribing...

> "The quick brown fox."

--- Document so far ---
1. The quick brown fox.
-----------------------

Press Enter to start recording, Ctrl+C to quit.
```

- [ ] **Step 3: Test immediate stop (empty audio)**

1. Press Enter to start
2. Press Enter immediately (no speech)

Expected: `(nothing recorded)` prompt re-appears

- [ ] **Step 4: Test Ctrl+C exit**

Press Ctrl+C at the ready prompt.

Expected: `Goodbye.` and clean exit (no traceback)

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: complete voice-to-text terminal app"
```
