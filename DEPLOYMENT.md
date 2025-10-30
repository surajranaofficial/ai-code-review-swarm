# Deployment Guide

## Quick Deploy Options

### Option 1: Railway (Easiest)

1. **Push to GitHub**
```bash
cd code-review-swarm
git init
git add .
git commit -m "Initial commit: AI Code Review Swarm"
git remote add origin YOUR_REPO_URL
git push -u origin main
```

2. **Deploy on Railway**
- Go to [Railway.app](https://railway.app/)
- Click "New Project" → "Deploy from GitHub repo"
- Select your repository
- Add environment variables from `.env`
- Railway auto-detects Python and starts the app!

### Option 2: Render

1. **Create `render.yaml`** in project root:
```yaml
services:
  - type: web
    name: code-review-swarm
    env: python
    buildCommand: "pip install -r backend/requirements.txt"
    startCommand: "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: TIGER_DB_HOST
        sync: false
      - key: TIGER_DB_PASSWORD
        sync: false
      - key: OPENAI_API_KEY
        sync: false
```

2. **Deploy**
- Go to [Render.com](https://render.com/)
- Connect GitHub
- Select repo
- Add environment variables
- Deploy!

### Option 3: Docker + Any Platform

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Build & Run:**
```bash
docker build -t code-review-swarm .
docker run -p 8000:8000 --env-file .env code-review-swarm
```

## Environment Variables for Production

```env
# Production Tiger Cloud
TIGER_SERVICE_ID=your_prod_service
TIGER_DB_HOST=your-prod.timescaledb.io
TIGER_DB_PASSWORD=strong_password_here

# AI Keys
OPENAI_API_KEY=sk-prod-key-here

# Production settings
APP_ENV=production
DEBUG=False
API_HOST=0.0.0.0
API_PORT=8000
```

## Post-Deployment Checklist

- [ ] Verify Tiger Cloud connection
- [ ] Test health endpoint
- [ ] Submit test review
- [ ] Check logs for errors
- [ ] Set up monitoring (optional)
- [ ] Configure domain (optional)

## Frontend Deployment

**Using GitHub Pages (Free):**
```bash
cd frontend
# Simple static hosting
python3 -m http.server 8080

# Or use any static host:
# - Vercel
# - Netlify
# - GitHub Pages
```

Update API_URL in `frontend/index.html`:
```javascript
const API_URL = 'https://your-backend-url.railway.app';
```

## Monitoring (Optional)

### Health Check Endpoint
```bash
curl https://your-app.railway.app/health
```

### Simple Uptime Monitor
- [UptimeRobot](https://uptimerobot.com/) - Free
- [Pingdom](https://www.pingdom.com/) - Free tier

## Production Tips

1. **Rate Limiting**: Add rate limits to prevent abuse
2. **Caching**: Cache similar code patterns
3. **Queue System**: Use Celery for long-running reviews
4. **Monitoring**: Add Sentry or similar
5. **Backup**: Regular DB backups (Tiger Cloud handles this!)

## Scaling

Tiger Cloud auto-scales, but for the app:

1. **Horizontal Scaling**: Deploy multiple instances
2. **Load Balancer**: Use Railway/Render built-in LB
3. **Database Connection Pooling**: Already configured!
4. **CDN**: Use Cloudflare for frontend

## Costs

**Free Tier (Development):**
- Tiger Cloud: 2 free services (750MB each)
- Railway: $5 credit/month
- OpenAI: Pay as you go (~$0.01 per review)

**Estimated Production (100 reviews/day):**
- Tiger Cloud: ~$25/month (Performance plan)
- Hosting: ~$10/month
- AI API: ~$3/month
- **Total: ~$38/month**

## Troubleshooting

### Database Connection Issues
```bash
# Test Tiger Cloud connection
tiger db test-connection

# Check service status
tiger service list
```

### Application Won't Start
```bash
# Check logs
railway logs
# or
render logs

# Verify environment variables are set
```

### AI API Errors
```bash
# Check API key is valid
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable Tiger Cloud IP allowlist
- [ ] Use environment variables (never commit secrets)
- [ ] Enable HTTPS (handled by hosting platforms)
- [ ] Set CORS origins properly
- [ ] Rate limit API endpoints
- [ ] Enable Tiger Cloud MFA

## Support

- Railway: [docs.railway.app](https://docs.railway.app/)
- Render: [render.com/docs](https://render.com/docs)
- Tiger Cloud: [docs.tigerdata.com](https://docs.tigerdata.com/)

Good luck! 🚀
