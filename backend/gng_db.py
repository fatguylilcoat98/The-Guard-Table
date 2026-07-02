"""
PathBack — SQLite persistence layer
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back

All durable state lives here: daily usage counters (per-IP, per-session,
global), access passes issued through Stripe, the usage log, admin tokens,
and app settings (emergency stop). Every mutation runs inside a SQLite
transaction so counters stay correct across multiple gunicorn workers —
nothing is cached in-process.
"""

import os
import sqlite3
import secrets
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'pathback.db')


def db_path():
    return os.getenv('PATHBACK_DB', DEFAULT_DB_PATH)


def get_conn():
    """New connection per call — no shared state between workers/requests."""
    path = db_path()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    conn = sqlite3.connect(path, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA busy_timeout=30000')
    conn.execute('PRAGMA foreign_keys=ON')
    return conn


SCHEMA = """
CREATE TABLE IF NOT EXISTS usage_counters (
    scope TEXT NOT NULL,              -- 'ip' | 'session' | 'global'
    key   TEXT NOT NULL,              -- ip address, session id, or 'global'
    day   TEXT NOT NULL,              -- YYYY-MM-DD
    count INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (scope, key, day)
);

CREATE TABLE IF NOT EXISTS access_passes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    pass_type TEXT NOT NULL,          -- 'pass_7day' | 'sub_monthly' | 'sub_yearly'
    expires_at TEXT,                  -- ISO timestamp; NULL = no expiry
    stripe_ref TEXT,                  -- payment_intent / subscription id
    checkout_session_id TEXT,         -- Stripe checkout session id
    status TEXT NOT NULL DEFAULT 'active',  -- 'active' | 'inactive' | 'canceled'
    cancel_at_period_end INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_passes_stripe_ref ON access_passes (stripe_ref);
CREATE INDEX IF NOT EXISTS idx_passes_checkout ON access_passes (checkout_session_id);

CREATE TABLE IF NOT EXISTS usage_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    ip TEXT,
    session_id TEXT,
    endpoint TEXT,
    user_plan TEXT,
    served_by TEXT,                   -- 'groq' | 'local' | 'claude' | NULL
    success INTEGER NOT NULL DEFAULT 1,
    error TEXT,
    day TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_usage_log_day ON usage_log (day);

CREATE TABLE IF NOT EXISTS admin_tokens (
    token TEXT PRIMARY KEY,
    label TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def init_db():
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()


def _now():
    return datetime.now().isoformat()


def current_day_key():
    return datetime.now().strftime('%Y-%m-%d')


# ── Settings (emergency stop lives here so all workers see it) ──────────

def get_setting(key, default=None):
    conn = get_conn()
    try:
        row = conn.execute('SELECT value FROM app_settings WHERE key = ?', (key,)).fetchone()
        return row['value'] if row else default
    finally:
        conn.close()


def set_setting(key, value):
    conn = get_conn()
    try:
        conn.execute(
            'INSERT INTO app_settings (key, value) VALUES (?, ?) '
            'ON CONFLICT(key) DO UPDATE SET value = excluded.value',
            (key, str(value)))
    finally:
        conn.close()


def emergency_stop_enabled():
    return get_setting('emergency_stop', '0') == '1'


def set_emergency_stop(enabled):
    set_setting('emergency_stop', '1' if enabled else '0')


# ── Usage counters ──────────────────────────────────────────────────────

def get_count(scope, key, day=None):
    day = day or current_day_key()
    conn = get_conn()
    try:
        row = conn.execute(
            'SELECT count FROM usage_counters WHERE scope = ? AND key = ? AND day = ?',
            (scope, key, day)).fetchone()
        return row['count'] if row else 0
    finally:
        conn.close()


def consume_quota(ip, session_id, ip_limit, session_limit, global_limit):
    """Atomically check all limits and, if allowed, increment all counters.

    Mirrors the original in-memory policy: request is allowed while the
    global cap holds AND (the IP is under its daily limit OR the session
    backup limit still has room — for shared IPs). All three counters are
    read and written inside one immediate transaction so concurrent
    gunicorn workers can't double-spend.

    Returns (allowed: bool, reason: str|None, remaining: int).
    """
    day = current_day_key()
    conn = get_conn()
    try:
        conn.execute('BEGIN IMMEDIATE')
        def count(scope, key):
            row = conn.execute(
                'SELECT count FROM usage_counters WHERE scope = ? AND key = ? AND day = ?',
                (scope, key, day)).fetchone()
            return row['count'] if row else 0

        global_count = count('global', 'global')
        if global_count >= global_limit:
            conn.execute('ROLLBACK')
            return False, 'global_limit_exceeded', 0

        ip_count = count('ip', ip)
        session_count = count('session', session_id)
        if ip_count >= ip_limit and session_count >= session_limit:
            conn.execute('ROLLBACK')
            return False, 'daily_limit_exceeded', 0

        for scope, key in (('ip', ip), ('session', session_id), ('global', 'global')):
            conn.execute(
                'INSERT INTO usage_counters (scope, key, day, count) VALUES (?, ?, ?, 1) '
                'ON CONFLICT(scope, key, day) DO UPDATE SET count = count + 1',
                (scope, key, day))
        conn.execute('COMMIT')
        return True, None, max(ip_limit - (ip_count + 1), 0)
    except Exception:
        try:
            conn.execute('ROLLBACK')
        except sqlite3.OperationalError:
            pass
        raise
    finally:
        conn.close()


def refund_quota(ip, session_id):
    """Give a consumed request back (generation failed before completing)."""
    day = current_day_key()
    conn = get_conn()
    try:
        conn.execute('BEGIN IMMEDIATE')
        for scope, key in (('ip', ip), ('session', session_id), ('global', 'global')):
            conn.execute(
                'UPDATE usage_counters SET count = MAX(count - 1, 0) '
                'WHERE scope = ? AND key = ? AND day = ?',
                (scope, key, day))
        conn.execute('COMMIT')
    except Exception:
        try:
            conn.execute('ROLLBACK')
        except sqlite3.OperationalError:
            pass
        logger.warning('Failed to refund quota for %s/%s', ip, session_id)
    finally:
        conn.close()


def global_usage_by_day():
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT day, count FROM usage_counters WHERE scope = 'global'").fetchall()
        return {row['day']: row['count'] for row in rows}
    finally:
        conn.close()


def unique_ips_for_day(day=None):
    day = day or current_day_key()
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM usage_counters "
            "WHERE scope = 'ip' AND day = ? AND count > 0", (day,)).fetchone()
        return row['n']
    finally:
        conn.close()


# ── Usage log ───────────────────────────────────────────────────────────

def log_usage(ip, session_id, endpoint, user_plan, served_by=None, success=True, error=None):
    conn = get_conn()
    try:
        conn.execute(
            'INSERT INTO usage_log (timestamp, ip, session_id, endpoint, user_plan, '
            'served_by, success, error, day) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (_now(), ip, session_id, endpoint, user_plan, served_by,
             1 if success else 0, error, current_day_key()))
    finally:
        conn.close()


def stamp_served_by(log_id_or_none, ip, session_id, endpoint, served_by):
    """Stamp served_by on the most recent matching log row for this request."""
    conn = get_conn()
    try:
        conn.execute(
            'UPDATE usage_log SET served_by = ? WHERE id = ('
            '  SELECT id FROM usage_log WHERE ip = ? AND session_id = ? AND endpoint = ? '
            '  ORDER BY id DESC LIMIT 1)',
            (served_by, ip, session_id, endpoint))
    finally:
        conn.close()


def recent_logs(limit=50):
    conn = get_conn()
    try:
        rows = conn.execute(
            'SELECT * FROM usage_log ORDER BY id DESC LIMIT ?', (limit,)).fetchall()
        return [dict(row) for row in reversed(rows)]
    finally:
        conn.close()


# ── Access passes ───────────────────────────────────────────────────────

def create_access_pass(pass_type, expires_at, stripe_ref=None,
                       checkout_session_id=None, status='active'):
    """Issue a new access pass; returns the token shown to the customer."""
    token = 'pb_' + secrets.token_urlsafe(18)
    conn = get_conn()
    try:
        conn.execute(
            'INSERT INTO access_passes (token, pass_type, expires_at, stripe_ref, '
            'checkout_session_id, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (token, pass_type,
             expires_at.isoformat() if isinstance(expires_at, datetime) else expires_at,
             stripe_ref, checkout_session_id, status, _now()))
    finally:
        conn.close()
    return token


def get_pass(token):
    conn = get_conn()
    try:
        row = conn.execute(
            'SELECT * FROM access_passes WHERE token = ?', (token,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_pass_by_checkout_session(session_id):
    conn = get_conn()
    try:
        row = conn.execute(
            'SELECT * FROM access_passes WHERE checkout_session_id = ?',
            (session_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def get_pass_by_stripe_ref(stripe_ref):
    conn = get_conn()
    try:
        row = conn.execute(
            'SELECT * FROM access_passes WHERE stripe_ref = ?', (stripe_ref,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def update_pass_by_stripe_ref(stripe_ref, status=None, expires_at=None,
                              cancel_at_period_end=None):
    sets, params = [], []
    if status is not None:
        sets.append('status = ?'); params.append(status)
    if expires_at is not None:
        sets.append('expires_at = ?')
        params.append(expires_at.isoformat() if isinstance(expires_at, datetime) else expires_at)
    if cancel_at_period_end is not None:
        sets.append('cancel_at_period_end = ?'); params.append(1 if cancel_at_period_end else 0)
    if not sets:
        return 0
    params.append(stripe_ref)
    conn = get_conn()
    try:
        cur = conn.execute(
            f"UPDATE access_passes SET {', '.join(sets)} WHERE stripe_ref = ?", params)
        return cur.rowcount
    finally:
        conn.close()


def is_pass_valid(token):
    """A pass grants paid access while active and unexpired."""
    if not token:
        return False
    record = get_pass(token)
    if not record or record['status'] != 'active':
        return False
    if record['expires_at']:
        try:
            if datetime.fromisoformat(record['expires_at']) < datetime.now():
                return False
        except ValueError:
            return False
    return True


# ── Admin tokens ────────────────────────────────────────────────────────

def add_admin_token(token, label=None):
    conn = get_conn()
    try:
        conn.execute(
            'INSERT OR IGNORE INTO admin_tokens (token, label, created_at) VALUES (?, ?, ?)',
            (token, label, _now()))
    finally:
        conn.close()


def is_admin_token(token):
    if not token:
        return False
    conn = get_conn()
    try:
        row = conn.execute(
            'SELECT token FROM admin_tokens WHERE token = ?', (token,)).fetchone()
        return row is not None
    finally:
        conn.close()
