# Adaptive Business Intelligence System — Comprehensive Project Documentation

> **Prepared for:** Interview / Presentation Reference  
> **Repository:** [bpdeepak/adaptive-bi](https://github.com/bpdeepak/adaptive-bi)  
> **Authors:** Deepak BP, Chandan HK, Aditya GS, Gaurav Kumar

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [System Architecture](#2-system-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Data Layer — Streaming & Generation](#4-data-layer--streaming--generation)
5. [AI / ML Service (Python · FastAPI)](#5-ai--ml-service-python--fastapi)
   - 5.1 [Configuration & Application Bootstrap](#51-configuration--application-bootstrap)
   - 5.2 [Data Processor](#52-data-processor)
   - 5.3 [Feature Engineering](#53-feature-engineering)
   - 5.4 [Sales Forecasting Model](#54-sales-forecasting-model)
   - 5.5 [Anomaly Detection Model](#55-anomaly-detection-model)
   - 5.6 [Recommendation Engine](#56-recommendation-engine)
   - 5.7 [Dynamic Pricing Model](#57-dynamic-pricing-model)
   - 5.8 [Customer Churn Prediction Model](#58-customer-churn-prediction-model)
   - 5.9 [Knowledge Graph — Customer Behavior](#59-knowledge-graph--customer-behavior)
   - 5.10 [Explainable AI (SHAP & LIME)](#510-explainable-ai-shap--lime)
   - 5.11 [Model Manager](#511-model-manager)
   - 5.12 [Service Layer (Phase 4)](#512-service-layer-phase-4)
   - 5.13 [Performance Tracker & Feedback Loop](#513-performance-tracker--feedback-loop)
   - 5.14 [API Endpoints (FastAPI Routes)](#514-api-endpoints-fastapi-routes)
6. [Backend Service (Node.js · Express)](#6-backend-service-nodejs--express)
   - 6.1 [Server Bootstrap](#61-server-bootstrap)
   - 6.2 [MongoDB Models](#62-mongodb-models)
   - 6.3 [Authentication & Authorization](#63-authentication--authorization)
   - 6.4 [REST API Routes](#64-rest-api-routes)
   - 6.5 [WebSocket / Socket.io Service](#65-websocket--socketio-service)
   - 6.6 [Middleware Stack](#66-middleware-stack)
7. [Frontend (React · Vite · TailwindCSS)](#7-frontend-react--vite--tailwindcss)
8. [Infrastructure & Deployment](#8-infrastructure--deployment)
9. [Model Training & Evaluation Summary](#9-model-training--evaluation-summary)
10. [Model Comparison](#10-model-comparison)
11. [Project Phases Roadmap](#11-project-phases-roadmap)
12. [Key Design Decisions](#12-key-design-decisions)

---

## 1. Project Overview

**Adaptive Business Intelligence (Adaptive BI)** is an end-to-end, production-ready Business Intelligence platform designed for e-commerce businesses. The system ingests continuously generated synthetic e-commerce data, trains multiple machine-learning models, and surfaces real-time predictions and insights through a modern React dashboard.

### Core Problems Solved

| Problem | Solution |
|---|---|
| Predicting next-week sales volume | Sales Forecasting (Random Forest / Linear Regression) |
| Catching fraudulent or unusual transactions | Anomaly Detection (Isolation Forest / One-Class SVM) |
| Personalising product suggestions | Collaborative Filtering (Truncated SVD) |
| Setting the right product price in real time | Dynamic Pricing (RF + LightGBM + XGBoost ensemble) |
| Identifying customers about to leave | Churn Prediction (Gradient Boosting Classifier + SMOTE) |
| Understanding WHY the model made a prediction | Explainable AI (SHAP + LIME) |
| Discovering hidden behaviour patterns | Knowledge Graph (NetworkX MultiDiGraph) |

---

## 2. System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        Client Browser                            │
│              React 18 + Vite + TailwindCSS + Recharts            │
│                         Port 5173                                │
└─────────────────────────────┬────────────────────────────────────┘
                              │ HTTP / WebSocket
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                     Backend API (Node.js)                         │
│           Express 4 + Mongoose + Socket.io + JWT                 │
│                         Port 3000                                │
└────────────┬────────────────┬─────────────────────────────────────┘
             │ MongoDB Driver │ HTTP (axios proxy to AI service)
             ▼                ▼
┌────────────────┐   ┌────────────────────────────────────────────┐
│   MongoDB 6    │   │          AI / ML Service (Python)           │
│   Port 27017   │   │  FastAPI + scikit-learn + XGBoost +         │
└────────────────┘   │  LightGBM + SHAP + LIME + NetworkX         │
        ▲            │                  Port 8000                  │
        │            └──────────────────────┬─────────────────────┘
        │                                   │ Motor (async)
        │           ┌───────────────────────┘
        │           ▼
        │   ┌───────────────┐
        │   │  Redis 7      │
        │   │  Port 6379    │
        │   └───────────────┘
        │
┌───────────────────────────────┐
│  Data Streaming / ETL         │
│  Python · PyMongo · Faker     │
│  Generates + inserts data     │
└───────────────────────────────┘
```

All services are containerised and orchestrated by **Docker Compose**.

---

## 3. Technology Stack

### Frontend
| Library | Purpose |
|---|---|
| React 18 | Component-based UI framework |
| Vite | Lightning-fast build tool / dev server |
| TailwindCSS | Utility-first CSS framework |
| Recharts | SVG-based chart library |
| Socket.io Client | Real-time WebSocket communication |
| Axios | HTTP client (REST calls) |
| React Router v6 | Client-side routing |

### Backend
| Library | Purpose |
|---|---|
| Node.js 18+ | JS runtime |
| Express 4 | Web framework |
| Mongoose | MongoDB ODM |
| Socket.io | Bidirectional real-time events |
| jsonwebtoken | JWT signing / verification |
| bcryptjs | Password hashing |
| Helmet | Security headers |
| express-rate-limit | API throttling |
| Winston | Structured logging |
| Morgan | HTTP request logger |
| compression | Response gzip compression |

### AI / ML Service
| Library | Purpose |
|---|---|
| FastAPI | Async Python web framework |
| Uvicorn | ASGI server |
| scikit-learn | Core ML algorithms + preprocessing |
| XGBoost | Gradient boosted trees |
| LightGBM | Gradient boosted trees (faster) |
| imbalanced-learn (SMOTE) | Class imbalance handling |
| category-encoders | Target encoding for categorical vars |
| SHAP | SHapley Additive exPlanations |
| LIME | Local Interpretable Model-agnostic Explanations |
| NetworkX | Knowledge graph (MultiDiGraph) |
| Pandas / NumPy | Data manipulation |
| Motor | Async MongoDB driver |
| APScheduler | Periodic model retraining scheduler |
| joblib | Model serialisation |
| Plotly / Matplotlib | Visualisation helpers |
| psutil | Memory monitoring |

### Infrastructure
| Tool | Purpose |
|---|---|
| Docker | Container runtime |
| Docker Compose | Multi-service orchestration |
| MongoDB 6 | Primary document store |
| Redis 7 | Caching / session store |

---

## 4. Data Layer — Streaming & Generation

### 4.1 `data_streaming/data_generator.py`

This module creates a synthetic e-commerce dataset using the `Faker` library. It simulates five entity types:

#### Constants
```python
NUM_USERS_TO_GENERATE    = 500   # Initial user pool
NUM_PRODUCTS_TO_GENERATE = 300   # Initial product pool
TRANSACTION_HISTORY_DAYS = 180   # Transactions span last 6 months
FEEDBACK_HISTORY_DAYS    = 60    # Feedback for last 2 months
ACTIVITY_HISTORY_DAYS    = 30    # Activities for last 1 month
```

#### Generator Functions

**`generate_user_data(existing_user_ids)`**  
Creates a user document with a UUID, Faker-generated username/email, a 3-year registration date span, a nested address (street, city, state, zip, country), and timestamps.

**`generate_product_data(existing_product_ids)`**  
Creates products across 10 categories: *Electronics, Books, Home & Kitchen, Apparel, Sports, Beauty, Automotive, Food & Beverage, Toys, Health*. Prices follow a log-normal distribution:
- Electronics/Automotive → `lognormvariate(μ=5.5, σ=0.8)` → capped at $10–$2500
- Other categories → `lognormvariate(μ=4.5, σ=0.5)` → more moderate prices

**`generate_transaction_data(users, products)`**  
Picks a random user and product. Quantity is sampled from a weighted distribution biased toward 1 unit (50%). Transaction status weights: *completed* (×3 weight), *pending*, *failed*, *returned*.

**`generate_feedback_data(users, products)`**  
Creates product reviews with ratings biased heavily toward 5 and 4 stars (50%/30% weight). Includes 15 hand-crafted comment templates.

**`generate_user_activity_data(users, products)`**  
Simulates click-stream events: `viewed_product` (40%), `added_to_cart` (20%), `searched` (15%), `logged_in` (10%), `logged_out` (5%), `removed_from_cart` (5%), `purchased` (5%).

### 4.2 `data_streaming/streaming_etl.py`

The ETL pipeline that drives data insertion into MongoDB.

#### Class: `MongoDBDataLoader`
- **`__init__`** — Connects to MongoDB using PyMongo, pings the server to validate the connection.
- **`create_collections_if_not_exists`** — Ensures collections (`users`, `products`, `transactions`, `feedback`, `useractivities`) are present.
- **`insert_data`** — Bulk-inserts using `insert_many(ordered=False)` for performance; handles `BulkWriteError` gracefully.
- **`get_existing_data_for_generators`** — Fetches only `userId` + `address` from users and `productId` + `price` from products to seed the generators.

### 4.3 `data_streaming/config.py`

```python
config = {
    "mongo_uri": "mongodb://localhost:27017",
    "db_name": "adaptive_bi",
    ...
}
```

### 4.4 `data_streaming/init-mongo.js`

A MongoDB init script (mounted into the Docker container at `/docker-entrypoint-initdb.d/`) that:
- Creates the `adaptive_bi` database
- Adds indexes on `userId`, `productId`, `transactionDate` for query performance
- Ensures an admin user for auth-sourced connections

---

## 5. AI / ML Service (Python · FastAPI)

The AI service is a standalone Python microservice running on **Port 8000**. It exposes a REST API backed by real trained ML models. All models are persisted to disk via `joblib` and re-loaded at startup to avoid retraining from scratch every time.

### 5.1 Configuration & Application Bootstrap

#### `ai_service/app/config.py` — `class Config`

A Python class that reads all settings from environment variables via `os.getenv`:

| Variable | Default | Description |
|---|---|---|
| `AI_SERVICE_HOST` | `0.0.0.0` | Bind address |
| `AI_SERVICE_PORT` | `8000` | Listen port |
| `MONGODB_URL` | `mongodb://localhost:27017/adaptive_bi` | Mongo connection string |
| `DATABASE_NAME` | `adaptive_bi` | Database name |
| `MODEL_SAVE_PATH` | `models/saved_models` | Where `.joblib`/`.pkl` files live |
| `MODEL_RETRAIN_INTERVAL_MINUTES` | `0` (disabled) | Periodic retraining cadence |
| `FORECAST_HORIZON` | `7` | Days to forecast |
| `FORECAST_MODEL_TYPE` | `RandomForestRegressor` | Forecasting algorithm |
| `ANOMALY_THRESHOLD` | `0.05` | Contamination rate |
| `ANOMALY_MODEL_TYPE` | `IsolationForest` | Anomaly algorithm |
| `RECOMMENDER_MODEL_TYPE` | `SVD` | Recommender algorithm |
| `DATA_COLLECTION_DAYS` | `3` | History window for training |
| `MEMORY_SAFE_MODE` | `True` | Aggressive memory management |
| `MAX_TRANSACTIONS_CHUNK` | `2000` | Max records loaded per query |

A singleton `settings = Config()` instance is imported throughout the codebase.

#### `ai_service/app/main.py` — FastAPI Application

The entry point wires everything together using FastAPI's **`lifespan`** context manager (replaces deprecated `startup`/`shutdown` event hooks).

**Startup sequence:**
1. Log memory usage baseline
2. Connect to MongoDB (via Motor async driver)
3. Initialise `ModelManager` (loads or trains Phase 3 models)
4. Create Phase 4 service singletons (`PricingService`, `ChurnService`, `ReasoningService`, `FeedbackService`) with lazy initialisation
5. If `MODEL_RETRAIN_INTERVAL_MINUTES > 0`, schedule `periodic_model_retraining_all` via APScheduler

**`should_retrain_models(retrain_interval)`**  
Intelligent gating function that queries the database to check if enough new data has arrived since the last training run before triggering retraining. Thresholds:
- Testing intervals (≤30 min): 10 new transactions + 2 feedback records
- Production intervals: 100 new transactions + 10 feedback records

**Global ASGI app:**
```python
app = FastAPI(
    title="Adaptive BI AI Service",
    version="1.0.0",
    lifespan=lifespan,
    description="FastAPI AI microservice for Adaptive Business Intelligence."
)
```

**Routers registered:**
```
/api/v1/health      → health.router
/api/v1/forecast    → forecast.router
/api/v1/anomaly     → anomaly.router
/api/v1/recommend   → recommend.router
/api/v1/ai          → advanced_endpoints.router
/api/v1             → explainable_endpoints.router
```

---

### 5.2 Data Processor

**`ai_service/app/services/data_processor.py` — `class DataProcessor`**

Bridge between the ML models and MongoDB. Supports both async (Motor) and sync (PyMongo) clients.

#### Key Methods

**`get_transactions_data(days, limit)`**  
Fetches transactions from the last N days. Renames `transactionDate → timestamp` and `totalPrice → totalAmount` for consistency with feature engineering pipelines. Returns a pandas `DataFrame`.

**`get_user_item_matrix()`**  
Builds a pivot table of user–product interactions for the recommendation engine. Rows = unique users, columns = unique products, values = interaction count.

**`prepare_time_series_data(df, value_col, freq)`**  
Groups transactions by date frequency (e.g., daily `'D'`) and sums the target column to produce a clean time series ready for the forecasting model.

**`get_transactions_data_chunked(days, max_records)`**  
Memory-safe variant that hard-caps the returned rows to prevent OOM during model training.

---

### 5.3 Feature Engineering

**`ai_service/app/services/feature_engineering.py` — `class FeatureEngineer`**

A stateful feature transformer that persists fitted `StandardScaler`/`MinMaxScaler` and `LabelEncoder` instances in instance dictionaries so the same transforms can be applied to new data at prediction time.

#### Methods

**`create_time_features(df, timestamp_col)`**  
Extracts from a datetime column:
- `year`, `month`, `day`, `day_of_week`, `day_of_year`, `week_of_year`, `hour`, `quarter`
- Binary flags: `is_weekend`, `is_month_start`, `is_month_end`

**`create_lag_features(df, cols, lags)`**  
For each target column and each lag value, creates `col_lag_N` columns via `df[col].shift(lag)`. Fills NaN with 0 after shifting.

```python
# Example: lags=[1, 2, 3, 7, 14] on 'totalAmount'
# Creates: totalAmount_lag_1, totalAmount_lag_2, ..., totalAmount_lag_14
```

**`create_rolling_features(df, cols, windows, agg_funcs)`**  
Creates rolling window statistics (mean, std, min, max). Example:
```python
windows=[7, 14], agg_funcs=['mean', 'std']
# Creates: totalAmount_roll_mean_7, totalAmount_roll_std_7,
#          totalAmount_roll_mean_14, totalAmount_roll_std_14
```

**`create_anomaly_features(df, value_col)`**  
Computes 7-day rolling mean, rolling std, deviation from mean, and Z-score for anomaly-focused contexts.

**`scale_features(df, cols, scaler_type, fit)`**  
Scales specified columns. When `fit=True`, a new scaler is fitted and stored in `self.scalers[col]`. When `fit=False`, the stored scaler is used (prevents data leakage).

**`encode_categorical_features(df, cols, encoder_type, fit)`**  
Label-encodes categorical columns. Handles unseen labels gracefully by assigning `-1`.

**`get_features_and_target(df, target_col, feature_cols)`**  
Splits a `DataFrame` into feature matrix `X` and target vector `y`.

---

### 5.4 Sales Forecasting Model

**`ai_service/app/models/forecasting.py` — `class ForecastingModel`**

#### Purpose
Predict daily sales (`totalAmount`) for the next `FORECAST_HORIZON` days (default: 7).

#### Supported Algorithms
| Algorithm | scikit-learn Class | Config Value |
|---|---|---|
| Random Forest | `RandomForestRegressor(n_estimators=100, random_state=42)` | `RandomForestRegressor` |
| Linear Regression | `LinearRegression()` | `LinearRegression` |

#### Instance Variables
```python
self.model           # The trained sklearn model object
self.model_type      # "RandomForestRegressor" or "LinearRegression"
self.feature_engineer  # FeatureEngineer instance (for scaling / lag features)
self.model_path      # Path to save/load the .joblib file
self.is_trained      # Boolean flag
self.metrics         # Dict: {"rmse": float, "r2_score": float, ...}
self._trained_features  # List[str] of column names used during training
```

#### `train(df, target_col='totalAmount')` → `dict`

**Pipeline:**
1. Parse `timestamp` column as datetime and sort ascending
2. Apply `FeatureEngineer.create_time_features` → adds year/month/day/etc.
3. Apply `create_lag_features` with `lags=[1, 2, 3, 7, 14]`
4. Apply `create_rolling_features` with `windows=[7, 14]`, `agg_funcs=['mean', 'std']`
5. Drop NaN rows (`dropna()`)
6. Require minimum `max(14, 14) + 2 = 16` rows after feature creation
7. 80/20 time-ordered split (no random shuffle to respect temporal order)
8. Fit the model on the training portion
9. Evaluate on the test portion: compute **RMSE** and **R² score**
10. Call `save_model()` to persist

**Evaluation Metrics returned:**
```python
{
    "rmse": float,           # Root Mean Squared Error on test set
    "r2_score": float,       # Coefficient of determination
    "trained_on_samples": int,
    "evaluated_on_samples": int
}
```

#### `forecast_future(historical_df, horizon, target_col)` → `DataFrame`

Extends the historical data with `horizon` zero-filled future dates, runs the full feature engineering pipeline on the combined frame, then predicts only the future rows. Returns a DataFrame with columns `[timestamp, totalAmount]`.

#### `save_model()` / `load_model()`
Three files persisted via `joblib`:
- `forecasting_model_RandomForestRegressor.joblib` — the fitted sklearn model
- `forecasting_feature_engineer_RandomForestRegressor.joblib` — the `FeatureEngineer` (with fitted scalers)
- `forecasting_trained_features_RandomForestRegressor.joblib` — the list of feature column names

---

### 5.5 Anomaly Detection Model

**`ai_service/app/models/anomaly_detection.py` — `class AnomalyDetectionModel`**

#### Purpose
Flag unusual transactions (potential fraud, data quality issues, operational anomalies).

#### Supported Algorithms
| Algorithm | scikit-learn Class | Notes |
|---|---|---|
| Isolation Forest | `IsolationForest(contamination=0.05, n_estimators=100, random_state=42)` | Default; tree-based; fast on large data |
| One-Class SVM | `OneClassSVM(kernel='rbf', nu=0.05)` | Kernel-based; better for small datasets |

#### Instance Variables
```python
self.contamination   # Expected anomaly rate (default 0.05 = 5%)
self._trained_features  # Feature columns list saved for consistent prediction
```

#### `train(df, features)` → `dict`

1. Selects the specified feature columns
2. Scales via `MinMaxScaler` (with `fit=True`) — important for SVM distance calculations
3. Fits the unsupervised model
4. Self-evaluates on training data to report outlier count:
```python
{
    "outliers_in_training_data": int,
    "outlier_percentage": "X.XX%"
}
```

#### `detect_anomalies(df, features)` → `DataFrame`

- Scales input features using the **existing fitted scaler** (`fit=False`)
- Aligns columns to `self._trained_features` (fills missing with 0)
- Adds two columns to the returned DataFrame:
  - `anomaly_score` — `decision_function()` output (lower = more anomalous)
  - `is_anomaly` — Boolean (`True` if model returned `-1`)

#### How to interpret scores
- **Isolation Forest** `decision_function`: Negative values → anomaly; positive → normal
- **One-Class SVM** `decision_function`: Negative values → outside the boundary (anomaly)

---

### 5.6 Recommendation Engine

**`ai_service/app/models/recommendation.py` — `class RecommendationModel`**

#### Purpose
Generate personalised product recommendations using **collaborative filtering**.

#### Algorithm: Truncated SVD (Matrix Factorisation)
```python
# User-item interaction matrix R (users × products)
# SVD factorises R ≈ U × Σ × V^T (low-rank approximation)
self.model = TruncatedSVD(n_components=actual_components, random_state=42)
```
`n_components` is capped at `min(n_users, n_items) - 1` and no more than 50.

#### Instance Variables
```python
self.user_item_matrix    # DataFrame: rows=users, cols=products, values=interaction count
self.user_mapper         # Dict: user_id → matrix row index
self.item_mapper         # Dict: product_id → matrix col index
self.user_inverse_mapper # Dict: matrix row index → user_id
self.item_inverse_mapper # Dict: matrix col index → product_id
```

#### `train(data_processor)` → `dict`

1. Calls `DataProcessor.get_user_item_matrix()` to build the pivot table
2. Creates bidirectional ID↔index mappings
3. Converts to a `scipy.sparse.csr_matrix` for memory-efficient SVD
4. Fits `TruncatedSVD`
5. Reports sparsity percentage (typical e-commerce: >99% sparse)

**Metrics returned:**
```python
{
    "users": int,
    "items": int,
    "components": int,
    "total_interactions": int,
    "sparsity_percentage": float
}
```

#### `get_user_recommendations(user_id, num_recommendations, product_data)` → `list`

**For known users:**
1. Reconstructs the approximate rating matrix: `U_transformed × V^T`
2. Gets the predicted ratings row for the target user
3. Removes items the user has already interacted with
4. Returns top-N items by predicted rating

**Cold-start (unknown users):** Falls back to `_get_popular_recommendations()` — sums column totals of the user-item matrix and returns globally popular items.

---

### 5.7 Dynamic Pricing Model

**`ai_service/app/models/advanced_models.py` — `class DynamicPricingModel`**

#### Purpose
Recommend an **optimal price** for each product given real-time demand, competition, inventory, and customer behaviour signals.

#### `prepare_features(data)` — Feature Engineering

The model engineers a rich feature set from raw transaction data:

| Feature Group | Features Created |
|---|---|
| **Time** | `hour`, `day_of_week`, `month`, `quarter`, `is_weekend`, `is_holiday_season` |
| **Demand elasticity** | `demand_ratio` (quantity / 7-day rolling mean), `price_elasticity` (Δprice / Δquantity) |
| **Market** | `market_share` (product's quantity share within category), `competitive_index` (z-score of price within category) |
| **Inventory** | `inventory_turnover` (quantity / stock_level), `stockout_risk` (binary: stock < 3-day rolling demand) |
| **Customer** | `customer_lifetime_value` (total spend per user), `avg_order_value`, `purchase_frequency` |

#### `train(data, target_col='optimal_price')` → `dict`

**Ensemble of three regressors:**
```python
models = {
    'rf':  RandomForestRegressor(n_estimators=100, random_state=42),
    'lgb': lgb.LGBMRegressor(random_state=42, verbose=-1),
    'xgb': xgb.XGBRegressor(random_state=42, verbosity=0)
}
```
All three are trained on the same 80/20 split. The best model (lowest **MAE** on the test set) is selected automatically.

**Metrics returned:**
```python
{
    "best_model": "rf" | "lgb" | "xgb",
    "mae": float,
    "all_scores": {"rf": float, "lgb": float, "xgb": float},
    "feature_count": int
}
```

#### `predict_optimal_price(data, demand_scenario)` → `dict`

After predicting base prices, applies **scenario multipliers**:
| Scenario | Multiplier |
|---|---|
| `high_demand` | ×1.15 |
| `normal` | ×1.0 |
| `low_demand` | ×0.90 |
| `clearance` | ×0.70 |

Prices are clipped to `[0.7×current, 1.5×current]` to prevent extreme swings.

**Output:**
```python
{
    "prices": [float, ...],
    "scenario": str,
    "price_changes": [float, ...],   # % change from current
    "expected_revenue_lift": float   # mean % change
}
```

---

### 5.8 Customer Churn Prediction Model

**`ai_service/app/models/advanced_models.py` — `class ChurnPredictionModel`**

#### Purpose
Predict the probability that each customer will stop making purchases.

#### `prepare_features(data)` — RFM + Behavioural Features

Computes per-customer metrics by grouping transactions by `user_id`:

**RFM (Recency-Frequency-Monetary) Metrics:**
| Feature | Description |
|---|---|
| `recency_days` | Days since last purchase |
| `frequency` | Total number of transactions |
| `total_spent` | Sum of all transaction amounts |
| `avg_order_value` | Mean transaction amount |
| `spending_volatility` | Standard deviation of amounts |

**Behavioural Metrics:**
| Feature | Description |
|---|---|
| `product_diversity` | Count of unique products purchased |
| `category_diversity` | Count of unique categories |
| `customer_lifetime_days` | Days between first and last purchase |
| `avg_days_between_purchases` | `customer_lifetime_days / frequency` |
| `monetary_trend` | `total_spent / customer_lifetime_days` |
| `engagement_score` | `frequency × category_diversity × avg_order_value` |

**Risk Indicator Flags:**
| Feature | Condition |
|---|---|
| `high_recency_risk` | `recency_days > 30` |
| `low_frequency_risk` | `frequency < 3` |
| `declining_value_risk` | `avg_order_value < median(avg_order_value)` |

#### Synthetic Churn Labels (when no ground-truth labels exist)

The model creates labels using **behavioural rules** (deliberately not using recency to avoid data leakage with `recency_days` feature):
```python
churn_conditions = (
    (total_spent < p25 & transaction_count <= 2) |
    (category_count == 1 & product_count == 1 & transaction_count <= 3) |
    (transaction_count == 1) |
    (amount_std > avg_amount & transaction_count <= 3)
)
```
A probabilistic risk score is added to inject controlled randomness, and the churn rate is calibrated to fall between **15–35%**.

#### `train(data, churn_col='churned')` → `dict`

**Class imbalance handling with SMOTE:**
- SMOTE is applied **only** when minority class < 10% AND minority count ≥ 6 AND total samples ≥ 20
- Conservative settings: `k_neighbors = min(5, minority_count - 1)`

**Model:**
```python
GradientBoostingClassifier(
    n_estimators=50,
    learning_rate=0.05,
    max_depth=3,
    min_samples_split=10,
    min_samples_leaf=5,
    subsample=0.8,
    random_state=42
)
```
Regularised to prevent overfitting (reduced n_estimators, shallow depth, high leaf requirements).

**Evaluation Metrics:**
- **ROC-AUC** (primary metric for imbalanced classification)
- Full classification report (precision, recall, F1 per class)
- Feature importances saved to `self.feature_importance`

---

### 5.9 Knowledge Graph — Customer Behavior

**`ai_service/app/models/knowledge_graph.py` — `class CustomerBehaviorGraph`**

#### Purpose
Represent relationships between customers, products, and categories as a directed multigraph, enabling graph-based reasoning that standard ML models cannot capture.

#### Graph Structure
Uses **NetworkX `MultiDiGraph`** — allows multiple directed edges between the same pair of nodes (e.g., multiple purchases of the same product).

**Node types:**
| Node Type | Key Attributes |
|---|---|
| `customer` | `username`, `email`, `registration_date`, `total_spent` (computed) |
| `product` | `name`, `category`, `price`, `stock` |
| `category` | `name`, `product_count` (computed) |

**Edge types:**
| Edge Type | Source → Target | Attributes |
|---|---|---|
| `purchased` | customer → product | `amount`, `quantity`, `transaction_date` |
| `reviewed` | customer → product | `rating`, `feedback_date` |
| `belongs_to` | product → category | — |
| `similar_to` | product ↔ product | `similarity_score`, `co_purchase_count` |
| `similar_customer` | customer ↔ customer | `similarity_score` |

**Memory limits applied:** Max 5,000 users and 100,000 transactions to prevent OOM.

#### `build_graph_from_data(transactions, products, users)` → `dict`
Iterates through all three DataFrames and inserts nodes/edges. Computes per-customer aggregates (total spent, transaction count) and per-product aggregates (avg rating, review count) and stores them as node attributes.

#### `class MemoryMonitor`
A lightweight helper that uses `psutil` to log current process RSS memory usage in MB at different stages of graph construction.

#### Graph I/O
- Save: `networkx.write_gml(self.graph, path)` → `knowledge_graph.gml`
- Load: `networkx.read_gml(path)`

---

### 5.10 Explainable AI (SHAP & LIME)

**`ai_service/app/models/explainable_ai.py` — `class ExplainableAI`**

#### Purpose
Provide human-readable explanations for why any model made a specific prediction.

#### Two Complementary Approaches

**SHAP (SHapley Additive exPlanations)**  
- Game-theory based, assigns each feature a contribution value
- For tree models: uses fast `TreeExplainer`
- For other models: falls back to `KernelExplainer` (model-agnostic)
- Outputs: feature importance bar charts and waterfall plots

**LIME (Local Interpretable Model-agnostic Explanations)**  
- Trains a simple linear model around a single prediction instance
- Works on any black-box model
- Configured via `LimeTabularExplainer` with discretised continuous features

#### `setup_explainer(model, X_train, model_name, explainer_type)` → `dict`

Determines model type (classifier vs. regressor) and sets up the appropriate SHAP explainer and/or LIME explainer. Stores explainers in dictionaries keyed by `model_name`.

```python
self.shap_explainers  # Dict[model_name, shap.Explainer]
self.lime_explainers  # Dict[model_name, lime.LimeTabularExplainer]
self.feature_names    # Dict[model_name, List[str]]
```

#### `explain_prediction_shap(model, X_instance, model_name)` → `dict`

Computes SHAP values for a single prediction instance. Returns:
```python
{
    "feature_contributions": {feature_name: shap_value, ...},
    "base_value": float,
    "prediction": float
}
```

#### Integration with Churn Model

The `/api/v1/explain/churn/{user_id}` endpoint:
1. Fetches the user's transaction history
2. Prepares RFM + behavioural features using `ChurnPredictionModel.prepare_features()`
3. Calls `predict_churn_with_reasoning()` for the raw prediction
4. Runs SHAP on numeric features only (drops `user_id` and string columns)
5. Returns the prediction + feature-level SHAP explanations + model performance metadata

---

### 5.11 Model Manager

**`ai_service/app/models/model_manager.py` — `class ModelManager`**

A **Singleton** that manages the complete lifecycle of all ML models.

```python
class ModelManager:
    _instance = None  # Singleton pattern via __new__

    def __init__(self):
        # Phase 3 models
        self.forecasting_model     = None  # ForecastingModel
        self.anomaly_model         = None  # AnomalyDetectionModel
        self.recommendation_model  = None  # RecommendationModel

        # Phase 4 models
        self.pricing_model         = None  # DynamicPricingModel
        self.churn_model           = None  # ChurnPredictionModel
        self.knowledge_graph       = None  # CustomerBehaviorGraph
        self.explainable_ai        = None  # ExplainableAI

        self.db_connected          = False
        self.models_loaded         = False
        self.last_retrain_time     = None
        self.memory_monitor        = MemoryMonitor()
```

#### `initialize_models()` — Startup Sequence

1. Instantiate all model objects
2. Attempt `load_model()` for each (reads from disk)
3. If load fails, the model is marked not-trained (training triggered via API or scheduler)
4. Phase 4 model paths: `dynamic_pricing_model.pkl`, `churn_model.pkl`, `knowledge_graph.gml`

#### `train_all_models()` — Full Retraining

Trains all Phase 3 models sequentially (memory-safe) with garbage collection after each:
1. Fetch data → Train `ForecastingModel`
2. GC → Fetch data → Train `AnomalyDetectionModel`
3. GC → Fetch data → Train `RecommendationModel`

---

### 5.12 Service Layer (Phase 4)

#### `PricingService`
Wraps `DynamicPricingModel`. Implements lazy initialisation — the model is not loaded/trained until the first API call.

**Key methods:**
- `ensure_initialized()` — triggers `initialize()` on first use
- `_load_and_train_model()` — loads up to 5,000 transactions (max 7 days) + product metadata, merges category info, then calls `DynamicPricingModel.train()`
- `predict_optimal_price_simple(product_id, current_demand, seasonal_factor, competitor_price)` — lightweight wrapper for single-product pricing
- `forecast_impact(product_id, proposed_price)` — simulates revenue impact of a price change
- `_create_mock_training_data()` — fallback synthetic data when fewer than 100 real transactions exist

#### `ChurnService`
Wraps `ChurnPredictionModel` for per-user churn scoring.

**Key methods:**
- `predict_churn_for_user(user_id)` — fetches user-specific transactions, prepares features, returns `{"churn_probability": float, "risk_level": str, "reasoning": [...]}` 
- `get_at_risk_customers(threshold)` — returns all users above a churn probability threshold
- `_prepare_churn_features_for_training(transactions)` — delegates to `ChurnPredictionModel.prepare_features()`

#### `ReasoningService`
Exposes the `CustomerBehaviorGraph` for cognitive insight queries.

**Key methods:**
- `_build_knowledge_graph()` — loads users/products/transactions/feedback/activities from DB and calls `CustomerBehaviorGraph.build_graph_from_data()`
- `get_customer_insights(user_id)` — traverses graph to compute: connected products, categories, purchase patterns, co-customer similarity
- `get_product_recommendations_from_graph(user_id)` — graph-walk-based recommendations (complementary to SVD-based ones)
- `get_market_insights()` — aggregates graph metrics (most connected products, top categories by purchase volume)

#### `FeedbackService`
Orchestrates model retraining triggered by new feedback data.

**Key methods:**
- `initialize()` — attempts to load all models from disk
- `trigger_retraining(model_type, force_retrain)` — dispatches to the correct retraining routine based on `model_type` (`'pricing'`, `'churn'`, `'knowledge_graph'`, `'forecasting'`, `'anomaly'`, `'recommendation'`)
- `record_prediction_feedback(prediction_type, prediction_data, actual_outcome)` — stores feedback to MongoDB `feedback` collection for future training

---

### 5.13 Performance Tracker & Feedback Loop

**`ai_service/app/services/performance_tracker.py`**

Tracks model accuracy over time by persisting evaluation metrics to JSON files in `ai_service/models/performance_history/`:

```
anomaly_detection_performance_history.json
churn_performance_history.json
forecasting_performance_history.json
recommendation_performance_history.json
```

Each entry records `timestamp`, model type, and all evaluation metrics, enabling drift detection over time.

---

### 5.14 API Endpoints (FastAPI Routes)

#### Phase 3 — Core ML Endpoints

**Forecasting (`/api/v1/forecast`)**
| Method | Path | Description |
|---|---|---|
| `POST` | `/train` | Trigger forecasting model training |
| `GET` | `/predict?horizon=7` | Get N-day sales forecast |
| `GET` | `/status` | Model training status + metrics |

**Anomaly Detection (`/api/v1/anomaly`)**
| Method | Path | Description |
|---|---|---|
| `POST` | `/train` | Train the anomaly model |
| `POST` | `/detect` | Detect anomalies in provided data points |
| `GET` | `/status` | Model status + contamination threshold |

The `/detect` endpoint accepts a Pydantic model:
```python
class AnomalyDetectionRequest(BaseModel):
    data_points: List[Dict[str, Any]]
    features: List[str] = ["totalAmount", "quantity"]
```

**Recommendation (`/api/v1/recommend`)**
| Method | Path | Description |
|---|---|---|
| `POST` | `/train` | Train recommendation model |
| `GET` | `/user/{user_id}` | Get personalised recommendations |
| `GET` | `/status` | Model status |

#### Phase 4 — Advanced AI Endpoints (`/api/v1/ai`)

**Dynamic Pricing:**
| Method | Path | Description |
|---|---|---|
| `POST` | `/pricing/predict` | Predict optimal price for a product |
| `POST` | `/pricing/retrain` | Force pricing model retraining |
| `GET` | `/pricing/forecast-impact` | Revenue impact of proposed price |

**Churn Prediction:**
| Method | Path | Description |
|---|---|---|
| `POST` | `/churn/predict` | Predict churn for a user |
| `GET` | `/churn/at-risk` | List all high-risk customers |

**Knowledge Graph / Reasoning:**
| Method | Path | Description |
|---|---|---|
| `GET` | `/reasoning/insights/{user_id}` | Graph-based customer insights |
| `GET` | `/reasoning/market` | Market-level graph insights |
| `POST` | `/reasoning/rebuild` | Rebuild the knowledge graph |

**Feedback:**
| Method | Path | Description |
|---|---|---|
| `POST` | `/feedback/record` | Submit prediction outcome feedback |
| `POST` | `/feedback/retrain/{model_type}` | Trigger specific model retraining |

**Explainable AI (`/api/v1`):**
| Method | Path | Description |
|---|---|---|
| `POST` | `/explain/churn/{user_id}` | SHAP-explained churn prediction |

**Health & Status:**
| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/health` | Service health check |
| `GET` | `/status` | All model readiness flags |

---

## 6. Backend Service (Node.js · Express)

### 6.1 Server Bootstrap

**`backend/server.js` — `class Server`**

An OOP-style server class that wraps Express and Socket.io:

```javascript
class Server {
    constructor() {
        this.app    = express();
        this.server = http.createServer(this.app);
        this.io     = socketIo(this.server, { cors: {...} });
        this.port   = process.env.BACKEND_PORT || 3000;
        this.setupMiddleware();
        this.setupRoutes();
        this.setupSocketIO();
        this.setupErrorHandling();
    }
}
```

**`connectDatabase()`** — Connects Mongoose to MongoDB using the URI from `config.database.uri`, with a connection pool of 10, 5-second server selection timeout, and 45-second socket timeout.

**`gracefulShutdown()`** — Closes the HTTP server, waits for in-flight requests to drain, closes the MongoDB connection, and exits. A 30-second watchdog forcefully exits if the drain takes too long.

---

### 6.2 MongoDB Models

#### `backend/models/User.js`
```javascript
{
  username:            String (unique, maxLength 20),
  email:               String (unique, lowercase, email regex validated),
  password:            String (minLength 8, hashed via bcrypt, not returned in queries),
  role:                String (enum: 'user' | 'admin' | 'superadmin', default 'user'),
  createdAt:           Date,
  passwordChangedAt:   Date,
  passwordResetToken:  String,
  passwordResetExpires:Date
}
```

**Pre-save hooks:**
- `bcrypt.genSalt(10)` + `bcrypt.hash()` — hashes password on creation/change
- Sets `passwordChangedAt = Date.now() - 1000` when password changes (ensures JWT issued at exactly that moment is still valid)

**Instance methods:**
- `matchPassword(enteredPassword)` — `bcrypt.compare()` wrapper
- `getSignedJwtToken()` — signs `{id, role}` payload with `config.app.jwt.secret`
- `changedPasswordAfter(JWTTimestamp)` — security check to invalidate old tokens after password reset

#### `backend/models/Transaction.js`
```javascript
{
  transactionId:   String (unique, indexed),
  userId:          String (required),
  productId:       String (required),
  quantity:        Number (min: 1),
  totalPrice:      Number (min: 0),
  transactionDate: Date (required),
  status:          Enum ['completed', 'pending', 'failed', 'returned'],
  paymentMethod:   Enum ['credit_card', 'paypal', 'bank_transfer', 'crypto', 'other'],
  shippingAddress: { street, city, state, zipCode, country },
  createdAt:       Date
}
```

#### `backend/models/Product.js`
Stores `productId`, `name`, `category`, `price`, `stock`, `description`, `imageUrl`, `addedDate`, `lastUpdated`.

#### `backend/models/Feedback.js`
Stores `feedbackId`, `userId`, `productId`, `rating` (1–5), `comment`, `feedbackDate`.

#### `backend/models/UserActivity.js`
Stores `activityId`, `userId`, `activityType`, `timestamp`, `ipAddress`, `device`, optional `productId` and `searchTerm`.

---

### 6.3 Authentication & Authorization

**`backend/controllers/authController.js`**

- **`register`** — Validates uniqueness, creates a `User` doc, returns a signed JWT
- **`login`** — Finds user by email, calls `matchPassword()`, returns JWT on success
- **`getProfile`** — Returns the authenticated user's profile (protected route)

**`backend/middleware/auth.js`**

JWT verification middleware used to protect routes:
1. Extracts `Bearer <token>` from the `Authorization` header
2. Verifies and decodes using `jsonwebtoken.verify()`
3. Checks `changedPasswordAfter(decoded.iat)` to catch post-token password changes
4. Attaches `req.user` for downstream route handlers

Role-based guard: `authorize(...roles)` — returns 403 if `req.user.role` is not in the allowed set.

---

### 6.4 REST API Routes

| Prefix | Controller | Key Endpoints |
|---|---|---|
| `/api/auth` | `authController` | `POST /register`, `POST /login`, `GET /profile` |
| `/api/users` | `userController` | `GET /`, `GET /:id`, `PUT /:id`, `DELETE /:id` (admin-only for delete) |
| `/api/metrics` | `metricsController` | `GET /sales`, `GET /users`, `GET /products`, `GET /overview` |
| `/api/dashboard` | `dashboardController` | `GET /summary`, `GET /recent-activity` |
| `/api/ai` | `aiController` | Proxies to AI service: `/forecast`, `/anomaly`, `/recommendations`, `/status` |
| `/health` | Inline handler | Service health: uptime, memory, version |

**`backend/controllers/aiController.js`** — Proxies requests to the AI service using `axios`. Handles timeouts and wraps AI service errors into standard API responses.

---

### 6.5 WebSocket / Socket.io Service

**`backend/services/socketService.js`**

Real-time event broadcasting:

| Event | Trigger | Payload |
|---|---|---|
| `dashboard:update` | New transaction inserted | Latest dashboard summary |
| `anomaly:detected` | AI service reports anomaly | Anomaly details |
| `metrics:update` | Periodic (every 30s) | Fresh metrics snapshot |
| `recommendation:new` | User activity event | Personalised recommendations |

The `io` instance is attached to `app.state.io` at startup and accessed by controllers via `req.app.get('io')`.

---

### 6.6 Middleware Stack

| Middleware | Purpose |
|---|---|
| `helmet` | Sets 14 security HTTP headers (CSP, HSTS, X-Frame, etc.) |
| `cors` | Allows `FRONTEND_URL`, `localhost:5174`, `localhost:3001` |
| `express-rate-limit` | 100 requests / 15 minutes per IP on `/api/*` |
| `compression` | Gzip responses for bandwidth reduction |
| `morgan` | HTTP request logging piped to Winston |
| `express.json({ limit: '10mb' })` | Body parsing with size cap |
| `asyncHandler` | Wraps async route handlers; forwards errors to the error handler |
| `errorHandler` | Global error middleware; returns JSON errors with status codes |

---

## 7. Frontend (React · Vite · TailwindCSS)

### 7.1 Application Entry Points

**`frontend/src/main.jsx`** — Renders `<App />` into `#root` with React 18's `createRoot`.

**`frontend/src/App.jsx`** — Router configuration:
```
/login                  → Login page (public)
/register               → Register page (public)
/ (ProtectedRoute)
  /dashboard            → Dashboard
  /analytics            → Analytics (lazy-loaded)
  /ai-insights          → AI Insights (lazy-loaded)
  /health               → System Health (lazy-loaded)
```
Lazy loading is used for Analytics, AI Insights, and Health pages to reduce initial bundle size.

### 7.2 Context & Hooks

**`frontend/src/context/AuthContext.jsx`**  
Provides `user`, `token`, `login(credentials)`, `logout()`, and `isAuthenticated` to the entire app via `useContext(AuthContext)`. Persists the JWT to `localStorage`.

**`frontend/src/hooks/useData.js`**  
Custom hook for fetching data from the backend API:
- Encapsulates loading, error, and data states
- Accepts a URL and optional polling interval for live-updating dashboards

### 7.3 Pages

| Page | File | Key Features |
|---|---|---|
| Dashboard | `pages/Dashboard.jsx` | KPI cards (total sales, users, anomalies), recent transactions, sales trend chart |
| Analytics | `pages/Analytics.jsx` | Sales over time, top products, category breakdown, payment method distribution |
| AI Insights | `pages/AIInsights.jsx` | Forecast charts, anomaly feed, recommendations panel, pricing insights |
| Health | `pages/Health.jsx` | AI service status, model readiness flags, response times |
| Login | `pages/Login.jsx` | JWT-based login form |
| Register | `pages/Register.jsx` | User registration form |
| Customers | `pages/Customers.jsx` | Customer list, churn risk indicators |
| Products | `pages/Products.jsx` | Product catalog with stock and price info |
| Sales | `pages/Sales.jsx` | Transaction history with filters |
| Settings | `pages/Settings.jsx` | User/system settings |
| User Management | `pages/UserManagement.jsx` | Admin-only user role management |

### 7.4 Components

| Component | Description |
|---|---|
| `Layout.jsx` | App shell with `<Sidebar>` + `<Header>` + `<Outlet>` for nested routes |
| `Sidebar.jsx` | Navigation menu with route links |
| `Header.jsx` | Top bar with user info and logout button |
| `ProtectedRoute.jsx` | Redirects to `/login` if `isAuthenticated` is false |
| `AIInsightsDashboard.jsx` | Composite component showing all AI model outputs |
| `ExplainableAI.jsx` | Renders SHAP feature contribution charts |
| `UI.jsx` | Shared UI primitives: `Card`, `Badge`, `Spinner`, `Button`, `Table` |

### 7.5 Services

**`frontend/src/services/api.js`**  
Axios instance pre-configured with `baseURL`, `Authorization: Bearer <token>` header injection, and 401 auto-redirect to login.

**`frontend/src/services/socket.js`**  
Socket.io client that connects to the backend WebSocket server. Exports an `on(event, callback)` helper used by components to subscribe to real-time events.

### 7.6 Utilities

**`frontend/src/utils/constants.js`** — API base URLs, chart colour palettes, role definitions.

**`frontend/src/utils/helpers.js`** — `formatCurrency()`, `formatDate()`, `truncateText()`, `calculatePercentageChange()`.

---

## 8. Infrastructure & Deployment

### 8.1 `docker-compose.yml` Services

| Service | Image / Build | Port | Memory Limit |
|---|---|---|---|
| `mongodb` | `mongo:6.0` | 27017 | Default |
| `redis` | `redis:7.0-alpine` | 6379 | Default |
| `backend` | `./backend/Dockerfile` | 3000 | Default |
| `ai_service` | `./ai_service/Dockerfile` | 8000 | **3 GB** |

The AI service has an explicit 3 GB memory limit (`mem_limit: 3g`) and 1.5 CPU cap because of the in-memory ML models. The `memswap_limit` is set equal to `mem_limit` (disables swap) to make OOM behaviour predictable.

### 8.2 Volumes
- `mongodb_data` — persistent MongoDB storage
- `redis_data` — persistent Redis storage
- `./ai_service/models/saved_models` → `/app/models/saved_models` — model files survive container restarts

### 8.3 Network
A single custom bridge network `adaptive-bi-network` connects all containers, so they can refer to each other by service name (e.g., `mongodb://mongodb:27017`).

### 8.4 Environment Variables (`.env`)

```bash
# Database
MONGO_URI=mongodb://admin:admin123@mongodb:27017/adaptive_bi?authSource=admin
MONGODB_URL=mongodb://admin:admin123@mongodb:27017/adaptive_bi?authSource=admin
DATABASE_NAME=adaptive_bi

# Backend
BACKEND_PORT=3000
JWT_SECRET=<your-secret>
JWT_EXPIRES_IN=24h
FRONTEND_URL=http://localhost:5173

# AI Service
AI_SERVICE_PORT=8000
MODEL_SAVE_PATH=/app/models/saved_models
LOG_LEVEL=INFO

# Model tuning
FORECAST_HORIZON=7
FORECAST_MODEL_TYPE=RandomForestRegressor
ANOMALY_THRESHOLD=0.01
ANOMALY_MODEL_TYPE=IsolationForest
MODEL_RETRAIN_INTERVAL_MINUTES=1440  # 0 = disabled

# Memory management
MEMORY_SAFE_MODE=True
MAX_TRANSACTIONS_CHUNK=2000
DATA_COLLECTION_DAYS=3
```

---

## 9. Model Training & Evaluation Summary

### Sales Forecasting

| Metric | Description |
|---|---|
| **Algorithm** | Random Forest Regressor (default) / Linear Regression |
| **Features** | Time features, 14-day lags, 7/14-day rolling mean & std |
| **Train/Test Split** | 80/20 time-ordered (no random shuffle) |
| **Primary metric** | RMSE (Root Mean Squared Error) |
| **Secondary metric** | R² score |
| **Minimum data** | 16 rows after feature engineering |
| **Persistence** | `forecasting_model_RandomForestRegressor.joblib` |

### Anomaly Detection

| Metric | Description |
|---|---|
| **Algorithm** | Isolation Forest (default) / One-Class SVM |
| **Features** | `totalAmount`, `quantity` (numeric transaction values) |
| **Contamination** | 5% (configurable via `ANOMALY_THRESHOLD`) |
| **Evaluation** | Outlier count + outlier % on training data (unsupervised — no ground truth) |
| **Persistence** | `anomaly_model_IsolationForest.joblib` + feature engineer + trained features |

### Recommendation Engine

| Metric | Description |
|---|---|
| **Algorithm** | Truncated SVD (Collaborative Filtering) |
| **Components** | `min(n_users, n_items) - 1`, capped at 50 |
| **Sparsity** | Typical e-commerce matrices are >99% sparse |
| **Cold-start** | Falls back to global popularity ranking |
| **Evaluation** | Matrix sparsity, user/item counts reported |
| **Persistence** | `recommendation_model_SVD.joblib` + user/item mappers + matrix |

### Dynamic Pricing

| Metric | Description |
|---|---|
| **Algorithms** | Random Forest + LightGBM + XGBoost (ensemble, best-of-three selected) |
| **Selection criterion** | Lowest MAE on 20% test split |
| **Features** | 15+ engineered features (time, demand elasticity, market share, inventory, CLV) |
| **Target** | `optimal_price` (or `price × 1.1` as a synthetic proxy) |
| **Evaluation** | MAE per model, winning model reported |
| **Persistence** | `dynamic_pricing_model.pkl` (model + scaler + feature columns) |

### Churn Prediction

| Metric | Description |
|---|---|
| **Algorithm** | Gradient Boosting Classifier (regularised) |
| **Class imbalance** | SMOTE (conservative, only when minority < 10%) |
| **Features** | 12 RFM + behavioural features |
| **Target** | `churned` (binary: 0/1) |
| **Primary metric** | ROC-AUC |
| **Secondary metrics** | Precision, Recall, F1 (per class, from `classification_report`) |
| **Churn rate** | Calibrated to 15–35% via behavioural rules |
| **Persistence** | `churn_model.pkl`, `GradientBoostingClassifier_churn_model.joblib` |

---

## 10. Model Comparison

### Forecasting: Why Random Forest over Linear Regression?

| Factor | Random Forest | Linear Regression |
|---|---|---|
| Non-linear patterns | ✅ Captures automatically | ❌ Requires manual feature transforms |
| Feature interactions | ✅ Built-in | ❌ Requires manual cross-terms |
| Outlier robustness | ✅ More robust | ❌ Sensitive to outliers |
| Interpretability | ⚠️ Feature importance only | ✅ Direct coefficient interpretation |
| Training speed | ⚠️ Slower | ✅ Very fast |

**Choice:** Random Forest is the default because real-world sales exhibit non-linear seasonality and product-specific patterns that linear regression cannot capture without extensive manual feature engineering.

### Anomaly Detection: Isolation Forest vs One-Class SVM

| Factor | Isolation Forest | One-Class SVM |
|---|---|---|
| Speed on large data | ✅ O(n·log n) | ❌ O(n²) |
| Memory | ✅ Low | ⚠️ Higher with RBF kernel |
| Small datasets | ⚠️ Needs sufficient data | ✅ Works with few samples |
| High-dimensional data | ✅ Good | ⚠️ Degrades |
| Interpretability | ⚠️ Path-based scores | ❌ Distance to hyperplane |

**Choice:** Isolation Forest is the default because transaction datasets are typically large and high-dimensional.

### Dynamic Pricing: Why an Ensemble?

Rather than committing to a single algorithm, the system trains all three (RF, LightGBM, XGBoost) and picks the best by MAE. This "auto-selection" pattern:
- Accounts for different dataset sizes (RF wins on small data; boosting wins on large)
- Requires no manual tuning per deployment
- The winning model is logged for transparency

### Churn: Why Gradient Boosting over Logistic Regression?

- Gradient Boosting captures complex, non-linear churn signals (e.g., engagement score × recency interaction)
- The regularised configuration (`max_depth=3`, `min_samples_leaf=5`, `subsample=0.8`) prevents overfitting on the small synthetic dataset
- SMOTE handles the inherent class imbalance without discarding majority-class data

---

## 11. Project Phases Roadmap

| Phase | Status | Deliverables |
|---|---|---|
| **Phase 1** | ✅ | Data streaming, MongoDB setup, synthetic data generation, ETL pipeline |
| **Phase 2** | ✅ | Backend API (Node.js/Express), JWT auth, REST endpoints, WebSocket (Socket.io) |
| **Phase 3** | ✅ | AI microservice (FastAPI), core ML models (forecasting, anomaly, recommendation), model manager |
| **Phase 4** | ✅ | Advanced AI: dynamic pricing, churn prediction, knowledge graph, explainable AI (SHAP/LIME), feedback loop |
| **Future** | 🔲 | Advanced dashboards, mobile app, multi-tenancy, MLOps pipeline, A/B testing |

---

## 12. Key Design Decisions

### Singleton `ModelManager`
All ML models are managed through a single `ModelManager` instance (enforced via `__new__`). This ensures:
- Models are loaded once at startup and reused across all requests
- No risk of two requests triggering concurrent retraining

### Lazy Initialization of Phase 4 Services
`PricingService`, `ChurnService`, `ReasoningService`, and `FeedbackService` are instantiated at startup but only fully initialised (model loaded/trained) on the first API call. This reduces startup time and memory footprint.

### Memory Safety as a First-Class Concern
The system has dedicated memory management throughout:
- `MemoryMonitor` class using `psutil`
- `force_memory_cleanup()` / `gc.collect()` after every model training step
- `DATA_COLLECTION_DAYS=3` default (rather than 90) to cap dataset size
- `MAX_TRANSACTIONS_CHUNK=2000` hard cap on all DB queries
- 3 GB Docker memory limit with swap disabled for predictable behaviour

### Data-Driven Retraining Gating
Rather than retraining on a blind timer, `should_retrain_models()` queries the database to verify that sufficient new data has arrived. This prevents wasteful retraining cycles during low-activity periods.

### Temporal Train/Test Split
The forecasting model uses a **chronological** 80/20 split rather than a random split. Random splitting would leak future information into the training set, producing artificially high R² scores that don't generalise.

### Synthetic Churn Labels Without Temporal Leakage
The synthetic churn label generation deliberately avoids using `recency_days` as an input to the labelling heuristic, even though `recency_days` appears as a training feature. If labels were defined as "no purchase in the last 30 days" and `recency_days > 30` was also a feature, the model would learn a trivially perfect rule rather than a generalisable pattern.

### API-First Architecture
The AI service is completely decoupled from the backend. The backend treats the AI service as an external HTTP dependency (`aiController.js` proxies calls via `axios`). This means:
- Either service can be scaled or replaced independently
- The AI service can be called directly during development/debugging
- The backend remains stateless with respect to ML state

---

*End of Documentation*
