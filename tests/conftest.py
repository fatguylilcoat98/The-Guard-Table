"""
PathBack — pytest fixtures
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

import os
import sys
import tempfile

import pytest

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(os.path.dirname(TESTS_DIR), 'backend')
sys.path.insert(0, BACKEND_DIR)
sys.path.insert(0, TESTS_DIR)

# Point the app at a throwaway database BEFORE it is imported.
_DB_DIR = tempfile.mkdtemp(prefix='pathback-test-')
os.environ['PATHBACK_DB'] = os.path.join(_DB_DIR, 'pathback-test.db')
os.environ.setdefault('GUARD_ADMIN_KEY', 'test-admin-key')

import gng_db  # noqa: E402
import gng_inference  # noqa: E402
import app as pathback_app  # noqa: E402

from mock_llm import MockLLMServer  # noqa: E402


@pytest.fixture(scope='session')
def mock_llm():
    server = MockLLMServer().start()
    yield server
    server.stop()


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setattr(pathback_app.app, 'testing', True)
    return pathback_app.app.test_client()


@pytest.fixture(autouse=True)
def clean_db():
    """Each test starts from an empty database (schema kept)."""
    conn = gng_db.get_conn()
    try:
        for table in ('usage_counters', 'access_passes', 'usage_log',
                      'admin_tokens', 'app_settings'):
            conn.execute(f'DELETE FROM {table}')
    finally:
        conn.close()
    yield


def canned_stream(text):
    """Build a fake lane streamer that yields `text` in chunks."""
    def streamer(system_prompt, messages, max_tokens, temperature):
        def generate():
            step = max(len(text) // 4, 1)
            for i in range(0, len(text), step):
                yield text[i:i + step]
        return generate()
    return streamer


def failing_stream(message='lane down'):
    def streamer(system_prompt, messages, max_tokens, temperature):
        raise gng_inference.LaneError(message)
    return streamer
