import os
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, UniqueConstraint, DateTime, MetaData, Table, update
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
import numpy as np
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from kiteconnect import KiteConnect
from flask import Flask, request, redirect, jsonify
import logging
from threading import Thread

# --- Zerodha (Kite Connect) Login Flow ---
# Remove hardcoded API keys; load from .env or prompt if missing
KITE_API_KEY = "v2qa0jwrkw1l7489"
KITE_API_SECRET = "17b9qraamiojz39sj7xa0hkaoqctf7fu"

REDIRECT_URL = "http://127.0.0.1:5000/kite_callback"

kite = KiteConnect(api_key=KITE_API_KEY)
access_token = None

# Set up logging
logging.basicConfig(level=logging.INFO)

# --- Flask server for Kite login callback ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Welcome! Visit /login to authenticate with Kite Connect."

@app.route('/login')
def login():
    login_url = kite.login_url()
    return redirect(login_url)

def run_data_download(token):
    kite = KiteConnect(api_key=KITE_API_KEY)
    kite.set_access_token(token)
    update_database(csv_file_path, kite)

@app.route('/callback')
def callback():
    global access_token
    request_token = request.args.get('request_token')
    try:
        data = kite.generate_session(request_token, api_secret=KITE_API_SECRET)
        access_token = data["access_token"]
        with open('kite_access_token.txt', 'w') as f:
            f.write(access_token)
        logging.info("Access token generated successfully.")
        # Start data download in background
        Thread(target=run_data_download, args=(access_token,), daemon=True).start()
        return "Access token generated successfully! Data download started in background. You can now close this tab."
    except Exception as e:
        logging.error(f"Error generating access token: {e}")
        return f"Error generating access token: {e}"

@app.route('/zerodha/callback')
def zerodha_callback():
    return callback()

@app.route('/get_token')
def get_token():
    if access_token:
        return jsonify({"access_token": access_token})
    else:
        return jsonify({"error": "No access token available. Please visit /login first."}), 401

# --- Main Data Downloader Logic ---

# Load environment variables from .env file
load_dotenv()

csv_file_path = 'prtflo.csv'
current_directory = os.path.dirname(os.path.abspath(__file__))
instance_folder = os.path.join(current_directory, 'instance')
os.makedirs(instance_folder, exist_ok=True)
db_file_path = os.path.join(instance_folder, os.getenv('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', ''))
engine = create_engine(f'sqlite:///{db_file_path}', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

class Symbol(Base):
    __tablename__ = 'symbols'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    symbol = Column(String, unique=True)
    __table_args__ = (UniqueConstraint('symbol', name='_symbol_uc'),)

class FinanceData(Base):
    __tablename__ = 'finance_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String)
    date = Column(Date)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    __table_args__ = (UniqueConstraint('symbol', 'date', name='_symbol_date_uc'),)

timestamps_table = Table('timestamps', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('symbol', String, nullable=False),
    Column('timestamp', DateTime, nullable=False),
    Column('operation', String, nullable=False)
)

Base.metadata.create_all(engine)
metadata.create_all(engine)

def upsert_timestamp(symbol, operation):
    timestamp = datetime.now(timezone.utc)
    stmt = (
        update(timestamps_table)
        .where(timestamps_table.c.symbol == symbol, timestamps_table.c.operation == operation)
        .values(timestamp=timestamp)
    )
    result = session.execute(stmt)
    if result.rowcount == 0:
        session.execute(
            timestamps_table.insert().values(symbol=symbol, timestamp=timestamp, operation=operation)
        )
    session.commit()

def read_csv(file_path):
    return pd.read_csv(file_path)

def insert_or_update_symbols(df):
    inserted_symbols = 0
    updated_symbols = 0
    for index, row in df.iterrows():
        name = row['SYMBOL']
        symbol = row['SYMBOL']
        symbol = session.query(Symbol).filter_by(symbol=symbol).first()
        if symbol:
            symbol.name = name
            updated_symbols += 1
        else:
            new_symbol = Symbol(name=name, symbol=symbol)
            session.add(new_symbol)
            inserted_symbols += 1
    session.commit()
    return inserted_symbols, updated_symbols

def fetch_and_insert_update_data(df, kite):
    inserted_data = 0
    updated_data = 0
    failed_downloads = []
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=2*365)
    for symbol in df['SYMBOL']:
        try:
            nse_symbol = symbol
            instrument_token = None
            if kite:
                instruments = kite.instruments('NSE')
                for inst in instruments:
                    if inst['tradingsymbol'] == nse_symbol:
                        instrument_token = inst['instrument_token']
                        break
            if not instrument_token:
                print(f'Instrument token not found for {nse_symbol}')
                failed_downloads.append(symbol)
                continue
            kite_data = kite.historical_data(
                instrument_token,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                interval='day',
                continuous=False
            )
            for row in kite_data:
                date = row['date'].date()
                open_p = row['open']
                high_p = row['high']
                low_p = row['low']
                close_p = row['close']
                volume = row['volume']
                finance_data = session.query(FinanceData).filter_by(symbol=symbol, date=date).first()
                if finance_data:
                    finance_data.open = open_p
                    finance_data.high = high_p
                    finance_data.low = low_p
                    finance_data.close = close_p
                    finance_data.volume = volume
                    updated_data += 1
                else:
                    new_finance_data = FinanceData(
                        symbol=symbol,
                        date=date,
                        open=open_p,
                        high=high_p,
                        low=low_p,
                        close=close_p,
                        volume=volume
                    )
                    session.add(new_finance_data)
                    inserted_data += 1
            print(f'Downloaded Kite data for {symbol}')
            upsert_timestamp(symbol, 'download')
        except Exception as e:
            print(f'Failed to download data for {symbol}: {e}')
            failed_downloads.append(symbol)
    session.commit()
    return inserted_data, updated_data, failed_downloads

def update_database(csv_file_path, kite):
    df = read_csv(csv_file_path)
    inserted_symbols, updated_symbols = insert_or_update_symbols(df)
    print(f'Inserted {inserted_symbols} new symbols.')
    print(f'Updated {updated_symbols} existing symbols.')
    inserted_data, updated_data, failed_downloads = fetch_and_insert_update_data(df, kite)
    print(f'Inserted {inserted_data} new data entries.')
    print(f'Updated {updated_data} existing data entries.')
    if failed_downloads:
        print(f'Failed to download data for the following symbols: {failed_downloads}')

# The main entry point is now only the Flask app
if __name__ == '__main__':
    app.run(port=5000)
