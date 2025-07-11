from sqlalchemy import create_engine, MetaData, Table, update, func
import os

# Path to your database
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'arthadvisor.db')
engine = create_engine(f'sqlite:///{db_path}')
metadata = MetaData()
metadata.reflect(bind=engine)

'''# Replace with your actual table and column names
table = metadata.tables['symbols']  # Change this to your actual table name
column_name = 'yahoo_symbol'  # Change this to your actual column name

with engine.connect() as conn:
    stmt = update(table).values({column_name: func.trim(func.replace(table.c[column_name], '.NS', ''), '.')})
    conn.execute(stmt)
    conn.commit()'''


'''# Change these to your actual table and column names
table_name = 'symbols'
old_column = 'yahoo_symbol'
new_column = 'symbol'

with engine.connect() as conn:
    # SQLite syntax for renaming a column (supported in SQLite >= 3.25.0)
    alter_sql = f'ALTER TABLE {table_name} RENAME COLUMN {old_column} TO {new_column};'
    conn.exec_driver_sql(alter_sql)
    conn.commit()'''