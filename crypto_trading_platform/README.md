# CryptoPlatform - Cryptocurrency Trading Platform

A secure, full-featured cryptocurrency investment and trading platform built with Django.

## 🚀 Features

### Core Features
- **User Authentication & Security**
  - Custom user model with email-based authentication
  - Two-factor authentication (2FA) support
  - KYC (Know Your Customer) compliance
  - Brute force protection with Django Axes
  - Comprehensive audit logging

- **Portfolio Management**
  - Real-time portfolio tracking
  - Profit/loss calculations
  - Transaction history
  - Asset allocation analytics
  - Performance metrics

- **Trading Interface**
  - Buy/sell cryptocurrency orders
  - Real-time price updates
  - Order management
  - Trading history
  - Risk management features

- **Market Data**
  - Real-time cryptocurrency prices
  - Market statistics and trends
  - Price alerts and notifications
  - Historical price charts
  - Market analysis tools

- **Real-time Features**
  - WebSocket support for live updates
  - Real-time portfolio value changes
  - Live market data streaming
  - Instant trade notifications

### Security Features
- **Enterprise-level Security**
  - HTTPS enforcement
  - CSRF protection
  - XSS protection
  - SQL injection prevention
  - Rate limiting
  - Session security
  - Audit trail logging

- **Compliance**
  - KYC document management
  - Transaction monitoring
  - Regulatory reporting tools
  - Anti-money laundering (AML) features

## 🛠 Technology Stack

- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **Cache/Message Broker**: Redis
- **Real-time**: Django Channels, WebSockets
- **Task Queue**: Celery
- **Frontend**: Bootstrap 5, Chart.js
- **Authentication**: Django Allauth, django-otp
- **Security**: Django Axes, custom middleware
- **API Integration**: CoinGecko, CoinMarketCap
- **Deployment**: Docker, Docker Compose

## 📦 Installation

### Prerequisites
- Python 3.11+
- PostgreSQL (for production)
- Redis
- Docker & Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd crypto_trading_platform
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Database setup**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Load initial data**
   ```bash
   python manage.py loaddata initial_cryptocurrencies.json
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

### Docker Setup

1. **Build and run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

2. **Run migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   docker-compose exec web python manage.py createsuperuser
   ```

## 🔧 Configuration

### Environment Variables

Key environment variables to configure:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=crypto_platform
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379

# API Keys
COINMARKETCAP_API_KEY=your-api-key
COINGECKO_API_KEY=your-api-key

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### API Keys Setup

