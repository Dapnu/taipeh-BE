"""
Schemas for ML models and predictions
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


class Coordinate(BaseModel):
    """Coordinate representation"""
    latitude: float = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude coordinate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "latitude": -6.2088,
                "longitude": 106.8456
            }
        }


class ModelInfo(BaseModel):
    """Information about an available ML model"""
    id: str = Field(..., description="Unique identifier for the model")
    name: str = Field(..., description="Display name of the model")
    category: Literal["tree", "linear", "temporal", "spatio_temporal"] = Field(
        ..., description="Category of the model"
    )
    description: str = Field(..., description="Detailed description of the model")
    how_it_works: str = Field(..., description="Explanation of how the model works")
    strengths: List[str] = Field(..., description="Strengths of the model")
    use_cases: List[str] = Field(..., description="Best use cases for this model")
    complexity: Literal["low", "medium", "high"] = Field(..., description="Computational complexity")
    accuracy_level: Literal["basic", "intermediate", "advanced"] = Field(
        ..., description="Expected accuracy level"
    )
    training_time: str = Field(..., description="Approximate training time")
    is_available: bool = Field(default=True, description="Whether the model is currently available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "random_forest",
                "name": "Random Forest",
                "category": "tree",
                "description": "Ensemble learning method using multiple decision trees",
                "how_it_works": "Combines predictions from multiple decision trees",
                "strengths": ["Handles non-linear relationships", "Resistant to overfitting"],
                "use_cases": ["General route prediction", "Feature importance analysis"],
                "complexity": "medium",
                "accuracy_level": "intermediate",
                "training_time": "5-10 minutes",
                "is_available": True
            }
        }


class RouteRequest(BaseModel):
    """Request for route prediction"""
    origin: Coordinate = Field(..., description="Starting point coordinate")
    destination: Coordinate = Field(..., description="Destination point coordinate")
    model_id: str = Field(..., description="ID of the model to use for prediction")
    departure_time: Optional[datetime] = Field(
        None, description="Planned departure time (for temporal models)"
    )
    preferences: Optional[dict] = Field(
        default_factory=dict,
        description="Additional preferences (e.g., avoid_tolls, prefer_highways)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "origin": {"latitude": -6.2088, "longitude": 106.8456},
                "destination": {"latitude": -6.1751, "longitude": 106.8650},
                "model_id": "lstm",
                "departure_time": "2025-12-31T14:00:00",
                "preferences": {"avoid_tolls": False, "prefer_highways": True}
            }
        }


class RoutePrediction(BaseModel):
    """Route prediction result"""
    route_id: str = Field(..., description="Unique identifier for this prediction")
    origin: Coordinate
    destination: Coordinate
    model_used: str = Field(..., description="Model ID used for prediction")
    predicted_duration_minutes: float = Field(..., description="Predicted travel time in minutes")
    predicted_distance_km: float = Field(..., description="Predicted distance in kilometers")
    confidence_score: float = Field(..., ge=0, le=1, description="Confidence score of prediction")
    alternative_routes: Optional[int] = Field(None, description="Number of alternative routes found")
    waypoints: Optional[List[Coordinate]] = Field(None, description="Intermediate waypoints")
    traffic_condition: Optional[str] = Field(None, description="Expected traffic condition")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "route_id": "pred_123abc",
                "origin": {"latitude": -6.2088, "longitude": 106.8456},
                "destination": {"latitude": -6.1751, "longitude": 106.8650},
                "model_used": "lstm",
                "predicted_duration_minutes": 25.5,
                "predicted_distance_km": 8.3,
                "confidence_score": 0.87,
                "alternative_routes": 3,
                "traffic_condition": "moderate",
                "created_at": "2025-12-31T14:00:00"
            }
        }


class ModelPerformance(BaseModel):
    """Model performance metrics"""
    model_id: str
    total_predictions: int
    average_accuracy: float = Field(..., ge=0, le=1)
    average_execution_time_ms: float
    last_trained: Optional[datetime] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": "gnn",
                "total_predictions": 1523,
                "average_accuracy": 0.89,
                "average_execution_time_ms": 45.2,
                "last_trained": "2025-12-15T10:00:00"
            }
        }
