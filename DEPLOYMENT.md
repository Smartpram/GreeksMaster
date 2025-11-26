# 🚀 MyBreezeApp Deployment Guide

## Quick Start

### 1. Automated Setup
```bash
python setup.py
```
This will create all necessary files, directories, and configurations.

### 2. Manual Setup (Alternative)

#### Prerequisites
- Python 3.8 or higher
- ICICIDirect Breeze API credentials
- Git (optional)

#### Installation Steps

1. **Clone/Download the project**
   ```bash
   git clone <repository-url>
   cd MyBreezeApp
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   - Copy `.env.example` to `.env`
   - Update with your API credentials

4. **Run tests**
   ```bash
   python -m pytest tests/ -v
   ```

5. **Start the application**
   ```bash
   python -m flask run
   ```

## 🔧 Configuration

### Environment Variables (.env file)

```env
# Essential Settings
BREEZE_API_KEY=your_api_key_here
BREEZE_SECRET_KEY=your_secret_key_here
BREEZE_USER_ID=your_user_id
BREEZE_PASSWORD=your_password

# Trading Configuration
PAPER_TRADING=True  # Set to False for live trading
DEFAULT_CAPITAL=100000
MAX_POSITION_SIZE=0.1  # 10% of capital per position

# Risk Management
DEFAULT_STOP_LOSS=0.05  # 5%
DEFAULT_TARGET=0.15     # 15%
MAX_DAILY_LOSS=0.02     # 2%

# Strategy Parameters
TREND_PERIOD=20
RSI_PERIOD=14
RSI_OVERBOUGHT=70
RSI_OVERSOLD=30
```

### API Credentials Setup

1. **Get ICICIDirect Breeze API credentials:**
   - Register at ICICIDirect Breeze API portal
   - Generate API key and secret
   - Note your user ID and password

2. **Update .env file:**
   ```env
   BREEZE_API_KEY=your_actual_api_key
   BREEZE_SECRET_KEY=your_actual_secret_key
   BREEZE_USER_ID=your_actual_user_id
   BREEZE_PASSWORD=your_actual_password
   ```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

1. **Build and start:**
   ```bash
   docker-compose up -d
   ```

2. **View logs:**
   ```bash
   docker-compose logs -f
   ```

3. **Stop:**
   ```bash
   docker-compose down
   ```

### Using Docker directly

1. **Build image:**
   ```bash
   docker build -t mybreeze-app .
   ```

2. **Run container:**
   ```bash
   docker run -d -p 5000:5000 --env-file .env mybreeze-app
   ```

## ☁️ Cloud Deployment

### AWS Elastic Beanstalk

1. **Install EB CLI:**
   ```bash
   pip install awsebcli
   ```

2. **Initialize and deploy:**
   ```bash
   eb init
   eb create mybreeze-app-env
   eb deploy
   ```

3. **Set environment variables:**
   ```bash
   eb setenv BREEZE_API_KEY=your_key BREEZE_SECRET_KEY=your_secret
   ```

### Digital Ocean Droplet

1. **Create Ubuntu droplet**
2. **Install dependencies:**
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   ```

3. **Deploy application:**
   ```bash
   git clone <your-repo>
   cd MyBreezeApp
   pip3 install -r requirements.txt
   ```

4. **Configure Nginx (optional):**
   ```nginx
   server {
       listen 80;
       server_name your_domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Heroku

1. **Install Heroku CLI**
2. **Create Procfile:**
   ```
   web: python -m flask run --host=0.0.0.0 --port=$PORT
   ```

3. **Deploy:**
   ```bash
   heroku create mybreeze-app
   git push heroku main
   heroku config:set BREEZE_API_KEY=your_key
   ```

## 🔒 Security Considerations

### Production Checklist

- [ ] Change default SECRET_KEY
- [ ] Set DEBUG=False
- [ ] Use HTTPS in production
- [ ] Secure API credentials
- [ ] Set up proper logging
- [ ] Configure firewall
- [ ] Regular backups
- [ ] Monitor resource usage

### API Security

```python
# Use environment variables, never hardcode
BREEZE_API_KEY = os.getenv('BREEZE_API_KEY')

# Validate and sanitize inputs
def validate_stock_symbol(symbol):
    return re.match(r'^[A-Z]{1,10}$', symbol)
```

## 📊 Monitoring & Maintenance

### Log Monitoring

```bash
# View application logs
tail -f logs/mybreeze.log

# View error logs
grep ERROR logs/mybreeze.log

# View trading activity
grep "ORDER" logs/mybreeze.log
```

### Health Checks

```bash
# Check application status
curl http://localhost:5000/health

# Check API connectivity
curl http://localhost:5000/api/status
```

### Backup Strategy

```bash
# Database backup
cp mybreeze.db backups/mybreeze_$(date +%Y%m%d).db

# Configuration backup
cp .env backups/env_$(date +%Y%m%d).backup
```

## 🚦 Testing in Production

### Paper Trading Mode

1. **Enable paper trading:**
   ```env
   PAPER_TRADING=True
   ```

2. **Monitor virtual trades:**
   - Check logs for simulated orders
   - Verify strategy performance
   - Test risk management

3. **Validate before live trading:**
   - Run for at least 1-2 weeks
   - Check all indicators working
   - Verify notification systems

### Live Trading Transition

1. **Gradual approach:**
   ```env
   PAPER_TRADING=False
   DEFAULT_CAPITAL=10000  # Start small
   MAX_POSITION_SIZE=0.05  # Conservative
   ```

2. **Monitor closely:**
   - Watch first few trades carefully
   - Check order execution
   - Verify risk management

## 🆘 Troubleshooting

### Common Issues

**Issue: API Connection Failed**
```
Solution: Check API credentials and network connectivity
```

**Issue: Insufficient Funds**
```
Solution: Verify account balance and position sizing
```

**Issue: Orders Not Executing**
```
Solution: Check market hours and stock availability
```

### Debug Mode

```bash
# Enable debug logging
export DEBUG=True
export LOG_LEVEL=DEBUG

# Run with verbose output
python -m flask run --debug
```

### Recovery Procedures

1. **Application crash:**
   ```bash
   # Check logs
   tail -100 logs/mybreeze.log
   
   # Restart application
   docker-compose restart
   ```

2. **Data corruption:**
   ```bash
   # Restore from backup
   cp backups/mybreeze_latest.db mybreeze.db
   ```

## 📞 Support

### Getting Help

1. **Check logs first:**
   ```bash
   grep ERROR logs/mybreeze.log
   ```

2. **Test connectivity:**
   ```bash
   python -c "from app.services.breeze_api import BreezeAPIService; print('API OK')"
   ```

3. **Validate configuration:**
   ```bash
   python -c "from app.config import Config; c=Config(); print('Config OK')"
   ```

### Performance Optimization

- **Database optimization:** Regular cleanup of old data
- **Memory usage:** Monitor pandas DataFrame usage
- **API rate limits:** Implement proper request throttling
- **Logging:** Use appropriate log levels in production

---

## 🎯 Next Steps After Deployment

1. **Monitor Performance:** Track strategy effectiveness
2. **Optimize Parameters:** Adjust based on market conditions
3. **Scale Gradually:** Increase capital allocation slowly
4. **Add Features:** Implement additional indicators or strategies
5. **Backup Regularly:** Maintain data and configuration backups