FROM python:3.9-slim

WORKDIR /app

# Install system dependencies if required (e.g. for potential PDF libraries)
# RUN apt-get update && apt-get install -y gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose the Flask port
EXPOSE 5000

# The command to run the application
CMD ["python", "run.py"]
