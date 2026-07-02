"""
PathBack — new-feature test suite (pytest)
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back

Covers the revenue-ready additions on top of the 17-test E2E baseline:
pass issuance via mocked Stripe webhook, pass validation, counter
persistence across a simulated restart, disclaimer presence, routing
policy per tier, 429 fallback, and served_by stamping.
"""

import importlib
import json
import os
from datetime import datetime, timedelta

import stripe as stripe_lib

import gng_db
import gng_inference
import app as pathback_app

from conftest import canned_stream, failing_stream
from mock_llm import CANNED_GUARD_RESPONSE


def sse_events(response):
    events = []
    for line in response.get_data(as_text=True).splitlines():
        if line.startswith('data:'):
            events.append(json.loads(line[5:].strip()))
    return events


def event_of(events, etype):
    matches = [e for e in events if e.get('type') == etype]
    return matches[0] if matches else None


def fake_checkout_event(product='pass_7day', session_id='cs_test_123',
                        payment_intent='pi_test_123', subscription=None):
    return {
        'type': 'checkout.session.completed',
        'data': {'object': {
            'id': session_id,
            'payment_intent': payment_intent,
            'subscription': subscription,
            'metadata': {'product': product},
        }},
    }


# ── JOB 3: Stripe passes ────────────────────────────────────────────────

def test_webhook_issues_7day_pass(client, monkeypatch):
    monkeypatch.setattr(stripe_lib.Webhook, 'construct_event',
                        staticmethod(lambda payload, sig, secret: fake_checkout_event()))
    r = client.post('/api/stripe/webhook', data=b'{}',
                    headers={'Stripe-Signature': 'sig'})
    assert r.status_code == 200

    r = client.get('/api/stripe/session-pass?session_id=cs_test_123')
    assert r.status_code == 200
    data = r.get_json()
    assert data['ready'] is True
    assert data['token'].startswith('pb_')
    assert data['pass_type'] == 'pass_7day'
    assert gng_db.is_pass_valid(data['token'])
    # ~7 days of access
    expires = datetime.fromisoformat(data['expires_at'])
    assert timedelta(days=6) < (expires - datetime.now()) <= timedelta(days=7, minutes=5)


def test_webhook_replay_does_not_duplicate(client, monkeypatch):
    monkeypatch.setattr(stripe_lib.Webhook, 'construct_event',
                        staticmethod(lambda payload, sig, secret: fake_checkout_event()))
    client.post('/api/stripe/webhook', data=b'{}', headers={'Stripe-Signature': 'sig'})
    client.post('/api/stripe/webhook', data=b'{}', headers={'Stripe-Signature': 'sig'})
    conn = gng_db.get_conn()
    count = conn.execute('SELECT COUNT(*) AS n FROM access_passes').fetchone()['n']
    conn.close()
    assert count == 1


def test_webhook_bad_signature_rejected(client, monkeypatch):
    def boom(payload, sig, secret):
        raise ValueError('bad signature')
    monkeypatch.setattr(stripe_lib.Webhook, 'construct_event', staticmethod(boom))
    r = client.post('/api/stripe/webhook', data=b'{}', headers={'Stripe-Signature': 'nope'})
    assert r.status_code == 400


def test_subscription_lifecycle_activates_and_deactivates(client, monkeypatch):
    monkeypatch.setattr(
        stripe_lib.Webhook, 'construct_event',
        staticmethod(lambda payload, sig, secret: fake_checkout_event(
            product='sub_monthly', session_id='cs_sub_1', subscription='sub_test_1')))
    monkeypatch.setattr(stripe_lib.Subscription, 'retrieve',
                        staticmethod(lambda _id: (_ for _ in ()).throw(RuntimeError('offline'))))
    client.post('/api/stripe/webhook', data=b'{}', headers={'Stripe-Signature': 'sig'})

    token = gng_db.get_pass_by_checkout_session('cs_sub_1')['token']
    assert gng_db.is_pass_valid(token)

    cancel_event = {'type': 'customer.subscription.deleted',
                    'data': {'object': {'id': 'sub_test_1', 'status': 'canceled'}}}
    monkeypatch.setattr(stripe_lib.Webhook, 'construct_event',
                        staticmethod(lambda payload, sig, secret: cancel_event))
    client.post('/api/stripe/webhook', data=b'{}', headers={'Stripe-Signature': 'sig'})
    assert not gng_db.is_pass_valid(token)
    assert gng_db.get_pass(token)['status'] == 'canceled'


