# Frontend Dockerfile for Adaptive BI System
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies for Vite)
RUN npm install

# Copy source code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose ports
EXPOSE 5173 3001

# For development, we'll use npm run dev
# For production, you'd build and serve with nginx
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
