# High-Performance FastAPI Gateway

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688.svg)](https://fastapi.tiangolo.com/)
[![Redis](https://img.shields.io/badge/Redis-7.2-red.svg)](https://redis.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A **production-grade API Gateway** built with FastAPI, designed for high throughput, low latency, and ease of extensibility.

## 🚀 Features

- **High Performance**: Built on Starlette and Pydantic for maximum speed.
- **Rate Limiting**: Redis-backed distributed rate limiting (Token Bucket).
- **Caching**: Smart response caching with Redis.
- **Async Architecture**: Fully asynchronous capability for IO-bound operations.
- **Middleware**: Request tracking, unique IDs, structured logging.
- **Scalable**: Dockerized and ready for Kubernetes orchestration.

## 📁 Project Structure

```
backend-fastapi-high-performance-gateway/
├── app/
│   ├── api/          # API Route Controllers
│   ├── core/         # Config, Security, Events
│   ├── middleware/   # Custom Middleware (Rate Limit, Logging)
│   ├── schemas/      # Pydantic Models
│   ├── services/     # Business Logic & External Calls
│   └── main.py       # Application Entrypoint
├── tests/            # Pytest Suite
├── Dockerfile        # Production Docker Image
├── docker-compose.yml# Local Dev Environment
└── pyproject.toml    # Dependency Management
```

## 🛠️ Quick Start

```bash
# Clone the repository
git clone https://github.com/Shivay00001/backend-fastapi-high-performance-gateway.git

# Run with Docker Compose (includes Redis)
docker-compose up --build

# Access Documentation
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

## ⚡ Benchmarks

Designed to handle 10k+ req/sec on modest hardware with proper tuning.

## 📄 License

MIT License
