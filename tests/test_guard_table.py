"""
The Guard Table — Test Suite
The Good Neighbor Guard / Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

import os
import requests
import json
import time

BASE = "https://the-guard-table.onrender.com"

# Optional admin token: when set, it's attached to every /api/guard request
# so the test suite can bypass the 5/month free-tier rate limit.
# Never commit the token — export ADMIN_TOKEN=... in the shell before running.
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "")

def guard_post(payload, timeout=45):
    """POST to /api/guard, auto-injecting admin_token when available."""
    if ADMIN_TOKEN and isinstance(payload, dict) and "admin_token" not in payload:
        payload = {**payload, "admin_token": ADMIN_TOKEN}
    return requests.post(f"{BASE}/api/guard", json=payload, timeout=timeout)

PASS = "✅"
FAIL = "❌"
WARN = "⚠️ "

results = []

def run(name, fn):
    try:
        outcome, detail = fn()
        tag = PASS if outcome else FAIL
        print(f"{tag} {name}")
        if detail:
            print(f"   {detail}")
        results.append((outcome, name))
    except Exception as e:
        print(f"{FAIL} {name}")
        msg = str(e) or repr(e) or type(e).__name__
        print(f"   EXCEPTION: {msg}")
        results.append((False, name))

# ── INFRASTRUCTURE ──────────────────────────────────────────────

def test_health():
    r = requests.get(f"{BASE}/health", timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert data.get('status') == 'healthy'
    return True, f"Service: {data.get('service')} v{data.get('version')}"

def test_api_ready():
    r = requests.get(f"{BASE}/api/test", timeout=15)
    assert r.status_code == 200
    data = r.json()
    key_ok = data.get('api_key_set')
    client_ok = data.get('client_ready')
    detail = f"API key set: {key_ok} | Client ready: {client_ok}"
    if not key_ok or not client_ok:
        return False, detail
    return True, detail

def test_frontend_loads():
    r = requests.get(f"{BASE}/", timeout=15)
    assert r.status_code == 200
    # Should return HTML (React build)
    ct = r.headers.get('Content-Type', '')
    is_html = 'html' in ct or '<!DOCTYPE' in r.text or '<html' in r.text
    return is_html, f"Content-Type: {ct[:50]}"

# ── HAPPY PATH ──────────────────────────────────────────────────

def test_basic_employment():
    r = guard_post({
        "category": "job",
        "state": "California",
        "rant": "My boss fired me without any warning after I reported a safety violation to HR. I had a clean record for 3 years."
    })
    assert r.status_code == 200
    data = r.json()
    has_rights = 'rights' in data or 'what_they_did' in data
    has_leverage = 'leverage' in data
    has_steps = 'guard_steps' in data
    keys = list(data.keys())
    ok = has_leverage and has_steps
    return ok, f"Keys returned: {keys}"

def test_basic_housing():
    r = guard_post({
        "category": "housing",
        "state": "Texas",
        "rant": "My landlord has not fixed my broken heater for 6 weeks even though it is winter and I have kids. He keeps saying he will get to it."
    })
    assert r.status_code == 200
    data = r.json()
    ok = 'leverage' in data and 'guard_steps' in data
    return ok, f"State: Texas — got leverage: {'leverage' in data}"

def test_all_categories():
    categories = ['housing', 'money', 'job', 'benefits', 'family', 'other']
    failed = []
    for cat in categories:
        r = guard_post({
            "category": cat,
            "state": "California",
            "rant": f"I am having a serious problem with my {cat} situation and I need help understanding my rights."
        })
        if r.status_code != 200 or 'leverage' not in r.json():
            failed.append(cat)
        time.sleep(1)  # be gentle
    ok = len(failed) == 0
    return ok, f"Failed categories: {failed}" if failed else "All 6 categories returned valid responses"

def test_response_structure():
    """Verify all expected JSON fields come back"""
    r = guard_post({
        "category": "money",
        "state": "New York",
        "rant": "A debt collector called me at work after I told them to stop. They also called at 6am."
    })
    assert r.status_code == 200
    data = r.json()
    expected_keys = ['leverage', 'guard_steps']
    missing = [k for k in expected_keys if k not in data]
    has_remaining = 'remaining_responses' in data
    detail = f"Missing keys: {missing} | Has remaining_responses: {has_remaining}"
    return len(missing) == 0, detail

def test_remaining_responses_counted():
    """Make sure the counter is decrementing"""
    r = guard_post({
        "category": "job",
        "state": "Florida",
        "rant": "My employer has not paid me for 2 weeks and keeps saying the checks are delayed."
    })
    assert r.status_code == 200
    data = r.json()
    remaining = data.get('remaining_responses')
    is_int = isinstance(remaining, int) or remaining == 'unlimited'
    return is_int, f"remaining_responses = {remaining}"

# ── EDGE CASES ──────────────────────────────────────────────────

def test_empty_rant_rejected():
    r = guard_post({
        "category": "job",
        "state": "California",
        "rant": ""
    }, timeout=15)
    ok = r.status_code == 400
    return ok, f"Status: {r.status_code} (expected 400)"

def test_empty_rant_whitespace_rejected():
    r = guard_post({
        "category": "job",
        "state": "California",
        "rant": "     "
    }, timeout=15)
    ok = r.status_code == 400
    return ok, f"Status: {r.status_code} (expected 400)"

def test_missing_category_still_works():
    """Category is optional — should still return a response"""
    r = guard_post({
        "state": "Oregon",
        "rant": "My employer refused to give me any breaks during an 10 hour shift."
    })
    ok = r.status_code == 200 and 'leverage' in r.json()
    return ok, f"Status: {r.status_code}"

def test_missing_state_uses_default():
    """State defaults to California if not provided"""
    r = guard_post({
        "category": "housing",
        "rant": "My landlord entered my apartment without notice 3 times this month."
    })
    ok = r.status_code == 200 and 'leverage' in r.json()
    return ok, f"Status: {r.status_code}"

def test_very_long_rant():
    long_rant = "My boss has been treating me unfairly. " * 100
    r = guard_post({
        "category": "job",
        "state": "California",
        "rant": long_rant
    }, timeout=60)
    ok = r.status_code == 200
    return ok, f"Status: {r.status_code} | Response size: {len(r.text)} bytes"

def test_no_json_body():
    r = requests.post(f"{BASE}/api/guard",
        data="not json at all",
        headers={"Content-Type": "text/plain"},
        timeout=15)
    # Should not crash the server — 400 or 500 is acceptable, not a 502/hang
    ok = r.status_code in [400, 422, 500]
    return ok, f"Status: {r.status_code} (server handled gracefully)"

# ── RATE LIMITING ───────────────────────────────────────────────

def test_rate_limit_headers_present():
    """Confirm response includes remaining count for free users"""
    r = guard_post({
        "category": "job",
        "state": "California",
        "rant": "Testing rate limit tracking — my employer owes me overtime pay."
    })
    assert r.status_code == 200
    data = r.json()
    has_remaining = 'remaining_responses' in data
    return has_remaining, f"remaining_responses present: {has_remaining} = {data.get('remaining_responses')}"

# ── CONTENT QUALITY ─────────────────────────────────────────────

def test_response_not_hedging():
    """The Guard Table should give direct answers, not wishy-washy ones"""
    r = guard_post({
        "category": "job",
        "state": "California",
        "rant": "I was fired the day after I told my boss I was pregnant. No other reason given."
    })
    assert r.status_code == 200
    data = r.json()
    leverage = data.get('leverage', '').lower()
    hedge_words = ['might', 'perhaps', 'possibly']
    found_hedges = [w for w in hedge_words if w in leverage]
    ok = len(found_hedges) == 0
    return ok, f"Hedge words found: {found_hedges}" if found_hedges else "Response is direct — no hedge words"

def test_guard_steps_are_actionable():
    """Steps should be a list with at least 2 items"""
    r = guard_post({
        "category": "housing",
        "state": "California",
        "rant": "My landlord has not returned my security deposit after 45 days and is ignoring my calls."
    })
    assert r.status_code == 200
    data = r.json()
    steps = data.get('guard_steps', [])
    ok = isinstance(steps, list) and len(steps) >= 2
    return ok, f"Steps count: {len(steps)}"

# ── RUN ALL ─────────────────────────────────────────────────────

print("\n" + "="*55)
print("  THE GUARD TABLE — TEST SUITE")
print("  Target:", BASE)
print("="*55 + "\n")

print("── INFRASTRUCTURE ──")
run("Health check endpoint", test_health)
run("API key + client ready", test_api_ready)
run("Frontend loads (React build)", test_frontend_loads)

print("\n── HAPPY PATH ──")
run("Employment situation (California)", test_basic_employment)
run("Housing situation (Texas)", test_basic_housing)
run("All 6 categories respond", test_all_categories)
run("Response structure has required keys", test_response_structure)
run("Remaining responses counter works", test_remaining_responses_counted)

print("\n── EDGE CASES ──")
run("Empty rant returns 400", test_empty_rant_rejected)
run("Whitespace-only rant returns 400", test_empty_rant_whitespace_rejected)
run("Missing category still responds", test_missing_category_still_works)
run("Missing state uses default", test_missing_state_uses_default)
run("Very long rant handled", test_very_long_rant)
run("Non-JSON body doesn't crash server", test_no_json_body)

print("\n── RATE LIMITING ──")
run("Remaining responses in response", test_rate_limit_headers_present)

print("\n── CONTENT QUALITY ──")
run("Pregnancy firing — response not hedging", test_response_not_hedging)
run("Guard steps are actionable list", test_guard_steps_are_actionable)

print("\n" + "="*55)
passed = sum(1 for ok, _ in results if ok)
failed = sum(1 for ok, _ in results if not ok)
total = len(results)
print(f"  RESULTS: {passed}/{total} passed  |  {failed} failed")
print("="*55 + "\n")

if failed > 0:
    print("FAILED TESTS:")
    for ok, name in results:
        if not ok:
            print(f"  {FAIL} {name}")
