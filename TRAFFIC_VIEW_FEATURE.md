# Traffic Visualization Feature

## Overview

The Traffic Visualization feature allows users to view real-time traffic conditions across all 242 detectors in Taipei at any given time. This complements the existing route-finding feature by providing a comprehensive traffic monitoring dashboard.

## Features

### 🎯 Dual Mode System

#### 1. **Route Finding Mode** (Default)
- Find optimal routes between two locations
- Compare shortest vs fastest paths
- Traffic-aware route optimization
- Real-time path visualization on map

#### 2. **Traffic Viewing Mode** (New!)
- View traffic conditions across all 242 detectors
- Time-based traffic exploration (30-minute intervals)
- Color-coded traffic levels with heatmap overlay
- Real-time statistics and distribution

### 🗺️ Traffic Map Components

#### Interactive Map
- **242 Detectors**: Color-coded circle markers showing traffic intensity
- **Heatmap Layer**: Gradient overlay showing traffic density patterns
- **Map Tiles**: Minimalist CartoDB Positron theme for clean visualization
- **Popups**: Click any detector for detailed information

#### Statistics Panel
Located in the top-left corner, displays:
- Total number of active detectors
- Average traffic across all detectors
- Traffic range (min-max values)
- Distribution breakdown by category:
  - 🟢 **Low** (< 25): Smooth traffic flow
  - 🟡 **Moderate** (25-50): Normal traffic
  - 🟠 **High** (50-100): Heavy congestion
  - 🔴 **Severe** (≥ 100): Critical congestion

#### Traffic Legend
Shows color-coding scheme for easy interpretation of traffic levels.

#### Time Slider
- **48 Time Intervals**: 30-minute steps covering full 24-hour period
- **Range**: 00:00 - 23:59
- **Interactive**: Drag slider to explore traffic at different times
- **Real-time Updates**: Map updates immediately when time changes

## Technical Implementation

### Backend API

#### New Endpoint: `GET /api/v1/detectors/traffic`

**Parameters:**
- `model` (string): Prediction model name (e.g., 'xgboost', 'gcn_gru')
- `time` (string): Time in HH:MM:SS format (00:00:00 - 23:59:59)

**Response:**
```json
{
  "success": true,
  "model": "xgboost",
  "time": "09:00:00",
  "interval": 180,
  "detectors": [
    {
      "detid": 61,
      "lat": 25.01258,
      "lon": 121.53899,
      "traffic": 53.5,
      "category": "high",
      "road": "Section 1 Civic Blvd"
    },
    ...
  ],
  "statistics": {
    "total_detectors": 242,
    "avg_traffic": 16.89,
    "min_traffic": 1.0,
    "max_traffic": 93.07,
    "low_count": 190,
    "moderate_count": 39,
    "high_count": 13,
    "severe_count": 0
  }
}
```

### Frontend Components

#### 1. **TrafficView Component** (`TrafficView.tsx`)
- Main component for traffic visualization mode
- Manages state for time selection and data loading
- Renders Leaflet map with markers and heatmap
- Displays statistics and legend panels

#### 2. **Mode Selector** (in `ControlPanel.tsx`)
- Toggle between "Find Route" and "View Traffic" modes
- Button-based interface with icons
- Conditional rendering of mode-specific controls

#### 3. **App Integration** (`App.tsx`)
- Manages global application mode state
- Routes between MapView (route mode) and TrafficView (traffic mode)
- Coordinates state between components

### Time Intervals

The system uses **30-minute intervals** for traffic data aggregation:

- **Total Intervals**: 48 (covering 24 hours)
- **Original Data**: 480 intervals (3-minute steps)
- **Aggregation**: Each 30-min interval aggregates 10 original intervals
- **Conversion Formula**: `interval = (hour * 60 + minute) / 30`

Example time mappings:
- 00:00 → Interval 0
- 09:00 → Interval 18
- 12:00 → Interval 24
- 18:00 → Interval 36
- 23:30 → Interval 47

### Color Coding System

Traffic levels are visualized using a consistent color scheme:

| Category | Range | Color | Hex Code | Meaning |
|----------|-------|-------|----------|---------|
| Low | < 25 | Green | #22c55e | Free flow |
| Moderate | 25-50 | Yellow | #facc15 | Normal |
| High | 50-100 | Orange | #f97316 | Congested |
| Severe | ≥ 100 | Red | #dc2626 | Critical |

### Heatmap Configuration

The heatmap overlay uses Leaflet.heat plugin with these settings:

```javascript
{
  radius: 25,           // Heat radius around each point
  blur: 35,             // Blur amount for smooth gradient
  maxZoom: 17,          // Max zoom level for heat effect
  max: 1.0,             // Maximum intensity
  gradient: {
    0.0: '#22c55e',     // Green (low)
    0.25: '#facc15',    // Yellow
    0.5: '#f97316',     // Orange
    0.75: '#dc2626',    // Red
    1.0: '#991b1b'      // Dark red (severe)
  }
}
```

## Usage Guide

### Accessing Traffic View

1. **From Globe View**: 
   - Click "View Traffic" mode button in control panel
   - Map automatically switches to 2D view

2. **From Map View (Route Mode)**:
   - Click "View Traffic" mode button
   - Route-specific controls hide, time slider appears

### Exploring Traffic Data

