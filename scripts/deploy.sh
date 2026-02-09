#!/bin/bash
# EC2 Deployment Script
# Run this on your EC2 instance after pulling the code

set -e

echo "🚀 Deploying Fund Anomaly Dashboard..."

# Navigate to project directory
cd /home/ec2-user/fund-anomaly-demo || cd /opt/fund-anomaly-demo

# Pull latest changes
git pull origin main

# Build and start containers
docker-compose down --remove-orphans || true
docker-compose build --no-cache
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to start..."
sleep 10

# Check status
docker-compose ps

echo ""
echo "✅ Deployment complete!"
echo "📊 Dashboard available at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "📖 API docs at: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/docs"
