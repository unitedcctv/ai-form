# **AI-Powered Registration System**

*AI-powered registration system built with FastAPI, React, LangGraph, DSPy, Guardrails AI, and MLflow. The system guides users through a structured conversation, collecting registration details while leveraging AI validation to ensure input accuracy.*

## **Project Structure**

```
/project-root
│── /app          # FastAPI backend
│── /app/docker-compose.yml  # Docker setup
│── /frontend     # React frontend
│── .venv         # Python virtual environment
│── README.md     # This file
```

---

## **1️Setup and Run the FastAPI Backend**

### **Option 1: Run Locally**

#### **Prerequisites**

- **Python 3.9+**
- **Poetry or pip (for dependency management)**
- **SQLite**

#### **Steps**

1. **Navigate to the backend directory:**

   ```sh
   cd app
   ```

2. **Activate the Python virtual environment:**

   ```sh
   source ../.venv/bin/activate  # macOS/Linux
   ../.venv/Scripts/activate     # Windows (PowerShell)
   ```

3. **Install dependencies:**

   ```sh
   pip install -r requirements.txt
   ```

4. **Start the FastAPI server:**

   ```sh
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

5. **Access the API docs in the browser:**

   - Open [http://localhost:8000/docs](http://localhost:8000/docs) (Swagger UI)
   - Open [http://localhost:8000/redoc](http://localhost:8000/redoc) (ReDoc)

---

### **Option 2: Run with Docker Compose**

#### **Prerequisites**

- **Docker & Docker Compose installed**

#### **Steps**

1. **Navigate to the project root:**

   ```sh
   cd /path/to/project-root/app
   ```

2. **Run Docker Compose:**

   ```sh
   docker-compose up --build
   ```

3. **Check if the backend is running:**

   ```sh
   docker logs -f <backend-container-name>
   ```

4. **Stop the containers when done:**

   ```sh
   docker-compose down
   ```

---

## **2️Setup and Run the React Frontend**

### **Prerequisites**

- **Node.js 16+**
- **Yarn or npm**

### **Steps**

1. **Navigate to the frontend directory:**

   ```sh
   cd frontend
   ```

2. **Install dependencies:**

   ```sh
   yarn install  # or npm install
   ```

3. **Start the development server:**

   ```sh
   yarn dev  # or npm run dev
   ```

4. **Open the frontend in your browser:**

   - [http://localhost:5173](http://localhost:5173)

---

## **3️Environment Variables**

Create a `.env` file in both `/app` and `/frontend` and configure as needed:

### **Backend**

```ini
OPENAI_API_KEY=your-api-key
MLFLOW_ENABLED=True
MLFLOW_EXPERIMENT_NAME=your-experiment
DATABASE_URL=sqlite:///./database.db  # or Snowflake credentials
```

### **Frontend**

```ini
VITE_API_URL=http://localhost:8000
```

---
