# Cambiamos a 3.10 para solucionar el error de importlib y Google API
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000

# IMPORTANTE: Añadimos --host=0.0.0.0 para que sea visible fuera del contenedor
CMD ["flask", "run", "--host=0.0.0.0"]