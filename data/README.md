# Prediction Data API

## Overview

Sistem ini menyediakan API untuk mengakses hasil prediksi traffic yang sudah di-inference sebelumnya. Data prediksi disimpan dalam format CSV untuk setiap model dan tanggal.

## Data Structure

### CSV File Format

File predictions tersimpan dengan format: `predictions_{date}_{model}.csv`

**Contoh**: `predictions_oct1_2017_catboost.csv`

**Columns**:
- `detid`: Detector ID (integer)
- `date`: Date (YYYY-MM-DD)
- `interval`: Time interval index (0-479 untuk 24 jam dengan interval 3 menit)
- `time`: Time in HH:MM:SS format
- `traffic_predict`: Predicted traffic value (float)
- `prediction_chain_step`: Step in prediction chain (optional)

## Available Models

Model yang sudah di-inference:
1. ✅ **catboost** - Gradient boosting dengan categorical features
2. ✅ **xgboost** - Extreme Gradient Boosting
3. ✅ **lightgbm** - Light Gradient Boosting Machine
4. ✅ **random_forest** - Random Forest Regressor
5. ✅ **linear_regression** - Linear Regression
6. ✅ **ridge** - Ridge Regression (L2)
7. ✅ **lasso** - Lasso Regression (L1)
8. ✅ **elasticnet** - Elastic Net (L1 + L2)

## API Endpoints

### 1. Get Available Data
```http
GET /api/v1/predictions/available
```

**Response**:
```json
{
  "available_models": ["catboost", "xgboost", "random_forest", ...],
  "available_dates": ["oct1_2017"],
  "total_models": 8,
  "total_dates": 1
}
```

### 2. Get Available Detectors
```http
GET /api/v1/predictions/detectors?model_name=catboost&date=oct1_2017
```

**Response**:
```json
{
  "model": "catboost",
  "date": "oct1_2017",
  "total_detectors": 241,
  "detector_ids": [61, 62, 63, 64, ...]
}
```

### 3. Query Single Prediction
```http
GET /api/v1/predictions/query?detector_id=61&model_name=catboost&date=oct1_2017&time=08:00:00
```

**Response**:
```json
{
  "detector_id": 61,
  "date": "2017-10-01",
  "interval": 160,
  "time": "08:00:00",
  "traffic_prediction": 45.23,
  "model": "catboost"
}
```

### 4. Query Prediction Range
```http
GET /api/v1/predictions/range?detector_id=61&model_name=catboost&date=oct1_2017&start_time=08:00:00&end_time=18:00:00
```

**Response**:
```json
{
  "detector_id": 61,
  "model": "catboost",
  "date": "2017-10-01",
  "total_predictions": 200,
  "predictions": [
    {
      "detector_id": 61,
      "date": "2017-10-01",
      "interval": 160,
      "time": "08:00:00",
      "traffic_prediction": 45.23,
      "model": "catboost"
    },
    ...
  ]
}
```

### 5. Compare Model Predictions
```http
GET /api/v1/predictions/compare?detector_id=61&date=oct1_2017&time=08:00:00&models=catboost,xgboost,random_forest
```

**Response**:
```json
{
  "detector_id": 61,
  "date": "oct1_2017",
  "time": "08:00:00",
  "models_compared": 3,
  "predictions": [
    {
      "detector_id": 61,
      "date": "2017-10-01",
      "interval": 160,
      "time": "08:00:00",
      "traffic_prediction": 45.23,
      "model": "catboost"
    },
    {
      "detector_id": 61,
      "date": "2017-10-01",
      "interval": 160,
      "time": "08:00:00",
      "traffic_prediction": 43.87,
      "model": "xgboost"
    },
    {
      "detector_id": 61,
      "date": "2017-10-01",
      "interval": 160,
      "time": "08:00:00",
      "traffic_prediction": 44.12,
      "model": "random_forest"
    }
  ],
  "statistics": {
    "average": 44.41,
    "minimum": 43.87,
    "maximum": 45.23,
    "range": 1.36
  }
}
```

### 6. Clear Cache
```http
POST /api/v1/predictions/cache/clear
```

**Response**:
```json
{
  "message": "Predictions cache cleared successfully",
  "status": "success"
}
```

## Usage Examples

