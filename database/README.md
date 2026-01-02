# Database Schema Documentation

## Struktur Database Supabase untuk Route Prediction System

Database ini dirancang untuk mendukung sistem prediksi rute menggunakan berbagai model Machine Learning dengan data spatio-temporal.

## Tables Overview

### 1. **locations** 
Menyimpan lokasi-lokasi yang sering digunakan (landmarks, POI, intersections)

**Key Fields:**
- `geom`: PostGIS geography untuk spatial queries
- `location_type`: Tipe lokasi (landmark, intersection, poi, custom)
- Spatial indexing untuk performa query cepat

### 2. **routes**
Menyimpan informasi rute yang telah diprediksi

**Key Fields:**
- `route_geometry`: LINESTRING untuk visualisasi rute
- `waypoints`: JSONB array koordinat intermediate points
- `distance_km`, `estimated_duration_minutes`: Estimasi rute
- Foreign keys ke `locations` untuk origin/destination

### 3. **ml_models**
Metadata model ML yang tersedia

**Key Fields:**
- `category`: tree, linear, temporal, spatio_temporal
- `is_trained`: Status apakah model sudah di-train
- `hyperparameters`: JSONB untuk config model
- `metrics`: Training metrics (accuracy, loss, etc.)

### 4. **predictions**
Hasil prediksi dari setiap model

**Key Fields:**
- `confidence_score`: Confidence level prediksi
- `actual_duration_minutes`: Durasi aktual (untuk evaluasi)
- `prediction_error`: Error prediksi vs aktual
- `traffic_condition`, `weather_condition`: Kondisi saat prediksi
- `features_used`: JSONB fitur yang digunakan model

### 5. **model_performance**
Tracking performa model per hari

**Key Fields:**
- `mae`, `rmse`, `mape`, `r2_score`: Metrics evaluasi
- `accuracy_by_traffic`: JSONB accuracy per kondisi traffic
- `accuracy_by_hour`, `accuracy_by_day_of_week`: Time-based accuracy
- `avg_execution_time_ms`: Inference speed

### 6. **traffic_data**
Data traffic real-time/historis untuk training

**Key Fields:**
- `traffic_speed_kmh`, `traffic_volume`, `traffic_density`
- `congestion_level`: Tingkat kemacetan
- `weather_condition`, `temperature_celsius`: Weather features
- `time_of_day`: Kategori waktu (morning_rush, etc.)
- `is_holiday`, `is_weekend`: Temporal features

### 7. **user_feedback**
Feedback user untuk improve model

**Key Fields:**
- `rating`: 1-5 stars
- `was_accurate`: Boolean accuracy dari user perspective
- `actual_duration_minutes`: Durasi sebenarnya menurut user
- `issues`: Array masalah yang dialami

### 8. **model_training_jobs**
Tracking proses training model

**Key Fields:**
- `status`: pending, running, completed, failed
- `training_metrics`, `validation_metrics`, `test_metrics`
- `duration_seconds`: Lamanya training

## Views

### model_performance_summary
Aggregate performance metrics untuk semua model

### daily_traffic_patterns
Pola traffic harian dengan agregasi per jam

## Indexes

### Spatial Indexes
- `idx_locations_geom`: GIST index untuk spatial queries
- `idx_routes_geometry`: GIST index untuk route geometry

### Performance Indexes
- Timestamp indexes untuk time-series queries
- Foreign key indexes untuk joins
- Category/type indexes untuk filtering

## Triggers

### Auto-update Triggers
- `update_updated_at_column`: Auto-update timestamp
- `calculate_prediction_error`: Auto-calculate error saat actual data masuk
- `sync_location_geometry`: Auto-sync PostGIS geometry dari lat/lng

## Setup Instructions

### 1. Di Supabase Dashboard:

1. Go to **SQL Editor**
2. Paste isi file `schema.sql`
3. Run query

### 2. Enable PostGIS Extension:

Pastikan PostGIS extension enabled untuk spatial queries:
```sql
CREATE EXTENSION IF NOT EXISTS "postgis";
```

### 3. Enable UUID Extension:

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### 4. Setup RLS (Optional):

Jika ingin Row Level Security, uncomment bagian RLS di schema.sql

## Relationships

```
locations (1) ←→ (N) routes
routes (1) ←→ (N) predictions
ml_models (1) ←→ (N) predictions
ml_models (1) ←→ (N) model_performance
ml_models (1) ←→ (N) model_training_jobs
predictions (1) ←→ (N) user_feedback
locations (1) ←→ (N) traffic_data
```

## Usage Examples

### Query Traffic Patterns
```sql
SELECT * FROM daily_traffic_patterns 
WHERE traffic_date = CURRENT_DATE 
ORDER BY hour_of_day;
```

### Get Model Performance
```sql
SELECT * FROM model_performance_summary 
ORDER BY avg_confidence DESC;
```

### Find Routes Near Location
```sql
SELECT * FROM routes 
WHERE ST_DWithin(
    route_geometry, 
    ST_SetSRID(ST_MakePoint(106.8456, -6.2088), 4326)::geography,
    1000 -- 1km radius
);
```

### Get Model Predictions with Feedback
```sql
SELECT p.*, uf.rating, uf.was_accurate
FROM predictions p
LEFT JOIN user_feedback uf ON p.id = uf.prediction_id
WHERE p.model_id = 'lstm'
ORDER BY p.created_at DESC
LIMIT 100;
```

## Data Types

### JSONB Fields

**routes.waypoints:**
```json
[
  {"lat": -6.2088, "lng": 106.8456},
  {"lat": -6.2100, "lng": 106.8500}
]
```

**predictions.features_used:**
```json
{
  "distance": 8.5,
  "time_of_day": "morning_rush",
  "day_of_week": "monday",
  "is_holiday": false,
  "historical_avg_speed": 35.2
}
```

**model_performance.accuracy_by_traffic:**
```json
{
  "light": 0.92,
  "moderate": 0.87,
  "heavy": 0.81,
  "severe": 0.75
}
```

## Maintenance

### Regular Tasks

1. **Archive Old Data**: Archive traffic_data older than 6 months
2. **Update Model Performance**: Run daily aggregation for model_performance
3. **Cleanup**: Remove old predictions without feedback after 90 days
4. **Backup**: Regular backups (Supabase handles this automatically)

### Monitoring Queries

```sql
-- Check prediction volume per model
SELECT model_id, COUNT(*) as count, DATE(created_at) as date
FROM predictions
GROUP BY model_id, DATE(created_at)
ORDER BY date DESC;

-- Check average prediction error per model
SELECT model_id, AVG(prediction_error) as avg_error
FROM predictions
WHERE prediction_error IS NOT NULL
GROUP BY model_id;
```

## Migration Strategy

1. Create schema with `schema.sql`
2. Insert initial model metadata
3. Populate historical traffic data (if available)
4. Test with sample predictions
5. Enable RLS for production
6. Setup backup and monitoring
