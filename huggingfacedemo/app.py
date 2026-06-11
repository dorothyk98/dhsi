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
    if not entries:
        return "(empty)"
    return "\n".join(f"{i + 1}. {entry}" for i, entry in enumerate(entries))


def main():
    pass


if __name__ == "__main__":
    main()
