# DS Backend API

A standardized FastAPI backend structure with Supabase database integration.

## Project Structure

```
ds-backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── api/                    # API endpoints
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── api.py          # API router aggregator
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── health.py   # Health check endpoint
│   └── core/                   # Core functionality
│       ├── __init__.py
│       ├── config.py           # Application configuration
│       └── database.py         # Supabase client setup
├── .env.example                # Environment variables template
├── .gitignore
├── requirements.txt            # Python dependencies
└── README.md
```

## Features

- ✅ FastAPI framework with automatic OpenAPI documentation
- ✅ Supabase database integration with PostGIS for spatial data
- ✅ Environment-based configuration
- ✅ CORS middleware setup
- ✅ Health check endpoint
- ✅ ML Models endpoint with 13 different prediction models
- ✅ Standardized project structure
- ✅ API versioning (v1)
- ✅ Comprehensive database schema for route prediction system

## Setup Instructions

### 1. Clone or navigate to the project directory

```bash
cd /home/daffaunu/Documents/ds-backend
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# or
venv\Scripts\activate  # On Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the `.env.example` file to `.env`:

```bash
cp .env.example .env
```

Then edit `.env` with your Supabase credentials:

```env
# Get these from your Supabase project settings
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

**Where to find Supabase credentials:**
1. Go to [supabase.com](https://supabase.com)
2. Select your project
3. Go to Settings → API
4. Copy the Project URL and anon/service_role keys

### 5. Run the application

**Option 1: Using uvicorn directly**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 2: Using Python**
```bash
python -m app.main
```

The API will be available at:
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs
- Alternative Docs: http://localhost:8000/redoc

## API Endpoints

### Root Endpoint
- **GET** `/` - Welcome message with API information

### Health Check
- **GET** `/api/v1/health` - Check API and database health status

Response example:
```json
{
  "status": "healthy",
  "api": {
    "status": "operational",
    "version": "1.0.0",
    "environment": "development"
  },
  "database": {
    "status": "connected",
    "type": "supabase"
  },
  "timestamp": "2025-12-31T10:00:00.000000"
}
```

### ML Models
- **GET** `/api/v1/models` - Get list of all available ML models
  - Query params: `?category=tree|linear|temporal|spatio_temporal` (optional filter)
- **GET** `/api/v1/models/{model_id}` - Get detailed info about specific model
- **GET** `/api/v1/models/categories` - Get model categories with counts

Available Model Categories:
- **Tree-based**: Decision Tree, Random Forest, Gradient Boosting (XGBoost)
- **Linear**: Linear Regression, Ridge Regression, Lasso Regression
- **Temporal**: LSTM, GRU, Temporal CNN
- **Spatio-Temporal**: GNN, GMAN, STGCN, ASTGCN

### Predictions (Pre-computed)
- **GET** `/api/v1/predictions/available` - Get available models and dates from data files
- **GET** `/api/v1/predictions/detectors` - Get list of detector IDs for a model/date
- **GET** `/api/v1/predictions/query` - Query single prediction by detector, model, date, time
- **GET** `/api/v1/predictions/range` - Get predictions within a time range
- **GET** `/api/v1/predictions/compare` - Compare predictions from multiple models
- **POST** `/api/v1/predictions/cache/clear` - Clear predictions cache

**Available Pre-computed Models**: CatBoost, XGBoost, LightGBM, Random Forest, Linear Regression, Ridge, Lasso, ElasticNet

## Development

### Adding New Endpoints

1. Create a new file in `app/api/v1/endpoints/`
2. Define your router and endpoints
3. Register the router in `app/api/v1/api.py`

Example:
```python
# app/api/v1/endpoints/example.py
from fastapi import APIRouter

router = APIRouter()

@router.get("/example")
async def example_endpoint():
    return {"message": "Example endpoint"}
```

Then in `app/api/v1/api.py`:
```python
from app.api.v1.endpoints import health, example

api_router.include_router(example.router, tags=["example"])
```

### Environment Variables

Configure your application through environment variables in `.env`:

- `APP_NAME`: Application name
- `APP_VERSION`: Application version
- `DEBUG`: Enable debug mode (True/False)
- `ENVIRONMENT`: Environment (development/production)
- `API_V1_PREFIX`: API version prefix (default: /api/v1)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon key
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key (optional)

## Database

This project uses Supabase (PostgreSQL) with PostGIS extension for spatial data. The connection is initialized in `app/core/database.py`.

### Database Setup

1. Go to your Supabase project's SQL Editor
2. Run the SQL script in `database/schema.sql`
3. This will create all tables, indexes, views, and triggers

### Database Schema

The database includes 8 main tables:
- **locations**: Location points with PostGIS geometry
- **routes**: Predicted and historical routes
- **ml_models**: ML model metadata
- **predictions**: Prediction results from models
- **model_performance**: Performance metrics over time
- **traffic_data**: Real-time and historical traffic data
- **user_feedback**: User feedback on predictions
- **model_training_jobs**: Training job tracking

See `database/README.md` for detailed documentation.

### Using Database in Endpoints

```python
from app.core.database import get_db

@router.get("/example")
async def example_endpoint():
    db = get_db()
    response = db.table('your_table').select("*").execute()
    return response.data
```

## Project Expansion

This structure is ready for expansion:

- **Models**: Add SQLAlchemy or Pydantic models in `app/models/`
- **Schemas**: Add Pydantic schemas in `app/schemas/`
- **Services**: Add business logic in `app/services/`
- **Utilities**: Add helper functions in `app/utils/`
- **Tests**: Add tests in `tests/`

## License

MIT
