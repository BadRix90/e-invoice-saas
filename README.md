# E-Invoice SaaS

A modern web application for generating legally compliant electronic invoices for German SMBs, built to meet the upcoming e-invoicing mandate (E-Rechnungspflicht 2025).

## Overview

E-Invoice SaaS enables small and medium-sized businesses in Germany to create, manage, and archive electronic invoices in compliance with EU Directive 2014/55/EU and German e-invoicing regulations.

### Supported Formats

| Format | Description | Use Case |
|--------|-------------|----------|
| **XRechnung** | Pure XML (EN 16931) | B2G invoices, public sector |
| **ZUGFeRD 2.1** | PDF/A-3 with embedded XML | B2B invoices, Factur-X compatible |
| **DATEV Export** | CSV batch export | Tax advisor integration |

## Features

- **Invoice Generation** – Create XRechnung (XML) and ZUGFeRD (PDF) invoices
- **Customer Management** – Store customer data, Leitweg-IDs, and payment terms
- **Product Catalog** – Manage items with prices and VAT rates
- **Invoice Archive** – GoBD-compliant storage (10 years, encrypted)
- **DATEV Export** – CSV export for seamless tax advisor handoff
- **Dashboard** – Revenue statistics, open invoices, payment tracking
- **Validation** – Built-in XRechnung validation (KoSIT Validator)

## Tech Stack

### Backend
- Python 3.12+
- Django 5.x
- Django REST Framework
- PostgreSQL
- Celery + Redis (async tasks)

### Frontend
- Angular 20.x (Standalone Components)
- Angular Signals
- Angular Material

### Infrastructure
- Docker & Docker Compose
- Nginx (reverse proxy)
- Hetzner Cloud / On-Premise

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Git
- Node.js 22+ (for local frontend development)
- Python 3.12+ (for local backend development)

### Quick Start (Docker)

```bash
# Clone the repository
git clone https://github.com/yourusername/e-invoice-saas.git
cd e-invoice-saas

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Run database migrations
docker-compose exec backend python manage.py migrate

# Create superuser
docker-compose exec backend python manage.py createsuperuser
```

The application will be available at:
- **Frontend:** http://localhost:4200
- **Backend API:** http://localhost:8000/api/
- **API Docs:** http://localhost:8000/api/docs/

### Local Development

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements/dev.txt
python manage.py migrate
python manage.py runserver
```

#### Frontend

```bash
cd frontend
npm install
ng serve
```

## Project Structure

```
e-invoice-saas/
├── backend/                 # Django application
│   ├── config/              # Project settings
│   ├── apps/
│   │   ├── invoices/        # Invoice generation & management
│   │   ├── customers/       # Customer management
│   │   ├── products/        # Product catalog
│   │   └── users/           # Authentication & multi-tenancy
│   └── requirements/
├── frontend/                # Angular application
│   └── src/
│       ├── app/
│       │   ├── features/    # Feature modules
│       │   ├── core/        # Singleton services
│       │   └── shared/      # Reusable components
│       └── environments/
├── docker/                  # Docker configurations
└── docs/                    # Documentation
```

## API Documentation

Interactive API documentation is available at `/api/docs/` (Swagger UI) and `/api/redoc/` (ReDoc) when running the backend.

## Deployment Options

| Option | Description | Target |
|--------|-------------|--------|
| **Cloud** | Multi-tenant, hosted on Hetzner | SMBs, quick setup |
| **On-Premise** | Single-tenant, self-hosted | Enterprise, data sovereignty |

## Compliance & Standards

- **XRechnung 3.0** – German CIUS of EN 16931
- **ZUGFeRD 2.1 / Factur-X** – Franco-German hybrid format
- **GoBD** – German archiving requirements (10 years, audit-proof)
- **GDPR** – Data protection compliant

## Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
ng test

# E2E tests
ng e2e
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is proprietary software. All rights reserved.

## Support

- **Documentation:** [docs.example.com](https://docs.example.com)
- **Email:** support@example.com
- **Issues:** GitHub Issues

---

Made with ❤️ in Germany
