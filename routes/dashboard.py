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
from utils import send_whatsapp_message
from whatsapp_ticker_sender import send_whatsapp_ticker
import requests
from flask import after_this_request
import time

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

def check_and_generate_ticker_if_needed():
    """
    Checks if gpt_system_prompt.txt or global_advice.json has changed since last ticker generation.
    If so, generates a new ticker_text for all users and sends to WhatsApp/Telegram.
    """
    from models import User, GPTTickerLog
    import openai
    import json
    import os
    from datetime import datetime
    prompt_path = 'gpt_system_prompt.txt'
    advice_path = 'global_advice.json'
    # Get latest file modification times
    prompt_mtime = os.path.getmtime(prompt_path) if os.path.exists(prompt_path) else 0
    advice_mtime = os.path.getmtime(advice_path) if os.path.exists(advice_path) else 0
    # Get last ticker log
    last_log = GPTTickerLog.query.order_by(GPTTickerLog.created_at.desc()).first()
    last_ticker_time = last_log.created_at.timestamp() if last_log else 0
    # If either file changed since last ticker, regenerate
    if prompt_mtime > last_ticker_time or advice_mtime > last_ticker_time:
        # Compose system prompt for each user
        users = User.query.all()
        for user in users:
            # Compose portfolio string (optional: fetch live holdings)
            portfolio_str = "Portfolio not loaded."
            # Try to get live holdings if possible
            try:
                from kiteconnect import KiteConnect
                kite = None
                if user.kite_api_key and user.kite_api_secret and user.kite_access_token:
                    kite = KiteConnect(api_key=user.kite_api_key)
                    kite.set_access_token(user.kite_access_token)
                if kite:
                    holdings = kite.holdings()
                    if holdings:
                        import pandas as pd
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
            except Exception:
                pass
            # Read latest advice
            latest_advice = "No advice available."
            if os.path.exists(advice_path):
                with open(advice_path, 'r', encoding='utf-8') as f:
                    advice_list = json.load(f)
                if advice_list:
                    latest_advice_entry = max(advice_list, key=lambda x: x.get('timestamp', ''))
                    latest_advice = latest_advice_entry['advice']
            # Read system prompt
            if os.path.exists(prompt_path):
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    system_prompt = f.read()
                system_prompt = system_prompt.replace('$portfolio$', portfolio_str)
                system_prompt = system_prompt.replace('$recommendation$', latest_advice)
                user_name = user.full_name or user.username or "User"
                system_prompt = system_prompt.replace('$User Name$', user_name)
            else:
                system_prompt = "You are ArthAdvisor."
            # Generate ticker using OpenAI
            openai_api_key = os.getenv('OPENAI_API_KEY')
            if openai_api_key:
                try:
                    client = openai.OpenAI(api_key=openai_api_key)
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "system", "content": system_prompt}]
                    )
                    gpt_ticker_text = response.choices[0].message.content.strip()
                    new_log = GPTTickerLog(
                        user_id=user.id,
                        system_prompt=system_prompt,
                        ticker_text=gpt_ticker_text,
                        created_at=datetime.now(),
                        global_advice_timestamp=None
                    )
                    db.session.add(new_log)
                    db.session.commit()
                    # Send WhatsApp/Telegram
                    if user.phone:
                        try:
                            send_whatsapp_ticker(user.phone, gpt_ticker_text)
                        except Exception as e:
                            print(f"WhatsApp send error for {user.phone}: {e}")
                    if getattr(user, 'telegram_user_id', None):
                        try:
                            bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
                            send_telegram_message(user.telegram_user_id, gpt_ticker_text, bot_token)
                        except Exception as e:
                            print(f"Telegram send error for {user.telegram_user_id}: {e}")
                except Exception as e:
                    print(f"GPT error for user {user.id}: {e}")

