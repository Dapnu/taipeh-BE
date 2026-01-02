# Traffic Prediction Models

This system supports **10 machine learning models** for traffic prediction in Taipei.

## Available Models

### Traditional Machine Learning

#### 1. Linear Regression (`regression`)
- **Type**: Statistical linear model
- **Strengths**: Fast, interpretable, works well for linear relationships
- **Use Case**: Quick baseline predictions, simple traffic patterns

#### 2. Lasso Regression (`lasso`)
- **Type**: Linear model with L1 regularization
- **Strengths**: Feature selection, prevents overfitting
- **Use Case**: Identifying key traffic factors

#### 3. Ridge Regression (`ridge`)
- **Type**: Linear model with L2 regularization
- **Strengths**: Stable predictions, handles multicollinearity
- **Use Case**: Robust baseline with many correlated features

#### 4. ElasticNet (`elasticnet`)
- **Type**: Combined L1 + L2 regularization
- **Strengths**: Balanced between Lasso and Ridge
- **Use Case**: Many features with some important ones

### Ensemble Methods

#### 5. Random Forest (`random_forest`)
- **Type**: Ensemble of decision trees
- **Strengths**: Robust, handles outliers well, non-linear patterns
- **Use Case**: General-purpose traffic prediction

#### 6. XGBoost (`xgboost`)
- **Type**: Extreme Gradient Boosting
- **Strengths**: High accuracy, handles feature interactions
- **Use Case**: Complex traffic patterns, competitions

#### 7. LightGBM (`lightgbm`)
- **Type**: Light Gradient Boosting Machine
- **Strengths**: Fast training, efficient memory usage
- **Use Case**: Large-scale traffic data

#### 8. CatBoost (`catboost`)
- **Type**: Categorical Boosting
- **Strengths**: Handles categorical features well, high accuracy
- **Use Case**: Mixed feature types, complex patterns

### Deep Learning (Graph Neural Networks)

#### 9. GCN-GRU (`gcn_gru`)
- **Type**: Graph Convolutional Network + Gated Recurrent Unit
- **Architecture**: 
  - GCN layers capture spatial dependencies through road network graph
  - GRU layers model temporal dependencies (time series)
- **Strengths**: 
  - Understands traffic flow patterns between connected roads
  - Captures short-term temporal dynamics
  - Efficient for sequential data
- **Use Case**: Real-time traffic forecasting with spatial correlations

#### 10. GCN-LSTM (`gcn_lstm`)
- **Type**: Graph Convolutional Network + Long Short-Term Memory
- **Architecture**:
  - GCN layers for spatial graph structure
  - LSTM layers for long-term temporal patterns
- **Strengths**:
  - Better at capturing long-term dependencies
  - Handles complex temporal patterns
  - State-of-the-art architecture
- **Use Case**: Advanced forecasting with long-term traffic trends

## Model Comparison

| Model | Type | Training Speed | Prediction Speed | Accuracy | Complexity |
|-------|------|---------------|------------------|----------|------------|
| Linear Regression | Traditional | ⚡⚡⚡ | ⚡⚡⚡ | ⭐⭐ | Low |
| Lasso | Traditional | ⚡⚡⚡ | ⚡⚡⚡ | ⭐⭐ | Low |
| Ridge | Traditional | ⚡⚡⚡ | ⚡⚡⚡ | ⭐⭐ | Low |
| ElasticNet | Traditional | ⚡⚡⚡ | ⚡⚡⚡ | ⭐⭐ | Low |
| Random Forest | Ensemble | ⚡⚡ | ⚡⚡ | ⭐⭐⭐ | Medium |
| XGBoost | Ensemble | ⚡⚡ | ⚡⚡ | ⭐⭐⭐⭐ | Medium |
| LightGBM | Ensemble | ⚡⚡⚡ | ⚡⚡ | ⭐⭐⭐⭐ | Medium |
| CatBoost | Ensemble | ⚡⚡ | ⚡⚡ | ⭐⭐⭐⭐ | Medium |
| GCN-GRU | Deep Learning | ⚡ | ⚡⚡ | ⭐⭐⭐⭐⭐ | High |
| GCN-LSTM | Deep Learning | ⚡ | ⚡⚡ | ⭐⭐⭐⭐⭐ | High |

## Data Format

All prediction files follow this format:
```
predictions_oct1_2017_<model_name>.csv
```

### Columns:
- `detid`: Detector ID (242 detectors)
- `prediction_chain_step`: Time interval (0-479, 3-minute steps = 24 hours)
- `traffic_predict`: Predicted traffic flow value
- `interval`: 3-hour period (0-7, deprecated)

### Time Intervals:
- Total: 480 intervals per day
- Resolution: 3 minutes
- Coverage: 00:00:00 - 23:57:00

## Usage in API

```bash
POST /api/v1/routes/optimize
{
  "start_lat": 25.0615,
  "start_lon": 121.5672,
  "end_lat": 25.0247,
  "end_lon": 121.5043,
  "model": "gcn_gru",  # or "gcn_lstm", "xgboost", etc.
  "departure_time": "09:00:00"
}
```

## Recommendations

- **For quick testing**: Use `regression` or `random_forest`
- **For best accuracy**: Use `gcn_lstm` or `xgboost`
- **For production (speed + accuracy)**: Use `lightgbm` or `gcn_gru`
- **For interpretability**: Use `lasso` or `ridge`

## Traffic Avoidance

All models use the same aggressive traffic avoidance strategy:
- Low traffic (< 25): 1.0x - 1.25x penalty
- Moderate traffic (25-50): 1.0x - 3.5x penalty
- High traffic (50-100): 100x - 500x penalty ⚠️
- Severe traffic (≥ 100): 500x - 5000x penalty 🚫

This ensures the "fastest path" actively avoids congested roads.
