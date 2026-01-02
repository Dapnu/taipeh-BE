-- ============================================
-- DS Backend - Supabase Database Schema
-- Route Prediction System with ML Models
-- ============================================

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- ============================================
-- 1. LOCATIONS TABLE
-- Menyimpan informasi lokasi/koordinat yang sering digunakan
-- ============================================
CREATE TABLE IF NOT EXISTS locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    address TEXT,
    location_type VARCHAR(50), -- 'landmark', 'intersection', 'poi', 'custom'
    geom GEOGRAPHY(POINT, 4326), -- PostGIS geography type
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_latitude CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT valid_longitude CHECK (longitude >= -180 AND longitude <= 180)
);

-- Index untuk spatial queries
CREATE INDEX idx_locations_geom ON locations USING GIST(geom);
CREATE INDEX idx_locations_type ON locations(location_type);

-- ============================================
-- 2. ROUTES TABLE
-- Menyimpan informasi rute yang telah diprediksi
-- ============================================
CREATE TABLE IF NOT EXISTS routes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_name VARCHAR(255),
    origin_lat DECIMAL(10, 8) NOT NULL,
    origin_lng DECIMAL(11, 8) NOT NULL,
    destination_lat DECIMAL(10, 8) NOT NULL,
    destination_lng DECIMAL(11, 8) NOT NULL,
    origin_location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    destination_location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    distance_km DECIMAL(10, 2),
    estimated_duration_minutes DECIMAL(10, 2),
    waypoints JSONB DEFAULT '[]', -- Array of {lat, lng} coordinates
    route_geometry GEOGRAPHY(LINESTRING, 4326), -- PostGIS linestring
    metadata JSONB DEFAULT '{}', -- Additional route info
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_origin_lat CHECK (origin_lat >= -90 AND origin_lat <= 90),
    CONSTRAINT valid_origin_lng CHECK (origin_lng >= -180 AND origin_lng <= 180),
    CONSTRAINT valid_dest_lat CHECK (destination_lat >= -90 AND destination_lat <= 90),
    CONSTRAINT valid_dest_lng CHECK (destination_lng >= -180 AND destination_lng <= 180)
);

CREATE INDEX idx_routes_origin ON routes(origin_lat, origin_lng);
CREATE INDEX idx_routes_destination ON routes(destination_lat, destination_lng);
CREATE INDEX idx_routes_geometry ON routes USING GIST(route_geometry);
CREATE INDEX idx_routes_created_at ON routes(created_at DESC);

-- ============================================
-- 3. ML_MODELS TABLE
-- Menyimpan metadata model ML yang tersedia
-- ============================================
CREATE TABLE IF NOT EXISTS ml_models (
    id VARCHAR(100) PRIMARY KEY, -- e.g., 'lstm', 'gnn', 'random_forest'
    name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'tree', 'linear', 'temporal', 'spatio_temporal'
    version VARCHAR(50) DEFAULT '1.0.0',
    description TEXT,
    how_it_works TEXT,
    strengths TEXT[], -- Array of strengths
    use_cases TEXT[], -- Array of use cases
    complexity VARCHAR(20), -- 'low', 'medium', 'high'
    accuracy_level VARCHAR(20), -- 'basic', 'intermediate', 'advanced'
    training_time VARCHAR(100),
    model_path TEXT, -- Path to saved model file
    is_available BOOLEAN DEFAULT TRUE,
    is_trained BOOLEAN DEFAULT FALSE,
    training_data_size INTEGER,
    last_trained_at TIMESTAMP WITH TIME ZONE,
    hyperparameters JSONB DEFAULT '{}',
    metrics JSONB DEFAULT '{}', -- Training metrics
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_category CHECK (category IN ('tree', 'linear', 'temporal', 'spatio_temporal')),
    CONSTRAINT valid_complexity CHECK (complexity IN ('low', 'medium', 'high')),
    CONSTRAINT valid_accuracy CHECK (accuracy_level IN ('basic', 'intermediate', 'advanced'))
);

