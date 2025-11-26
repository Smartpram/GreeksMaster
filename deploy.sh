# MyBreezeApp Production Deployment Script

echo "DEPLOYING MYBREEZE APP TO PRODUCTION"
echo "=================================="

# Check Python environment
python --version
pip --version

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run production readiness check
echo "Running production readiness check..."
python production_check.py

# Start the application
echo "Starting MyBreezeApp..."
python app/main.py

echo "MyBreezeApp deployed successfully!"
echo "Access at: http://localhost:5000"
