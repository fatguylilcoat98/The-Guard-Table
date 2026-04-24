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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
# Format: ip_usage[ip][month_key] = count
# Format: ip_last_request[ip] = timestamp
# Format: daily_usage[day_key] = count
ip_usage = defaultdict(lambda: defaultdict(int))
ip_last_request = defaultdict(float)
daily_usage = defaultdict(int)

# Limits
MONTHLY_LIMIT = 5           # 5 requests per IP per month
DAILY_GLOBAL_LIMIT = 100    # Max 100 API calls per day total (adjust based on budget)
EMERGENCY_STOP = False      # Manual circuit breaker

def get_current_month_key():
    """Get current month as YYYY-MM for tracking"""
    return datetime.now().strftime("%Y-%m")

def get_current_day_key():
    """Get current day as YYYY-MM-DD for tracking"""
    return datetime.now().strftime("%Y-%m-%d")

def check_emergency_stop():
    """Check if emergency stop is enabled"""
    global EMERGENCY_STOP
    return EMERGENCY_STOP

def check_global_daily_limit():
    """Check if global daily limit exceeded. Returns (allowed, remaining)"""
    day_key = get_current_day_key()
    current_usage = daily_usage[day_key]

    if current_usage >= DAILY_GLOBAL_LIMIT:
        return False, 0

    return True, DAILY_GLOBAL_LIMIT - current_usage


def check_rate_limit(ip):
    """Check if IP has exceeded monthly limit. Returns (allowed, remaining)"""
    month_key = get_current_month_key()
    current_usage = ip_usage[ip][month_key]

    if current_usage >= MONTHLY_LIMIT:
        return False, 0

    return True, MONTHLY_LIMIT - current_usage

def increment_usage(ip):
    """Increment usage counters for IP and global daily"""
    month_key = get_current_month_key()
    day_key = get_current_day_key()
    now = datetime.now().timestamp()

    # Update all counters
    ip_usage[ip][month_key] += 1
    ip_last_request[ip] = now
    daily_usage[day_key] += 1

    return MONTHLY_LIMIT - ip_usage[ip][month_key]

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

        # Plan detection and rate limiting
        user_plan = get_plan(request)
        logger.info(f"User plan: {user_plan} for {client_ip}")

        if user_plan in ['admin', 'paid']:
            logger.info(f"{user_plan.title()} access, bypassing rate limits for {client_ip}")
        else:
            # Check 1: Emergency stop (manual circuit breaker)
            if check_emergency_stop():
                logger.warning("Emergency stop activated - service temporarily disabled")
                return jsonify({
                    'error': 'service_temporarily_disabled',
                    'message': "The Guard Table is temporarily unavailable due to high demand. Please email us at thegoodneighborguard@gmail.com and we'll help you directly."
                }), 503

            # Check 2: Global daily limit (protect against viral traffic)
            global_allowed, global_remaining = check_global_daily_limit()
            if not global_allowed:
                logger.warning(f"Global daily limit reached: {DAILY_GLOBAL_LIMIT}")
                return jsonify({
                    'error': 'daily_limit_reached',
                    'message': "We've hit our daily response limit but we're here to help. Email us at thegoodneighborguard@gmail.com with your situation and we'll respond within 24 hours."
                }), 429

            # Check 3: Monthly limit per IP (original limit)
            monthly_allowed, monthly_remaining = check_rate_limit(client_ip)
            if not monthly_allowed:
                logger.warning(f"Monthly limit exceeded for IP: {client_ip}")
                return jsonify({
                    'error': 'monthly_limit_reached',
                    'message': "You've used your 5 free responses this month. Need more help? Email us at thegoodneighborguard@gmail.com — we'll figure it out together."
                }), 429

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

Your job is to return three things:

1. WAIT — What actually happens to real people who do nothing in this exact situation. Be direct. No hedging. No 'may' or 'might' or 'could.' State consequences as they are. Two to three lines maximum. Make them understand why acting matters.

2. LEVERAGE — The exact message they should send to the other party today. This message must: sound like a lawyer wrote it, cite the actual relevant law or statute for their specific state, be firm and professional without being emotional, make clear that the person knows their rights, and end with a consequence if the issue is not resolved. Make it copy-paste ready.

3. GUARD_STEPS — An array of exactly three escalation steps if the other party ignores the leverage message. Step 1 is 48 hours. Step 2 is 10 days. Step 3 always names the specific government agency for their state and issue type with the direct URL to file a complaint.

Never use the words might, may, could, possibly, or perhaps.
Never mention that you are an AI.
Never give generic advice.
Always cite real law.
Always be specific to their state.

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
                remaining_after = increment_usage(client_ip)
                result['remaining_responses'] = remaining_after
            else:
                result['remaining_responses'] = 'unlimited'

            # Add plan information to response
            result['plan'] = user_plan

            logger.info(f"Successfully generated response. Plan: {user_plan}, Remaining for {client_ip}: {result['remaining_responses']}")
            return jsonify(result)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}")
            return jsonify({'error': 'Something went wrong — try again'}), 500

    except Exception as e:
        import traceback
        logger.error(f"FULL ERROR: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'The Guard Table',
        'version': '1.0.1'
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
        'daily_usage': daily_usage[day_key],
        'daily_limit': DAILY_GLOBAL_LIMIT,
        'daily_remaining': DAILY_GLOBAL_LIMIT - daily_usage[day_key]
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
