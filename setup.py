#!/usr/bin/env python3
"""
GreeksMaster Setup and Installation Script
"""
import os
import sys
import subprocess
import platform
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    print("🔍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    print(f"✅ Python {sys.version.split()[0]} detected")

def install_dependencies():
    """Install required Python packages"""
    print("📦 Installing dependencies...")
    
    requirements = [
        "flask>=2.3.0",
        "pandas>=1.5.0",
        "numpy>=1.24.0",
        "requests>=2.28.0",
        "python-dotenv>=1.0.0",
        "flask-cors>=4.0.0",
        "cryptography>=3.4.8",
        "jwt>=1.3.1",
        "pyjwt>=2.6.0",
        "yfinance>=0.2.0",  # For backtesting data
        "plotly>=5.15.0",   # For charts
        "dash>=2.10.0",     # For interactive dashboard
        "dash-bootstrap-components>=1.4.0",
        "APScheduler>=3.10.0",  # For scheduling
        "sqlalchemy>=2.0.0",    # For database
        "flask-sqlalchemy>=3.0.0",
        "alembic>=1.11.0",      # For database migrations
        "pytest>=7.4.0",        # For testing
        "pytest-cov>=4.1.0",    # For test coverage
        "black>=23.0.0",        # For code formatting
        "flake8>=6.0.0",        # For code linting
    ]
    
    try:
        for package in requirements:
            print(f"  Installing {package}...")
            subprocess.run([sys.executable, "-m", "pip", "install", package], 
                         check=True, capture_output=True)
        print("✅ All dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)

def create_environment_file():
    """Create .env file with default configuration"""
    print("⚙️  Creating environment configuration...")
    
    env_content = """# GreeksMaster Configuration
# Flask Settings
SECRET_KEY=your-secret-key-change-this-in-production
DEBUG=True
FLASK_ENV=development

# ICICIDirect Breeze API Settings
BREEZE_API_KEY=your_breeze_api_key_here
BREEZE_SECRET_KEY=your_breeze_secret_key_here
BREEZE_SESSION_TOKEN=your_session_token_here
BREEZE_USER_ID=your_user_id_here
BREEZE_PASSWORD=your_password_here

# Trading Settings
PAPER_TRADING=True
DEFAULT_CAPITAL=100000
MAX_POSITION_SIZE=0.1

# Risk Management Settings
DEFAULT_STOP_LOSS=0.05
DEFAULT_TARGET=0.15
TRAILING_STOP_LOSS=0.03
MAX_DAILY_LOSS=0.02

# Strategy Settings
TREND_PERIOD=20
RSI_PERIOD=14
RSI_OVERBOUGHT=70
RSI_OVERSOLD=30

# Notification Settings
EMAIL_ENABLED=False
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=your_email@gmail.com

# Telegram Settings (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id

# Database Settings
DATABASE_URL=sqlite:///mybreeze.db

# Logging Settings
LOG_LEVEL=INFO
LOG_FILE=logs/mybreeze.log
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ .env file created with default settings")
        print("⚠️  Please update .env file with your actual API credentials")
    else:
        print("ℹ️  .env file already exists")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "logs",
        "data",
        "backups",
        "reports",
        "static/css",
        "static/js",
        "static/images",
        "templates"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("✅ All directories created")

def setup_database():
    """Initialize database"""
    print("🗄️  Setting up database...")
    
    try:
        # Import here to avoid import errors before dependencies are installed
        from app.models import db
        from app.main import create_app
        
        app = create_app()
        with app.app_context():
            db.create_all()
        
        print("✅ Database initialized successfully")
    except ImportError:
        print("ℹ️  Database setup will be completed on first run")
    except Exception as e:
        print(f"⚠️  Database setup warning: {e}")

def create_startup_scripts():
    """Create startup scripts for different platforms"""
    print("🚀 Creating startup scripts...")
    
    # Windows batch script
    windows_script = """@echo off
echo Starting MyBreezeApp...
cd /d "%~dp0"
set FLASK_APP=app.main:app
set FLASK_ENV=development
python -m flask run --host=0.0.0.0 --port=5000
pause
"""
    
    with open("start_windows.bat", "w") as f:
        f.write(windows_script)
    
    # Linux/Mac shell script
    unix_script = """#!/bin/bash
echo "Starting MyBreezeApp..."
cd "$(dirname "$0")"
export FLASK_APP=app.main:app
export FLASK_ENV=development
python3 -m flask run --host=0.0.0.0 --port=5000
"""
    
    with open("start_unix.sh", "w") as f:
        f.write(unix_script)
    
    # Make Unix script executable
    if platform.system() != "Windows":
        os.chmod("start_unix.sh", 0o755)
    
    print("✅ Startup scripts created")

def create_docker_files():
    """Create Docker configuration files"""
    print("🐳 Creating Docker configuration...")
    
    dockerfile_content = """# MyBreezeApp Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data backups reports

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.main:app
ENV FLASK_ENV=production

# Run the application
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
"""
    
    with open("Dockerfile", "w") as f:
        f.write(dockerfile_content)
    
    # Docker Compose file
    docker_compose_content = """version: '3.8'

services:
  mybreeze-app:
    build: .
    ports:
      - "5000:5000"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./backups:/app/backups
      - ./reports:/app/reports
    environment:
      - FLASK_ENV=production
      - PAPER_TRADING=True
    env_file:
      - .env
    restart: unless-stopped
    
  # Optional: Add Redis for caching (uncomment if needed)
  # redis:
  #   image: redis:7-alpine
  #   ports:
  #     - "6379:6379"
  #   restart: unless-stopped
"""
    
    with open("docker-compose.yml", "w") as f:
        f.write(docker_compose_content)
    
    print("✅ Docker files created")

def create_requirements_file():
    """Create requirements.txt file"""
    print("📋 Creating requirements.txt...")
    
    requirements_content = """flask>=2.3.0
pandas>=1.5.0
numpy>=1.24.0
requests>=2.28.0
python-dotenv>=1.0.0
flask-cors>=4.0.0
cryptography>=3.4.8
pyjwt>=2.6.0
yfinance>=0.2.0
plotly>=5.15.0
dash>=2.10.0
dash-bootstrap-components>=1.4.0
APScheduler>=3.10.0
sqlalchemy>=2.0.0
flask-sqlalchemy>=3.0.0
alembic>=1.11.0
pytest>=7.4.0
pytest-cov>=4.1.0
black>=23.0.0
flake8>=6.0.0
"""
    
    with open("requirements.txt", "w") as f:
        f.write(requirements_content)
    
    print("✅ requirements.txt created")

def show_completion_message():
    """Show completion message with next steps"""
    print("\n" + "="*60)
    print("🎉 GreeksMaster Setup Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Update .env file with your ICICIDirect Breeze API credentials")
    print("2. Install dependencies: pip install -r requirements.txt")
    print("3. Run tests: python -m pytest tests/ -v")
    print("4. Start the application:")
    print("   - Windows: start_windows.bat")
    print("   - Linux/Mac: ./start_unix.sh")
    print("   - Docker: docker-compose up")
    print("\n🌐 Access the application at: http://localhost:5000")
    print("\n📚 Documentation:")
    print("   - README.md - General information")
    print("   - STRATEGY_ENHANCEMENTS.md - Strategy details")
    print("   - TEST_RESULTS.md - Test results")
    print("\n⚠️  Important:")
    print("   - Start with PAPER_TRADING=True for testing")
    print("   - Test thoroughly before live trading")
    print("   - Monitor logs in the logs/ directory")

def main():
    """Main setup function"""
    print("🚀 GreeksMaster Setup Script")
    print("="*40)
    
    try:
        check_python_version()
        create_directories()
        create_environment_file()
        create_requirements_file()
        create_startup_scripts()
        create_docker_files()
        
        # Ask user if they want to install dependencies
        response = input("\n📦 Install Python dependencies now? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            install_dependencies()
            setup_database()
        else:
            print("ℹ️  Skipping dependency installation")
            print("   Run: pip install -r requirements.txt")
        
        show_completion_message()
        
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()