"""
PathBack — Stripe payments blueprint
Built by Christopher Hughes · Sacramento, CA
Created with the help of AI collaborators (Claude · GPT · Gemini · Groq)
Truth · Safety · We Got Your Back

Products:
  pass_7day   — 7-Day Pass, $6.99 one-time, unlimited responses for 7 days
  sub_monthly — Subscription, $11.99/month
  sub_yearly  — Subscription, $99/year

Flow (modeled on Swoono's working Stripe integration, reimplemented for
Flask + SQLite): the frontend asks /api/stripe/create-checkout for a hosted
Checkout URL; Stripe redirects back to /success?session_id=...; the webhook
(checkout.session.completed) issues an access-pass token in SQLite which
the success page fetches and shows; subscription lifecycle events keep the
pass active/inactive.

Env: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, PRICE_ID_PASS_7DAY,
PRICE_ID_SUB_MONTHLY, PRICE_ID_SUB_YEARLY, PUBLIC_BASE_URL (optional).
"""

import os
import logging
from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify

import gng_db

logger = logging.getLogger(__name__)

payments_bp = Blueprint('payments', __name__)

PRODUCTS = {
    'pass_7day': {
        'mode': 'payment',
        'price_env': 'PRICE_ID_PASS_7DAY',
        'label': '7-Day Pass — $6.99',
        'duration_days': 7,
    },
    'sub_monthly': {
        'mode': 'subscription',
        'price_env': 'PRICE_ID_SUB_MONTHLY',
        'label': 'PathBack Subscription — $11.99/month',
        'fallback_days': 35,   # used only if Stripe period end can't be read
    },
    'sub_yearly': {
        'mode': 'subscription',
        'price_env': 'PRICE_ID_SUB_YEARLY',
        'label': 'PathBack Subscription — $99/year',
        'fallback_days': 370,
    },
}


def _stripe():
    import stripe
    stripe.api_key = os.getenv('STRIPE_SECRET_KEY', '')
    return stripe


def _public_base_url():
    base = os.getenv('PUBLIC_BASE_URL')
    if base:
        return base.rstrip('/')
    return request.host_url.rstrip('/')


@payments_bp.route('/api/stripe/create-checkout', methods=['POST'])
def create_checkout():
    """Create a Stripe Checkout session for one of the PathBack products."""
    if not os.getenv('STRIPE_SECRET_KEY'):
        return jsonify({'error': 'Payments are not configured yet'}), 503

    data = request.get_json(force=True, silent=True) or {}
    product_key = data.get('product', '')
    product = PRODUCTS.get(product_key)
    if not product:
        return jsonify({'error': f'Unknown product. Choose one of: {", ".join(PRODUCTS)}'}), 400

    price_id = os.getenv(product['price_env'])
    if not price_id:
        return jsonify({'error': f'{product["price_env"]} is not configured'}), 503

    base = _public_base_url()
    try:
        session = _stripe().checkout.Session.create(
            mode=product['mode'],
            payment_method_types=['card'],
            line_items=[{'price': price_id, 'quantity': 1}],
            success_url=f'{base}/success?session_id={{CHECKOUT_SESSION_ID}}',
            cancel_url=f'{base}/cancel',
            metadata={'product': product_key},
        )
        return jsonify({'url': session.url})
    except Exception as exc:
        logger.error('Stripe checkout creation failed: %s', exc)
        return jsonify({'error': str(exc)}), 500


def _subscription_period_end(stripe_mod, subscription_id, fallback_days):
    try:
        sub = stripe_mod.Subscription.retrieve(subscription_id)
        period_end = getattr(sub, 'current_period_end', None) or sub.get('current_period_end')
        if period_end:
            return datetime.fromtimestamp(period_end)
    except Exception as exc:
        logger.warning('Could not read subscription period end (%s); using fallback', exc)
    return datetime.now() + timedelta(days=fallback_days)


