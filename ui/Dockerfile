# Builder stage - install dependencies and build
FROM node:20-slim as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY ui/package*.json ui/yarn.lock ./

# Install dependencies
RUN yarn install --frozen-lockfile

# Copy source code
COPY ui/ ./

# Build the application
RUN yarn build

# Runtime stage - serve with serve
FROM node:20-slim

# Install serve globally
RUN npm install -g serve

# Set working directory
WORKDIR /app

# Copy built assets from builder
COPY --from=builder /app/dist ./dist

# Expose port 3000
EXPOSE 3000

# Serve the application
CMD ["serve", "-s", "dist", "-l", "3000"]