### Python Example
```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Get available data
response = requests.get(f"{BASE_URL}/predictions/available")
data = response.json()
print(f"Available models: {data['available_models']}")

# Query single prediction
params = {
    "detector_id": 61,
    "model_name": "catboost",
    "date": "oct1_2017",
    "time": "08:00:00"
}
response = requests.get(f"{BASE_URL}/predictions/query", params=params)
prediction = response.json()
print(f"Traffic prediction: {prediction['traffic_prediction']}")

# Compare models
params = {
    "detector_id": 61,
    "date": "oct1_2017",
    "time": "08:00:00",
    "models": "catboost,xgboost,random_forest"
}
response = requests.get(f"{BASE_URL}/predictions/compare", params=params)
comparison = response.json()
print(f"Average prediction: {comparison['statistics']['average']}")
```

### JavaScript Example
```javascript
const BASE_URL = 'http://localhost:8000/api/v1';

// Get available data
const response = await fetch(`${BASE_URL}/predictions/available`);
const data = await response.json();
console.log('Available models:', data.available_models);

// Query single prediction
const params = new URLSearchParams({
  detector_id: 61,
  model_name: 'catboost',
  date: 'oct1_2017',
  time: '08:00:00'
});
const predResponse = await fetch(`${BASE_URL}/predictions/query?${params}`);
const prediction = await predResponse.json();
console.log('Traffic prediction:', prediction.traffic_prediction);
```

### cURL Example
```bash
# Get available data
curl "http://localhost:8000/api/v1/predictions/available"

# Query single prediction
curl "http://localhost:8000/api/v1/predictions/query?detector_id=61&model_name=catboost&date=oct1_2017&time=08:00:00"

# Get prediction range
curl "http://localhost:8000/api/v1/predictions/range?detector_id=61&model_name=catboost&date=oct1_2017&start_time=08:00:00&end_time=18:00:00"

# Compare models
curl "http://localhost:8000/api/v1/predictions/compare?detector_id=61&date=oct1_2017&time=08:00:00&models=catboost,xgboost,random_forest"
```

## Data Loading & Caching

### How It Works
1. Data CSV files di-load on-demand saat pertama kali diakses
2. Data di-cache dalam memory untuk akses cepat
3. Cache bisa di-clear manual jika diperlukan

### Performance Tips
- First query untuk setiap model/date akan slower (loading CSV)
- Subsequent queries sangat cepat (from cache)
- Clear cache jika update data files
- Untuk production, consider pre-loading data at startup

### Memory Management
- Setiap CSV file ~10-20MB
- Cache semua 8 models untuk 1 date = ~80-160MB RAM
- Monitor memory usage untuk banyak dates

## Time Intervals

Data tersedia dengan interval 3 menit:
- 00:00:00, 00:03:00, 00:06:00, ... 23:57:00
- Total 480 intervals per day (24 hours × 20 intervals per hour)
- `interval` column: 0-479

## Error Handling

**404 Not Found**:
```json
{
  "detail": "No prediction found for detector 61, model 'catboost', date 'oct1_2017', time '08:00:00'"
}
```

**Possible Causes**:
- File tidak ada di directory `data/`
- Detector ID tidak ada dalam data
- Time tidak valid atau tidak ada dalam data
- Model name typo

## Adding New Data

Untuk add data baru:

1. Place CSV file di `data/` directory
2. Format: `predictions_{date}_{model}.csv`
3. Ensure columns: `detid`, `date`, `interval`, `time`, `traffic_predict`
4. Clear cache: `POST /api/v1/predictions/cache/clear`
5. Data akan auto-detected oleh `/predictions/available`

## Integration with Frontend

### Route Planning Flow
```
1. User selects origin detector & destination detector
2. User selects departure time
3. Frontend queries predictions for both detectors
4. Compare predictions from multiple models
5. Select best model based on confidence/accuracy
6. Display route with predicted traffic
```

### Real-time Updates
```
1. Poll predictions every N minutes
2. Compare current prediction vs previous
3. Alert user if traffic conditions change significantly
4. Suggest re-routing if needed
```

## Next Steps

Planned enhancements:
- [ ] Detector to coordinate mapping
- [ ] Route calculation between detectors
- [ ] Historical accuracy tracking
- [ ] Model recommendation based on conditions
- [ ] Batch prediction endpoints
- [ ] WebSocket for real-time updates
