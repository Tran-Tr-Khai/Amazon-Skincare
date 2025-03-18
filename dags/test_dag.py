from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import os
import pandas as pd

from dags.scrape import AmazonScraper
from dags.sendNotifications import fileSender
from dags.transform import process_dataframe
from dags.feature_engineering import cluster_products
from dags.load import load_to_postgresql
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
DATA_DIR = "/opt/airflow/data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def scrape_data(ti):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(DATA_DIR, f"raw_{timestamp}.csv")
    url_template = "https://www.amazon.com/Best-Sellers-Beauty-Personal-Care-Skin-Care-Products/zgbs/beauty/11060451/ref=zg_bs_nav_beauty_1?pg={}"
    scraper = AmazonScraper(url_template, scroll_times=5, num_pages=2, output_file=output_file)
    scraper.scrape()
    ti.xcom_push(key="raw_file", value=output_file)

def send_file(ti):
    raw_file = ti.xcom_pull(task_ids='scrape_amazon_data', key='raw_file')
    sender = fileSender(bot_token=BOT_TOKEN, chat_id=CHAT_ID, csv_file=raw_file)
    sender.send_file()

def transform(ti):
    raw_file = ti.xcom_pull(task_ids='scrape_amazon_data', key='raw_file')
    processed_df = process_dataframe(raw_file)
    processed_file = os.path.join(DATA_DIR, f"processed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    processed_df.to_csv(processed_file, index=False)
    ti.xcom_push(key="processed_file", value=processed_file)

def feature_engineering(ti):
    processed_file = ti.xcom_pull(task_ids='transform_data', key='processed_file')
    df = pd.read_csv(processed_file)
    use_df = df.drop(columns=['link', 'id', 'skin_type', 'brand', 'price', 'category'])
    clustered_df = cluster_products(use_df)
    df['cluster_label'] = clustered_df['cluster_label']
    gold_file = os.path.join(DATA_DIR, f"gold_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    df.to_csv(gold_file, index=False)
    ti.xcom_push(key="gold_file", value=gold_file)

def load_data(ti):
    gold_file = ti.xcom_pull(task_ids='feature_engineering', key='gold_file')
    df = pd.read_csv(gold_file)
    load_to_postgresql(df, "amazon_products")

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'amazon_etl_dag',
    default_args=default_args,
    description='DAG to ETL Skincare Products on Amazon Ecommerce',
    schedule_interval=timedelta(minutes=60),
    start_date=datetime(2025, 3, 14, 6, 21),
    catchup=False
) as dag:
    
    scrape_task = PythonOperator(task_id='scrape_amazon_data', python_callable=scrape_data, provide_context=True)
    send_task = PythonOperator(task_id='send_file_to_telegram', python_callable=send_file, provide_context=True)
    transform_task = PythonOperator(task_id='transform_data', python_callable=transform, provide_context=True)
    feature_engineering_task = PythonOperator(task_id='feature_engineering', python_callable=feature_engineering, provide_context=True)
    load_data_to_postgres = PythonOperator(task_id='load_data', python_callable=load_data, provide_context=True)

    scrape_task >> send_task >> transform_task >> feature_engineering_task >> load_data_to_postgres