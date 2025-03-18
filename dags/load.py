import pandas as pd
#from sqlalchemy import create_engine
#import sqlalchemy
import psycopg2
import os 
import logging
from dotenv import load_dotenv


# Cấu hình logging
logging.basicConfig(
    filename="load_to_postgresql.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

def load_to_postgresql(df, table_name):
    load_dotenv()
    db_name = os.getenv("PG_NAME")
    user = os.getenv("PG_USER")
    password = os.getenv("PG_PASSWORD")
    host = os.getenv("PG_HOST")
    port = os.getenv("PG_PORT")

    conn = None
    try:
        # connect to PostgreSQL
        conn = psycopg2.connect(
            dbname=db_name,
            user=user,
            password=password,
            host=host,
            port=port
        )
        cur = conn.cursor()

        # delete table if exists. 
        cur.execute(f"DROP TABLE IF EXISTS {table_name}")
        
        # Tạo bảng với schema cụ thể
        create_table_query = f"""
        CREATE TABLE {table_name} (
            id TEXT,
            top INTEGER,
            link TEXT,
            rating_count INTEGER,
            price DECIMAL,
            skin_type TEXT,
            category TEXT,
            brand TEXT,
            bought_info INTEGER,
            cluster_label TEXT
        )
        """
        cur.execute(create_table_query)    

        # Ghi dữ liệu
        values = [tuple(row) for row in df.to_numpy()]
        placeholders = ",".join(["%s"] * len(df.columns))
        insert_query = f"INSERT INTO {table_name} VALUES ({placeholders})"
        cur.executemany(insert_query, values)
        
        conn.commit()
        logging.info(f"Data successfully loaded into table '{table_name}'")
    except Exception as e:
        logging.error(f"Error loading data into table '{table_name}': {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


## khong tuong thich version
# def load_to_postgresql(df, table_name):
#     # config
#     load_dotenv()
#     db_name = os.getenv("PG_NAME")
#     user = os.getenv("PG_USER")
#     password = os.getenv("PG_PASSWORD")
#     host = os.getenv("PG_HOST")
#     port = os.getenv("PG_PORT")
    
#     try: 
#         engine = create_engine(f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{db_name}')
#         df.to_sql(table_name, engine, if_exists='replace', index=False)
#         logging.info(f"Data successfully loaded into table '{table_name}'")
#     except Exception as e:
#         logging.error(f"Error loading data into table '{table_name}': {e}")

if __name__ == "__main__":
    file_path = "C:\\Users\\trong\\OneDrive\\Documents\\Project\\amazon-ecommerce\\gold.csv"
    df = pd.read_csv(file_path)
    load_to_postgresql(df, "amazon_products")