CREATE INDEX idx_models_category ON ml_models(category);
CREATE INDEX idx_models_available ON ml_models(is_available) WHERE is_available = TRUE;

-- ============================================
-- 4. PREDICTIONS TABLE
-- Menyimpan hasil prediksi dari model
-- ============================================
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    route_id UUID REFERENCES routes(id) ON DELETE CASCADE,
    model_id VARCHAR(100) REFERENCES ml_models(id) ON DELETE SET NULL,
    origin_lat DECIMAL(10, 8) NOT NULL,
    origin_lng DECIMAL(11, 8) NOT NULL,
    destination_lat DECIMAL(10, 8) NOT NULL,
    destination_lng DECIMAL(11, 8) NOT NULL,
    predicted_duration_minutes DECIMAL(10, 2) NOT NULL,
    predicted_distance_km DECIMAL(10, 2) NOT NULL,
    confidence_score DECIMAL(5, 4), -- 0.0000 to 1.0000
    actual_duration_minutes DECIMAL(10, 2), -- Filled later if feedback available
    actual_distance_km DECIMAL(10, 2),
    prediction_error DECIMAL(10, 2), -- |predicted - actual|
    traffic_condition VARCHAR(50), -- 'light', 'moderate', 'heavy', 'severe'
    weather_condition VARCHAR(50),
    departure_time TIMESTAMP WITH TIME ZONE,
    arrival_time TIMESTAMP WITH TIME ZONE,
    alternative_routes_count INTEGER DEFAULT 0,
    execution_time_ms DECIMAL(10, 2), -- Model inference time
    user_preferences JSONB DEFAULT '{}',
    features_used JSONB DEFAULT '{}', -- Features used for prediction
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

CREATE INDEX idx_predictions_route ON predictions(route_id);
CREATE INDEX idx_predictions_model ON predictions(model_id);
CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX idx_predictions_departure ON predictions(departure_time);
CREATE INDEX idx_predictions_traffic ON predictions(traffic_condition);

-- ============================================
-- 5. MODEL_PERFORMANCE TABLE
-- Tracking performa model dari waktu ke waktu
-- ============================================
CREATE TABLE IF NOT EXISTS model_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(100) REFERENCES ml_models(id) ON DELETE CASCADE,
    evaluation_date DATE NOT NULL,
    total_predictions INTEGER DEFAULT 0,
    predictions_with_feedback INTEGER DEFAULT 0,
    
    -- Accuracy Metrics
    mae DECIMAL(10, 4), -- Mean Absolute Error
    rmse DECIMAL(10, 4), -- Root Mean Squared Error
    mape DECIMAL(10, 4), -- Mean Absolute Percentage Error
    r2_score DECIMAL(10, 4), -- R² Score
    
    -- Performance Metrics
    avg_execution_time_ms DECIMAL(10, 2),
    p95_execution_time_ms DECIMAL(10, 2),
    p99_execution_time_ms DECIMAL(10, 2),
    
    -- Accuracy by Traffic Condition
    accuracy_by_traffic JSONB DEFAULT '{}', -- {light: 0.9, moderate: 0.85, ...}
    
    -- Time-based Accuracy
    accuracy_by_hour JSONB DEFAULT '{}', -- {0: 0.88, 1: 0.89, ...}
    accuracy_by_day_of_week JSONB DEFAULT '{}', -- {monday: 0.87, ...}
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(model_id, evaluation_date)
);

CREATE INDEX idx_performance_model ON model_performance(model_id);
CREATE INDEX idx_performance_date ON model_performance(evaluation_date DESC);

