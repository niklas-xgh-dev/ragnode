FROM node:18-slim

WORKDIR /app

# Copy package.json and package-lock.json
COPY app/svelte/package*.json ./

# Install dependencies
RUN npm install

# Copy Svelte app files
COPY app/svelte/ ./

# Expose port
EXPOSE 3000

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]