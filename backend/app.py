"""
The Guard Table — The Good Neighbor Guard
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back
"""

from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
import os
import anthropic
import json
import logging

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

client = anthropic.Anthropic(api_key=anthropic_api_key) if anthropic_api_key else None

@app.route('/api/guard', methods=['POST'])
def guard_endpoint():
    """
    The heart of The Guard Table.
    Takes raw anger and fear, returns legal leverage.
    """
    try:
        data = request.get_json()
        category = data.get('category', '')
        state = data.get('state', 'California')
        rant = data.get('rant', '')

        if not rant.strip():
            return jsonify({'error': 'Please tell us what happened'}), 400

        if not client:
            return jsonify({'error': 'Service temporarily unavailable'}), 503

        # The system prompt - this is the soul of the product
        system_prompt = """You are The Guard Table. You exist for one reason: to give regular people the same fighting power that companies, landlords, hospitals, and debt collectors have always had. The person talking to you is scared, angry, or both. They are not a lawyer. They do not know the system. But they are being wronged and they deserve to fight back with real tools.

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
{
  "wait": ["line1", "line2", "line3"],
  "leverage": "full message text",
  "guard_steps": ["step1", "step2", "step3"]
}"""

        user_prompt = f"""Category: {category}
State: {state}
Situation: {rant}"""

        logger.info(f"Processing request for {state} - {category}")

        # Call Claude API
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": user_prompt
                }
            ]
        )

        response_text = response.content[0].text.strip()

        # Parse JSON response
        try:
            result = json.loads(response_text)
            logger.info("Successfully generated response")
            return jsonify(result)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response: {response_text[:200]}")
            return jsonify({'error': 'Something went wrong — try again'}), 500

    except Exception as e:
        logger.error(f"Error in guard_endpoint: {str(e)}")
        return jsonify({'error': 'Something went wrong — try again'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        'status': 'healthy',
        'service': 'The Guard Table',
        'version': '1.0.0'
    })

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