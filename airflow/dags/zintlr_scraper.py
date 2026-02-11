from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

# Import Airflow task entrypoints
from scripts.scraper import scrape_pipeline
from scripts.cleaner import clean_pipeline


# ================== DEFAULT ARGS ==================
default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}
# =================================================


with DAG(
    dag_id="zauba_scraping_cleaning_pipeline",
    default_args=default_args,
    description="Scrape ZaubaCorp → Store Raw → Clean → Store Cleaned",
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,   # Manual trigger (recommended)
    catchup=False,
    tags=["zintlr", "scraping", "mongodb"],
) as dag:

    # ----------- TASK 1: SCRAPING -----------
    scrape_task = PythonOperator(
        task_id="scrape_and_store_raw",
        python_callable=scrape_pipeline,
    )

    # ----------- TASK 2: CLEANING ------------
    clean_task = PythonOperator(
        task_id="clean_and_store_cleaned",
        python_callable=clean_pipeline,
    )

    # ----------- PIPELINE FLOW ---------------
    scrape_task >> clean_task
