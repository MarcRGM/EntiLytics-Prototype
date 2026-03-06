FROM python:3.11-slim

# Install prerequisites 
RUN apt-get update && apt-get install -y \
    curl \
    gnupg2 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft's key to the modern keyring 
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg

# Add the repo for Debian 12 
RUN curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list | tee /etc/apt/sources.list.d/mssql-release.list

# Install the drivers
RUN apt-get update && \
    ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# SET THE PYTHON PATH
ENV PYTHONPATH="/app"

# Copy everything
COPY . /app

# Install torch CPU-only first (saves ~1GB vs default CUDA build)
RUN pip install --no-cache-dir torch==2.9.1 --index-url https://download.pytorch.org/whl/cpu

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

# Run Solara
CMD ["solara", "run", "ui/app.py", "--host", "0.0.0.0", "--port", "80"]