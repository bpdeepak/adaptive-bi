# Adaptive Business Intelligence System

This repository contains the implementation of the Adaptive Business Intelligence System,
developed in phases.

## Phase 1: Foundation & Data Streaming

**Goal**: Establish core infrastructure, MongoDB setup, and real-time data streaming.

### Deliverables:
- Project structure and configuration
- MongoDB schema design
- Data streaming service (`streaming_etl.py`)
- Synthetic e-commerce data generator
- Docker configuration for MongoDB
- Basic documentation setup

### Key Components:
- **`docker-compose.yml`**: Defines the MongoDB service.
- **`.env`**: Environment variables for service configurations.
- **`data_streaming/`**:
    - **`streaming_etl.py`**: Main script for orchestrating data generation and ingestion.
    - **`data_generator.py`**: Contains functions to generate synthetic e-commerce data (users, products, transactions, feedback, user activities).
    - **`config.py`**: Manages application configuration, loading from `.env`.
    - **`requirements.txt`**: Python dependencies (`pymongo`, `Faker`, `python-dotenv`).
    - **`init-mongo.js`**: MongoDB initialization script for setting up the database and users.

### How to Run Phase 1:

1.  **Navigate to the project root:**
    ```bash
    cd adaptive-bi-system/
    ```

2.  **Start MongoDB with Docker Compose:**
    ```bash
    docker-compose up -d mongodb
    ```
    * Verify it's running: `docker logs adaptive-bi-mongodb`
    * Connect to MongoDB: `docker exec -it adaptive-bi-mongodb mongosh -u admin -p admin123 --authenticationDatabase admin` (then `use adaptive_bi` and `show collections`).

3.  **Install Python Dependencies (from `data_streaming` directory):**
    ```bash
    cd data_streaming/
    pip install -r requirements.txt
    ```

4.  **Run the Data Streaming Service (from `data_streaming` directory):**
    ```bash
    python streaming_etl.py
    ```
    * This will continuously generate and insert data. Keep this terminal window open.

5.  **Verify Data (in a new terminal):**
    * Connect to MongoDB (as shown in step 2) and run `db.transactions.countDocuments()` etc., to see data accumulating.

---

## Phase 2: Backend API Development

**Goal**: Build the Node.js backend service, including user authentication, RESTful APIs, and WebSocket integration for real-time data.

### Deliverables:
- User authentication system (JWT)
- Role-based access control
- RESTful API endpoints for data, authentication, and user management
- WebSocket integration for real-time updates
- Comprehensive MongoDB integration for data access

### Key Components:
- **`docker-compose.yml`**: Updated to include the `backend` service.
- **`.env`**: Updated with backend-specific environment variables (`BACKEND_PORT`, `MONGO_URI` for internal Docker communication, `JWT_SECRET`, `FRONTEND_URL`).
- **`backend/`**:
    - **`Dockerfile`**: Defines the Docker image for the Node.js backend.
    - **`package.json`**: Node.js project configuration and dependencies.
    - **`server.js`**: Main Express application entry point, setting up middleware, routes, and WebSocket.
    - **`config/config.js`**: Centralized application configuration, loading from `.env`.
    - **`database/connection.js`**: Handles Mongoose MongoDB connection.
    - **`middleware/`**:
        - **`errorHandler.js`**: Custom error handling.
        - **`asyncHandler.js`**: Utility for handling async route errors.
        - **`auth.js`**: JWT authentication and role-based authorization middleware.
        - **`rateLimiter.js`**: Middleware for API rate limiting.
        - **`cors.js`**: Custom CORS configuration.
    - **`models/`**: Mongoose schemas for `User`, `Product`, `Transaction`, `UserActivity`, `Feedback`.
    - **`routes/`**: API endpoint definitions for `auth`, `users`, `metrics`, `ai`, `dashboard`, `health`.
    - **`controllers/`**: Logic for handling API requests (`authController`, `userController`, `metricsController`, `aiController`, `dashboardController`).
    - **`services/socketService.js`**: Manages Socket.IO events and real-time data broadcasting.
    - **`services/dataService.js`**: Abstracts database queries for BI data retrieval.
    - **`utils/logger.js`**: Centralized logging utility using Winston.

### How to Run Phase 2:

1.  **Navigate to the project root:**
    ```bash
    cd adaptive-bi-system/
    ```

2.  **Ensure MongoDB is running (from Phase 1):**
    * `docker-compose up -d mongodb` (if not already running)

3.  **Ensure your `.env` file in the project root (`adaptive-bi-system/.env`) is updated** with the `BACKEND_PORT`, `MONGO_URI` (pointing to `mongodb` service), `JWT_SECRET`, and `FRONTEND_URL` as specified in the Phase 2 implementation instructions.

4.  **Install Node.js Dependencies (from `backend` directory):**
    ```bash
    cd backend/
    npm install
    ```

5.  **Build the Backend Docker Image (from project root):**
    ```bash
    cd ../ # Go back to adaptive-bi-system/
    docker-compose build backend
    ```

6.  **Start the Backend Service (from project root):**
    ```bash
    docker-compose up -d backend
    ```
    * Verify it's running: `docker logs adaptive-bi-backend`
        * Look for "✓ Connected to MongoDB successfully" and "🚀 Server running on port 3000".

7.  **Test API Endpoints (in a new terminal):**

    * **Health Check:**
        ```bash
        curl http://localhost:3000/health
        ```

    * **Register an Admin User:**
        ```bash
        curl -X POST -H "Content-Type: application/json" -d '{ "username": "adminuser", "email": "admin@example.com", "password": "adminpassword123", "role": "admin" }' http://localhost:3000/api/auth/register
        ```
        * **Save the `token` from the response.**

    * **Login User (to get a fresh token if needed):**
        ```bash
        curl -X POST -H "Content-Type: application/json" -d '{ "email": "admin@example.com", "password": "adminpassword123" }' http://localhost:3000/api/auth/login
        ```
        * **Save the `token` from the response.**

    * **Get All Users (requires JWT token, replace `YOUR_ADMIN_JWT_TOKEN_HERE`):**
        ```bash
        curl -X GET -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN_HERE" http://localhost:3000/api/users
        ```

    * **Get Sales Metrics (requires JWT token):**
        ```bash
        curl -X GET -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN_HERE" http://localhost:3000/api/metrics/sales
        ```

    * **Get Dashboard Summary (requires JWT token):**
        ```bash
        curl -X GET -H "Authorization: Bearer YOUR_ADMIN_JWT_TOKEN_HERE" http://localhost:3000/api/dashboard/summary
        ```

---

**Current Status**: Phase 2 Complete ✅ | **Next**: Phase 3 Development