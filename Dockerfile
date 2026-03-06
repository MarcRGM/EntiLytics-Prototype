FROM python:3.11-slim

# Install prerequisites 
# Add Microsoft's GPG key to the modern keyring
# Add the Microsoft repo for Debian 12 
# Install the ODBC driver
RUN apt-get update && apt-get install -y \
    curl gnupg2 \
    && mkdir -p /etc/apt/sources.list.d \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev \
    && apt-get clean


WORKDIR /app

# Copy everything
COPY . /app

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80

# Run Solara
CMD ["solara", "run", "ui/app.py", "--host", "0.0.0.0", "--port", "80"]