def test_pass_validation_grants_paid_plan(client, monkeypatch):
    monkeypatch.setitem(gng_inference._STREAMERS, 'claude', canned_stream(CANNED_GUARD_RESPONSE))
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', canned_stream(CANNED_GUARD_RESPONSE))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', canned_stream(CANNED_GUARD_RESPONSE))

    token = gng_db.create_access_pass('pass_7day', datetime.now() + timedelta(days=7))
    r = client.post('/api/guard', json={'category': 'job', 'state': 'California',
                                        'rant': 'test', 'access_token': token})
    events = sse_events(r)
    assert event_of(events, 'meta')['plan'] == 'paid'
    assert event_of(events, 'done')['remaining_responses'] == 'unlimited'


def test_expired_pass_falls_back_to_free(client, monkeypatch):
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', canned_stream(CANNED_GUARD_RESPONSE))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', canned_stream(CANNED_GUARD_RESPONSE))

    token = gng_db.create_access_pass('pass_7day', datetime.now() - timedelta(days=1))
    assert not gng_db.is_pass_valid(token)
    r = client.post('/api/guard', json={'category': 'job', 'state': 'California',
                                        'rant': 'test', 'access_token': token})
    assert event_of(sse_events(r), 'meta')['plan'] == 'free'


# ── JOB 2: persistence ──────────────────────────────────────────────────

def test_counters_survive_simulated_restart():
    allowed, _, remaining = gng_db.consume_quota('1.2.3.4', 'sess-1', 3, 3, 200)
    assert allowed and remaining == 2

    # Simulated restart: reload the module — no in-process state may remain.
    importlib.reload(gng_db)
    assert gng_db.get_count('ip', '1.2.3.4') == 1
    assert gng_db.get_count('global', 'global') == 1

    allowed, _, remaining = gng_db.consume_quota('1.2.3.4', 'sess-1', 3, 3, 200)
    assert allowed and remaining == 1


def test_free_limit_enforced_after_restart(client, monkeypatch):
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', canned_stream(CANNED_GUARD_RESPONSE))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', canned_stream(CANNED_GUARD_RESPONSE))
    body = {'category': 'job', 'state': 'California', 'rant': 'help me'}
    headers = {'X-Forwarded-For': '9.9.9.9'}
    client.set_cookie('guard_session', 'fixed-session')  # pin the session backup limit too
    for _ in range(3):
        r = client.post('/api/guard', json=body, headers=headers)
        assert r.status_code == 200

    importlib.reload(gng_db)  # restart between request 3 and 4

    r = client.post('/api/guard', json=body, headers=headers)
    assert r.status_code == 429
    assert r.get_json()['error'] == 'daily_limit_reached'


def test_global_cap_enforced(client, monkeypatch):
    monkeypatch.setattr(pathback_app, 'GLOBAL_DAILY_LIMIT', 2)
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', canned_stream(CANNED_GUARD_RESPONSE))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', canned_stream(CANNED_GUARD_RESPONSE))
    body = {'category': 'job', 'state': 'California', 'rant': 'help me'}
    assert client.post('/api/guard', json=body, headers={'X-Forwarded-For': '1.1.1.1'}).status_code == 200
    assert client.post('/api/guard', json=body, headers={'X-Forwarded-For': '2.2.2.2'}).status_code == 200
    r = client.post('/api/guard', json=body, headers={'X-Forwarded-For': '3.3.3.3'})
    assert r.status_code == 429


