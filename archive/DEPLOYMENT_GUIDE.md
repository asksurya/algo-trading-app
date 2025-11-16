# 🚀 Deployment Guide - Algo Trading App

This guide covers deploying your algo trading app to cloud providers and accessing it on mobile devices.

## 📱 Mobile Access

Streamlit apps are **automatically mobile-responsive**! Once deployed, you can:
- Open the URL on your iPhone/Android
- App adapts to screen size
- All features work on mobile
- Add to home screen for app-like experience

### Adding to iPhone Home Screen:
1. Open app URL in Safari
2. Tap Share button
3. Select "Add to Home Screen"
4. App appears as icon on home screen!

## 🐳 Docker Deployment (Recommended)

### Build and Run Locally:
```bash
# Build Docker image
docker build -t algo-trading-app .

# Run container
docker run -p 8501:8501 algo-trading-app

# Or use docker-compose
docker-compose up -d
```

### With Environment Variables:
```bash
# Create .env file
echo "ALPACA_API_KEY=your_key" >> .env
echo "ALPACA_SECRET_KEY=your_secret" >> .env

# Run with env file
docker-compose --env-file .env up -d
```

## ☁️ Cloud Deployment Options

### 1. Streamlit Cloud (Easiest - Free Tier)

**Best for:** Quick deployment, free hosting

**Steps:**
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app"
4. Connect your GitHub repo
5. Select `app.py` as main file
6. Add secrets in Settings → Secrets:
   ```toml
   ALPACA_API_KEY = "your_key"
   ALPACA_SECRET_KEY = "your_secret"
   ```
7. Deploy!

**Access:** You get a URL like `your-app.streamlit.app`

**Mobile:** Works perfectly on iPhone/Android

---

### 2. Heroku (Easy - Paid)

**Best for:** Production deployments, custom domains

**Steps:**
1. Install Heroku CLI
2. Create `Procfile`:
   ```
   web: sh setup.sh && streamlit run app.py
   ```

3. Create `setup.sh`:
   ```bash
   mkdir -p ~/.streamlit/
   echo "\
   [server]\n\
   headless = true\n\
   port = $PORT\n\
   enableCORS = false\n\
   " > ~/.streamlit/config.toml
   ```

4. Deploy:
   ```bash
   heroku login
   heroku create your-algo-trading-app
   heroku config:set ALPACA_API_KEY=your_key
   heroku config:set ALPACA_SECRET_KEY=your_secret
   git push heroku main
   ```

**Cost:** $7/month (Eco dynos)

**Access:** `your-algo-trading-app.herokuapp.com`

---

### 3. Railway (Easy - Free Tier)

**Best for:** Modern deployment, free tier available

**Steps:**
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub"
3. Select your repo
4. Railway auto-detects Docker
5. Add environment variables in Settings
6. Deploy!

**Free Tier:** 500 hours/month, $5 credit

**Access:** Get custom railway.app subdomain

---

### 4. Google Cloud Run (Scalable)

**Best for:** Auto-scaling, pay-per-use

**Steps:**
1. Install gcloud CLI
2. Build and push image:
   ```bash
   gcloud builds submit --tag gcr.io/YOUR_PROJECT/algo-trading-app
   ```

3. Deploy:
   ```bash
   gcloud run deploy algo-trading-app \
     --image gcr.io/YOUR_PROJECT/algo-trading-app \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars ALPACA_API_KEY=your_key
   ```

**Cost:** Pay per request (free tier: 2M requests/month)

**Access:** Get `*.run.app` URL

---

### 5. AWS (EC2 + Docker)

**Best for:** Full control, custom networking

**Steps:**
1. Launch EC2 instance (t2.small or larger)
2. SSH into instance
3. Install Docker:
   ```bash
   sudo yum update -y
   sudo yum install docker -y
   sudo service docker start
   ```

4. Clone repo and run:
   ```bash
   git clone your-repo
   cd algo-trading-app
   docker-compose up -d
   ```

5. Configure security group (allow port 8501)

**Cost:** ~$10-30/month depending on instance

