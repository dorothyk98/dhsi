# Voice-to-Text Word Processor — Design Spec

**Date:** 2026-06-11  
**Status:** Approved  
**Scope:** Minimalist terminal test application

---

## Overview

A single-file Python terminal app that records speech via the Mac microphone and transcribes it locally using NVIDIA's Parakeet model running on Apple Silicon via the MLX framework (`parakeet-mlx`). Each transcription is appended to an in-memory document printed after every entry. The goal is a working test harness — not a production app.

---

## Architecture

Single file: `app.py`

Three logical sections:

1. **Model loader** — loads the Parakeet MLX model `mlx-community/parakeet-tdt-0.6b-v2` via `parakeet_mlx.from_pretrained` at startup. Prints a "ready" prompt once loaded.
2. **Recorder** — captures mic audio via `sounddevice` into a `numpy` array on a background thread. `start()` begins capture; `stop()` ends it and returns the array.
3. **Main loop** — drives the terminal interaction and accumulates transcripts.

---

## Data Flow

```
mic → sounddevice stream (float32, 16kHz mono)
    → numpy array
    → mx.array → get_logmel (parakeet_mlx.audio)
    → model.generate(mel)[0].text  (Parakeet TDT 0.6b-v2)
    → text string
    → appended to in-memory document list
    → printed to terminal
```

Audio is captured at 16kHz mono to match Parakeet's expected input — no resampling required. The in-memory array is fed directly through `get_logmel` + `generate`, bypassing `parakeet_mlx`'s file-based `transcribe()` path (which requires ffmpeg) since the recorder already provides raw PCM samples.

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
| `parakeet-mlx` | Parakeet ASR on Apple Silicon (loads model, mel + decode) |
| `mlx` | Apple MLX array framework (pulled in by parakeet-mlx) |
| `sounddevice` | Mic audio capture |
| `numpy` | Audio buffer |
| `portaudio` (Homebrew) | Required by sounddevice on macOS |

Requires **Apple Silicon** (arm64) — MLX does not run on Intel Macs. No ffmpeg needed (raw PCM is fed directly to the model).

Install:
```bash
brew install portaudio
pip install parakeet-mlx mlx sounddevice numpy
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
