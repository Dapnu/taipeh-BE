# Data Files Information

## Taipei Traffic Prediction Dataset

### Files Overview

1. **taipeh_detectors.csv** (445 detectors)
   - Filtered from `detectors_public.csv` 
   - Contains only Taipei city traffic detectors
   - Columns: `detid`, `length`, `pos`, `fclass`, `road`, `limit`, `citycode`, `lanes`, `linkid`, `long`, `lat`

2. **taipeh_adjacency_matrix_transposed_normalized.csv**
   - Adjacency matrix representing detector network connectivity
   - Format: Detector x Detector with normalized weights (0-1)
   - Values represent distance/connectivity between detectors
   - Used for shortest distance routing

3. **predictions_oct1_2017_{model}.csv** (8 models)
   - Models: catboost, xgboost, lightgbm, random_forest, linear_regression, ridge, lasso, elasticnet
   - Columns: `detid`, `date`, `interval`, `time`, `traffic_predict`, `prediction_chain_step`
   - `traffic_predict`: Traffic congestion level (0-800, higher = more congested)
   - `interval`: Time slots 0-479 (3-minute intervals, 24 hours)
   - Date: October 1, 2017

### Data Usage

#### Routing System

**Shortest Path:**
- Uses adjacency matrix weights as edge costs
- Algorithm: Dijkstra's shortest path
- Optimizes for physical distance

**Fastest Path:**
- Uses `traffic_predict` values as edge costs
- Algorithm: A* with traffic-based heuristic
- Optimizes for travel time considering congestion
- Higher traffic_predict = higher cost (avoid congested routes)

#### Traffic Predict Values

- **Range**: 0 - 800
- **0-200**: Light traffic (green)
- **201-400**: Moderate traffic (yellow)
- **401-600**: Heavy traffic (orange)
- **601-800**: Severe congestion (red)

### Detector IDs

Sample detector IDs: 51, 61, 73, 77, 121, 134, 207, 224, 226, 227, 228, 232, 233, 235, 236, 238, 241, 243, 245, 246, 247...

Total: 445 unique detectors in Taipei network

### Coordinate System

- **Longitude**: 121.xx (East)
- **Latitude**: 25.xx (North)
- Example: Detector 51 at (121.5375893, 25.0236326)
