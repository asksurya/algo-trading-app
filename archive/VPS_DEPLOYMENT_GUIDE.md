# VPS Deployment Guide

Complete guide to deploy your algo trading app on a VPS for 24/7 operation.

---

## Table of Contents
1. [Why Use a VPS?](#why-use-a-vps)
2. [VPS Providers](#vps-providers)
3. [Initial VPS Setup](#initial-vps-setup)
4. [Deploy the Application](#deploy-the-application)
5. [Configure Secrets](#configure-secrets)
6. [Start the Daemon](#start-the-daemon)
7. [Access the Web UI](#access-the-web-ui)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Why Use a VPS?

✅ **24/7 Trading** - Runs continuously even when your laptop is off
✅ **Reliable** - Professional uptime and connectivity
✅ **Background Operation** - Daemon runs independently
✅ **Cost Effective** - $5-10/month for basic plans
✅ **Remote Access** - Monitor from anywhere

---

## VPS Providers

### Recommended Options

**1. DigitalOcean** ($6/month)
- Easy to use
- Great documentation
- 1GB RAM, 1 vCPU
- Perfect for algo trading
- [Sign up](https://www.digitalocean.com/)

**2. Linode** ($5/month)
- Reliable performance
- Good support
- Similar specs
- [Sign up](https://www.linode.com/)

**3. Vultr** ($5/month)
- Fast deployment
- Multiple locations
- Good for beginners
- [Sign up](https://www.vultr.com/)

**4. AWS Lightsail** ($5/month)
- Part of AWS ecosystem
- Easy to scale
- [Sign up](https://aws.amazon.com/lightsail/)

### Recommended Specs
- **OS**: Ubuntu 22.04 LTS
- **RAM**: 1-2GB minimum
- **Storage**: 25GB SSD
- **CPU**: 1 vCPU
- **Bandwidth**: 1TB/month

---

## Initial VPS Setup

### Step 1: Create Your VPS

1. Sign up for a VPS provider
2. Create a new droplet/instance
3. Choose:
   - **OS**: Ubuntu 22.04 LTS
   - **Plan**: Basic ($5-10/month)
   - **Region**: Closest to you
   - **SSH Key**: Add your SSH key (recommended)

### Step 2: Connect to Your VPS

```bash
# SSH into your VPS (replace with your IP)
ssh root@YOUR_VPS_IP

# Example:
ssh root@167.71.123.45
```

### Step 3: Update System

```bash
# Update package list
sudo apt update

# Upgrade installed packages
sudo apt upgrade -y

# Install essential tools
sudo apt install -y git python3 python3-pip python3-venv curl wget
```

### Step 4: Create Non-Root User (Recommended)

```bash
# Create new user
adduser trader

# Add to sudo group
usermod -aG sudo trader

# Switch to new user
su - trader
```

---

## Deploy the Application

### Step 1: Clone Repository

```bash
# Navigate to home directory
cd ~

# Clone your repo (replace with your repo URL)
git clone https://github.com/YOUR_USERNAME/algo-trading-app.git

# Or upload files directly
# scp -r /path/to/algo-trading-app trader@YOUR_VPS_IP:~/
```

### Step 2: Set Up Python Environment

```bash
# Navigate to project
cd ~/algo-trading-app

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Make Scripts Executable

```bash
# Make daemon scripts executable
chmod +x start_daemon.sh
chmod +x stop_daemon.sh
```

---

## Configure Secrets

### Create Secrets File

```bash
# Create .streamlit directory if not exists
mkdir -p .streamlit

# Copy example secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml

# Edit secrets file
nano .streamlit/secrets.toml
```

### Add Your Credentials

```toml
# APP PASSWORD (REQUIRED!)
APP_PASSWORD = "your_secure_password_here"

# Alpaca API Keys (for trading)
ALPACA_API_KEY = "your_alpaca_api_key"
ALPACA_SECRET_KEY = "your_alpaca_secret_key"

# Optional: News API for sentiment
NEWSAPI_KEY = "your_newsapi_key"
ALPHA_VANTAGE_KEY = "your_alphavantage_key"
```

**Save and exit**: `Ctrl+X`, then `Y`, then `Enter`

### Secure the Secrets File

```bash
# Restrict file permissions
chmod 600 .streamlit/secrets.toml

# Verify permissions
ls -la .streamlit/secrets.toml
# Should show: -rw------- (only you can read/write)
```

---

## Start the Daemon

### Option 1: Manual Start (Testing)

```bash
# Navigate to project
cd ~/algo-trading-app

# Activate virtual environment
source .venv/bin/activate

# Start daemon
./start_daemon.sh

# Check it's running
cat data/daemon.pid

# View logs
tail -f data/trading_daemon.log
```

### Option 2: Systemd Service (Production - Recommended)

Create a systemd service for automatic restart and startup:

```bash
# Create service file
sudo nano /etc/systemd/system/trading-daemon.service
```

Add this content:

```ini
[Unit]
Description=Algo Trading Daemon
After=network.target

[Service]
Type=forking
User=trader
WorkingDirectory=/home/trader/algo-trading-app
Environment="PATH=/home/trader/algo-trading-app/.venv/bin"
ExecStart=/home/trader/algo-trading-app/start_daemon.sh
ExecStop=/home/trader/algo-trading-app/stop_daemon.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (start on boot)
sudo systemctl enable trading-daemon

# Start service
sudo systemctl start trading-daemon

# Check status
sudo systemctl status trading-daemon

# View logs
journalctl -u trading-daemon -f
```

---

## Access the Web UI

### Option 1: SSH Tunnel (Secure)

From your local machine:

```bash
# Create SSH tunnel
ssh -L 8501:localhost:8501 trader@YOUR_VPS_IP

# In another terminal on VPS, start Streamlit
cd ~/algo-trading-app
source .venv/bin/activate
streamlit run app.py
```

Then open in browser: `http://localhost:8501`

### Option 2: Nginx + Domain (Production)

#### Install Nginx

```bash
sudo apt install nginx
```

#### Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/trading
```

Add:

```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN.com;

    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/trading /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Start Streamlit as Service

```bash
sudo nano /etc/systemd/system/streamlit.service
```

Add:

```ini
[Unit]
Description=Streamlit Dashboard
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/home/trader/algo-trading-app
Environment="PATH=/home/trader/algo-trading-app/.venv/bin"
ExecStart=/home/trader/algo-trading-app/.venv/bin/streamlit run app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable streamlit
sudo systemctl start streamlit
```

#### Add SSL (Optional but Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d YOUR_DOMAIN.com
```

Now access via: `https://YOUR_DOMAIN.com`

---

## Monitoring and Maintenance

### Check Daemon Status

```bash
# Via systemd
sudo systemctl status trading-daemon

# Via script
cat data/daemon.pid
ps aux | grep trading_daemon
```

### View Logs

```bash
# Daemon logs
tail -f data/trading_daemon.log

# System logs
journalctl -u trading-daemon -f

# Streamlit logs
journalctl -u streamlit -f
```

### Monitor System Resources

```bash
# CPU and memory usage
htop

# Disk usage
df -h

# Network connections
netstat -tuln
```

### Backup Database

```bash
# Create backup script
nano ~/backup_trading_db.sh
```

Add:

```bash
#!/bin/bash
BACKUP_DIR=~/backups
DB_FILE=~/algo-trading-app/data/trading_state.db
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp $DB_FILE $BACKUP_DIR/trading_state_$DATE.db

# Keep only last 7 days
find $BACKUP_DIR -name "trading_state_*.db" -mtime +7 -delete

echo "Backup completed: trading_state_$DATE.db"
```

Make executable and schedule:

```bash
chmod +x ~/backup_trading_db.sh

# Add to crontab (daily at 2 AM)
crontab -e

# Add this line:
0 2 * * * /home/trader/backup_trading_db.sh
```

### Update Application

```bash
# Stop daemon
./stop_daemon.sh

# Pull latest changes
git pull origin main

# Update dependencies
source .venv/bin/activate
pip install --upgrade -r requirements.txt

# Restart daemon
./start_daemon.sh
```

---

## Troubleshooting

### Daemon Won't Start

```bash
# Check if port is in use
lsof -i :8501

# Check Python path
which python3

# Check logs
tail -100 data/trading_daemon.log

# Try manual start
source .venv/bin/activate
python -m src.trading.trading_daemon
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R trader:trader ~/algo-trading-app

# Fix permissions
chmod +x start_daemon.sh stop_daemon.sh
chmod 600 .streamlit/secrets.toml
```

### Out of Memory

```bash
# Check memory
free -h

# Add swap space
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Database Issues

```bash
# Check database
cd ~/algo-trading-app
source .venv/bin/activate
python3 -c "from src.trading.state_manager import StateManager; sm = StateManager(); print('DB OK')"

# Reset database (if needed)
rm data/trading_state.db
python -m src.trading.trading_daemon
# Database will be recreated
```

### Firewall Configuration

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS (if using Nginx)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
```

---

## Quick Reference Commands

```bash
# Daemon Control
./start_daemon.sh          # Start daemon
./stop_daemon.sh           # Stop daemon
tail -f data/trading_daemon.log  # View logs

# Systemd Control
sudo systemctl start trading-daemon
sudo systemctl stop trading-daemon
sudo systemctl restart trading-daemon
sudo systemctl status trading-daemon

# Streamlit Control
sudo systemctl start streamlit
sudo systemctl stop streamlit
sudo systemctl restart streamlit
sudo systemctl status streamlit

# System Monitoring
htop                       # CPU/Memory
df -h                      # Disk usage
journalctl -u trading-daemon -f  # Service logs

# Database Backup
./backup_trading_db.sh     # Manual backup
```

---

## Security Best Practices

1. **Use SSH Keys** - Disable password authentication
2. **Enable Firewall** - Only open necessary ports
3. **Regular Updates** - Keep system packages updated
4. **Secure Secrets** - Use proper file permissions (600)
5. **Monitor Logs** - Check for suspicious activity
6. **Backup Data** - Regular database backups
7. **Use HTTPS** - SSL certificate for web access
8. **Strong Passwords** - For APP_PASSWORD and Alpaca

---

## Cost Estimate

**Monthly VPS Cost**: $5-10/month
**Domain (Optional)**: $10-15/year
**SSL Certificate**: Free (Let's Encrypt)

**Total**: ~$5-10/month for 24/7 automated trading!

---

## Next Steps

1. ✅ Choose and set up VPS
2. ✅ Deploy application
3. ✅ Configure secrets
4. ✅ Start daemon
5. ✅ Set up web access
6. ✅ Configure monitoring
7. ✅ Test trading
8. ✅ Monitor and maintain

Your algo trading system is now running 24/7 on a VPS! 🚀