@payments_bp.route('/api/stripe/webhook', methods=['POST'])
def webhook():
    """Stripe webhook: issue passes on checkout, track subscription lifecycle."""
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET', '')
    signature = request.headers.get('Stripe-Signature', '')
    stripe_mod = _stripe()
    try:
        event = stripe_mod.Webhook.construct_event(
            request.get_data(), signature, webhook_secret)
    except Exception as exc:
        logger.warning('Webhook signature verification failed: %s', exc)
        return jsonify({'error': str(exc)}), 400

    event_type = event['type']
    obj = event['data']['object']

    if event_type == 'checkout.session.completed':
        product_key = (obj.get('metadata') or {}).get('product', 'pass_7day')
        product = PRODUCTS.get(product_key, PRODUCTS['pass_7day'])
        session_id = obj.get('id')

        if gng_db.get_pass_by_checkout_session(session_id):
            logger.info('Webhook replay for session %s — pass already issued', session_id)
            return jsonify({'received': True})

        if product['mode'] == 'payment':
            expires_at = datetime.now() + timedelta(days=product['duration_days'])
            stripe_ref = obj.get('payment_intent') or session_id
        else:
            stripe_ref = obj.get('subscription') or session_id
            expires_at = _subscription_period_end(
                stripe_mod, stripe_ref, product['fallback_days'])

        token = gng_db.create_access_pass(
            pass_type=product_key,
            expires_at=expires_at,
            stripe_ref=stripe_ref,
            checkout_session_id=session_id,
        )
        logger.info('Issued %s pass (…%s) for checkout session %s',
                    product_key, token[-4:], session_id)

    elif event_type in ('customer.subscription.updated', 'customer.subscription.deleted'):
        subscription_id = obj.get('id')
        status = obj.get('status')
        if event_type == 'customer.subscription.deleted' or status not in ('active', 'trialing'):
            new_status = 'canceled' if event_type == 'customer.subscription.deleted' else 'inactive'
            gng_db.update_pass_by_stripe_ref(subscription_id, status=new_status)
            logger.info('Subscription %s → %s', subscription_id, new_status)
        else:
            period_end = obj.get('current_period_end')
            expires_at = datetime.fromtimestamp(period_end) if period_end else None
            gng_db.update_pass_by_stripe_ref(
                subscription_id, status='active', expires_at=expires_at,
                cancel_at_period_end=bool(obj.get('cancel_at_period_end')))
            logger.info('Subscription %s active through %s', subscription_id, expires_at)

    return jsonify({'received': True})


@payments_bp.route('/api/stripe/session-pass', methods=['GET'])
def session_pass():
    """Success page: exchange the checkout session id for the issued token."""
    session_id = request.args.get('session_id', '')
    if not session_id:
        return jsonify({'error': 'session_id required'}), 400
    record = gng_db.get_pass_by_checkout_session(session_id)
    if not record:
        # Webhook may not have arrived yet — the success page retries.
        return jsonify({'ready': False}), 202
    return jsonify({
        'ready': True,
        'token': record['token'],
        'pass_type': record['pass_type'],
        'expires_at': record['expires_at'],
    })


@payments_bp.route('/api/stripe/status', methods=['GET'])
def pass_status():
    token = request.args.get('token', '')
    record = gng_db.get_pass(token) if token else None
    if not record:
        return jsonify({'valid': False, 'plan': 'free'})
    return jsonify({
        'valid': gng_db.is_pass_valid(token),
        'plan': 'paid' if gng_db.is_pass_valid(token) else 'free',
        'pass_type': record['pass_type'],
        'status': record['status'],
        'expires_at': record['expires_at'],
        'cancel_at_period_end': bool(record['cancel_at_period_end']),
    })


@payments_bp.route('/api/stripe/cancel', methods=['POST'])
def cancel():
    """Cancel a subscription at period end (7-day passes just expire)."""
    data = request.get_json(force=True, silent=True) or {}
    token = data.get('token', '')
    record = gng_db.get_pass(token) if token else None
    if not record:
        return jsonify({'error': 'No pass found for that token'}), 404
    if not record['pass_type'].startswith('sub_'):
        return jsonify({'error': '7-Day Passes are one-time purchases — they simply expire'}), 400
    try:
        _stripe().Subscription.modify(record['stripe_ref'], cancel_at_period_end=True)
    except Exception as exc:
        logger.error('Stripe cancel failed: %s', exc)
        return jsonify({'error': str(exc)}), 500
    gng_db.update_pass_by_stripe_ref(record['stripe_ref'], cancel_at_period_end=True)
    return jsonify({'success': True, 'message': 'Your subscription will end at the current period.'})
