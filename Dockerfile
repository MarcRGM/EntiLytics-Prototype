FROM python:3.11-slim

# Install SQL Drivers (Required for Azure SQL)
RUN apt-get update && apt-get install -y \
    curl gnupg2 \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev \
    && apt-get clean

WORKDIR /app

# Copy everything (ui and features folders)
COPY . /app

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

# 4. IMPORTANT: Run Solara from the root context
# This allows 'import features' to work correctly inside app.py
CMD ["solara", "run", "ui/app.py", "--host", "0.0.0.0", "--port", "80"]