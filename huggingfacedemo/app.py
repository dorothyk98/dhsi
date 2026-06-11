import sys
import numpy as np
import sounddevice as sd
from transformers import pipeline

SAMPLE_RATE = 16000
MODEL_ID = "openai/whisper-large-v3-turbo"


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


def load_pipeline():
    return pipeline("automatic-speech-recognition", model=MODEL_ID)


def transcribe(pipe, audio: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
    if len(audio) == 0:
        return ""
    result = pipe({"array": audio, "sampling_rate": sample_rate})
    return result["text"].strip()


def format_document(entries: list[str]) -> str:
    if not entries:
        return "(empty)"
    return "\n".join(f"{i + 1}. {entry}" for i, entry in enumerate(entries))


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


if __name__ == "__main__":
    main()
