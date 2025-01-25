from sqlalchemy import create_engine, MetaData
import pandas as pd

DATABASE_URI = 'sqlite:///instance/reviews.db'
engine = create_engine(DATABASE_URI)

metadata = MetaData()
metadata.reflect(bind=engine)

tables_to_export = [table for table in metadata.tables.keys() if table != 'users']

for table_name in tables_to_export:
    df = pd.read_sql_table(table_name, con=engine)
    df.to_csv(f'{table_name}.csv', index=False)
    print(f'Exported {table_name} to {table_name}.csv') 