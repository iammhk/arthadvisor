from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from kiteconnect import KiteConnect
import pandas as pd
from extensions import db
from models import User, GPTTickerLog
from datetime import datetime, date
import os
import openai
import json

dashboard_bp = Blueprint('dashboard', __name__)

def get_kite_client():
    api_key = current_user.kite_api_key
    api_secret = current_user.kite_api_secret
    if not api_key or not api_secret:
        return None
    kite = KiteConnect(api_key=api_key)
    access_token = getattr(current_user, 'kite_access_token', None)
    if not access_token:
        return None
    kite.set_access_token(access_token)
    return kite

@dashboard_bp.route('/connect_zerodha')
@login_required
def connect_zerodha():
    api_key = current_user.kite_api_key
    if not api_key:
        flash('Please set your Kite API Key in your profile.', 'danger')
        return redirect(url_for('auth.profile'))
    kite = KiteConnect(api_key=api_key)
    login_url = kite.login_url()  # No redirect_uri argument
    return redirect(login_url)

@dashboard_bp.route('/zerodha_callback')
@dashboard_bp.route('/zerodha/callback')
@login_required
def zerodha_callback():
    api_key = current_user.kite_api_key
    api_secret = current_user.kite_api_secret
    request_token = request.args.get('request_token')
    if not request_token:
        flash('Zerodha login failed or cancelled.', 'danger')
        return redirect(url_for('dashboard.show_dashboard'))
    kite = KiteConnect(api_key=api_key)
    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
        access_token = data['access_token']
        # Store access_token in user profile
        current_user.kite_access_token = access_token
        db.session.commit()
        flash('Zerodha account connected successfully!', 'success')
    except Exception as e:
        flash(f'Failed to connect Zerodha: {e}', 'danger')
    return redirect(url_for('dashboard.show_dashboard'))