def test_emergency_stop_via_sqlite(client):
    r = client.post('/admin/emergency-stop/enable', headers={'X-Admin-Key': 'test-admin-key'})
    assert r.status_code == 200 and gng_db.emergency_stop_enabled()
    r = client.post('/api/guard', json={'category': 'job', 'state': 'CA', 'rant': 'x'})
    assert r.status_code == 503
    client.post('/admin/emergency-stop/disable', headers={'X-Admin-Key': 'test-admin-key'})
    assert not gng_db.emergency_stop_enabled()


def test_admin_status_reads_sqlite(client):
    gng_db.consume_quota('7.7.7.7', 'sess-7', 3, 3, 200)
    r = client.get('/admin/status', headers={'X-Admin-Key': 'test-admin-key'})
    assert r.status_code == 200
    assert r.get_json()['global_daily_usage'] == 1


# ── JOB 5: disclaimer ───────────────────────────────────────────────────

DISCLAIMER = ('PathBack provides information and drafting help, not legal advice. '
              'For legal advice, consult a licensed attorney.')


def test_disclaimer_on_guard_response(client, monkeypatch):
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', canned_stream(CANNED_GUARD_RESPONSE))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', canned_stream(CANNED_GUARD_RESPONSE))
    r = client.post('/api/guard', json={'category': 'job', 'state': 'California', 'rant': 'test'})
    events = sse_events(r)
    assert event_of(events, 'meta')['disclaimer'] == DISCLAIMER
    assert event_of(events, 'done')['disclaimer'] == DISCLAIMER


def test_disclaimer_on_thought_partner(client, monkeypatch):
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', canned_stream('A thoughtful reply.'))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', canned_stream('A thoughtful reply.'))
    r = client.post('/api/thought-partner', json={'message': 'Big decision ahead'})
    assert r.get_json()['disclaimer'] == DISCLAIMER


def test_disclaimer_shown_on_input_screen():
    input_screen = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                'frontend', 'src', 'components', 'InputScreen.js')
    with open(input_screen) as f:
        assert DISCLAIMER.split('.')[0] in f.read()


# ── JOB 4: routing policy, 429 fallback, served_by ─────────────────────

def test_free_tier_never_uses_claude(client, monkeypatch):
    claude_calls = []

    def spying_claude(system_prompt, messages, max_tokens, temperature):
        claude_calls.append(1)
        def generate():
            yield 'claude text'
        return generate()

    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', failing_stream('groq down'))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', failing_stream('local down'))
    monkeypatch.setitem(gng_inference._STREAMERS, 'claude', spying_claude)

    r = client.post('/api/guard', json={'category': 'job', 'state': 'California', 'rant': 'test'})
    events = sse_events(r)
    error = event_of(events, 'error')
    assert error is not None and 'capacity' in error['message']
    assert claude_calls == []  # free users NEVER fall back to claude


def test_free_tier_failure_refunds_quota(client, monkeypatch):
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', failing_stream())
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', failing_stream())
    r = client.post('/api/guard', json={'category': 'job', 'state': 'CA', 'rant': 'x'},
                    headers={'X-Forwarded-For': '5.5.5.5'})
    r.get_data()  # drain the SSE stream so the refund runs
    assert gng_db.get_count('ip', '5.5.5.5') == 0


def test_paid_tier_prefers_claude(client, monkeypatch):
    monkeypatch.setitem(gng_inference._STREAMERS, 'claude', canned_stream(CANNED_GUARD_RESPONSE))
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', canned_stream(CANNED_GUARD_RESPONSE))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', canned_stream(CANNED_GUARD_RESPONSE))
    token = gng_db.create_access_pass('sub_monthly', datetime.now() + timedelta(days=30))
    r = client.post('/api/guard', json={'category': 'job', 'state': 'CA',
                                        'rant': 'x', 'access_token': token})
    done = event_of(sse_events(r), 'done')
    assert done['served_by'] == 'claude'
    assert done['downgraded'] is False


