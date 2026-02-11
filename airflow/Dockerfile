FROM apache/airflow:2.8.1-python3.10

# -----------------------------
# Switch to root to install OS deps
# -----------------------------
USER root

# -----------------------------
# Install Chromium + Chromedriver
# -----------------------------
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    unzip \
    curl \
    gnupg \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# -----------------------------
# Set Chromium environment vars
# -----------------------------
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# -----------------------------
# Switch back to airflow user
# -----------------------------
USER airflow

# -----------------------------
# Install Python dependencies
# -----------------------------
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt
