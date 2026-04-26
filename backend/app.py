"""
The Guard Table — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from collections import defaultdict
import os
import anthropic
import httpx
import json
import logging
import traceback
from datetime import datetime
import subprocess

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

# Determine if we're in production (Render) or development
FRONTEND_BUILD_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'build')
IS_PRODUCTION = os.path.exists(FRONTEND_BUILD_PATH)

if IS_PRODUCTION:
    # In production, serve the React build from Flask
    app = Flask(__name__, static_folder=FRONTEND_BUILD_PATH, static_url_path='')
else:
    # In development, just run API server
    app = Flask(__name__)

CORS(app)

# Initialize Anthropic client
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
if not anthropic_api_key:
    logger.error("ANTHROPIC_API_KEY environment variable not set")

client = None
if anthropic_api_key:
    try:
        client = anthropic.Anthropic(
            api_key=anthropic_api_key,
            http_client=httpx.Client()
        )
        logger.info("Anthropic client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Anthropic client: {str(e)}")
        client = None

# Admin token system
ADMIN_TOKENS = os.getenv('ADMIN_TOKENS', '').split(',')
PAID_TOKENS = os.getenv('PAID_TOKENS', '').split(',')

def is_admin(request):
    token = request.headers.get('X-Admin-Token') or (request.json.get('admin_token', '') if request.is_json else '')
    return token in ADMIN_TOKENS and token != ''

def get_plan(request):
    token_data = request.get_json(force=True, silent=True) or {}
    admin_token = token_data.get('admin_token', '')
    if admin_token in PAID_TOKENS and admin_token != '':
        return 'paid'
    if admin_token in ADMIN_TOKENS and admin_token != '':
        return 'admin'
    return 'free'

# Rate limiting: Multiple layers of protection
# Format: ip_daily_usage[ip][day_key] = count
# Format: session_usage[session_id][day_key] = count
# Format: global_daily_usage[day_key] = count
ip_daily_usage = defaultdict(lambda: defaultdict(int))
session_usage = defaultdict(lambda: defaultdict(int))
global_daily_usage = defaultdict(int)
request_log = []  # Store all requests for monitoring

# Limits
IP_DAILY_LIMIT = 3         # 3 free requests per IP per 24 hours
SESSION_DAILY_LIMIT = 3    # Backup limit using session cookies
GLOBAL_DAILY_LIMIT = 200   # Max total requests per day (increased for video launch)
EMERGENCY_STOP = False     # Manual circuit breaker

def get_current_day_key():
    """Get current day as YYYY-MM-DD for tracking"""
    return datetime.now().strftime("%Y-%m-%d")

def get_session_id(request):
    """Get or create session ID from cookies"""
    session_id = request.cookies.get('guard_session')
    if not session_id:
        # Create new session ID
        import uuid
        session_id = str(uuid.uuid4())[:16]
    return session_id

def check_emergency_stop():
    """Check if emergency stop is enabled"""
    global EMERGENCY_STOP
    return EMERGENCY_STOP

def check_global_daily_limit():
    """Check if global daily limit exceeded. Returns (allowed, remaining)"""
    day_key = get_current_day_key()
    current_usage = global_daily_usage[day_key]

    if current_usage >= GLOBAL_DAILY_LIMIT:
        return False, 0

    return True, GLOBAL_DAILY_LIMIT - current_usage

def check_ip_daily_limit(ip):
    """Check if IP has exceeded daily limit. Returns (allowed, remaining)"""
    day_key = get_current_day_key()
    current_usage = ip_daily_usage[ip][day_key]

    if current_usage >= IP_DAILY_LIMIT:
        return False, 0

    return True, IP_DAILY_LIMIT - current_usage

def check_session_daily_limit(session_id):
    """Check if session has exceeded daily limit. Returns (allowed, remaining)"""
    day_key = get_current_day_key()
    current_usage = session_usage[session_id][day_key]

    if current_usage >= SESSION_DAILY_LIMIT:
        return False, 0

    return True, SESSION_DAILY_LIMIT - current_usage

def log_request(ip, session_id, endpoint, user_plan, success=True, error=None):
    """Log request for monitoring"""
    global request_log

    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'ip': ip,
        'session_id': session_id,
        'endpoint': endpoint,
        'user_plan': user_plan,
        'success': success,
        'error': error,
        'day': get_current_day_key()
    }

    request_log.append(log_entry)

    # Keep only last 1000 requests to prevent memory issues
    if len(request_log) > 1000:
        request_log = request_log[-1000:]

def increment_usage(ip, session_id):
    """Increment usage counters for IP, session, and global daily"""
    day_key = get_current_day_key()

    # Update all counters
    ip_daily_usage[ip][day_key] += 1
    session_usage[session_id][day_key] += 1
    global_daily_usage[day_key] += 1

    return IP_DAILY_LIMIT - ip_daily_usage[ip][day_key]

@app.route('/api/guard', methods=['POST'])
def guard_endpoint():
    """
    The heart of The Guard Table.
    Takes raw anger and fear, returns legal leverage.
    """
    try:
        logger.info(f"Request received - Content-Type: {request.content_type}")
        logger.info(f"Raw data: {request.get_data(as_text=True)[:200]}")
        data = request.get_json(force=True, silent=True)
        logger.info(f"Parsed data: {data}")
        category = data.get('category', '')
        state = data.get('state', 'California')
        rant = data.get('rant', '')

        if not rant.strip():
            return jsonify({'error': 'Please tell us what happened'}), 400

        # Multi-layer rate limiting checks
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            # Handle multiple IPs in X-Forwarded-For (take the first one)
            client_ip = client_ip.split(',')[0].strip()

        # Get session ID for backup rate limiting
        session_id = get_session_id(request)

        # Plan detection and rate limiting
        user_plan = get_plan(request)
        logger.info(f"User plan: {user_plan} for IP: {client_ip}, Session: {session_id}")

        # Initialize response for session cookie
        response_data = {}
        should_set_session_cookie = not request.cookies.get('guard_session')

        if user_plan in ['admin', 'paid']:
            logger.info(f"{user_plan.title()} access, bypassing rate limits for {client_ip}")
            log_request(client_ip, session_id, '/api/guard', user_plan, success=True)
        else:
            # Check 1: Emergency stop (manual circuit breaker)
            if check_emergency_stop():
                logger.warning("Emergency stop activated - service temporarily disabled")
                log_request(client_ip, session_id, '/api/guard', user_plan, success=False, error='emergency_stop')
                return jsonify({
                    'error': 'service_temporarily_disabled',
                    'message': "The Guard Table is temporarily unavailable due to high demand. Please email us at thegoodneighborguard@gmail.com and we'll help you directly."
                }), 503

            # Check 2: Global daily limit (protect against viral traffic)
            global_allowed, global_remaining = check_global_daily_limit()
            if not global_allowed:
                logger.warning(f"Global daily limit reached: {GLOBAL_DAILY_LIMIT}")
                log_request(client_ip, session_id, '/api/guard', user_plan, success=False, error='global_limit_exceeded')
                return jsonify({
                    'error': 'daily_limit_reached',
                    'message': "We've hit our daily response limit but we're here to help. Email us at thegoodneighborguard@gmail.com with your situation and we'll respond within 24 hours."
                }), 429

            # Check 3: IP daily limit (3 free requests per day per IP)
            ip_allowed, ip_remaining = check_ip_daily_limit(client_ip)
            if not ip_allowed:
                # Check 4: Session backup limit (in case of shared IP)
                session_allowed, session_remaining = check_session_daily_limit(session_id)
                if not session_allowed:
                    logger.warning(f"Daily limit exceeded for IP {client_ip} and session {session_id}")
                    log_request(client_ip, session_id, '/api/guard', user_plan, success=False, error='daily_limit_exceeded')
                    return jsonify({
                        'error': 'daily_limit_reached',
                        'message': "You've used your free requests for today. Come back tomorrow or upgrade for unlimited access."
                    }), 429
                else:
                    # IP limit exceeded but session still has requests
                    logger.info(f"IP {client_ip} exceeded limit, using session {session_id} backup ({session_remaining} remaining)")

            # Log successful request before processing
            log_request(client_ip, session_id, '/api/guard', user_plan, success=True)

        if not client:
            return jsonify({'error': 'Service temporarily unavailable'}), 503

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

Return as clean JSON only:

CRITICAL: Return raw JSON only. No markdown. No code fences. No backticks. Just the JSON object starting with { and ending with }.

{
  "wait": ["line1", "line2", "line3"],
  "leverage": "full message text",
  "guard_steps": ["step1", "step2", "step3"]
}"""

        user_prompt = f"""Category: {category}
State: {state}
Situation: {rant}"""

        logger.info(f"Processing request for {state} - {category}")

        # Call Claude API with prompt caching
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0.3,
            system=[{
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}
            }],
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        # Strip markdown code fences if present
        response_text = response.content[0].text.strip()
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()

        # Parse JSON response
        try:
            result = json.loads(response_text)

            # Two-model verification layer with Haiku 4.5
            try:
                # Verification 1: Check law citations
                citation_check = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=200,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": f"You are a legal citation checker. Review this response and verify the law citations look real and correctly formatted for the stated state. Return JSON: {{\"citations_valid\": true/false, \"concern\": \"string or null\"}}\n\nResponse to check:\n{response_text}"
                    }]
                )

                # Verification 2: Check for hedging language
                hedge_check = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=200,
                    temperature=0.1,
                    messages=[{
                        "role": "user",
                        "content": f"Review this response for hedge words: might, may, could, possibly, perhaps. Return JSON: {{\"hedge_free\": true/false, \"flagged_words\": []}}\n\nResponse to check:\n{response_text}"
                    }]
                )

                # Parse verification results
                citation_result = json.loads(citation_check.content[0].text.strip())
                hedge_result = json.loads(hedge_check.content[0].text.strip())

                # Add citation warning if invalid
                if not citation_result.get('citations_valid', True):
                    if 'leverage' in result:
                        result['leverage'] += "\n\nNote: verify this citation with a local legal aid organization before relying on it."

                logger.info(f"Verification - Citations valid: {citation_result.get('citations_valid')}, Hedge-free: {hedge_result.get('hedge_free')}")

            except Exception as verify_error:
                logger.warning(f"Verification layer failed: {str(verify_error)}")
                # Continue without verification if it fails

            # Increment usage and add remaining count (only for free users)
            if user_plan == 'free':
                remaining_after = increment_usage(client_ip, session_id)
                result['remaining_responses'] = remaining_after
            else:
                result['remaining_responses'] = 'unlimited'

            # Add plan and version information to response
            result['plan'] = user_plan
            result['version'] = VERSION

            logger.info(f"Successfully generated response. Plan: {user_plan}, Remaining for {client_ip}: {result['remaining_responses']}")

            # Create response and set session cookie if needed
            response = jsonify(result)
            if should_set_session_cookie:
                response.set_cookie('guard_session', session_id, max_age=86400, secure=True, httponly=True)  # 24 hour cookie
                logger.info(f"Set session cookie for {client_ip}: {session_id}")

            return response
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}")
            return jsonify({'error': 'Something went wrong — try again'}), 500

    except Exception as e:
        import traceback
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

        # Rate limiting (same as guard endpoint but separate counters)
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()

        user_plan = get_plan(request)
        logger.info(f"Thought Partner - User plan: {user_plan} for {client_ip}")

        if not client:
            return jsonify({'error': 'Service temporarily unavailable'}), 503

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

        # Call Claude
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_input
            }]
        )

        response_text = response.content[0].text.strip()

        logger.info(f"Thought Partner response generated successfully for {client_ip}")

        return jsonify({
            'response': response_text,
            'version': VERSION
        })

    except Exception as e:
        import traceback
        logger.error(f"Thought Partner ERROR: {traceback.format_exc()}")
        return jsonify({'error': 'I\'m having trouble connecting right now. Could you try rephrasing your thought?'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'The Guard Table',
        'version': VERSION,
        'deployed': datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    })

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint to check API key and client status"""
    return jsonify({
        'api_key_set': bool(anthropic_api_key),
        'client_ready': bool(client),
        'key_preview': anthropic_api_key[:8] + '...' if anthropic_api_key else 'NOT SET'
    })

@app.route('/api/debug', methods=['GET'])
def debug_test():
    """Debug endpoint to test Claude API call directly"""
    try:
        if not client:
            return jsonify({'success': False, 'error': 'Claude client not initialized'})

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=100,
            messages=[{"role": "user", "content": "Say hello in one word"}]
        )
        return jsonify({'success': True, 'response': response.content[0].text})
    except Exception as e:
        import traceback
        return jsonify({'success': False, 'error': str(e), 'trace': traceback.format_exc()})

@app.route('/', methods=['GET'])
def root():
    """Serve React app or API info"""
    if IS_PRODUCTION:
        return send_file(os.path.join(FRONTEND_BUILD_PATH, 'index.html'))
    else:
        return jsonify({
            'message': 'The Guard Table API',
            'description': 'Every company has a system. Now so do you.',
            'endpoints': {
                '/api/guard': 'POST - Main guard table endpoint',
                '/health': 'GET - Health check'
            }
        })

@app.route('/admin/emergency-stop/<action>', methods=['POST'])
def emergency_stop_control(action):
    """Emergency stop control - admin only (requires special header)"""
    # Simple auth check - require special header
    if request.headers.get('X-Admin-Key') != os.getenv('GUARD_ADMIN_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401

    global EMERGENCY_STOP
    if action == 'enable':
        EMERGENCY_STOP = True
        logger.critical("EMERGENCY STOP ENABLED - All Guard Table requests blocked")
        return jsonify({'status': 'Emergency stop ENABLED', 'emergency_stop': True})
    elif action == 'disable':
        EMERGENCY_STOP = False
        logger.info("Emergency stop disabled - service resumed")
        return jsonify({'status': 'Emergency stop DISABLED', 'emergency_stop': False})
    else:
        return jsonify({'error': 'Invalid action. Use enable or disable'}), 400

@app.route('/admin/status', methods=['GET'])
def admin_status():
    """Admin status - show current limits and usage"""
    if request.headers.get('X-Admin-Key') != os.getenv('GUARD_ADMIN_KEY'):
        return jsonify({'error': 'Unauthorized'}), 401

    day_key = get_current_day_key()
    return jsonify({
        'emergency_stop': EMERGENCY_STOP,
        'global_daily_usage': global_daily_usage[day_key],
        'global_daily_limit': GLOBAL_DAILY_LIMIT,
        'global_daily_remaining': GLOBAL_DAILY_LIMIT - global_daily_usage[day_key],
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

    # Calculate totals
    total_requests = sum(global_daily_usage.values())
    requests_today = global_daily_usage[day_key]

    # Calculate requests this week (last 7 days)
    from datetime import datetime, timedelta
    week_total = 0
    for i in range(7):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        week_total += global_daily_usage[date]

    # Check if we've hit the threshold
    if total_requests >= 500:
        logger.warning("🚨 PAID TIER THRESHOLD REACHED - Total requests: {}".format(total_requests))

    # Get recent request logs (last 50)
    recent_logs = request_log[-50:] if request_log else []

    # Calculate unique IPs today
    unique_ips_today = len(set(ip for ip, day_usage in ip_daily_usage.items() if day_usage.get(day_key, 0) > 0))

    return jsonify({
        'total_requests': total_requests,
        'requests_today': requests_today,
        'requests_this_week': week_total,
        'unique_ips_today': unique_ips_today,
        'threshold_status': '🚨 PAID TIER THRESHOLD REACHED' if total_requests >= 500 else 'Below threshold',
        'limits': {
            'ip_daily_limit': IP_DAILY_LIMIT,
            'global_daily_limit': GLOBAL_DAILY_LIMIT,
            'threshold': 500
        },
        'recent_requests': recent_logs,
        'daily_breakdown': dict(global_daily_usage),
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
