# Setup Guide - AI Code Review Swarm

## Step-by-Step Setup

### 1. Tiger Cloud Setup

#### Create Account
1. Go to [Tiger Cloud](https://www.tigerdata.com/)
2. Sign up for free account
3. Verify email

#### Create Free Service
```bash
# Install Tiger CLI
curl -fsSL https://cli.tigerdata.com | sh

# Add to PATH (if needed)
export PATH="$HOME/.local/bin:$PATH"

# Login to Tiger Cloud
tiger auth login
# This will open browser for authentication

# Create service
tiger service create --name code-review-swarm

# List services to get service ID
tiger service list
```

#### Get Connection Details
```bash
# Get connection string
tiger db connection-string

# Example output:
# postgresql://tsdbadmin:password@abc123.timescaledb.io:5432/tsdb
```

### 2. API Keys Setup

#### OpenAI (Recommended)
1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Create API key
3. Copy key (starts with `sk-`)

#### Anthropic (Alternative)
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create API key
3. Copy key (starts with `sk-ant-`)

### 3. Backend Setup

```bash
cd code-review-swarm/backend

# Create virtual environment
python3 -m venv venv

# Activate (Mac/Linux)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit .env file
nano .env  # or use your favorite editor
```

**Fill in these values:**

```env
# From Tiger Cloud
TIGER_SERVICE_ID=abc123xyz
TIGER_DB_HOST=abc123.timescaledb.io
TIGER_DB_PORT=5432
TIGER_DB_NAME=tsdb
TIGER_DB_USER=tsdbadmin
TIGER_DB_PASSWORD=your_tiger_password

# From OpenAI or Anthropic
OPENAI_API_KEY=sk-your-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-key-here

# App settings (leave as is)
APP_ENV=development
DEBUG=True
API_HOST=0.0.0.0
API_PORT=8000
```

### 5. Database Initialization

```bash
# Test connection
python3 << 'EOF'
import asyncio
from db.connection import db_connection

async def test():
    await db_connection.connect()
    result = await db_connection.test_connection()
    print(f"Connection: {'✅ Success' if result else '❌ Failed'}")
    await db_connection.disconnect()

asyncio.run(test())
EOF

# Initialize schema
python3 << 'EOF'
import asyncio
from db.connection import db_connection
from db.operations import code_review_db

async def init():
    await db_connection.connect()
    await code_review_db.setup_schema()
    print("✅ Schema initialized!")
    await db_connection.disconnect()

asyncio.run(init())
EOF
```

### 6. Run Application

```bash
# Option 1: Direct Python
python app/main.py

# Option 2: With uvicorn (hot reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# You should see:
# INFO: 🚀 Starting AI Code Review Swarm...
# INFO: ✅ Connected to Tiger Cloud successfully
# INFO: ✅ Schema created successfully
# INFO: Application startup complete.
```

### 7. Verify Setup

Open another terminal:

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "tiger_connected": true,
  "agents_available": ["security", "performance", "quality"],
  "version": "0.1.0"
}
```

## Troubleshooting

### Connection Failed

**Problem**: Can't connect to Tiger Cloud

**Solutions**:
```bash
# 1. Verify credentials
tiger db test-connection

# 2. Check if service is running
tiger service list

# 3. Restart service if paused
tiger service update --service-id YOUR_ID --resume

# 4. Check IP allowlist in Tiger Cloud Console
```

### Import Errors

**Problem**: Module not found errors

**Solutions**:
```bash
# Make sure venv is activated
which python  # Should show path with 'venv'

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check Python version
python --version  # Should be 3.10+
```

### AI API Errors

**Problem**: AI model calls failing

**Solutions**:
```bash
# Test OpenAI key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer YOUR_KEY"

# Check rate limits and billing
# Make sure you have credits/active subscription
```

### Port Already in Use

**Problem**: Port 8000 already taken

**Solutions**:
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 PID

# Or use different port
uvicorn app.main:app --port 8001
```

## Testing the System

### Basic Test

```bash
# Create test file
cat > test_code.json << 'EOF'
{
  "submission": {
    "code": "def login(username, password):\n    query = 'SELECT * FROM users WHERE username=' + username\n    result = db.execute(query)\n    return result",
    "language": "python",
    "filename": "auth.py"
  },
  "agents": ["security", "performance", "quality"]
}
EOF

# Submit for review
curl -X POST http://localhost:8000/review \
  -H "Content-Type: application/json" \
  -d @test_code.json

# Save the review_id from response
REVIEW_ID="review_abc123"

# Wait 10-15 seconds, then get results
curl http://localhost:8000/review/$REVIEW_ID | jq .
```

### Load Test

```bash
# Install Apache Bench
# Mac: brew install httpd
# Ubuntu: sudo apt-get install apache2-utils

# Run 10 requests
ab -n 10 -c 2 \
  -p test_code.json \
  -T application/json \
  http://localhost:8000/review
```

## Production Deployment

### Using Docker (Recommended)

```dockerfile
# Create Dockerfile in backend/
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build
docker build -t code-review-swarm .

# Run
docker run -p 8000:8000 --env-file .env code-review-swarm
```

### Using Railway/Render/Heroku

1. Push code to GitHub
2. Connect repo to platform
3. Set environment variables
4. Deploy!

### Environment Variables for Production

```env
APP_ENV=production
DEBUG=False

# Use production database
TIGER_DB_HOST=your-prod-instance.timescaledb.io

# Secure secrets
# Generate strong passwords
# Use secrets manager if available
```

## Next Steps

1. ✅ Backend running
2. ☐ Build frontend
3. ☐ Add GitHub integration
4. ☐ Deploy to production
5. ☐ Submit to DEV.to challenge!

## Need Help?

- Tiger Cloud Slack: [Join community](https://www.tigerdata.com/community)
- Documentation: [docs.tigerdata.com](https://docs.tigerdata.com/)
- Issues: Create issue in this repo
