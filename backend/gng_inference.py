"""
PathBack — multi-provider inference client
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back

The single client for ALL model calls. Three lanes:

  "groq"   — Groq API (OpenAI-compatible), llama-3.3-70b-versatile, streaming.
             Free tier is ~30 RPM / 6K TPM / 1K req-day; TPM is the binding
             cap, so 429s are expected under load — one retry with backoff,
             then shed gracefully down the chain.
  "local"  — Ollama at OLLAMA_URL (default http://localhost:11434),
             model OLLAMA_MODEL (default qwen2.5:7b).
  "claude" — Anthropic API with prompt caching (cache_control on the large
             system prompt).

Routing (env-overridable):
  free main response  → groq → local → honest "at capacity" (NEVER claude)
  paid main response  → claude → groq (downgrade noted in metadata)
  citation verification → groq → local → skip (never blocks a response)
"""

import os
import json
import time
import logging

import httpx

logger = logging.getLogger(__name__)

GROQ_MODEL_DEFAULT = 'llama-3.3-70b-versatile'
OLLAMA_MODEL_DEFAULT = 'qwen2.5:7b'
CLAUDE_MODEL_DEFAULT = 'claude-sonnet-4-20250514'

# How long a lane may wait before retrying a 429 once. Kept short so a
# stalled lane sheds to the next one instead of hanging the stream.
RATE_LIMIT_MAX_BACKOFF_SECONDS = 5.0


class LaneError(Exception):
    """This lane can't serve the request (missing key, down, rate-limited)."""


class AllLanesFailed(Exception):
    """Every lane in the chain failed; caller decides how to degrade."""


def _parse_chain(env_name, default):
    raw = os.getenv(env_name, default)
    chain = [lane.strip() for lane in raw.split(',') if lane.strip()]
    unknown = [lane for lane in chain if lane not in ('groq', 'local', 'claude')]
    if unknown:
        logger.warning('Ignoring unknown lanes in %s: %s', env_name, unknown)
        chain = [lane for lane in chain if lane not in unknown]
    return chain


def free_chain():
    return _parse_chain('PATHBACK_FREE_CHAIN', 'groq,local')


def paid_chain():
    return _parse_chain('PATHBACK_PAID_CHAIN', 'claude,groq')


def verify_chain():
    return _parse_chain('PATHBACK_VERIFY_CHAIN', 'groq,local')


def configured_lanes():
    """Lanes that have enough configuration to be worth trying."""
    lanes = []
    if os.getenv('GROQ_API_KEY'):
        lanes.append('groq')
    lanes.append('local')  # Ollama needs no key; reachability checked at call time
    if os.getenv('ANTHROPIC_API_KEY'):
        lanes.append('claude')
    return lanes


# ── Groq lane (OpenAI-compatible SSE) ───────────────────────────────────

def _groq_base_url():
    return os.getenv('GROQ_BASE_URL', 'https://api.groq.com/openai/v1').rstrip('/')


def _backoff_seconds(response, attempt):
    retry_after = response.headers.get('retry-after')
    try:
        seconds = float(retry_after)
    except (TypeError, ValueError):
        seconds = 1.0 + attempt
    return min(seconds, RATE_LIMIT_MAX_BACKOFF_SECONDS)


def _groq_stream(system_prompt, messages, max_tokens, temperature):
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        raise LaneError('groq: GROQ_API_KEY not set')

    payload = {
        'model': os.getenv('GROQ_MODEL', GROQ_MODEL_DEFAULT),
        'messages': [{'role': 'system', 'content': system_prompt}] + messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
        'stream': True,
    }
    headers = {'Authorization': f'Bearer {api_key}'}
    url = f'{_groq_base_url()}/chat/completions'

    client = httpx.Client(timeout=httpx.Timeout(120.0, connect=10.0))
    stream_ctx = None
    try:
        # One retry on 429 (Groq free-tier TPM is the binding cap), then shed.
        for attempt in range(2):
            stream_ctx = client.stream('POST', url, json=payload, headers=headers)
            response = stream_ctx.__enter__()
            if response.status_code == 429:
                stream_ctx.__exit__(None, None, None)
                stream_ctx = None
                if attempt == 0:
                    wait = _backoff_seconds(response, attempt)
                    logger.info('groq: 429, retrying once in %.1fs', wait)
                    time.sleep(wait)
                    continue
                raise LaneError('groq: rate limited (429) after retry')
            if response.status_code != 200:
                body = response.read()[:200]
                stream_ctx.__exit__(None, None, None)
                stream_ctx = None
                raise LaneError(f'groq: HTTP {response.status_code}: {body}')
            break

        def generate():
            try:
                for line in response.iter_lines():
                    if not line or not line.startswith('data:'):
                        continue
                    data = line[5:].strip()
                    if data == '[DONE]':
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = (event.get('choices') or [{}])[0].get('delta', {})
                    chunk = delta.get('content')
                    if chunk:
                        yield chunk
            finally:
                stream_ctx.__exit__(None, None, None)
                client.close()

        return generate()
    except LaneError:
        client.close()
        raise
    except Exception as exc:
        if stream_ctx is not None:
            stream_ctx.__exit__(None, None, None)
        client.close()
        raise LaneError(f'groq: {exc}') from exc


