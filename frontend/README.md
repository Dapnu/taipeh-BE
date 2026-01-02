# Taipei Traffic Routing System - Frontend

React + TypeScript + Vite frontend for visualizing traffic-optimized routes in Taipei.

## Features

- 🗺️ **2D Map View**: Interactive Leaflet map with route visualization
- 🌍 **3D Globe View**: Three.js-powered globe visualization
- 🚦 **Traffic Levels**: Real-time traffic detection visualization (color-coded by severity)
- 📊 **8 ML Models**: Compare different prediction models (XGBoost, CatBoost, LightGBM, Random Forest, etc.)
- 🛣️ **Dual Routing**: View both shortest path (blue, dashed) and fastest path (green, solid)
- ⏰ **Time-based Prediction**: Traffic predictions based on departure time

## Setup

### Install Dependencies

```bash
cd frontend
npm install
```

### Start Development Server

```bash
npm run dev
```

The frontend will run on `http://localhost:5173` (or the next available port).

## Integration with Backend

The frontend connects to the FastAPI backend running on `http://localhost:8000`.

Make sure the backend is running:

```bash
cd /home/daffaunu/Documents/ds-backend
uvicorn app.main:app --reload
```

## API Integration

### Endpoint: `POST /api/v1/routes/optimize`

**Request:**
```json
{
  "start_lat": 25.033,
  "start_lon": 121.565,
  "end_lat": 25.047,
  "end_lon": 121.517,
  "model": "xgboost",
  "departure_time": "09:00:00"
}
```

**Response:**
```json
{
  "shortest_path": {
    "path": [123, 456, 789],
    "geometry": [[121.565, 25.033], [121.560, 25.035], ...],
    "distance": 5.2,
    "traffic_levels": {
      "low": 10,
      "moderate": 5,
      "high": 2,
      "severe": 0
    }
  },
  "fastest_path": {
    "path": [123, 789, 101],
    "geometry": [[121.565, 25.033], [121.570, 25.040], ...],
    "distance": 6.1,
    "traffic_levels": {
      "low": 15,
      "moderate": 2,
      "high": 0,
      "severe": 0
    }
  },
  "all_detectors": [
    {
      "detector_id": 123,
      "lat": 25.033,
      "lon": 121.565,
      "traffic": 15.5,
      "traffic_level": "low"
    }
  ]
}
```

## Traffic Level Thresholds

- **Low** (Green): < 25
- **Moderate** (Yellow): 25 - 50
- **High** (Orange): 50 - 100
- **Severe** (Red): ≥ 100

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── ControlPanel.tsx   # Route parameters & model selection
│   │   ├── GlobeView.tsx      # 3D globe visualization
│   │   ├── MapView.tsx        # 2D Leaflet map
│   │   └── LocationSearch.tsx # Location search component
│   ├── types.ts               # TypeScript interfaces
│   ├── App.tsx                # Main application component
│   └── main.tsx               # Entry point
├── index.html
└── package.json
```

## Technologies Used

- **React 18**: UI framework
- **TypeScript**: Type safety
- **Vite**: Build tool and dev server
- **Leaflet**: 2D map library
- **Globe.gl**: 3D globe visualization
- **Three.js**: WebGL rendering
