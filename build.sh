#!/bin/bash

# Update system and install dependencies
apt-get update && apt-get install -y curl gnupg unixodbc-dev

# Add Microsoft repository for ODBC driver
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Install ODBC Driver 17 for SQL Server
apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# Install Python dependencies
pip install -r requirements.txt
