# Build stage
FROM node:18-alpine AS builder
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install --no-fund --no-audit

# Copy source code including .env file
COPY . .

# Build with environment variables
ARG REACT_APP_GOOGLE_CLIENT_ID
ARG REACT_APP_API_URL
ENV REACT_APP_GOOGLE_CLIENT_ID=${REACT_APP_GOOGLE_CLIENT_ID}
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

RUN npm run build

# Production stage
FROM node:18-alpine
WORKDIR /app

# Copy built app
COPY --from=builder /app/build ./build

# Install serve
RUN npm install -g serve

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]