def test_paid_tier_downgrade_to_groq_is_flagged(client, monkeypatch):
    monkeypatch.setitem(gng_inference._STREAMERS, 'claude', failing_stream('claude down'))
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', canned_stream(CANNED_GUARD_RESPONSE))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', canned_stream(CANNED_GUARD_RESPONSE))
    token = gng_db.create_access_pass('sub_monthly', datetime.now() + timedelta(days=30))
    r = client.post('/api/guard', json={'category': 'job', 'state': 'CA',
                                        'rant': 'x', 'access_token': token})
    done = event_of(sse_events(r), 'done')
    assert done['served_by'] == 'groq'
    assert done['downgraded'] is True


def test_groq_429_falls_back_to_local(client, monkeypatch, mock_llm):
    """Real HTTP path: Groq keeps returning 429 → one retry → local lane."""
    mock_llm.reset(groq_mode='429')
    monkeypatch.setenv('GROQ_API_KEY', 'test-key')
    monkeypatch.setenv('GROQ_BASE_URL', mock_llm.groq_base_url)
    monkeypatch.setenv('OLLAMA_URL', mock_llm.ollama_url)

    r = client.post('/api/guard', json={'category': 'job', 'state': 'CA', 'rant': 'x'})
    events = sse_events(r)
    done = event_of(events, 'done')
    assert done['served_by'] == 'local'
    assert mock_llm.groq_requests >= 2  # original attempt + one retry
    # Local lane responses carry the citation-reliability caution
    notice = event_of(events, 'notice')
    assert notice is not None and 'double-check' in notice['message']


def test_groq_429_once_recovers_after_retry(client, monkeypatch, mock_llm):
    mock_llm.reset(groq_mode='429_once')
    monkeypatch.setenv('GROQ_API_KEY', 'test-key')
    monkeypatch.setenv('GROQ_BASE_URL', mock_llm.groq_base_url)
    monkeypatch.setenv('OLLAMA_URL', mock_llm.ollama_url)

    r = client.post('/api/guard', json={'category': 'job', 'state': 'CA', 'rant': 'x'})
    done = event_of(sse_events(r), 'done')
    assert done['served_by'] == 'groq'


def test_streaming_works_through_abstraction(client, monkeypatch, mock_llm):
    """Full text arrives as SSE chunks and parses into the three sections."""
    mock_llm.reset()
    monkeypatch.setenv('GROQ_API_KEY', 'test-key')
    monkeypatch.setenv('GROQ_BASE_URL', mock_llm.groq_base_url)
    monkeypatch.setenv('OLLAMA_URL', mock_llm.ollama_url)

    r = client.post('/api/guard', json={'category': 'job', 'state': 'CA', 'rant': 'x'})
    events = sse_events(r)
    text = ''.join(e['chunk'] for e in events if e.get('type') == 'text')
    assert '===WAIT===' in text and '===LEVERAGE===' in text and '===GUARD_STEPS===' in text
    assert len([e for e in events if e.get('type') == 'text']) > 1  # actually streamed


def test_served_by_stamped_in_usage_log(client, monkeypatch):
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', canned_stream(CANNED_GUARD_RESPONSE))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', canned_stream(CANNED_GUARD_RESPONSE))
    r = client.post('/api/guard', json={'category': 'job', 'state': 'CA', 'rant': 'x'},
                    headers={'X-Forwarded-For': '6.6.6.6'})
    r.get_data()  # drain the SSE stream so served_by gets stamped
    logs = gng_db.recent_logs(5)
    guard_logs = [l for l in logs if l['endpoint'] == '/api/guard' and l['ip'] == '6.6.6.6']
    assert guard_logs and guard_logs[-1]['served_by'] == 'groq'


def test_thought_partner_stamps_served_by(client, monkeypatch):
    monkeypatch.setitem(gng_inference._STREAMERS, 'groq', canned_stream('Reply.'))
    monkeypatch.setitem(gng_inference._STREAMERS, 'local', canned_stream('Reply.'))
    r = client.post('/api/thought-partner', json={'message': 'hello'},
                    headers={'X-Forwarded-For': '8.8.8.8'})
    assert r.get_json()['served_by'] == 'groq'
    logs = [l for l in gng_db.recent_logs(5) if l['endpoint'] == '/api/thought-partner']
    assert logs and logs[-1]['served_by'] == 'groq'
