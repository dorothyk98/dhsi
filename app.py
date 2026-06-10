"""Bare-minimum chat web app — Flask + Ollama.

Run:
    pip install flask requests
    python app.py
Then open http://localhost:5000
"""

import os
from flask import Flask, request, Response, render_template_string, jsonify
import requests

MODEL = "gemma4:latest"
OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_TIMEOUT = (10, 120)  # (connect, read) seconds

app = Flask(__name__)

PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Ollama Chat</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, system-ui, sans-serif; margin: 0; height: 100vh;
         display: flex; flex-direction: column; background: #f5f5f5; }
  header { padding: 12px 20px; background: #222; color: #fff; font-weight: 600; }
  #chat { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 12px; }
  .msg { max-width: 75%; padding: 10px 14px; border-radius: 12px; line-height: 1.4;
         white-space: pre-wrap; word-wrap: break-word; }
  .user { align-self: flex-end; background: #007aff; color: #fff; }
  .assistant { align-self: flex-start; background: #fff; border: 1px solid #ddd; }
  form { display: flex; gap: 8px; padding: 12px; background: #fff; border-top: 1px solid #ddd; }
  #input { flex: 1; padding: 10px; font-size: 16px; border: 1px solid #ccc;
           border-radius: 8px; resize: none; font-family: inherit; }
  button { padding: 10px 18px; font-size: 16px; background: #007aff; color: #fff;
           border: none; border-radius: 8px; cursor: pointer; }
  button:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
</head>
<body>
<header>Ollama Chat — {{ model }}</header>
<div id="chat"></div>
<form id="form">
  <textarea id="input" rows="2" placeholder="Type a message... (Enter to send, Shift+Enter for newline)"></textarea>
  <button type="submit" id="send">Send</button>
</form>

<script>
const chat = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const history = [];

function addMsg(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
  return div;
}

async function send(userText) {
  history.push({ role: "user", content: userText });
  addMsg("user", userText);

  const assistantDiv = addMsg("assistant", "");
  let assistantText = "";

  try {
    const res = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: history }),
    });
    if (!res.ok) throw new Error("HTTP " + res.status);

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        const data = JSON.parse(line);
        if (data.message?.content) {
          assistantText += data.message.content;
          assistantDiv.textContent = assistantText;
          chat.scrollTop = chat.scrollHeight;
        }
      }
    }
    history.push({ role: "assistant", content: assistantText });
  } catch (err) {
    assistantDiv.textContent = "Error: " + err.message;
  }
}

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;
  input.value = "";
  sendBtn.disabled = true;
  await send(text);
  sendBtn.disabled = false;
  input.focus();
});

input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(PAGE, model=MODEL)


@app.route("/chat", methods=["POST"])
def chat():
    body = request.get_json(silent=True)
    if body is None or "messages" not in body:
        return jsonify({"error": "invalid request"}), 400
    messages = body["messages"]

    def stream():
        try:
            with requests.post(
                OLLAMA_URL,
                json={"model": MODEL, "messages": messages, "stream": True},
                stream=True,
                timeout=OLLAMA_TIMEOUT,
            ) as r:
                r.raise_for_status()
                for line in r.iter_lines():
                    if line:
                        yield line + b"\n"
        except requests.RequestException:
            yield b'{"error": "upstream error"}\n'

    return Response(stream(), mimetype="application/x-ndjson")


if __name__ == "__main__":
    app.run(port=5000, debug=os.getenv("FLASK_DEBUG", "").lower() == "true")
