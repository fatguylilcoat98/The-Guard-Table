"""
PathBack — mock LLM server for tests
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back

Speaks just enough of two dialects to stand in for the real lanes:
  * Groq / OpenAI-compatible SSE:  POST /openai/v1/chat/completions
  * Ollama NDJSON:                 POST /api/chat

Behavior is switchable per lane (`groq_mode`, `ollama_mode`) so tests can
simulate 429 rate limits and outages without touching the network.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

CANNED_GUARD_RESPONSE = """===WAIT===
They are trying to get you to give up without a fight.
If you do nothing, you could lose money and leverage you cannot get back.
Start with a written record.
===LEVERAGE===
This is regarding the issue we discussed.

I am requesting written confirmation of what happened and a correction date. Under state law, I have the right to a clear answer in writing.

Send me written confirmation within 10 business days.
===GUARD_STEPS===
Step 1: Send one follow-up asking for written confirmation and a correction date.
Step 2: Save screenshots of every message, letter, and call log.
Step 3: File a complaint with the appropriate state agency if they ignore this."""

CANNED_VERIFY_RESPONSE = '{"citations_valid": true, "concern": null}'


def _pick_response(body):
    text = json.dumps(body.get('messages', []))
    if 'citation checker' in text:
        return CANNED_VERIFY_RESPONSE
    return CANNED_GUARD_RESPONSE


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length) or b'{}')

    def do_POST(self):
        server = self.server
        if self.path.endswith('/chat/completions'):
            self._handle_groq(server)
        elif self.path == '/api/chat':
            self._handle_ollama(server)
        else:
            self.send_error(404)

    def _handle_groq(self, server):
        server.groq_requests += 1
        mode = server.groq_mode
        if mode == 'down':
            self.send_error(503)
            return
        if mode == '429' or (mode == '429_once' and server.groq_requests == 1):
            self.send_response(429)
            self.send_header('Retry-After', '0')
            self.end_headers()
            self.wfile.write(b'{"error": {"message": "Rate limit reached (TPM)"}}')
            return

        text = _pick_response(self._read_body())
        self.send_response(200)
        self.send_header('Content-Type', 'text/event-stream')
        self.end_headers()
        # Stream in a few chunks like the real API does
        step = max(len(text) // 5, 1)
        for i in range(0, len(text), step):
            event = {'choices': [{'delta': {'content': text[i:i + step]}}]}
            self.wfile.write(f'data: {json.dumps(event)}\n\n'.encode())
        self.wfile.write(b'data: [DONE]\n\n')

    def _handle_ollama(self, server):
        server.ollama_requests += 1
        if server.ollama_mode == 'down':
            self.send_error(503)
            return
        text = _pick_response(self._read_body())
        self.send_response(200)
        self.send_header('Content-Type', 'application/x-ndjson')
        self.end_headers()
        step = max(len(text) // 5, 1)
        for i in range(0, len(text), step):
            line = {'message': {'content': text[i:i + step]}, 'done': False}
            self.wfile.write((json.dumps(line) + '\n').encode())
        self.wfile.write((json.dumps({'message': {'content': ''}, 'done': True}) + '\n').encode())


class MockLLMServer(ThreadingHTTPServer):
    """Threaded mock server; set groq_mode / ollama_mode per test."""

    def __init__(self, port=0):
        super().__init__(('127.0.0.1', port), _Handler)
        self.groq_mode = 'ok'       # ok | 429 | 429_once | down
        self.ollama_mode = 'ok'     # ok | down
        self.groq_requests = 0
        self.ollama_requests = 0
        self._thread = None

    @property
    def port(self):
        return self.server_address[1]

    @property
    def groq_base_url(self):
        return f'http://127.0.0.1:{self.port}/openai/v1'

    @property
    def ollama_url(self):
        return f'http://127.0.0.1:{self.port}'

    def reset(self, groq_mode='ok', ollama_mode='ok'):
        self.groq_mode = groq_mode
        self.ollama_mode = ollama_mode
        self.groq_requests = 0
        self.ollama_requests = 0

    def start(self):
        self._thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self.shutdown()
        self.server_close()


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9606
    server = MockLLMServer(port).start()
    print(f'Mock LLM server on :{server.port} (Groq at {server.groq_base_url}, Ollama at {server.ollama_url})')
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        server.stop()