# Call this check at the start of show_dashboard
@dashboard_bp.route('/dashboard')
@login_required
def show_dashboard():
    check_and_generate_ticker_if_needed()
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
        # Replace $User Name$ with user's full name or username
        user_name = current_user.full_name or current_user.username or "User"
        system_prompt = system_prompt.replace('$User Name$', user_name)
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
                # Send WhatsApp ticker to all users with phone number
                from models import User
                users = User.query.all()
                for user in users:
                    if user.phone:
                        try:
                            send_whatsapp_ticker(user.phone, gpt_ticker_text)
                        except Exception as e:
                            print(f"WhatsApp send error for {user.phone}: {e}")
                    # Send Telegram ticker to all users with telegram_user_id
                    if getattr(user, 'telegram_user_id', None):
                        try:
                            bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or getattr(current_app.config, 'TELEGRAM_BOT_TOKEN', None)
                            send_telegram_message(user.telegram_user_id, gpt_ticker_text, bot_token)
                        except Exception as e:
                            print(f"Telegram send error for {user.telegram_user_id}: {e}")
            except Exception as e:
                gpt_ticker_text = f"GPT error: {e}"
        else:
            gpt_ticker_text = "GPT not configured."
    # --- Treemap Data Preparation using MCP server holdings ---
    try:
        # Use holdings from MCP server if available
        mcp_holdings = []
        if kite:
            try:
                mcp_holdings = kite.holdings()
            except Exception:
                mcp_holdings = []
        if mcp_holdings:
            holdings_df = pd.DataFrame([
                {
                    'SYMBOL': h['tradingsymbol'],
                    'Value': h['last_price'] * h['quantity'],
                    'Quantity': h['quantity']
                }
                for h in mcp_holdings
            ])
            holdings_df['Sector'] = holdings_df['SYMBOL'].map(symbol_to_sector).fillna('Unknown')
            holdings_df = holdings_df[holdings_df['Value'] > 0]
            sectors = holdings_df['Sector'].unique().tolist()
            labels = ['Portfolio'] + sectors + holdings_df['SYMBOL'].tolist()
            parents = [''] + ['Portfolio']*len(sectors) + holdings_df['Sector'].tolist()
            sector_values = holdings_df.groupby('Sector')['Value'].sum().reindex(sectors).fillna(0).tolist()
            values = [''] + sector_values + holdings_df['Value'].tolist()
            # For backward compatibility, also build stockwise/sectorwise treemap lists
            stockwise_treemap = [
                {'label': row['SYMBOL'], 'parent': row['Sector'], 'value': row['Value']}
                for _, row in holdings_df.iterrows()
            ]
            sectorwise_treemap = [
                {'label': sector, 'parent': '', 'value': val}
                for sector, val in zip(sectors, sector_values)
            ]
        else:
            labels, parents, values = [], [], []
            stockwise_treemap, sectorwise_treemap = [], []
    except Exception as e:
        labels, parents, values = [], [], []
        stockwise_treemap, sectorwise_treemap = [], []

    # Pass gpt_ticker_text to template for chat initialization
    return render_template('dashboard.html', 
                           stock_data=stock_data, 
                           total_holdings_value=total_holdings_value,
                           total_pnl=total_pnl,
                           market_indices=market_indices,
                           zerodha_connected=zerodha_connected,
                           funds_info=funds_info,
                           gpt_ticker_text=gpt_ticker_text,
                           stockwise_treemap=json.dumps(stockwise_treemap),
                           sectorwise_treemap=json.dumps(sectorwise_treemap),
                           treemap_labels=json.dumps(labels),
                           treemap_parents=json.dumps(parents),
                           treemap_values=json.dumps(values),
                           symbol_to_sector=symbol_to_sector)

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

def send_whatsapp_curl_equivalent(phone_number):
    import requests
    url = "https://graph.facebook.com/v22.0/728214020370908/messages"
    access_token = "EAAU8wLq0epYBPIc1oSrkC9k7TvQWqVXWi7A3nkDLemY2768utEo5hDAGhTbeHWbyZAIEOtK3ngGC93yqL39ghfWzAsVjAwfv4ci8TvIqIXlXkolTWj0EmpG5qZAxmmqemmz1DpwYNxyhZCP7dTnrcJt5Kye8x1OOEt6C3M1RA6m4vAM9ZCgoOEHxsCtHi2wAwWJJpZCJ1GXrteh9V06DxjFkO72zcBAnTDD5jOYAa"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "template",
        "template": {
            "name": "hello_world",
            "language": {"code": "en_US"}
        }
    }
    response = requests.post(url, headers=headers, json=data)
    return response

@dashboard_bp.route('/send_ticker_whatsapp', methods=['POST'])
@login_required
def send_ticker_whatsapp():
    # Ignore ticker_text, just send the hello_world template as per curl
    if not current_user.phone:
        flash('No phone number found in your profile.', 'danger')
        return redirect(url_for('dashboard.show_dashboard'))
    try:
        resp = send_whatsapp_curl_equivalent(current_user.phone)
        if resp.status_code == 200:
            flash('WhatsApp hello_world template sent!', 'success')
        else:
            flash(f'WhatsApp send failed: {resp.text}', 'danger')
    except Exception as e:
        flash(f'WhatsApp send error: {e}', 'danger')
    return redirect(url_for('dashboard.show_dashboard'))

# Build a lookup table for stock symbol to sector
import pandas as pd
try:
    sector_df = pd.read_csv('sector_stocks_extracted.csv')
    symbol_to_sector = dict(zip(sector_df['Symbol'], sector_df['Sector']))
except Exception:
    symbol_to_sector = {}

def send_telegram_message(telegram_user_id, message, bot_token=None):
    if not bot_token:
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not bot_token or not telegram_user_id:
        return False, 'Missing bot token or user id'
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    data = {'chat_id': telegram_user_id, 'text': message}
    resp = requests.post(url, data=data)
    if resp.status_code == 200:
        return True, None
    return False, resp.text

@dashboard_bp.route('/send_ticker_telegram', methods=['POST'])
@login_required
def send_ticker_telegram():
    ticker_text = request.form.get('ticker_text')
    telegram_user_id = getattr(current_user, 'telegram_user_id', None)
    if not telegram_user_id:
        flash('No Telegram user ID found in your profile.', 'danger')
        return redirect(url_for('dashboard.show_dashboard'))
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN') or current_app.config.get('TELEGRAM_BOT_TOKEN')
    success, error = send_telegram_message(telegram_user_id, ticker_text, bot_token)
    if success:
        flash('Ticker sent to your Telegram!', 'success')
    else:
        flash(f'Telegram send failed: {error}', 'danger')
    return redirect(url_for('dashboard.show_dashboard'))