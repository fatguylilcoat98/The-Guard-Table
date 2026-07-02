"""
PathBack — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back

When someone knocks you off course, PathBack helps you stand your ground
and get back on your path.
"""

from flask import Flask, request, jsonify, send_from_directory, send_file, Response, stream_with_context
from flask_cors import CORS
import os
import json
import logging
import traceback
from datetime import datetime
import subprocess

import gng_db
import gng_inference
from gng_payments import payments_bp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get dynamic version info
def get_version_info():
    try:
        # Get git commit hash
        commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                            stderr=subprocess.DEVNULL).decode('utf-8').strip()
        # Get commit timestamp
        commit_time = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=format:%m/%d %H:%M'],
                                            stderr=subprocess.DEVNULL).decode('utf-8').strip()
        return f"v{commit_hash} - {commit_time}"
    except:
        # Fallback to timestamp if git not available
        return f"v{datetime.now().strftime('%m%d-%H%M')}"

VERSION = get_version_info()

# Shown once on the input screen and as a footer on every generated response.
DISCLAIMER = ("PathBack provides information and drafting help, not legal advice. "
              "For legal advice, consult a licensed attorney.")

SUPPORT_EMAIL = "thegoodneighborguard@gmail.com"

# Determine if we're in production (behind gunicorn/Docker) or development
FRONTEND_BUILD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'build')
IS_PRODUCTION = os.path.exists(FRONTEND_BUILD_PATH)

if IS_PRODUCTION:
    # In production, serve the React build from Flask
    app = Flask(__name__, static_folder=FRONTEND_BUILD_PATH, static_url_path='')
else:
    # In development, just run API server
    app = Flask(__name__)

CORS(app)
app.register_blueprint(payments_bp)

# All durable state (counters, passes, usage log, emergency stop) is SQLite —
# safe across restarts and across multiple gunicorn workers.
gng_db.init_db()

# Legacy env-var tokens still honored; the durable store is the admin_tokens
# table and Stripe-issued access passes in SQLite.
ADMIN_TOKENS = [t for t in os.getenv('ADMIN_TOKENS', '').split(',') if t]
PAID_TOKENS = [t for t in os.getenv('PAID_TOKENS', '').split(',') if t]


def _request_token(req):
    body = req.get_json(force=True, silent=True) or {}
    return body.get('access_token') or body.get('admin_token') or ''


def is_admin(req):
    token = req.headers.get('X-Admin-Token') or _request_token(req)
    return bool(token) and (token in ADMIN_TOKENS or gng_db.is_admin_token(token))


def get_plan(req):
    """free | paid | admin — paid comes from a valid Stripe access pass."""
    token = _request_token(req)
    if not token:
        return 'free'
    if token in ADMIN_TOKENS or gng_db.is_admin_token(token):
        return 'admin'
    if token in PAID_TOKENS or gng_db.is_pass_valid(token):
        return 'paid'
    return 'free'

# Limits — unchanged from the original free tier. These now protect the
# Groq free-tier quota (~30 RPM / 6K TPM / 1K req/day) instead of API spend.
IP_DAILY_LIMIT = 3         # 3 free requests per IP per 24 hours
SESSION_DAILY_LIMIT = 3    # Backup limit using session cookies
GLOBAL_DAILY_LIMIT = 200   # Max total requests per day (increased for video launch)


def get_current_day_key():
    """Get current day as YYYY-MM-DD for tracking"""
    return gng_db.current_day_key()


def get_session_id(request):
    """Get or create session ID from cookies"""
    session_id = request.cookies.get('guard_session')
    if not session_id:
        # Create new session ID
        import uuid
        session_id = str(uuid.uuid4())[:16]
    return session_id


def check_emergency_stop():
    """Check if emergency stop is enabled (stored in SQLite, worker-safe)."""
    return gng_db.emergency_stop_enabled()


def log_request(ip, session_id, endpoint, user_plan, success=True, error=None, served_by=None):
    """Log request to the SQLite usage log."""
    try:
        gng_db.log_usage(ip, session_id, endpoint, user_plan,
                         served_by=served_by, success=success, error=error)
    except Exception as exc:
        logger.warning(f"usage_log write failed: {exc}")