**Access:** http://YOUR_EC2_IP:8501

---

### 6. Azure Container Instances

**Best for:** Microsoft ecosystem

**Steps:**
1. Install Azure CLI
2. Create container:
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name algo-trading-app \
     --image your-dockerhub/algo-trading-app \
     --dns-name-label algo-trading \
     --ports 8501
   ```

**Cost:** Pay per second of runtime

**Access:** `algo-trading.region.azurecontainer.io:8501`

---

### 7. DigitalOcean App Platform

**Best for:** Simple deployment, predictable pricing

**Steps:**
1. Go to DigitalOcean
2. Create new App
3. Connect GitHub repo
4. Auto-detects Dockerfile
5. Add environment variables
6. Deploy!

**Cost:** $5-12/month

**Access:** Get `*.ondigitalocean.app` URL

---

## 🔒 Security Best Practices

### Never Commit Secrets:
```bash
# Add to .gitignore
.env
config/*_config.py
*.key
*.pem
```

### Use Environment Variables:
```python
import os

ALPACA_API_KEY = os.getenv('ALPACA_API_KEY')
ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY')
```

### Restrict Access:
- Use authentication (Streamlit Cloud supports OAuth)
- Whitelist IPs if possible
- Use HTTPS (most platforms provide this automatically)

## 📱 Mobile Optimization Tips

### Already Mobile-Friendly:
- ✅ Streamlit is responsive by default
- ✅ Tables scroll horizontally
- ✅ Buttons are touch-friendly
- ✅ Charts zoom and pan

### For Best Mobile Experience:
1. Use sidebar for controls (collapses on mobile)
2. Use `st.columns()` for layout (stacks on mobile)
3. Avoid very wide tables
4. Test on actual device

### Mobile-Specific Features:
```python
# Detect mobile
import streamlit as st

# Streamlit automatically adapts layout
# No special code needed!
```

## 🔧 Troubleshooting

### Port Issues:
- Streamlit default: 8501
- Cloud providers may assign different port
- Use `$PORT` environment variable

### Memory Issues:
- Upgrade instance size
- Reduce data caching
- Use lighter ML models

### API Rate Limits:
- Free tiers have limits
- Cache API responses
- Use paid tiers for production

## 🎯 Recommended Setup

**For Personal Use (Free):**
- Streamlit Cloud
- Access on mobile
- Perfect for paper trading

**For Production (Paid):**
- Railway or Heroku
- Custom domain
- Always-on server
- Auto-scaling

**For Enterprise:**
- AWS EC2 or GCP Cloud Run
- VPC networking
- Load balancing
- High availability

## 📊 Cost Comparison

| Provider | Free Tier | Paid | Best For |
|----------|-----------|------|----------|
| Streamlit Cloud | ✅ Yes | N/A | Personal |
| Railway | 500h/month | $5/month | Dev/Test |
| Heroku | ❌ No | $7/month | Production |
| GCP Cloud Run | 2M req/month | Pay-per-use | Scalable |
| AWS EC2 | 750h/month (1yr) | $10-30/month | Full control |
| DigitalOcean | ❌ No | $5/month | Simple |

## ✅ Quick Start - Deploy in 5 Minutes:

```bash
# 1. Commit your code
git add .
git commit -m "Ready for deployment"
git push origin main

# 2. Go to share.streamlit.io
# 3. Click "New app"
# 4. Connect GitHub
# 5. Add secrets
# 6. Deploy!

# Done! Access on mobile 📱
```

## 🌐 Custom Domain

Most providers support custom domains:

**Streamlit Cloud:**
- Settings → Custom domain
- Add CNAME record: `your-domain.com` → `your-app.streamlit.app`

**Heroku:**
```bash
heroku domains:add www.your-domain.com
```

**Others:** Check provider documentation

## 📞 Need Help?

- Streamlit Docs: https://docs.streamlit.io
- Docker Docs: https://docs.docker.com
- Provider-specific support

---

**Ready to deploy?** Follow your chosen provider's steps above!

Your app will be accessible from anywhere, including your iPhone! 📱🚀
