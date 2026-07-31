FROM node:20-slim AS builder

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Multi-stage fallback for production or dev
EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
