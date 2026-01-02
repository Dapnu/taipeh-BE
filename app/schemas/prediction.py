"""
Schemas for prediction queries and responses
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, time


class PredictionQuery(BaseModel):
    """Query parameters for getting predictions"""
    detector_id: int = Field(..., description="Detector ID")
    model_name: str = Field(..., description="Model name (e.g., catboost, xgboost)")
    date: str = Field(..., description="Date in format 'oct1_2017' or '2017-10-01'")
    time: str = Field(..., description="Time in format 'HH:MM:SS' or 'HH:MM'")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detector_id": 61,
                "model_name": "catboost",
                "date": "oct1_2017",
                "time": "08:00:00"
            }
        }


class PredictionRangeQuery(BaseModel):
    """Query for getting predictions within a time range"""
    detector_id: int = Field(..., description="Detector ID")
    model_name: str = Field(..., description="Model name")
    date: str = Field(..., description="Date in format 'oct1_2017' or '2017-10-01'")
    start_time: Optional[str] = Field(None, description="Start time (HH:MM:SS)")
    end_time: Optional[str] = Field(None, description="End time (HH:MM:SS)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detector_id": 61,
                "model_name": "catboost",
                "date": "oct1_2017",
                "start_time": "08:00:00",
                "end_time": "18:00:00"
            }
        }


class PredictionResponse(BaseModel):
    """Single prediction response"""
    detector_id: int
    date: str
    interval: int
    time: str
    traffic_prediction: float
    model: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "detector_id": 61,
                "date": "2017-10-01",
                "interval": 160,
                "time": "08:00:00",
                "traffic_prediction": 45.23,
                "model": "catboost"
            }
        }


class PredictionRangeResponse(BaseModel):
    """Response for prediction range query"""
    detector_id: int
    model: str
    date: str
    total_predictions: int
    predictions: List[PredictionResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "detector_id": 61,
                "model": "catboost",
                "date": "2017-10-01",
                "total_predictions": 120,
                "predictions": [
                    {
                        "detector_id": 61,
                        "date": "2017-10-01",
                        "interval": 160,
                        "time": "08:00:00",
                        "traffic_prediction": 45.23,
                        "model": "catboost"
                    }
                ]
            }
        }


class AvailableDataResponse(BaseModel):
    """Response for available data metadata"""
    available_models: List[str]
    available_dates: List[str]
    total_models: int
    total_dates: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "available_models": [
                    "catboost",
                    "xgboost",
                    "random_forest"
                ],
                "available_dates": [
                    "oct1_2017"
                ],
                "total_models": 3,
                "total_dates": 1
            }
        }


class DetectorListResponse(BaseModel):
    """Response for detector list"""
    model: str
    date: str
    total_detectors: int
    detector_ids: List[int]
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "catboost",
                "date": "oct1_2017",
                "total_detectors": 241,
                "detector_ids": [61, 62, 63]
            }
        }
