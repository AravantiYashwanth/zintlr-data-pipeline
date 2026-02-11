# ⚙️ ZaubaCorp Data Pipeline (Web Scraping · Airflow · Mongodb · API)

---

## 📘 Overview

**ZaubaCorp Data Pipeline** is an **end-to-end data engineering project** built entirely in **Python**, designed to scrape company profile data from **ZaubaCorp**, process it through a structured **ETL pipeline**, and expose the cleaned data via a **REST API**.

The pipeline is orchestrated using **Apache Airflow**, stores data in **MongoDB**, and serves results through a **FastAPI** application. The entire system is containerized using **Docker Compose** for easy setup and reproducibility.

It enables:
1. **Automated Web Scraping** of company profiles
2. **Raw & Cleaned Data Storage** in MongoDB
3. **Scheduled ETL Orchestration** using Airflow
4. **API-based Data Access** using CIN

---

## 🏗️ Solution Architecture
```
ZaubaCorp Website
│
▼
Selenium Scraper
│
▼
MongoDB (companies_raw)
│
▼
Data Cleaning & Transformation
│
▼
MongoDB (companies_cleaned)
│
▼
FastAPI REST Service
│
▼
Client / Postman / curl
```

All steps are executed and monitored through an **Apache Airflow DAG**.

---

## ⚙️ Technologies Used

| Category | Technologies |
|---|---|
| **Language** | Python |
| **Web Scraping** | Selenium |
| **Workflow Orchestration** | Apache Airflow |
| **Database** | MongoDB Atlas |
| **API Framework** | FastAPI |
| **Containerization** | Docker, Docker Compose |
| **Libraries** | Pydantic, PyMongo, Uvicorn |

---

## 🔄 Pipeline Breakdown

### 🔹 Step 1: Web Scraping

- Selenium scrapes **100 company profiles** from ZaubaCorp
- Extracted fields include:
  - CIN
  - Company Name
  - Company Status
  - ROC
  - Registration Number
  - Company Category & Sub-category
  - Class of Company
  - Date of Incorporation
  - Authorized & Paid-up Capital

Minimum mandatory fields:
- CIN
- Company Name
- Incorporation Date
- Company Status

---

### 🔹 Step 2: Store Raw Data

- Scraped data is stored as-is in MongoDB
- Collection name:
```
companies_raw
```

This ensures traceability and allows reprocessing if needed.

---

### 🔹 Step 3: Data Cleaning & Transformation

The cleaning script performs:
- Removal of extra spaces and invalid characters
- Standardization of key names
- Date normalization to ISO format
- Numeric type conversion
- Duplicate removal based on CIN

Cleaned output is stored in:
```
companies_cleaned
```

---

### 🔹 Step 4: Airflow Orchestration

All steps are orchestrated using a single **Airflow DAG** with clear task separation:
```
scrape_data → save_raw → clean_data → save_cleaned
```

Features:
- End-to-end execution
- Task-level logging
- Retry support
- Docker-based Airflow deployment

---

### 🔹 Step 5: REST API for Data Access

A **FastAPI** service exposes cleaned company data using CIN as input.

#### API Endpoint
```
POST /company
```

#### Request Body
```json
{
  "cin": "L12345MH2010PLC123456"
}
```

#### Sample Response
```json
{
  "cin": "L12345MH2010PLC123456",
  "name": "ABC PRIVATE LIMITED",
  "company_status": "Active",
  "date_of_incorporation": "2010-05-12T00:00:00",
  "roc": "ROC-Mumbai"
}
```

If CIN is not found, the API returns a proper HTTP error response.

---

## 🚀 Setup & Execution

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Google Chrome & ChromeDriver
- MongoDB Atlas account

---

### 1️⃣ Clone Repository
```bash
git clone <your-github-repo-url>
cd ZINTLR-DATA-PIPELINE
```

---

### 2️⃣ Configure Environment Variables

Create a `.env` file and set:
```env
MONGODB_URI=mongodb+srv://<username>:<password>@cluster.mongodb.net/
MONGODB_DB=zintlr
```

---

### 3️⃣ Start Services
```bash
docker-compose up --build
```

---

### 4️⃣ Run Airflow DAG

- Open Airflow UI: `http://localhost:8080`
- Login:
  - Username: `airflow`
  - Password: `airflow`
- Enable and trigger the `zintlr_scraper` DAG
- Monitor logs for successful execution

---

### 5️⃣ Verify MongoDB Data

Check the following collections:
- `companies_raw`
- `companies_cleaned`

Using MongoDB Atlas UI or MongoDB Compass.

---

### 6️⃣ Run & Test API

- API Base URL: `http://localhost:8000`
- Health Check:
```
GET /
```

- Fetch company by CIN:
```
POST /company
```

---

## 🧠 Key Features

✅ End-to-end automated ETL pipeline  
✅ Selenium-based controlled scraping  
✅ Airflow DAG orchestration  
✅ Raw and cleaned data separation  
✅ CIN-based deduplication  
✅ REST API for real-time access  
✅ Fully Dockerized setup  

---

## ⚔️ Challenges & Solutions

| Challenge | Solution |
|---|---|
| Dynamic website structure | Explicit waits and stable selectors |
| Duplicate company records | CIN-based deduplication |
| Data inconsistency | Centralized cleaning logic |
| Local setup complexity | Docker Compose orchestration |

---

## 📂 Screenshots

All required screenshots are available in the `/screenshots` folder:

- Airflow DAG view
- Successful DAG logs
- MongoDB collections
- API response (Postman/curl)

---

## 🏁 Conclusion

This project demonstrates a complete **production-style data pipeline** using Python, Apache Airflow, MongoDB, and FastAPI. It highlights best practices in scraping, data cleaning, orchestration, and API development while maintaining modular and scalable design.

---

## 👨‍💻 Author

**A. Yashwanth**  
Aspiring Data Engineer | Python & Data Engineering Enthusiast

🔗 [www.linkedin.com/in/yashwantharavanti](http://www.linkedin.com/in/yashwantharavanti)






```text
ZINTLR-DATA-PIPELINE/
│
├── airflow/
│   ├── dags/
│   │   └── zintlr_scraper.py
│   ├── logs/
│   └── plugins/
│
├── api/
│   ├── main.py
│   ├── db.py
│   ├── schemas.py
│   ├── Dockerfile
│   └── requirements.txt
│
├── scripts/
│   ├── scraper.py
│   ├── cleaner.py
│   └── links.txt
│
├── docker-compose.yml
├── requirements.txt
├── README.md
└── screenshots/