# ── Local lane (Ollama, NDJSON streaming) ───────────────────────────────

def _ollama_url():
    return os.getenv('OLLAMA_URL', 'http://localhost:11434').rstrip('/')


def _local_stream(system_prompt, messages, max_tokens, temperature):
    payload = {
        'model': os.getenv('OLLAMA_MODEL', OLLAMA_MODEL_DEFAULT),
        'messages': [{'role': 'system', 'content': system_prompt}] + messages,
        'stream': True,
        'options': {'num_predict': max_tokens, 'temperature': temperature},
    }
    url = f'{_ollama_url()}/api/chat'

    client = httpx.Client(timeout=httpx.Timeout(300.0, connect=5.0))
    stream_ctx = None
    try:
        stream_ctx = client.stream('POST', url, json=payload)
        response = stream_ctx.__enter__()
        if response.status_code != 200:
            body = response.read()[:200]
            stream_ctx.__exit__(None, None, None)
            stream_ctx = None
            raise LaneError(f'local: HTTP {response.status_code}: {body}')

        def generate():
            try:
                for line in response.iter_lines():
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    chunk = (event.get('message') or {}).get('content')
                    if chunk:
                        yield chunk
                    if event.get('done'):
                        break
            finally:
                stream_ctx.__exit__(None, None, None)
                client.close()

        return generate()
    except LaneError:
        client.close()
        raise
    except Exception as exc:
        if stream_ctx is not None:
            stream_ctx.__exit__(None, None, None)
        client.close()
        raise LaneError(f'local: {exc}') from exc


# ── Claude lane (Anthropic, prompt caching on the system prompt) ────────

_anthropic_client = None


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise LaneError('claude: ANTHROPIC_API_KEY not set')
        import anthropic
        _anthropic_client = anthropic.Anthropic(api_key=api_key, http_client=httpx.Client())
    return _anthropic_client


def _claude_stream(system_prompt, messages, max_tokens, temperature):
    client = _get_anthropic_client()
    model = os.getenv('CLAUDE_MODEL', CLAUDE_MODEL_DEFAULT)
    system_blocks = [{
        'type': 'text',
        'text': system_prompt,
        'cache_control': {'type': 'ephemeral'},
    }]

    def open_stream():
        return client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_blocks,
            messages=messages,
        )

    try:
        stream_manager = open_stream()
        stream = stream_manager.__enter__()
    except Exception as exc:
        # One retry with backoff on rate limits, then shed down the chain.
        if getattr(exc, 'status_code', None) == 429 or 'rate' in str(exc).lower():
            time.sleep(min(2.0, RATE_LIMIT_MAX_BACKOFF_SECONDS))
            try:
                stream_manager = open_stream()
                stream = stream_manager.__enter__()
            except Exception as retry_exc:
                raise LaneError(f'claude: {retry_exc}') from retry_exc
        else:
            raise LaneError(f'claude: {exc}') from exc

    def generate():
        try:
            for chunk in stream.text_stream:
                if chunk:
                    yield chunk
        finally:
            stream_manager.__exit__(None, None, None)

    return generate()


_STREAMERS = {
    'groq': _groq_stream,
    'local': _local_stream,
    'claude': _claude_stream,
}


# ── Chain runners ───────────────────────────────────────────────────────

def open_stream_chain(chain, system_prompt, messages,
                      max_tokens=2000, temperature=0.3):
    """Try each lane until one starts producing text.

    Returns (lane, generator). The first chunk is pulled eagerly so an
    unreachable or rate-limited lane falls through to the next one before
    anything reaches the user. Raises AllLanesFailed when the chain is dry.
    """
    errors = []
    for lane in chain:
        try:
            gen = _STREAMERS[lane](system_prompt, messages, max_tokens, temperature)
            first = next(gen, None)
            if first is None:
                raise LaneError(f'{lane}: empty response')

            def replay(first_chunk=first, rest=gen):
                yield first_chunk
                yield from rest

            logger.info('Inference lane selected: %s', lane)
            return lane, replay()
        except LaneError as exc:
            logger.warning('Lane %s unavailable: %s', lane, exc)
            errors.append(str(exc))
        except Exception as exc:  # unexpected — treat as lane failure, keep going
            logger.warning('Lane %s failed unexpectedly: %s', lane, exc)
            errors.append(f'{lane}: {exc}')
    raise AllLanesFailed('; '.join(errors) or 'no lanes configured')


def complete_chain(chain, system_prompt, messages,
                   max_tokens=2000, temperature=0.3):
    """Non-streaming convenience: returns (lane, full_text)."""
    lane, gen = open_stream_chain(chain, system_prompt, messages,
                                  max_tokens=max_tokens, temperature=temperature)
    return lane, ''.join(gen)
