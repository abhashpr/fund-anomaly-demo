# 🧭 Mutual Fund Anomaly Monitoring Dashboard

A real-time mutual fund anomaly monitoring dashboard with AI-powered surveillance capabilities. Built with Vue 3 + FastAPI for demo purposes.

![Dashboard Preview](https://via.placeholder.com/1200x600/0a0e14/00ff88?text=Fund+Anomaly+Monitor)

## ✨ Features

- **Multi-fund visualization** - Monitor all funds at a glance with interactive heatmap
- **NAV anomaly detection** - Statistical z-score based anomaly detection
- **Real-time updates** - WebSocket-powered live data streaming
- **Rich trading-style UI** - Dark theme Bloomberg-inspired interface
- **Dark/Light mode** - Toggle between themes with persistence
- **Signal feed** - Live anomaly alerts with PrimeIcons indicators
- **Fund deep-dive** - Detailed charts with risk metrics and historical anomalies
- **Data upload** - Upload your own NAV data (CSV/Parquet) with preview

## 🏗️ Architecture

```
fund-anomaly-demo/
├── backend/                 # Python FastAPI backend
│   ├── app/
│   │   ├── main.py         # FastAPI app entry point
│   │   ├── data_loader.py  # NAV data loading & processing
│   │   ├── anomaly.py      # Anomaly detection logic
│   │   ├── routes.py       # REST API endpoints
│   │   └── simulator.py    # WebSocket live simulation
│   ├── data/nav/           # Parquet data files
│   ├── Dockerfile          # Backend container
│   └── requirements.txt
│
├── frontend/                # Vue 3 frontend
│   ├── src/
│   │   ├── components/     # Vue components
│   │   │   ├── HeaderStats.vue
│   │   │   ├── Heatmap.vue
│   │   │   ├── FundTable.vue
│   │   │   ├── FundChart.vue
│   │   │   ├── SignalFeed.vue
│   │   │   └── ThemeToggle.vue
│   │   ├── pages/
│   │   │   ├── Upload.vue  # Data upload landing page
│   │   │   └── Dashboard.vue
│   │   ├── services/
│   │   │   └── api.js      # API client + WebSocket
│   │   └── store/
│   │       └── dashboard.js # Pinia state management
│   ├── Dockerfile          # Frontend container (Nginx)
│   ├── nginx.conf          # Nginx configuration
│   └── package.json
│
├── docker-compose.yml       # Container orchestration
├── buildspec.yml            # AWS CodeBuild specification
├── scripts/
│   └── deploy.sh           # EC2 deployment script
└── README.md
```

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Build and run both services
docker-compose up --build

# Access the dashboard
open http://localhost
```

### Option 2: Local Development

#### Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## 🐳 Docker Deployment

### Build Images

```bash
# Build backend
docker build -t fund-anomaly-backend ./backend

# Build frontend
docker build -t fund-anomaly-frontend --build-arg VITE_API_URL=http://your-api-url:8000 ./frontend
```

### Run with Docker Compose

```bash
# Development
docker-compose up --build

# Production (detached)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## ☁️ AWS Deployment (CodeCommit → CodeBuild → EC2)

### Prerequisites

1. **ECR Repositories** - Create two repositories:
   - `fund-anomaly-backend`
   - `fund-anomaly-frontend`

2. **CodeBuild Project** - Configure with:
   - Source: CodeCommit repository
   - Environment: `aws/codebuild/amazonlinux2-x86_64-standard:4.0`
   - Privileged mode: Enabled (for Docker)
   - Environment variables:
     - `AWS_ACCOUNT_ID`: Your AWS account ID
     - `AWS_DEFAULT_REGION`: e.g., `us-east-1`
     - `API_URL`: Your production API URL

3. **EC2 Instance** - Amazon Linux 2 with Docker installed

### Deploy to EC2

```bash
# SSH into EC2
ssh ec2-user@your-ec2-ip

# Clone repository
git clone https://git-codecommit.region.amazonaws.com/v1/repos/fund-anomaly-demo
cd fund-anomaly-demo

# Run deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

### CI/CD Pipeline

The `buildspec.yml` handles:
1. Login to ECR
2. Build Docker images
3. Tag with commit hash
4. Push to ECR
5. Generate `imagedefinitions.json` for ECS

## 📦 Data Setup

### Using Parquet File (Recommended)

Place your NAV data file at:
```
backend/data/nav/mutual_fund_nav_history.parquet
```

Expected format:
- Index: `Scheme_Code` (fund identifier)
- Columns: `Date`, `NAV`

### Using the Upload Feature

1. Navigate to `http://localhost:5173/`
2. Drag & drop your CSV or Parquet file
3. Preview the data (first 15 rows)
4. Click "Launch Dashboard"

### Without Data

The app loads demo data automatically if no file is present.

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/funds` | GET | List all funds with metrics |
| `/api/fund/{code}` | GET | Fund details + history |
| `/api/overview` | GET | Dashboard statistics |
| `/api/signals` | GET | Anomaly signal feed |
| `/api/heatmap` | GET | Heatmap visualization data |
| `/api/upload` | POST | Upload NAV file |
| `/ws/stream` | WS | Real-time WebSocket updates |

## 🧠 Anomaly Detection

Simple statistical approach:

1. **Compute daily returns** - `(NAV_t - NAV_{t-1}) / NAV_{t-1}`
2. **Rolling statistics** - 20-day rolling mean and standard deviation
3. **Z-score** - `(return - rolling_mean) / rolling_std`
4. **Flag anomaly** - When `|z-score| > 2`

Each anomaly includes an AI-style explanation:
> "Unusual NAV decrease detected. Significant deviation from rolling mean (z-score: -2.8). Large-cap sector showing abnormal movement."

## ⚡ Performance Optimizations

For demo responsiveness with large datasets:

| Setting | Value | Purpose |
|---------|-------|---------|
| `MAX_FUNDS` | 200 | Limit funds loaded |
| `MAX_ROWS_PER_SCHEME` | 60 | NAV records per fund |
| `MAX_DETAIL_POINTS` | 60 | Chart data points |

**Results:**
- API response time: ~50-60ms (after initial load)
- First load: ~3s (one-time data processing)

## 🎨 UI Components

### Upload Page
- Drag & drop file upload
- CSV/Parquet support
- Data preview table
- Summary statistics
- Theme toggle

### HeaderStats
- Total funds count
- Active anomalies
- Average NAV change (30-day)
- Market volatility (30-day)
- WebSocket connection status
- Dark/Light mode toggle

### Heatmap
- Grid visualization of all funds
- Color-coded by daily return
- Pulsing indicators for anomalies
- Click to view fund details

### FundTable
- Sortable data table
- Scheme code, category, NAV
- Daily return percentage
- Volatility metrics
- Anomaly status badges

### FundChart
- NAV line chart with area fill
- Daily return bar chart
- Anomaly markers
- Risk metrics panel

### SignalFeed
- Live scrolling feed
- PrimeIcons arrow indicators
- Severity badges (HIGH/MEDIUM)
- Confidence scores
- Click to view fund details

## 🛠️ Tech Stack

**Backend:**
- FastAPI (REST + WebSocket)
- Pandas (data processing)
- NumPy (statistics)
- PyArrow (Parquet support)
- Uvicorn (ASGI server)

**Frontend:**
- Vue 3 (Composition API)
- Vite (build tool)
- Tailwind CSS (styling)
- ECharts (charts)
- Pinia (state management)
- PrimeIcons (icon library)
- Axios (HTTP client)

**Infrastructure:**
- Docker & Docker Compose
- Nginx (reverse proxy)
- AWS CodeBuild (CI/CD)
- AWS ECR (container registry)

## 🔧 Environment Variables

### Backend
| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | 8000 | API server port |

### Frontend
| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | http://localhost:8000 | Backend API URL |

## 📄 License

MIT License - For demo/educational purposes.

---

Built with ❤️ for the AI-powered finance demo world.

### Backend Setup

```bash
cd backend
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

- Swagger docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:3000`

## 📦 Kaggle Data Setup

If you have the Kaggle mutual fund NAV dataset:

1. Download and unzip the dataset
2. Place files in `backend/data/nav/`:
   - `historical_nav.csv`
   - `scheme_details.csv`

If files are named differently, rename them to match.

**Without data:** The app will generate realistic sample data automatically.

## 🔌 API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/funds` | List all funds with metrics |
| `GET /api/fund/{code}` | Fund details + history |
| `GET /api/overview` | Dashboard statistics |
| `GET /api/signals` | Anomaly signal feed |
| `GET /api/heatmap` | Heatmap visualization data |
| `WS /ws/stream` | Real-time WebSocket updates |

## 🧠 Anomaly Detection

Simple statistical approach:

1. **Compute daily returns** - `(NAV_t - NAV_{t-1}) / NAV_{t-1}`
2. **Rolling statistics** - 20-day rolling mean and standard deviation
3. **Z-score** - `(return - rolling_mean) / rolling_std`
4. **Flag anomaly** - When `|z-score| > 2`

Each anomaly includes an AI-style explanation:
> "Unusual NAV decrease detected. Significant deviation from rolling mean (z-score: -2.8). Large-cap sector showing abnormal movement."

## 🎨 UI Components

### HeaderStats
Real-time dashboard header showing:
- Total funds count
- Active anomalies
- Average NAV change
- Market volatility
- WebSocket connection status

### Heatmap
Grid visualization of all funds:
- Color-coded by daily return (green positive, red negative)
- Pulsing indicators for anomalies
- Grouped by category
- Hover tooltips with fund details

### FundTable
Sortable data table with:
- Fund name and category
- Current NAV
- Daily return percentage
- Volatility metrics
- Anomaly status badges

### FundChart
Detailed fund view with:
- NAV line chart with area fill
- Daily return bar chart
- Anomaly markers
- Risk metrics panel
- Historical anomaly list

### SignalFeed
Live scrolling feed of:
- Anomaly alerts with severity
- AI-generated explanations
- Confidence scores
- Click to view fund details

## 🛠️ Tech Stack

**Backend:**
- FastAPI (REST + WebSocket)
- Pandas (data processing)
- NumPy (statistics)
- Uvicorn (ASGI server)

**Frontend:**
- Vue 3 (Composition API)
- Vite (build tool)
- Tailwind CSS (styling)
- ECharts (charts)
- Pinia (state management)
- Axios (HTTP client)

## 📝 Development Tips

1. **Hot reload** - Both frontend and backend support hot reload
2. **WebSocket testing** - Open browser console to see live events
3. **API testing** - Use Swagger UI at `/docs`
4. **Sample data** - Auto-generated if no CSV files present

## 🎯 Design Philosophy

- **UI over model complexity** - Focus on stunning visuals
- **Believable anomalies** - Statistics-based, not random
- **Trading terminal feel** - Dark theme, neon accents
- **Real-time experience** - WebSocket for live updates
- **Explainable AI** - Every anomaly has a reason

## 📄 License

MIT License - For demo/educational purposes.

---

Built with ❤️ for the AI-powered finance demo world.