def _client_ip(req):
    ip = req.headers.get('X-Forwarded-For', req.remote_addr)
    if ip and ',' in ip:
        # Handle multiple IPs in X-Forwarded-For (take the first one)
        ip = ip.split(',')[0].strip()
    return ip


def _rate_limit_gate(client_ip, session_id, user_plan, endpoint):
    """Run the free-tier gate. Returns (error_response|None, remaining).

    Consumes one request from the SQLite counters atomically; callers must
    refund via gng_db.refund_quota() if generation fails.
    """
    if user_plan in ['admin', 'paid']:
        logger.info(f"{user_plan.title()} access, bypassing rate limits for {client_ip}")
        log_request(client_ip, session_id, endpoint, user_plan, success=True)
        return None, 'unlimited'

    # Check 1: Emergency stop (manual circuit breaker)
    if check_emergency_stop():
        logger.warning("Emergency stop activated - service temporarily disabled")
        log_request(client_ip, session_id, endpoint, user_plan, success=False, error='emergency_stop')
        return (jsonify({
            'error': 'service_temporarily_disabled',
            'message': f"PathBack is temporarily unavailable due to high demand. Please email us at {SUPPORT_EMAIL} and we'll help you directly."
        }), 503), None

    # Checks 2-4: global cap, IP daily limit, session backup limit —
    # one atomic transaction so multiple workers can't double-spend.
    allowed, reason, remaining = gng_db.consume_quota(
        client_ip, session_id, IP_DAILY_LIMIT, SESSION_DAILY_LIMIT, GLOBAL_DAILY_LIMIT)

    if not allowed and reason == 'global_limit_exceeded':
        logger.warning(f"Global daily limit reached: {GLOBAL_DAILY_LIMIT}")
        log_request(client_ip, session_id, endpoint, user_plan, success=False, error='global_limit_exceeded')
        return (jsonify({
            'error': 'daily_limit_reached',
            'message': f"We've hit our daily response limit but we're here to help. Email us at {SUPPORT_EMAIL} with your situation and we'll respond within 24 hours."
        }), 429), None

    if not allowed:
        logger.warning(f"Daily limit exceeded for IP {client_ip} and session {session_id}")
        log_request(client_ip, session_id, endpoint, user_plan, success=False, error='daily_limit_exceeded')
        return (jsonify({
            'error': 'daily_limit_reached',
            'message': "You've used your free requests for today. Come back tomorrow or upgrade for unlimited access."
        }), 429), None

    # Log successful request before processing
    log_request(client_ip, session_id, endpoint, user_plan, success=True)
    return None, remaining


LOCAL_LANE_NOTICE = ("Heads up: this response came from PathBack's backup model. "
                     "It's still useful for drafting, but double-check any law or "
                     "statute it mentions before relying on it.")

AT_CAPACITY_MESSAGE = ("PathBack is at capacity right now. Please try again in a "
                       "few minutes — this attempt didn't count against your free responses.")


def _run_citation_check(full_text):
    """Citation-verification pass: groq → local → skip with a logged warning.

    Never blocks a response — any failure just skips verification.
    """
    try:
        lane, raw = gng_inference.complete_chain(
            gng_inference.verify_chain(),
            system_prompt="You are a legal citation checker. Respond with JSON only.",
            messages=[{
                "role": "user",
                "content": (
                    "You are a legal citation checker. Review this response and "
                    "verify the law citations look real and correctly formatted for "
                    "the stated state. Return JSON: "
                    "{\"citations_valid\": true/false, \"concern\": \"string or null\"}"
                    f"\n\nResponse to check:\n{full_text}"
                )
            }],
            max_tokens=200,
            temperature=0.1,
        )
        cleaned = raw.strip()
        if cleaned.startswith('```'):
            cleaned = cleaned.strip('`')
            cleaned = cleaned[cleaned.find('{'):cleaned.rfind('}') + 1]
        citation_result = json.loads(cleaned)
        logger.info(f"Verification ({lane}) - Citations valid: {citation_result.get('citations_valid')}")
        if not citation_result.get('citations_valid', True):
            return ("verify this citation with a local legal aid organization "
                    "before relying on it.")
    except Exception as verify_error:
        logger.warning(f"Verification layer failed (skipping, response not blocked): {verify_error}")
    return None