1. **Select ML Model**: Choose from 10 available prediction models
2. **Choose Time**: Use the time slider to select desired hour
3. **Interact with Map**:
   - Zoom in/out for detailed/overview
   - Click markers for detector information
   - Observe heatmap pattern changes

### Interpreting Results

#### Morning Rush (07:00-09:00)
Typically shows:
- High traffic on major arterial roads
- Moderate to high on highways
- Low traffic in residential areas

#### Evening Rush (17:00-19:00)
Usually displays:
- Heavy congestion on outbound routes
- High traffic near commercial districts
- Moderate traffic on secondary roads

#### Late Night (00:00-05:00)
Generally exhibits:
- Very low traffic overall
- Sparse detector activity
- Minimal congestion anywhere

## Performance Optimizations

### Frontend
- **Marker Clustering**: (Future enhancement) Group nearby markers at low zoom
- **Debounced Updates**: 500ms delay on slider changes to reduce API calls
- **React.memo**: Memoized marker components to prevent unnecessary re-renders
- **Lazy Loading**: Heatmap layer only rendered when detectors data is available

### Backend
- **Efficient Data Loading**: Pandas vectorized operations for fast filtering
- **Pre-computed Categories**: Traffic categories calculated during load
- **Indexed Access**: Dictionary-based detector lookup (O(1) complexity)

## API Documentation

### Get Traffic Snapshot

**Endpoint**: `GET /api/v1/detectors/traffic`

**Query Parameters**:
- `model` (required): Model name matching prediction file
- `time` (required): Time in HH:MM:SS format with regex validation

**Response Codes**:
- `200 OK`: Successfully retrieved traffic data
- `404 Not Found`: Model predictions not found
- `422 Unprocessable Entity`: Invalid time format

**Example Usage**:
```bash
# Get traffic at 9 AM using XGBoost model
curl "http://localhost:8000/api/v1/detectors/traffic?model=xgboost&time=09:00:00"

# Get traffic at 6 PM using GCN-GRU model
curl "http://localhost:8000/api/v1/detectors/traffic?model=gcn_gru&time=18:00:00"
```

## Comparison: Route Mode vs Traffic Mode

| Feature | Route Mode | Traffic Mode |
|---------|------------|--------------|
| **Primary Function** | Find optimal paths | Monitor traffic conditions |
| **Input Required** | Start & end locations | Time of day |
| **Map Display** | Route polylines | Detector markers + heatmap |
| **Data Shown** | 2 paths with stats | 242 detectors with traffic |
| **Interactivity** | Click to set waypoints | Click for detector details |
| **Time Control** | Departure time picker | Time slider (48 intervals) |
| **Output** | Path comparison | Traffic distribution stats |

## Future Enhancements

### Planned Features
1. **Historical Playback**: Animate traffic changes over time
2. **Comparison Mode**: Side-by-side view of different time periods
3. **Export Functionality**: Download traffic data as CSV/JSON
4. **Custom Alerts**: Set thresholds for high-traffic notifications
5. **Route Overlay**: Show optimal routes on traffic view map
6. **3D Visualization**: Height-based traffic intensity representation

### Technical Improvements
1. **WebSocket Integration**: Real-time traffic updates without polling
2. **Caching Layer**: Redis cache for frequently accessed time intervals
3. **Progressive Loading**: Load visible detectors first, then others
4. **Service Worker**: Offline mode with cached traffic data
5. **Performance Metrics**: Track and display API response times

## Troubleshooting

### Common Issues

**Problem**: Map shows no markers
- **Cause**: Backend API not running or CORS error
- **Solution**: Ensure backend is running on port 8000, check browser console

**Problem**: Heatmap not displaying
- **Cause**: leaflet.heat plugin not loaded
- **Solution**: Verify `npm install leaflet.heat` was successful

**Problem**: Slider not updating traffic
- **Cause**: API request failing or slow network
- **Solution**: Check network tab, verify endpoint returns 200 OK

**Problem**: Statistics show zero detectors
- **Cause**: No predictions for selected model/time
- **Solution**: Verify prediction CSV file exists and has data

## Development Notes

### File Structure
```
backend/
  app/
    api/v1/endpoints/
      detectors.py        # New endpoint
    services/
      detector_service.py # get_traffic_snapshot() method

frontend/
  src/
    components/
      TrafficView.tsx     # Main traffic visualization component
      TrafficView.css     # Styling for traffic view
      ControlPanel.tsx    # Updated with mode selector
    App.tsx               # Updated with mode routing
```

### Dependencies Added
- **Backend**: pandas (already installed)
- **Frontend**: 
  - `leaflet.heat` - Heatmap plugin
  - `@types/leaflet.heat` - TypeScript definitions

### Testing
Run comprehensive tests with:
```bash
# Backend API test
python -c "import requests; ..."

# Frontend manual testing
npm run dev  # Visit http://localhost:3001
```

## Credits

- **Backend Development**: FastAPI + Pandas
- **Frontend Framework**: React + TypeScript + Vite
- **Mapping Library**: Leaflet + React-Leaflet
- **Heatmap Plugin**: Leaflet.heat by Vladimir Agafonkin
- **Design Style**: Minimalist CartoDB Positron theme

---

**Last Updated**: January 2, 2026
**Version**: 1.0.0
**Feature Status**: ✅ Production Ready
