# Use official Python image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy dependencies file and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose the application port
EXPOSE 8000

# Command to run FastAPI using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]