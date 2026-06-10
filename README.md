# dhsi

Minimal streaming chat UI for [Ollama](https://ollama.com), two ways:

- **`app.py`** — Flask backend that proxies requests to Ollama (recommended)
- **`index.html`** — standalone page that talks to Ollama directly (no server needed)

Both use the `gemma4:latest` model by default.

## Requirements

- [Ollama](https://ollama.com) running locally (`ollama serve`)
- `gemma4:latest` pulled (`ollama pull gemma4:latest`)

## Usage

### Flask app

```bash
pip install flask requests
python app.py
```

Open http://localhost:5000

Set `FLASK_DEBUG=true` to enable the Werkzeug debugger (development only).

### Standalone

Open `index.html` directly in a browser. Ollama must be reachable at `http://localhost:11434`.
