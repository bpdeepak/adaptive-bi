# Adaptive BI Frontend

A modern React-based dashboard for the Adaptive Business Intelligence system with real-time visualizations, AI insights, and interactive analytics.

## Features

- 🔐 **Authentication System** - JWT-based login with role management
- 📊 **Real-time Dashboard** - Live KPI tracking and data visualization
- 📈 **Advanced Analytics** - Deep insights into business performance
- 🤖 **AI Insights** - Machine learning predictions and recommendations
- 🔄 **WebSocket Integration** - Real-time data updates
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile
- 🎨 **Modern UI** - Built with TailwindCSS and Lucide icons

## Technology Stack

- **React 18** - Modern React with hooks and context
- **Vite** - Fast build tool and development server
- **TailwindCSS** - Utility-first CSS framework
- **Recharts** - Responsive chart library
- **Axios** - HTTP client for API calls
- **Socket.io Client** - Real-time communication
- **React Router** - Client-side routing
- **React Hot Toast** - Beautiful notifications

## Getting Started

### Prerequisites

- Node.js 16+ and npm
- Backend API running on port 3000
- AI Service running on port 8000

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start development server:
```bash
npm run dev
```

The application will be available at `http://localhost:5173`

## Quick Start

For the fastest setup, use the development script:

```bash
./start-dev.sh
```

This script will:
- Install dependencies if needed
- Create .env file with defaults
- Start the development server

## Environment Variables

Create a `.env` file in the root directory:

```env
# Backend API URL
VITE_BACKEND_URL=http://localhost:3000

# AI Service URL  
VITE_AI_SERVICE_URL=http://localhost:8000

# Environment
VITE_NODE_ENV=development
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Layout.jsx      # Main layout wrapper
│   ├── KPICard.jsx     # Key performance indicator cards
│   ├── ChartCard.jsx   # Chart container component
│   └── StatusIndicator.jsx # Status display component
├── contexts/           # React contexts for state management
│   ├── AuthContext.jsx # Authentication state
│   ├── DataContext.jsx # Application data state
│   └── SocketContext.jsx # WebSocket connection
├── pages/              # Main application pages
│   ├── Login.jsx       # Authentication page
│   ├── Dashboard.jsx   # Main dashboard
│   ├── Analytics.jsx   # Advanced analytics
│   └── AIInsights.jsx  # AI predictions & insights
├── services/           # External service integrations
│   └── api.js         # API configuration and endpoints
├── App.jsx            # Main application component
├── main.jsx           # Application entry point
└── index.css          # Global styles and Tailwind imports
```

## Features Overview

### Dashboard
- Real-time KPI metrics
- Revenue vs target charts
- Sales by category breakdown
- User activity monitoring
- Recent activity feed

### Analytics
- Sales trend analysis
- Product performance metrics
- Customer segmentation
- Cohort retention analysis
- Exportable reports

### AI Insights
- Revenue forecasting
- Anomaly detection
- AI model performance metrics
- Explainable AI features
- Automated recommendations

## API Integration

The frontend integrates with two main services:

### Backend API (Node.js)
- Authentication endpoints
- Dashboard data aggregation
- Real-time WebSocket updates
- Business metrics APIs

### AI Service (FastAPI)
- Machine learning predictions
- Anomaly detection
- Recommendation engine
- Model performance metrics

## Real-time Features

The application uses WebSocket connections for:
- Live dashboard updates
- Real-time metric changes
- System status notifications
- AI model updates

## Building for Production

1. Build the application:
```bash
npm run build
```

2. The built files will be in the `dist/` directory

3. Serve using any static file server:
```bash
npm run preview
```

## Contributing

1. Follow the existing code structure
2. Use TypeScript for type safety (optional)
3. Ensure responsive design
4. Add proper error handling
5. Include loading states for async operations

## Troubleshooting

### Common Issues

1. **WebSocket connection fails**
   - Check if backend is running
   - Verify CORS settings
   - Check firewall settings

2. **Charts not rendering**
   - Ensure data format matches chart expectations
   - Check for missing dependencies
   - Verify responsive container setup

3. **Authentication issues**
   - Clear localStorage tokens
   - Check API endpoint URLs
   - Verify JWT token format

### Development Tips

- Use React DevTools for debugging
- Check browser console for errors
- Monitor network tab for API calls
- Use the Redux DevTools for state inspection

## ✅ Issue Resolution

### Fixed: TailwindCSS Configuration Error
The initial setup had invalid CSS classes (`border-border`, `bg-background`) that don't exist in standard TailwindCSS. These have been replaced with proper utility classes:

- `border-border` → `border-gray-200`
- `bg-background text-foreground` → `bg-gray-50 text-gray-900`

### Status: ✅ Working
- ✅ Development server running on http://localhost:5173
- ✅ All React components created and functional
- ✅ TailwindCSS properly configured
- ✅ All dependencies installed
- ✅ Environment variables configured

## License

This project is part of the Adaptive Business Intelligence system.