-- ============================================
-- 6. TRAFFIC_DATA TABLE
-- Data traffic real-time atau historis untuk training
-- ============================================
CREATE TABLE IF NOT EXISTS traffic_data (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    location_lat DECIMAL(10, 8) NOT NULL,
    location_lng DECIMAL(11, 8) NOT NULL,
    location_id UUID REFERENCES locations(id) ON DELETE SET NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    traffic_speed_kmh DECIMAL(10, 2),
    traffic_volume INTEGER, -- vehicles per hour
    traffic_density DECIMAL(10, 2), -- vehicles per km
    congestion_level VARCHAR(50), -- 'free_flow', 'light', 'moderate', 'heavy', 'severe'
    incident_nearby BOOLEAN DEFAULT FALSE,
    weather_condition VARCHAR(50),
    temperature_celsius DECIMAL(5, 2),
    precipitation_mm DECIMAL(10, 2),
    visibility_km DECIMAL(10, 2),
    road_type VARCHAR(50), -- 'highway', 'arterial', 'local', 'residential'
    is_holiday BOOLEAN DEFAULT FALSE,
    is_weekend BOOLEAN DEFAULT FALSE,
    time_of_day VARCHAR(20), -- 'morning_rush', 'midday', 'evening_rush', 'night'
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_traffic_location ON traffic_data(location_lat, location_lng);
CREATE INDEX idx_traffic_timestamp ON traffic_data(timestamp DESC);
CREATE INDEX idx_traffic_congestion ON traffic_data(congestion_level);
CREATE INDEX idx_traffic_time_of_day ON traffic_data(time_of_day);

-- ============================================
-- 7. USER_FEEDBACK TABLE
-- Feedback dari user untuk improve model
-- ============================================
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    prediction_id UUID REFERENCES predictions(id) ON DELETE CASCADE,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    was_accurate BOOLEAN,
    actual_duration_minutes DECIMAL(10, 2),
    comments TEXT,
    issues TEXT[], -- Array of issues like 'traffic_worse', 'route_blocked', etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_feedback_prediction ON user_feedback(prediction_id);
CREATE INDEX idx_feedback_rating ON user_feedback(rating);
CREATE INDEX idx_feedback_created_at ON user_feedback(created_at DESC);

-- ============================================
-- 8. MODEL_TRAINING_JOBS TABLE
-- Track training jobs untuk model
-- ============================================
CREATE TABLE IF NOT EXISTS model_training_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id VARCHAR(100) REFERENCES ml_models(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL, -- 'pending', 'running', 'completed', 'failed'
    training_data_start_date DATE,
    training_data_end_date DATE,
    training_samples INTEGER,
    validation_samples INTEGER,
    test_samples INTEGER,
    hyperparameters JSONB DEFAULT '{}',
    training_metrics JSONB DEFAULT '{}',
    validation_metrics JSONB DEFAULT '{}',
    test_metrics JSONB DEFAULT '{}',
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed'))
);

CREATE INDEX idx_training_jobs_model ON model_training_jobs(model_id);
CREATE INDEX idx_training_jobs_status ON model_training_jobs(status);
CREATE INDEX idx_training_jobs_created_at ON model_training_jobs(created_at DESC);

-- ============================================
-- FUNCTIONS & TRIGGERS
-- ============================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at trigger to relevant tables
CREATE TRIGGER update_locations_updated_at BEFORE UPDATE ON locations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_routes_updated_at BEFORE UPDATE ON routes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ml_models_updated_at BEFORE UPDATE ON ml_models
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_model_performance_updated_at BEFORE UPDATE ON model_performance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to calculate prediction error when actual data is added
CREATE OR REPLACE FUNCTION calculate_prediction_error()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.actual_duration_minutes IS NOT NULL AND NEW.predicted_duration_minutes IS NOT NULL THEN
        NEW.prediction_error = ABS(NEW.predicted_duration_minutes - NEW.actual_duration_minutes);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_error_on_update BEFORE UPDATE ON predictions
    FOR EACH ROW EXECUTE FUNCTION calculate_prediction_error();

-- Function to sync location geometry from lat/lng
CREATE OR REPLACE FUNCTION sync_location_geometry()
RETURNS TRIGGER AS $$
BEGIN
    NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::geography;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER sync_location_geom BEFORE INSERT OR UPDATE ON locations
    FOR EACH ROW EXECUTE FUNCTION sync_location_geometry();

-- ============================================
-- VIEWS
-- ============================================

-- View: Model Performance Summary
CREATE OR REPLACE VIEW model_performance_summary AS
SELECT 
    m.id,
    m.name,
    m.category,
    m.is_available,
    COUNT(DISTINCT p.id) as total_predictions,
    AVG(p.confidence_score) as avg_confidence,
    AVG(p.execution_time_ms) as avg_execution_time_ms,
    COUNT(DISTINCT uf.id) as feedback_count,
    AVG(CASE WHEN uf.was_accurate THEN 1.0 ELSE 0.0 END) as user_accuracy_rate,
    m.last_trained_at,
    m.updated_at
FROM ml_models m
LEFT JOIN predictions p ON m.id = p.model_id
LEFT JOIN user_feedback uf ON p.id = uf.prediction_id
GROUP BY m.id, m.name, m.category, m.is_available, m.last_trained_at, m.updated_at;

-- View: Daily Traffic Patterns
CREATE OR REPLACE VIEW daily_traffic_patterns AS
SELECT 
    DATE(timestamp) as traffic_date,
    EXTRACT(HOUR FROM timestamp) as hour_of_day,
    time_of_day,
    congestion_level,
    COUNT(*) as sample_count,
    AVG(traffic_speed_kmh) as avg_speed,
    AVG(traffic_volume) as avg_volume,
    AVG(traffic_density) as avg_density
FROM traffic_data
GROUP BY DATE(timestamp), EXTRACT(HOUR FROM timestamp), time_of_day, congestion_level
ORDER BY traffic_date DESC, hour_of_day;

-- ============================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================

-- Insert sample models
INSERT INTO ml_models (id, name, category, description, complexity, accuracy_level, is_available) VALUES
('decision_tree', 'Decision Tree', 'tree', 'Basic tree-based model', 'low', 'basic', TRUE),
('random_forest', 'Random Forest', 'tree', 'Ensemble tree model', 'medium', 'intermediate', TRUE),
('lstm', 'LSTM', 'temporal', 'Long Short-Term Memory RNN', 'high', 'advanced', TRUE),
('gru', 'GRU', 'temporal', 'Gated Recurrent Unit', 'high', 'advanced', TRUE),
('gnn', 'Graph Neural Network', 'spatio_temporal', 'Graph-based spatial model', 'high', 'advanced', TRUE),
('gman', 'GMAN', 'spatio_temporal', 'Graph Multi-Attention Network', 'high', 'advanced', TRUE)
ON CONFLICT (id) DO NOTHING;

-- ============================================
-- ROW LEVEL SECURITY (RLS) - Optional
-- Uncomment if you want to enable RLS
-- ============================================

-- ALTER TABLE routes ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE predictions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;

-- Example RLS policy (adjust based on your auth setup)
-- CREATE POLICY "Users can view their own predictions" ON predictions
--     FOR SELECT USING (auth.uid() = user_id);

-- ============================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================

COMMENT ON TABLE locations IS 'Stores frequently used location points';
COMMENT ON TABLE routes IS 'Stores predicted and historical routes';
COMMENT ON TABLE ml_models IS 'Metadata for available ML models';
COMMENT ON TABLE predictions IS 'Predictions made by ML models';
COMMENT ON TABLE model_performance IS 'Performance metrics tracked over time';
COMMENT ON TABLE traffic_data IS 'Real-time and historical traffic information';
COMMENT ON TABLE user_feedback IS 'User feedback on prediction accuracy';
COMMENT ON TABLE model_training_jobs IS 'Training job tracking for models';

-- ============================================
-- END OF SCHEMA
-- ============================================