1. **CoinGecko API**
   - Sign up at [CoinGecko](https://www.coingecko.com/en/api)
   - Get your API key
   - Add to `.env` file

2. **CoinMarketCap API**
   - Sign up at [CoinMarketCap](https://coinmarketcap.com/api/)
   - Get your API key
   - Add to `.env` file

## 🏗 Architecture

### Project Structure
```
crypto_trading_platform/
├── accounts/           # User management and authentication
├── portfolio/          # Portfolio and transaction management
├── trading/           # Trading functionality
├── market_data/       # Market data and API integration
├── security/          # Security middleware and utilities
├── compliance/        # Compliance and regulatory features
├── templates/         # HTML templates
├── static/           # CSS, JS, images
├── crypto_platform/  # Main Django project
└── requirements.txt
```

### Database Models

- **User**: Custom user model with KYC fields
- **UserProfile**: Extended user preferences
- **Cryptocurrency**: Supported cryptocurrencies
- **Portfolio**: User portfolio container
- **PortfolioHolding**: Individual crypto holdings
- **Transaction**: Trading and transfer history
- **PriceAlert**: User price notifications
- **KYCDocument**: KYC document storage
- **LoginHistory**: Security audit trail

### API Endpoints

- `/api/auth/` - Authentication endpoints
- `/api/portfolio/` - Portfolio management
- `/api/trading/` - Trading operations
- `/api/market-data/` - Market data and prices
- `/api/alerts/` - Price alerts management

### WebSocket Endpoints

- `/ws/market-data/` - Real-time market data
- `/ws/portfolio/<user_id>/` - Portfolio updates
- `/ws/trading/<user_id>/` - Trading notifications

## 🔐 Security

### Security Features Implemented

1. **Authentication Security**
   - Email-based authentication
   - Strong password requirements
   - Two-factor authentication
   - Account lockout protection

2. **Data Protection**
   - HTTPS enforcement
   - Encrypted sensitive data
   - Secure session management
   - CSRF protection

3. **API Security**
   - Rate limiting
   - API key authentication
   - Request validation
   - SQL injection prevention

4. **Audit & Monitoring**
   - Comprehensive logging
   - Login history tracking
   - Transaction monitoring
   - Security event alerts

### Security Best Practices

- Regular security updates
- Penetration testing
- Code security reviews
- Compliance monitoring
- Backup and recovery procedures

## 📊 Monitoring & Analytics

### Logging
- Application logs in `/logs/crypto_platform.log`
- Security events logged separately
- Trading activity monitoring
- Performance metrics tracking

### Metrics
- User activity analytics
- Trading volume statistics
- Portfolio performance metrics
- System performance monitoring

## 🚀 Deployment

### Production Deployment

1. **Server Setup**
   - Ubuntu 20.04+ or similar
   - PostgreSQL 13+
   - Redis 6+
   - Nginx (reverse proxy)
   - SSL certificate

2. **Application Deployment**
   ```bash
   # Clone repository
   git clone <repository-url>
   cd crypto_trading_platform
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Configure environment
   cp .env.example .env
   # Edit .env with production settings
   
   # Database setup
   python manage.py migrate
   python manage.py collectstatic
   
   # Start services
   gunicorn crypto_platform.wsgi:application
   celery -A crypto_platform worker -D
   celery -A crypto_platform beat -D
   ```

3. **Nginx Configuration**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;
       return 301 https://$server_name$request_uri;
   }
   
   server {
       listen 443 ssl;
       server_name yourdomain.com;
       
       ssl_certificate /path/to/certificate.crt;
       ssl_certificate_key /path/to/private.key;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
       
       location /ws/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection "upgrade";
       }
   }
   ```

## 🧪 Testing

### Running Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test accounts
python manage.py test portfolio
python manage.py test trading

# Run with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Test Categories
- Unit tests for models and utilities
- Integration tests for API endpoints
- Security tests for authentication
- Performance tests for trading operations

## 📝 API Documentation

### Authentication
```python
# Login
POST /api/auth/login/
{
    "email": "user@example.com",
    "password": "password123"
}

# Register
POST /api/auth/register/
{
    "email": "user@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Portfolio Management
```python
# Get portfolio
GET /api/portfolio/

# Get holdings
GET /api/portfolio/holdings/

# Get transactions
GET /api/portfolio/transactions/
```

### Trading
```python
# Place buy order
POST /api/trading/orders/
{
    "cryptocurrency": "BTC",
    "order_type": "buy",
    "quantity": "0.1",
    "price": "50000.00"
}

# Get order history
GET /api/trading/orders/
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Write comprehensive tests
- Update documentation
- Ensure security best practices
- Add proper error handling

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Email: support@cryptoplatform.com
- Documentation: [docs.cryptoplatform.com](https://docs.cryptoplatform.com)

## 🔮 Roadmap

### Upcoming Features
- [ ] Advanced trading features (limit orders, stop-loss)
- [ ] Mobile app (React Native)
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
- [ ] Social trading features
- [ ] DeFi integration
- [ ] NFT marketplace
- [ ] Advanced charting tools

### Version History
- **v1.0.0** - Initial release with core features
- **v1.1.0** - Enhanced security and KYC features
- **v1.2.0** - Real-time features and WebSocket support
- **v2.0.0** - Advanced trading and analytics (planned)

---

**⚠️ Disclaimer**: This platform is for educational and demonstration purposes. Always ensure compliance with local regulations when dealing with cryptocurrency trading platforms.