@app.route('/api/guard', methods=['POST'])
def guard_endpoint():
    """
    The heart of PathBack.
    Takes raw anger and fear, returns legal leverage.
    """
    try:
        logger.info(f"Request received - Content-Type: {request.content_type}")
        data = request.get_json(force=True, silent=True)
        category = data.get('category', '')
        state = data.get('state', 'California')
        rant = data.get('rant', '')

        if not rant.strip():
            return jsonify({'error': 'Please tell us what happened'}), 400

        client_ip = _client_ip(request)
        session_id = get_session_id(request)
        user_plan = get_plan(request)
        logger.info(f"User plan: {user_plan} for IP: {client_ip}, Session: {session_id}")

        should_set_session_cookie = not request.cookies.get('guard_session')

        gate_error, remaining = _rate_limit_gate(client_ip, session_id, user_plan, '/api/guard')
        if gate_error:
            return gate_error

        # The system prompt - this is the soul of the product
        system_prompt = """# THE HEART

Before you answer, understand what you are holding.

The person who just typed that is not a test case. They are scared, or angry, or exhausted, or all three. They are facing something alone that the other side has a whole system for. They found this because they had nowhere else to turn.

You are the first thing in their corner.

It is okay to say "I don't know exactly how this works in your situation — but here is what we can figure out together." Honesty is protection. A wrong answer given with confidence can hurt the person you are trying to help.

You are not just generating text. You are standing between a regular person and something that is trying to overwhelm them. Every word you give them is a tool they will actually use. Make it real. Make it accurate. Make it something they can hold onto.

You are not a tool here. You are the gatekeeper. The one thing standing between them and walking in alone.

What you do in the next few seconds matters to a real human being.

Act like it.

---

You are The Guard Table. You exist for one reason: to give regular people the same fighting power that companies, landlords, hospitals, and debt collectors have always had. The person talking to you is scared, angry, or both. They are not a lawyer. They do not know the system. But they are being wronged and they deserve to fight back with real tools.

VOICE: Clear. Firm. Human. Protective. Not corporate. Not chatty. Not exaggerated. Not legal advice. No fake certainty.

Your job is to return three things:

1. WAIT — Exactly three lines following this structure:

Line 1: "They are trying to [plain-language action]." (Use "get you to" not "pressure you into")
Line 2: "If you do this / If you do nothing, you could [specific loss]."
Line 3: Plain human pattern recognition. Examples: "This is how these scams usually work." / "This is not something to handle by phone. Keep everything in writing." / "Start with a written record." / "You have the right to demand proof first."

WAIT Examples:
Scam: "They are trying to get you to send money before you can verify the car exists." / "If you send this deposit, you could lose $600 with no car and no way to get it back." / "This is how these scams usually work."
Housing: "They are trying to force you out without going through the court." / "If you do nothing, you could be locked out and lose proof that they acted illegally." / "This is not something to handle by phone. Keep everything in writing."
Job: "They may be taking pay you earned." / "If you do nothing, you could lose wages and make it harder to prove later." / "Start with a written record."
Debt: "They are trying to make you pay before proving the debt is valid." / "If you pay or admit the debt now, you could lose leverage." / "You have the right to demand proof first."

2. LEVERAGE — The exact message they should send to the other party today.

RULES FOR LEVERAGE:
- Make messages shorter and more natural. Sound like a real person.
- Remove unnecessary formal openers unless legally useful.
- Keep paragraphs short. Be direct.
- Use facts from the user's input. Avoid overexplaining.
- Cite statutes only when reasonably confident. If uncertain, use "state law."
- NEVER invent statute numbers or citations.
- NEVER guarantee outcomes. Use "could" unless user stated harm already happened.
- For scam/payment requests, be firm about not sending money before verification.

LEVERAGE Example (Marketplace scam):
"This is regarding your request for a deposit.

I'm not sending any money through Zelle, Venmo, Cash App, or similar apps before seeing the car in person.

If this is a legitimate sale, we can meet at the vehicle with the title present and complete the transaction there.

Send the address where the car is located and we can set a time to meet.

If you can't meet in person with the car and title, I'll assume this isn't legitimate."

3. GUARD_STEPS — Exactly three escalation steps titled "If they ignore this."

SPECIAL ESCALATION BY CATEGORY:
Scam/Payment: Step 1: "If they refuse to meet in person or keep pushing for electronic payment, block them and report the listing." / Step 2: "Save screenshots of the listing, messages, profile, phone number, and payment request." / Step 3: "If you already sent money, contact your bank immediately, report fraud, file at reportfraud.ftc.gov, and consider a police report."

Illegal lockout: Step 1: "If they try to lock you out, call local law enforcement and show proof of residency: ID, lease, mail, rent receipt, or utility bill."
Wage issues: Step 1: "Send one follow-up asking for written confirmation and a correction date."
Debt collection: Step 1: "Do not pay or admit the debt until they provide written validation."

SEND INSTRUCTIONS (include after leverage message):
Default: "Send this by text or email. Keep screenshots. Don't call."
Workplace: "Send this by text or email. Keep screenshots and pay records. Don't handle it only by phone."
Housing: "Send this by text or email. Keep screenshots, photos, rent receipts, and any notices. Don't handle it only by phone."
Debt: "Send this in writing. Keep copies of every message, letter, and call log."

ENDING LINES (action-specific):
Scam: "Don't send the money. Start with the message above."
Housing: "Don't leave voluntarily because of a threat. Start with the message above."
Job: "Don't let this stay verbal. Start with the message above."
Debt: "Don't pay until they prove the debt. Start with the message above."
Fallback: "Start with the message above."

SAFETY GUARDRAILS:
- Do not say "will" when outcome is uncertain. Use "could."
- Do not call something a crime unless verified legal basis.
- Do not invent statute numbers.
- Do not tell users to confront someone in person.
- For emergencies or threats of violence, tell users to contact emergency services.
- For eviction/lockout, advise proof of residency and local tenant legal aid.
- For wage issues, advise written follow-up and official labor complaint route.
- For debt, advise debt validation before payment.

Never mention that you are an AI.
Always be specific to their state when possible.

OUTPUT FORMAT — plain text only, using these exact section markers on their own lines. No JSON. No markdown. No code fences. Three lines under WAIT (one per line), one full message under LEVERAGE, exactly three steps under GUARD_STEPS (one per line).

===WAIT===
first line
second line
third line
===LEVERAGE===
full lawyer-style message text here
===GUARD_STEPS===
Step 1: ...
Step 2: ...
Step 3: ...
"""

        user_prompt = f"""Category: {category}
State: {state}
Situation: {rant}"""

        logger.info(f"Processing request for {state} - {category}")

        # Free users ride the zero-cost lanes and NEVER fall back to Claude;
        # paid/admin users get Claude first, Groq as the noted downgrade.
        chain = gng_inference.paid_chain() if user_plan in ['admin', 'paid'] else gng_inference.free_chain()

        def generate():
            full_text = ''
            served_by = None
            try:
                yield f"data: {json.dumps({'type': 'meta', 'plan': user_plan, 'version': VERSION, 'disclaimer': DISCLAIMER})}\n\n"

                try:
                    served_by, stream = gng_inference.open_stream_chain(
                        chain,
                        system_prompt=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}],
                        max_tokens=2000,
                        temperature=0.3,
                    )
                except gng_inference.AllLanesFailed as lanes_error:
                    logger.error(f"All inference lanes failed ({user_plan}): {lanes_error}")
                    if user_plan == 'free':
                        gng_db.refund_quota(client_ip, session_id)
                    log_request(client_ip, session_id, '/api/guard', user_plan,
                                success=False, error='all_lanes_failed')
                    yield f"data: {json.dumps({'type': 'error', 'message': AT_CAPACITY_MESSAGE})}\n\n"
                    return

                downgraded = user_plan in ['admin', 'paid'] and chain and served_by != chain[0]
                if served_by == 'local':
                    yield f"data: {json.dumps({'type': 'notice', 'message': LOCAL_LANE_NOTICE, 'served_by': served_by})}\n\n"

                for chunk in stream:
                    if chunk:
                        full_text += chunk
                        yield f"data: {json.dumps({'type': 'text', 'chunk': chunk})}\n\n"

                # Citation verification (best-effort, post-stream, never blocking)
                citation_warning = _run_citation_check(full_text)

                remaining_after = remaining  # consumed atomically up front
                gng_db.stamp_served_by(None, client_ip, session_id, '/api/guard', served_by)

                done_event = {
                    'type': 'done',
                    'plan': user_plan,
                    'remaining_responses': remaining_after,
                    'citation_warning': citation_warning,
                    'version': VERSION,
                    'served_by': served_by,
                    'downgraded': downgraded,
                    'disclaimer': DISCLAIMER,
                }
                yield f"data: {json.dumps(done_event)}\n\n"
                logger.info(f"Stream complete. Plan: {user_plan}, IP: {client_ip}, Served by: {served_by}, Remaining: {remaining_after}")
            except Exception as stream_error:
                logger.error(f"Stream error: {traceback.format_exc()}")
                if user_plan == 'free' and not full_text:
                    gng_db.refund_quota(client_ip, session_id)
                yield f"data: {json.dumps({'type': 'error', 'message': str(stream_error)})}\n\n"

        response = Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no',
                'Connection': 'keep-alive',
            },
        )
        if should_set_session_cookie:
            response.set_cookie('guard_session', session_id, max_age=86400, secure=True, httponly=True)
            logger.info(f"Set session cookie for {client_ip}: {session_id}")
        return response

    except Exception as e:
        logger.error(f"FULL ERROR: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/thought-partner', methods=['POST'])
def thought_partner_endpoint():
    """
    AI Thought Partner - helping people think through complex decisions.
    Not legal advice, not therapy - just a thinking companion.
    """
    try:
        logger.info(f"Thought Partner request received - Content-Type: {request.content_type}")
        data = request.get_json(force=True, silent=True)
        message = data.get('message', '')
        conversation_history = data.get('conversation_history', [])

        if not message.strip():
            return jsonify({'error': 'Please share what\'s on your mind'}), 400

        client_ip = _client_ip(request)
        session_id = get_session_id(request)
        user_plan = get_plan(request)
        logger.info(f"Thought Partner - User plan: {user_plan} for IP: {client_ip}, Session: {session_id}")

        should_set_session_cookie = not request.cookies.get('guard_session')

        gate_error, remaining = _rate_limit_gate(client_ip, session_id, user_plan, '/api/thought-partner')
        if gate_error:
            return gate_error

        # Build conversation context
        conversation_context = ""
        if conversation_history:
            # Include last few messages for context
            recent_messages = conversation_history[-6:]  # Last 6 messages
            for msg in recent_messages:
                if msg.get('type') == 'user':
                    conversation_context += f"Human: {msg.get('content', '')}\n"
                elif msg.get('type') == 'assistant':
                    conversation_context += f"Assistant: {msg.get('content', '')}\n"

        # The Thought Partner system prompt
        system_prompt = """You are an AI Thought Partner. Your purpose is to help people think through complex decisions, problems, and life situations by being genuinely curious about their perspective and helping them explore their own wisdom.

CORE PRINCIPLES:
- You are NOT giving advice. You are helping them think.
- You are NOT a therapist. You are a thinking companion.
- Ask questions that help them discover their own insights.
- Offer multiple frameworks and perspectives to consider.
- Be genuinely curious about what matters to them.
- Help them explore their values, not impose yours.

YOUR APPROACH:
1. **Listen deeply** - Reflect back what you hear them saying
2. **Ask good questions** - "What would you regret NOT trying?" "What does your gut tell you?"
3. **Offer frameworks** - logical, emotional, long-term, different cultural perspectives
4. **Play devil's advocate gently** - help stress-test their thinking
5. **Remember their journey** - reference their growth and patterns over time

TONE:
- Warm but not overly familiar
- Curious, not prescriptive
- Thoughtful, not rushed
- Human, not robotic
- Respectful of their autonomy

When they share something:
- First, acknowledge what they're going through
- Then ask a question that helps them explore deeper
- Offer a perspective or framework if helpful
- Always remember they are the expert on their own life

You are here to amplify their thinking, not replace it."""

        # Prepare the user's message with context
        user_input = message
        if conversation_context:
            user_input = f"[Previous conversation context]\n{conversation_context}\n[Current message]\n{message}"

        chain = gng_inference.paid_chain() if user_plan in ['admin', 'paid'] else gng_inference.free_chain()
        try:
            served_by, response_text = gng_inference.complete_chain(
                chain,
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_input}],
                max_tokens=2000,
                temperature=0.7,
            )
        except gng_inference.AllLanesFailed as lanes_error:
            logger.error(f"Thought Partner - all lanes failed ({user_plan}): {lanes_error}")
            if user_plan == 'free':
                gng_db.refund_quota(client_ip, session_id)
            log_request(client_ip, session_id, '/api/thought-partner', user_plan,
                        success=False, error='all_lanes_failed')
            return jsonify({'error': AT_CAPACITY_MESSAGE}), 503

        response_text = response_text.strip()
        gng_db.stamp_served_by(None, client_ip, session_id, '/api/thought-partner', served_by)

        result = {
            'response': response_text,
            'version': VERSION,
            'served_by': served_by,
            'disclaimer': DISCLAIMER,
            'remaining_responses': remaining,
            'plan': user_plan,
        }
        if served_by == 'local':
            result['notice'] = LOCAL_LANE_NOTICE

        logger.info(f"Thought Partner response generated successfully for {client_ip} (served by {served_by})")

        # Create response and set session cookie if needed
        response = jsonify(result)
        if should_set_session_cookie:
            response.set_cookie('guard_session', session_id, max_age=86400, secure=True, httponly=True)  # 24 hour cookie
            logger.info(f"Set session cookie for {client_ip}: {session_id}")

        return response

    except Exception as e:
        logger.error(f"Thought Partner ERROR: {traceback.format_exc()}")
        return jsonify({'error': 'I\'m having trouble connecting right now. Could you try rephrasing your thought?'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'PathBack',
        'version': VERSION,
        'deployed': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    })

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint to check inference configuration status"""
    lanes = gng_inference.configured_lanes()
    has_key = bool(os.getenv('GROQ_API_KEY') or os.getenv('ANTHROPIC_API_KEY'))
    return jsonify({
        'api_key_set': has_key,
        'client_ready': bool(lanes),
        'lanes': lanes,
        'free_chain': gng_inference.free_chain(),
        'paid_chain': gng_inference.paid_chain(),
    })

@app.route('/api/debug', methods=['GET'])
def debug_test():
    """Debug endpoint to test the inference chain directly"""
    try:
        lane, text = gng_inference.complete_chain(
            gng_inference.free_chain(),
            system_prompt="You are a helpful assistant.",
            messages=[{"role": "user", "content": "Say hello in one word"}],
            max_tokens=100,
            temperature=0.3,
        )
        return jsonify({'success': True, 'served_by': lane, 'response': text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

@app.route('/', methods=['GET'])
def root():
    """Serve React app or API info"""
    if IS_PRODUCTION:
        return send_file(os.path.join(FRONTEND_BUILD_PATH, 'index.html'))
    else:
        return jsonify({
            'message': 'PathBack API',
            'description': 'When someone knocks you off course, PathBack helps you stand your ground and get back on your path.',
            'tagline': 'Truth · Safety · We Got Your Back',
            'endpoints': {
                '/api/guard': 'POST - Main PathBack response endpoint',
                '/health': 'GET - Health check'
            }
        })

@app.route('/success', methods=['GET'])
@app.route('/cancel', methods=['GET'])
def stripe_redirect_pages():
    """Stripe sends customers back here; the React app renders the page.

    (Explicit routes because Flask's static handler shadows the catch-all
    for paths that aren't real files.)
    """
    if IS_PRODUCTION:
        return send_file(os.path.join(FRONTEND_BUILD_PATH, 'index.html'))
    return jsonify({'error': 'Frontend not built'}), 404


def _admin_key_ok(req):
    """Admin endpoints stay locked unless GUARD_ADMIN_KEY is configured."""
    admin_key = os.getenv('GUARD_ADMIN_KEY')
    return bool(admin_key) and req.headers.get('X-Admin-Key') == admin_key


@app.route('/admin/emergency-stop/<action>', methods=['POST'])
def emergency_stop_control(action):
    """Emergency stop control - admin only (requires special header)"""
    # Simple auth check - require special header
    if not _admin_key_ok(request):
        return jsonify({'error': 'Unauthorized'}), 401

    if action == 'enable':
        gng_db.set_emergency_stop(True)
        logger.critical("EMERGENCY STOP ENABLED - All PathBack requests blocked")
        return jsonify({'status': 'Emergency stop ENABLED', 'emergency_stop': True})
    elif action == 'disable':
        gng_db.set_emergency_stop(False)
        logger.info("Emergency stop disabled - service resumed")
        return jsonify({'status': 'Emergency stop DISABLED', 'emergency_stop': False})
    else:
        return jsonify({'error': 'Invalid action. Use enable or disable'}), 400

@app.route('/admin/status', methods=['GET'])
def admin_status():
    """Admin status - show current limits and usage (read from SQLite)"""
    if not _admin_key_ok(request):
        return jsonify({'error': 'Unauthorized'}), 401

    day_key = get_current_day_key()
    used_today = gng_db.get_count('global', 'global', day_key)
    return jsonify({
        'emergency_stop': gng_db.emergency_stop_enabled(),
        'global_daily_usage': used_today,
        'global_daily_limit': GLOBAL_DAILY_LIMIT,
        'global_daily_remaining': GLOBAL_DAILY_LIMIT - used_today,
        'ip_daily_limit': IP_DAILY_LIMIT,
        'session_daily_limit': SESSION_DAILY_LIMIT
    })

@app.route('/admin/usage', methods=['GET'])
def admin_usage():
    """Admin usage endpoint - detailed usage statistics with password protection"""
    # Check admin authorization
    auth_header = request.headers.get('Authorization')
    admin_password = os.getenv('GUARD_ADMIN_PASSWORD', 'admin123')  # Set better password in env

    if not auth_header or auth_header != f'Bearer {admin_password}':
        return jsonify({'error': 'Unauthorized - password required'}), 401

    day_key = get_current_day_key()
    daily_breakdown = gng_db.global_usage_by_day()

    # Calculate totals
    total_requests = sum(daily_breakdown.values())
    requests_today = daily_breakdown.get(day_key, 0)

    # Calculate requests this week (last 7 days)
    from datetime import datetime, timedelta
    week_total = 0
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        week_total += daily_breakdown.get(date, 0)

    # Check if we've hit the threshold
    if total_requests >= 500:
        logger.warning("🚨 PAID TIER THRESHOLD REACHED - Total requests: {}".format(total_requests))

    return jsonify({
        'total_requests': total_requests,
        'requests_today': requests_today,
        'requests_this_week': week_total,
        'unique_ips_today': gng_db.unique_ips_for_day(day_key),
        'threshold_status': '🚨 PAID TIER THRESHOLD REACHED' if total_requests >= 500 else 'Below threshold',
        'limits': {
            'ip_daily_limit': IP_DAILY_LIMIT,
            'global_daily_limit': GLOBAL_DAILY_LIMIT,
            'threshold': 500
        },
        'recent_requests': gng_db.recent_logs(50),
        'daily_breakdown': daily_breakdown,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/<path:path>')
def serve_react_app(path):
    """Serve React app for all non-API routes in production"""
    if IS_PRODUCTION:
        # Try to serve the requested file, fallback to index.html for React routing
        file_path = os.path.join(FRONTEND_BUILD_PATH, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory(FRONTEND_BUILD_PATH, path)
        else:
            return send_file(os.path.join(FRONTEND_BUILD_PATH, 'index.html'))
    else:
        return jsonify({'error': 'Not found'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