@dashboard_bp.route('/dashboard')
@login_required
def show_dashboard():
    kite = get_kite_client()
    stock_data = {}
    holdings = []
    zerodha_connected = False
    total_holdings_value = 0
    total_pnl = 0
    funds_info = None
    if kite:
        zerodha_connected = True
        try:
            holdings = kite.holdings()
            # Remove writing to user_holdings_{current_user.username}.txt and .csv
            stock_rows = []
            for h in holdings:
                stock_data[h['tradingsymbol']] = {
                    'current_price': h['last_price'],
                    'quantity': h['quantity'],
                    'avg_price': h['average_price']
                }
                total_holdings_value += h['last_price'] * h['quantity']
                total_pnl += h.get('pnl', 0)
                stock_rows.append({
                    'Stock': h['tradingsymbol'],
                    'Quantity': h['quantity'],
                    'Avg. Price': h['average_price'],
                    'Current Price': h['last_price'],
                    'P&L': h.get('pnl', 0)
                })
            # No CSV or TXT file creation here
            # Fetch funds info
            try:
                funds_info = kite.margins()['equity']
            except Exception:
                funds_info = None
        except Exception as e:
            flash(f'Error fetching portfolio from Zerodha: {e}', 'danger')
    else:
        stock_data = {}
        funds_info = None
    # Fetch live index data from Kite
    indices = {
        'Nifty': 'NSE:NIFTY 50',
        'Sensex': 'BSE:SENSEX',
        'Bank Nifty': 'NSE:NIFTY BANK'
    }
    market_indices = {}
    if kite:
        try:
            quotes = kite.ltp(list(indices.values()))
            for name, symbol in indices.items():
                ltp = quotes[symbol]['last_price'] if symbol in quotes else None
                change = None
                if symbol in quotes and 'ohlc' in quotes[symbol]:
                    open_ = quotes[symbol]['ohlc']['open']
                    prev_close = quotes[symbol]['ohlc']['close']
                    if prev_close:
                        change = ((ltp - prev_close) / prev_close) * 100
                market_indices[name] = {
                    'value': ltp,
                    'change': change
                }
        except Exception as e:
            # fallback to static values if Kite fails
            market_indices = {
                'Nifty': {'value': 24000, 'change': 0.5},
                'Sensex': {'value': 80000, 'change': 0.3},
                'Bank Nifty': {'value': 52000, 'change': -0.2}
            }
    else:
        market_indices = {
            'Nifty': {'value': 24000, 'change': 0.5},
            'Sensex': {'value': 80000, 'change': 0.3},
            'Bank Nifty': {'value': 52000, 'change': -0.2}
        }
    # --- GPT Ticker Integration ---
    # 1. Get portfolio from Kite MCP server (live holdings)
    if kite:
        try:
            holdings = kite.holdings()
            if holdings:
                df = pd.DataFrame([
                    {
                        'Stock': h['tradingsymbol'],
                        'Quantity': h['quantity'],
                        'Avg. Price': h['average_price'],
                        'Current Price': h['last_price'],
                        'P&L': h.get('pnl', 0)
                    }
                    for h in holdings
                ])
                portfolio_str = df.to_string(index=False)
            else:
                portfolio_str = "No portfolio data."
        except Exception as e:
            portfolio_str = f"Kite error: {e}"
    else:
        portfolio_str = "No portfolio data."
    # 2. Read latest advice
    advice_path = 'global_advice.json'
    latest_advice = "No advice available."
    latest_advice_timestamp = None
    if os.path.exists(advice_path):
        with open(advice_path, 'r', encoding='utf-8') as f:
            advice_list = json.load(f)
        if advice_list:
            latest_advice_entry = max(advice_list, key=lambda x: x.get('timestamp', ''))
            latest_advice = latest_advice_entry['advice']
            latest_advice_timestamp = latest_advice_entry.get('timestamp')
    # 3. Read system prompt and substitute
    prompt_path = 'gpt_system_prompt.txt'
    if os.path.exists(prompt_path):
        with open(prompt_path, 'r', encoding='utf-8') as f:
            system_prompt = f.read()
        system_prompt = system_prompt.replace('$portfolio$', portfolio_str)
        system_prompt = system_prompt.replace('$recommendation$', latest_advice)
    else:
        system_prompt = "You are ArthAdvisor."
    today = date.today()
    ticker_log = GPTTickerLog.query.filter_by(user_id=current_user.id).order_by(GPTTickerLog.created_at.desc()).first()
    gpt_ticker_text = None
    should_generate = True
    if ticker_log:
        ticker_date = ticker_log.created_at.date()
        if ticker_date == today:
            if (not latest_advice_timestamp) or (ticker_log.global_advice_timestamp == latest_advice_timestamp):
                gpt_ticker_text = ticker_log.ticker_text
                should_generate = False
    if should_generate:
        openai_api_key = os.getenv('OPENAI_API_KEY') or getattr(current_app.config, 'OPENAI_API_KEY', None)
        if openai_api_key:
            try:
                client = openai.OpenAI(api_key=openai_api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "system", "content": system_prompt}]
                )
                gpt_ticker_text = response.choices[0].message.content.strip()
                new_log = GPTTickerLog(
                    user_id=current_user.id,
                    system_prompt=system_prompt,
                    ticker_text=gpt_ticker_text,
                    created_at=datetime.now(),
                    global_advice_timestamp=latest_advice_timestamp
                )
                db.session.add(new_log)
                db.session.commit()
            except Exception as e:
                gpt_ticker_text = f"GPT error: {e}"
        else:
            gpt_ticker_text = "GPT not configured."
    # Pass gpt_ticker_text to template for chat initialization
    return render_template('dashboard.html', 
                           stock_data=stock_data, 
                           total_holdings_value=total_holdings_value,
                           total_pnl=total_pnl,
                           market_indices=market_indices,
                           zerodha_connected=zerodha_connected,
                           funds_info=funds_info,
                           gpt_ticker_text=gpt_ticker_text)

@dashboard_bp.route('/chat_gpt', methods=['POST'])
@login_required
def chat_gpt():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({'error': 'No message provided.'}), 400
    openai_api_key = current_app.config.get('OPENAI_API_KEY')
    if not openai_api_key:
        return jsonify({'error': 'OpenAI API key not configured.'}), 500
    # --- Kite MCP context for GPT ---
    kite = get_kite_client()
    kite_context = None
    if kite:
        try:
            holdings = kite.holdings()
            kite_context = json.dumps(holdings, indent=2)
        except Exception as e:
            kite_context = f"Kite error: {e}"
    else:
        kite_context = "Kite not connected."
    # Compose system prompt with Kite context
    system_prompt = (
        "You are ArthAdvisor, a helpful and concise stock advisor for Indian retail investors. "
        "You have access to the user's live portfolio and can use the following Zerodha Kite holdings data: "
        f"\n{kite_context}\n"
        "Always provide actionable, ethical, and SEBI-compliant advice. "
        "If asked for stock tips, focus on risk management and long-term investing principles."
    )
    try:
        client = openai.OpenAI(api_key=openai_api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        reply = response.choices[0].message.content
        return jsonify({'reply': reply})
    except Exception as e:
        return jsonify({'error': str(e)}), 500