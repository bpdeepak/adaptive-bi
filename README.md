# Adaptive Business Intelligence System

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/bpdeepak/adaptive-bi)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Node.js](https://img.shields.io/badge/node.js-18+-green.svg)](https://nodejs.org/)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🎯 Overview

The Adaptive Business Intelligence System is a comprehensive, microservices-based platform that provides real-time business intelligence, advanced machine learning analytics, and explainable AI capabilities for e-commerce businesses. The system combines real-time data streaming, sophisticated AI models, and modern web technologies to deliver actionable insights and predictions.

## 🚀 Key Features

### 🤖 Advanced AI & Machine Learning
- **Sales Forecasting**: Time-series forecasting using Random Forest and Linear Regression models
- **Anomaly Detection**: Real-time anomaly detection using Isolation Forest and One-Class SVM
- **Recommendation Engine**: Collaborative filtering-based product recommendations
- **Dynamic Pricing**: AI-driven pricing optimization with demand elasticity analysis
- **Churn Prediction**: Customer churn prediction with explainable reasoning
- **Explainable AI**: LIME and SHAP integration for model interpretability

### 📊 Real-time Analytics
- **Live Data Streaming**: Continuous data ingestion from multiple sources
- **Real-time Dashboards**: Interactive dashboards with live metrics
- **WebSocket Integration**: Real-time updates for all connected clients
- **Performance Monitoring**: Comprehensive system and model performance tracking

### 🏗️ Modern Architecture
- **Microservices Design**: Scalable, maintainable service architecture
- **Docker Containerization**: Full containerization for easy deployment
- **API-First Approach**: RESTful APIs with comprehensive documentation
- **Event-Driven Architecture**: Asynchronous processing and real-time updates

### 🔐 Security & Authentication
- **JWT-based Authentication**: Secure user authentication and authorization
- **Role-based Access Control**: Granular permissions system
- **API Rate Limiting**: Protection against abuse and DDoS attacks
- **CORS Configuration**: Secure cross-origin resource sharing

## 🏛️ System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Service    │
│   (React)       │◄──►│   (Node.js)     │◄──►│   (FastAPI)     │
│   Port: 5173    │    │   Port: 3000    │    │   Port: 8000    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Data Layer    │
                    │                 │
                    │   MongoDB       │   Redis
                    │   Port: 27017   │   Port: 6379
                    └─────────────────┘
```

## 📁 Project Structure

```
adaptive-bi/
├── frontend/                 # React.js frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Application pages
│   │   ├── services/       # API services
│   │   ├── context/        # React context providers
│   │   └── hooks/          # Custom React hooks
│   ├── package.json
│   └── Dockerfile
│
├── backend/                 # Node.js backend API
│   ├── controllers/        # Request handlers
│   ├── models/            # MongoDB models
│   ├── routes/            # API route definitions
│   ├── middleware/        # Custom middleware
│   ├── services/          # Business logic services
│   ├── utils/             # Utility functions
│   ├── package.json
│   └── Dockerfile
│
├── ai_service/             # Python AI/ML service
│   ├── app/
│   │   ├── models/        # ML models (forecasting, anomaly, etc.)
│   │   ├── api/           # FastAPI routes
│   │   ├── services/      # AI service logic
│   │   ├── utils/         # Utility functions
│   │   └── config.py      # Configuration management
│   ├── requirements.txt
│   └── Dockerfile
│
├── data_streaming/         # Data generation and streaming
│   ├── streaming_etl.py   # Main ETL pipeline
│   ├── data_generator.py  # Synthetic data generation
│   ├── config.py          # Configuration
│   └── requirements.txt
│
├── docs/                   # Documentation
├── docker-compose.yml      # Docker orchestration
├── .env                   # Environment variables
└── README.md              # This file
```

## 🛠️ Technology Stack

### Frontend
- **React 18+**: Modern React with hooks and functional components
- **Vite**: Fast build tool and development server
- **TailwindCSS**: Utility-first CSS framework
- **Recharts**: Data visualization library
- **Socket.io Client**: Real-time communication
- **Axios**: HTTP client for API calls

### Backend
- **Node.js 18+**: JavaScript runtime
- **Express.js**: Web application framework
- **Socket.io**: Real-time bidirectional communication
- **Mongoose**: MongoDB object modeling
- **JWT**: JSON Web Token authentication
- **Winston**: Logging library
- **Helmet**: Security middleware

### AI/ML Service
- **Python 3.10+**: Programming language
- **FastAPI**: Modern, fast web framework
- **scikit-learn**: Machine learning library
- **XGBoost/LightGBM**: Gradient boosting frameworks
- **Pandas/NumPy**: Data manipulation libraries
- **LIME/SHAP**: Explainable AI libraries
- **MLflow**: ML lifecycle management
- **Redis**: Caching and session storage

### Databases & Infrastructure
- **MongoDB**: NoSQL document database
- **Redis**: In-memory data store
- **Docker**: Containerization platform
- **Docker Compose**: Multi-container orchestration

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Node.js 18+ (for local development)
- Python 3.10+ (for local development)
- 8GB+ RAM (recommended for AI models)

### 1. Clone the Repository
```bash
git clone https://github.com/bpdeepak/adaptive-bi.git
cd adaptive-bi
```

### 2. Environment Setup
Create a `.env` file in the project root with the following variables:
```bash
# Database Configuration
MONGO_URI=mongodb://admin:admin123@mongodb:27017/adaptive_bi?authSource=admin
REDIS_URL=redis://redis:6379

# Backend Configuration
BACKEND_PORT=3000
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRES_IN=24h
FRONTEND_URL=http://localhost:5173

# AI Service Configuration
AI_SERVICE_PORT=8000
MODEL_SAVE_PATH=/app/models/saved_models
LOG_LEVEL=INFO

# Model Configuration
FORECAST_HORIZON=7
FORECAST_MODEL_TYPE=RandomForestRegressor
ANOMALY_THRESHOLD=0.01
ANOMALY_MODEL_TYPE=IsolationForest
MODEL_RETRAIN_INTERVAL_MINUTES=1440

# Data Configuration
DATA_COLLECTION_DAYS=90
```

### 3. Start the System
```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Access the Application
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:3000
- **AI Service**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

### 5. Initial Setup
```bash
# Generate sample data
cd data_streaming
python streaming_etl.py

# Create admin user (via API)
curl -X POST http://localhost:3000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "password123",
    "role": "admin"
  }'
```

## 📊 Available Models & APIs

### Machine Learning Models

#### 1. Sales Forecasting Model
- **Endpoint**: `GET /forecast`
- **Description**: Predicts future sales based on historical data
- **Models**: Random Forest Regressor, Linear Regression
- **Features**: Time series analysis, seasonal patterns, trend detection

#### 2. Anomaly Detection Model
- **Endpoint**: `POST /anomaly/detect`
- **Description**: Detects unusual patterns in transaction data
- **Models**: Isolation Forest, One-Class SVM
- **Use Cases**: Fraud detection, system monitoring, quality control

#### 3. Recommendation Engine
- **Endpoint**: `GET /recommendations`
- **Description**: Provides personalized product recommendations
- **Algorithm**: Collaborative filtering with matrix factorization
- **Features**: User-item interactions, content-based filtering

#### 4. Dynamic Pricing Model
- **Endpoint**: `POST /pricing-simulation`
- **Description**: AI-driven pricing optimization
- **Features**: Demand elasticity, competitive analysis, market trends

#### 5. Churn Prediction Model
- **Endpoint**: `GET /explain/churn/:userId`
- **Description**: Predicts customer churn probability
- **Features**: Customer behavior analysis, engagement metrics, purchase patterns

### API Endpoints

#### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/profile` - Get user profile

#### Analytics & Metrics
- `GET /api/metrics/sales` - Sales analytics
- `GET /api/metrics/users` - User analytics
- `GET /api/dashboard/summary` - Dashboard overview

#### AI & Machine Learning
- `GET /ai/forecast` - Sales forecasting
- `POST /ai/anomaly` - Anomaly detection
- `GET /ai/recommendations` - Product recommendations
- `GET /ai/status` - AI service status

## 🔧 Configuration

### Model Configuration
Models can be configured via environment variables:

```bash
# Forecasting Model
FORECAST_HORIZON=7                    # Days to forecast
FORECAST_MODEL_TYPE=RandomForestRegressor  # Model type

# Anomaly Detection
ANOMALY_THRESHOLD=0.01               # Contamination rate
ANOMALY_MODEL_TYPE=IsolationForest   # Model type

# Recommendation System
MIN_INTERACTIONS_FOR_RECOMMENDATION=5  # Minimum user interactions
RECOMMENDER_MODEL_TYPE=SVD            # Recommendation algorithm

# Training Configuration
MODEL_RETRAIN_INTERVAL_MINUTES=1440  # Retrain every 24 hours
DATA_COLLECTION_DAYS=90              # Days of data for training
```

### Performance Tuning
```bash
# Memory limits for AI service
AI_SERVICE_MEMORY_LIMIT=3g
AI_SERVICE_CPU_LIMIT=1.5

# Database optimization
MONGO_CACHE_SIZE=1g
REDIS_MAX_MEMORY=512mb
```

## 📈 Monitoring & Logging

### Health Checks
- **Backend**: `GET /health`
- **AI Service**: `GET /health`
- **Model Status**: `GET /ai/status`

### Logging
- Application logs: `./logs/`
- AI service logs: `./ai_service/logs/`
- Database logs: Docker container logs

### Performance Metrics
- Response times
- Model accuracy metrics
- System resource usage
- Error rates and alerts

## 🧪 Testing

### Running Tests
```bash
# Backend tests
cd backend
npm test

# AI service tests
cd ai_service
python -m pytest tests/

# Frontend tests
cd frontend
npm test
```

### Test Coverage
- Unit tests for all models
- Integration tests for APIs
- End-to-end tests for critical workflows

## 🚀 Deployment

### Production Deployment
```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy to production
docker-compose -f docker-compose.prod.yml up -d
```

### Scaling
```bash
# Scale AI service
docker-compose up -d --scale ai_service=3

# Scale backend
docker-compose up -d --scale backend=2
```

## 🔒 Security Considerations

- JWT token expiration and refresh
- API rate limiting and throttling
- Input validation and sanitization
- CORS configuration
- Docker security best practices
- Regular security updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow established coding standards
- Write comprehensive tests
- Update documentation
- Ensure Docker builds succeed

## 📚 Documentation

- [API Documentation](http://localhost:8000/docs) - Interactive API docs
- [Model Documentation](./docs/models.md) - ML model specifications
- [Deployment Guide](./docs/deployment.md) - Production deployment
- [Troubleshooting](./docs/troubleshooting.md) - Common issues and solutions

## 🐛 Troubleshooting

### Common Issues

#### Docker Issues
```bash
# Reset Docker containers
docker-compose down -v
docker-compose up --build

# Check container logs
docker-compose logs <service_name>
```

#### Model Training Issues
```bash
# Check AI service logs
docker-compose logs ai_service

# Manually retrain models
curl -X POST http://localhost:8000/train/all
```

#### Database Connection Issues
```bash
# Reset database
docker-compose down -v mongodb
docker-compose up -d mongodb
```

## 📋 Roadmap

### Phase 1 ✅
- [x] Foundation & Data Streaming
- [x] MongoDB setup and data generation
- [x] Basic ETL pipeline

### Phase 2 ✅
- [x] Backend API Development
- [x] Authentication & authorization
- [x] RESTful APIs and WebSocket integration

### Phase 3 ✅
- [x] AI Microservice Foundation
- [x] Core ML models (forecasting, anomaly, recommendation)
- [x] Model management and training

### Phase 4 ✅
- [x] Advanced AI & Cognitive Reasoning
- [x] Dynamic pricing and churn prediction
- [x] Explainable AI integration
- [x] Model feedback and optimization

### Future Enhancements
- [ ] Advanced visualization dashboard
- [ ] Mobile application
- [ ] Multi-tenant architecture
- [ ] Advanced MLOps pipeline
- [ ] Real-time model deployment
- [ ] A/B testing framework

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

- **Project Lead & Owner**: [Deepak BP](https://github.com/bpdeepak)
- **AI/ML Engineer**: [Chandan HK](https://github.com/chandanhk304)
- **Backend Developer**: [Aditya GS](https://github.com/adityamsrit)
- **Frontend Developer**: [Gaurav Kumar](https://github.com/Gauravkr28)

## 📞 Support

For support and questions:
- Create an issue on [GitHub](https://github.com/bpdeepak/adaptive-bi/issues)
- Email: bpdeepak@example.com
- Documentation: [Project Repository](https://github.com/bpdeepak/adaptive-bi)

---

**Built with ❤️ using modern technologies and best practices**
