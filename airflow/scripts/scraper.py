import time
import random
from datetime import datetime
from pathlib import Path

from airflow.exceptions import AirflowFailException

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

from pymongo import MongoClient, errors
from pymongo.errors import (
    AutoReconnect,
    NetworkTimeout,
    ServerSelectionTimeoutError,
)

# ================== PATH CONFIG ==================
LINKS_FILE = Path("/opt/airflow/scripts/links.txt")

# ================== MONGODB CONFIG ==================
CONNECTION_STRING = (
    "mongodb+srv://yashwantharavanti_zintlr:"
    "kdLyBldFohW9dYI6@cluster0.ebb7yqo.mongodb.net/"
)

DB_NAME = "zintlr"
RAW_COLLECTION = "companies_raw"

client = MongoClient(CONNECTION_STRING, serverSelectionTimeoutMS=5000)
db = client[DB_NAME]
collection = db[RAW_COLLECTION]

# Prevent duplicate CIN inserts
collection.create_index("CIN", unique=True)

# ================== CONSTANTS ==================
WAIT_TIME = 25
SCROLL_PAUSE_TIME = 1.2
MAX_FAILURE_THRESHOLD = 10
MONGO_MAX_RETRIES = 3

# ================== UTILITIES ==================
def read_links():
    if not LINKS_FILE.exists():
        raise AirflowFailException(f"links.txt not found at {LINKS_FILE}")

    with open(LINKS_FILE, "r", encoding="utf-8") as f:
        links = [line.strip() for line in f if line.strip()]

    if not links:
        raise AirflowFailException("links.txt is empty")

    return links


def create_driver():
    options = Options()

    # REQUIRED: Chromium binary
    options.binary_location = "/usr/bin/chromium"

    # 🔥 HEADLESS IS MANDATORY IN DOCKER
    options.add_argument("--headless=new")

    # 🔥 REQUIRED Docker flags
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--remote-debugging-port=9222")
    options.add_argument("--window-size=1920,1080")

    # Automation mitigation (best effort)
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service("/usr/bin/chromedriver")

    return webdriver.Chrome(
        service=service,
        options=options
    )



def auto_scroll(driver):
    last_height = driver.execute_script("return document.body.scrollHeight")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            break
        last_height = new_height


# ================== SCRAPING ==================
def scrape_company(url):
    driver = create_driver()
    wait = WebDriverWait(driver, WAIT_TIME)

    try:
        driver.get(url)

        # Allow Cloudflare JS to complete
        time.sleep(6)

        auto_scroll(driver)

        container = wait.until(
            EC.presence_of_element_located((By.ID, "company-information"))
        )

        rows = container.find_elements(By.XPATH, ".//table/tbody/tr")
        data = {}

        for row in rows:
            key = row.find_element(By.XPATH, "./td[1]").text.strip()
            value = row.find_element(By.XPATH, "./td[2]").text.strip()

            if key == "Activity":
                for line in value.split("\n"):
                    if "NIC Code" in line:
                        data["NIC Code"] = line.replace("NIC Code", "").replace(":", "").strip()
                    elif "NIC Description" in line:
                        data["NIC Description"] = line.replace("NIC Description", "").replace(":", "").strip()
            else:
                data[key] = value

        if not data:
            raise ValueError("No data extracted")

        return data

    except TimeoutException:
        raise Exception("Timed out waiting for company information (Cloudflare likely)")

    finally:
        driver.quit()


# ================== MONGODB ==================
def insert_raw_company(data, source_url):
    cin = data.get("CIN")

    if not cin:
        print("⚠️ CIN missing — skipping")
        return False

    document = {
        "CIN": cin,
        "source_url": source_url,
        "scraped_at": datetime.utcnow(),
        "raw_data": data,
    }

    for attempt in range(1, MONGO_MAX_RETRIES + 1):
        try:
            collection.insert_one(document)
            print(f"✅ Inserted CIN: {cin}")
            return True

        except errors.DuplicateKeyError:
            print(f"⚠️ Duplicate CIN skipped: {cin}")
            return True

        except (AutoReconnect, NetworkTimeout, ServerSelectionTimeoutError):
            wait_time = 2 ** attempt
            print(f"🔄 Mongo retry {attempt} for CIN {cin}")
            time.sleep(wait_time)

        except Exception as e:
            print(f"❌ MongoDB error for CIN {cin}: {e}")
            return False

    return False


# ================== AIRFLOW ENTRYPOINT ==================
def scrape_pipeline():
    links = read_links()
    total = len(links)

    success = 0
    failure = 0

    print(f"🔹 Total links: {total}")

    for i, url in enumerate(links, start=1):
        print(f"\n[{i}/{total}] {url}")

        try:
            data = scrape_company(url)

            if insert_raw_company(data, url):
                success += 1
            else:
                failure += 1

            time.sleep(random.uniform(4, 7))

        except Exception as e:
            failure += 1
            print(f"❌ Failed: {url}")
            print(f"❌ Reason: {e}")

        if failure > MAX_FAILURE_THRESHOLD:
            raise AirflowFailException(
                f"Too many failures: {failure}/{total}"
            )

    print("\n=========== SUMMARY ===========")
    print(f"✅ Success: {success}")
    print(f"❌ Failed: {failure}")

    if success == 0:
        raise AirflowFailException("Scraping failed completely")

    print("🎯 Scraping task completed")
