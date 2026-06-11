# Voice-to-Text Word Processor — Design Spec

**Date:** 2026-06-11  
**Status:** Approved  
**Scope:** Minimalist terminal test application

---

## Overview

A single-file Python terminal app that records speech via the Mac microphone and transcribes it using OpenAI's Whisper model served from Hugging Face. Each transcription is appended to an in-memory document printed after every entry. The goal is a working test harness — not a production app.

---

## Architecture

Single file: `app.py`

Three logical sections:

1. **Model loader** — initializes the `transformers` ASR pipeline with `openai/whisper-large-v3-turbo` at startup. Prints a "ready" prompt once loaded.
2. **Recorder** — captures mic audio via `sounddevice` into a `numpy` array on a background thread. `start()` begins capture; `stop()` ends it and returns the array.
3. **Main loop** — drives the terminal interaction and accumulates transcripts.

---

## Data Flow

```
mic → sounddevice stream (float32, 16kHz mono)
    → numpy array
    → transformers ASR pipeline (openai/whisper-large-v3-turbo)
    → text string
    → appended to in-memory document list
    → printed to terminal
```

Audio is captured at 16kHz mono to match Whisper's expected input — no resampling required.

---

## User Interaction

```
Loading model... (first run downloads ~800MB)
Ready. Press Enter to start recording, Ctrl+C to quit.

[user presses Enter]
Recording... Press Enter to stop.

[user presses Enter]
Transcribing...
> "your transcribed text here"

--- Document so far ---
1. your transcribed text here
-----------------------

Press Enter to start recording, Ctrl+C to quit.
```

---

## Dependencies

| Package | Purpose |
|---|---|
| `torch` | Transformers inference backend |
| `transformers` | HF pipeline + Whisper model |
| `sounddevice` | Mic audio capture |
| `numpy` | Audio buffer |
| `portaudio` (Homebrew) | Required by sounddevice on macOS |

Install:
```bash
brew install portaudio
pip install torch transformers sounddevice numpy
```

---

## Error Handling

| Scenario | Behavior |
|---|---|
| Model load failure | Print error, exit |
| Mic not found | Catch `sounddevice` error, print message + hint to run `python -m sounddevice`, exit |
| No audio captured (immediate stop) | Skip transcription, re-prompt |
| Transcription error | Print error, continue loop |

---

## Out of Scope

- File saving / export
- Configuration files
- Logging
- Real-time streaming transcription
- GUI of any kind
