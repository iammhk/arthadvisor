import os
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, UniqueConstraint, DateTime, MetaData, Table, update
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
import numpy as np
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get file paths from environment variables
csv_file_path = os.getenv('PORTFOLIO_CSV')

# Get the directory of the current script
current_directory = os.path.dirname(os.path.abspath(__file__))

# Set the path to the instance folder
instance_folder = os.path.join(current_directory, 'instance')

# Ensure the instance folder exists
os.makedirs(instance_folder, exist_ok=True)

# Construct the absolute path to the database file within the instance folder
db_file_path = os.path.join(instance_folder, os.getenv('SQLALCHEMY_DATABASE_URI').replace('sqlite:///', ''))

# SQLAlchemy setup
engine = create_engine(f'sqlite:///{db_file_path}', echo=False)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()
metadata = MetaData()

# Define the Symbols table
class Symbol(Base):
    __tablename__ = 'symbols'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    yahoo_symbol = Column(String, unique=True)
    __table_args__ = (UniqueConstraint('yahoo_symbol', name='_yahoo_symbol_uc'),)

# Define the Data table
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

# Define the Timestamps table
timestamps_table = Table('timestamps', metadata,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('symbol', String, nullable=False),
    Column('timestamp', DateTime, nullable=False),
    Column('operation', String, nullable=False)  # download, training, or prediction
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
    if result.rowcount == 0:  # If no row was updated, insert a new one
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
        yahoo_symbol = row['YAHOO_SYMBOL']

        symbol = session.query(Symbol).filter_by(yahoo_symbol=yahoo_symbol).first()

        if symbol:
            symbol.name = name
            updated_symbols += 1
        else:
            new_symbol = Symbol(name=name, yahoo_symbol=yahoo_symbol)
            session.add(new_symbol)
            inserted_symbols += 1

    session.commit()
    return inserted_symbols, updated_symbols

def fetch_and_insert_update_data(df):
    inserted_data = 0
    updated_data = 0
    failed_downloads = []

    # Generate daily dates for the last 2 years
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=2*365)
    date_range = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days only

    for yahoo_symbol in df['YAHOO_SYMBOL']:
        try:
            # Generate random walk for prices
            price = np.random.uniform(100, 1000)  # Start price
            prices = [price]
            for _ in range(1, len(date_range)):
                # Simulate daily return
                price = prices[-1] * np.random.normal(1.0002, 0.02)  # Slight upward drift
                prices.append(max(price, 1))  # Price can't go below 1
            prices = np.array(prices)
            
            # Generate OHLCV
            for i, date in enumerate(date_range):
                open_p = prices[i] * np.random.uniform(0.98, 1.02)
                close_p = prices[i] * np.random.uniform(0.98, 1.02)
                high_p = max(open_p, close_p) * np.random.uniform(1.00, 1.03)
                low_p = min(open_p, close_p) * np.random.uniform(0.97, 1.00)
                volume = np.random.randint(10000, 1000000)

                finance_data = session.query(FinanceData).filter_by(symbol=yahoo_symbol, date=date.date()).first()
                if finance_data:
                    finance_data.open = open_p
                    finance_data.high = high_p
                    finance_data.low = low_p
                    finance_data.close = close_p
                    finance_data.volume = volume
                    updated_data += 1
                else:
                    new_finance_data = FinanceData(
                        symbol=yahoo_symbol,
                        date=date.date(),
                        open=open_p,
                        high=high_p,
                        low=low_p,
                        close=close_p,
                        volume=volume
                    )
                    session.add(new_finance_data)
                    inserted_data += 1
            print(f'Generated random data for {yahoo_symbol}')
            upsert_timestamp(yahoo_symbol, 'download')
        except Exception as e:
            print(f'Failed to generate data for {yahoo_symbol}: {e}')
            failed_downloads.append(yahoo_symbol)

    session.commit()
    return inserted_data, updated_data, failed_downloads

def update_database(csv_file_path):
    df = read_csv(csv_file_path)
    inserted_symbols, updated_symbols = insert_or_update_symbols(df)
    print(f'Inserted {inserted_symbols} new symbols.')
    print(f'Updated {updated_symbols} existing symbols.')
    
    inserted_data, updated_data, failed_downloads = fetch_and_insert_update_data(df)
    print(f'Inserted {inserted_data} new data entries.')
    print(f'Updated {updated_data} existing data entries.')
    if failed_downloads:
        print(f'Failed to download data for the following symbols: {failed_downloads}')

if __name__ == '__main__':
    update_database(csv_file_path)
