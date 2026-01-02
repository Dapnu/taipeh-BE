"""
Predictions endpoint - Query pre-computed predictions
"""

from fastapi import APIRouter, HTTPException, Query, status
from typing import List, Optional
from app.schemas.prediction import (
    PredictionResponse,
    PredictionRangeResponse,
    AvailableDataResponse,
    DetectorListResponse
)
from app.services.prediction_loader import prediction_loader

router = APIRouter()


@router.get(
    "/predictions/available",
    response_model=AvailableDataResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Available Data",
    description="Get list of available models and dates from data files"
)
async def get_available_data():
    """
    Get metadata about available prediction data
    
    Returns:
        Available models and dates
    """
    models = prediction_loader.get_available_models()
    dates = prediction_loader.get_available_dates()
    
    return {
        "available_models": models,
        "available_dates": dates,
        "total_models": len(models),
        "total_dates": len(dates)
    }


@router.get(
    "/predictions/detectors",
    response_model=DetectorListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Available Detectors",
    description="Get list of detector IDs for a specific model and date"
)
async def get_detectors(
    model_name: str = Query(..., description="Model name (e.g., catboost)"),
    date: str = Query(..., description="Date (e.g., oct1_2017)")
):
    """
    Get list of unique detector IDs for a specific model and date
    
    Args:
        model_name: Name of the model
        date: Date string
    
    Returns:
        List of detector IDs
    """
    detectors = prediction_loader.get_unique_detectors(model_name, date)
    
    if not detectors:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for model '{model_name}' and date '{date}'"
        )
    
    return {
        "model": model_name,
        "date": date,
        "total_detectors": len(detectors),
        "detector_ids": detectors
    }


@router.get(
    "/predictions/query",
    response_model=PredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Single Prediction",
    description="Get prediction for specific detector, model, date, and time"
)
async def query_prediction(
    detector_id: int = Query(..., description="Detector ID", example=61),
    model_name: str = Query(..., description="Model name", example="catboost"),
    date: str = Query(..., description="Date", example="oct1_2017"),
    time: str = Query(..., description="Time (HH:MM:SS)", example="08:00:00")
):
    """
    Query single prediction for specific parameters
    
    Args:
        detector_id: Detector ID
        model_name: Model name (e.g., catboost, xgboost)
        date: Date in format 'oct1_2017' or '2017-10-01'
        time: Time in format 'HH:MM:SS'
    
    Returns:
        Prediction data
    """
    result = prediction_loader.get_prediction(
        detector_id=detector_id,
        model_name=model_name,
        date=date,
        time_str=time
    )
    
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No prediction found for detector {detector_id}, model '{model_name}', date '{date}', time '{time}'"
        )
    
    return result


@router.get(
    "/predictions/range",
    response_model=PredictionRangeResponse,
    status_code=status.HTTP_200_OK,
    summary="Query Prediction Range",
    description="Get predictions for a detector within a time range"
)
async def query_prediction_range(
    detector_id: int = Query(..., description="Detector ID", example=61),
    model_name: str = Query(..., description="Model name", example="catboost"),
    date: str = Query(..., description="Date", example="oct1_2017"),
    start_time: Optional[str] = Query(None, description="Start time (HH:MM:SS)", example="08:00:00"),
    end_time: Optional[str] = Query(None, description="End time (HH:MM:SS)", example="18:00:00")
):
    """
    Query predictions within a time range
    
    Args:
        detector_id: Detector ID
        model_name: Model name
        date: Date string
        start_time: Start time (optional)
        end_time: End time (optional)
    
    Returns:
        List of predictions
    """
    results = prediction_loader.get_predictions_by_detector(
        detector_id=detector_id,
        model_name=model_name,
        date=date,
        start_time=start_time,
        end_time=end_time
    )
    
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for detector {detector_id}, model '{model_name}', date '{date}'"
        )
    
    return {
        "detector_id": detector_id,
        "model": model_name,
        "date": date,
        "total_predictions": len(results),
        "predictions": results
    }


@router.post(
    "/predictions/cache/clear",
    status_code=status.HTTP_200_OK,
    summary="Clear Predictions Cache",
    description="Clear the in-memory predictions cache"
)
async def clear_cache():
    """
    Clear the predictions cache
    
    This can be useful after updating data files or to free memory
    
    Returns:
        Success message
    """
    prediction_loader.clear_cache()
    
    return {
        "message": "Predictions cache cleared successfully",
        "status": "success"
    }


@router.get(
    "/predictions/compare",
    status_code=status.HTTP_200_OK,
    summary="Compare Model Predictions",
    description="Compare predictions from multiple models for same detector, date, and time"
)
async def compare_model_predictions(
    detector_id: int = Query(..., description="Detector ID", example=61),
    date: str = Query(..., description="Date", example="oct1_2017"),
    time: str = Query(..., description="Time (HH:MM:SS)", example="08:00:00"),
    models: str = Query(
        ...,
        description="Comma-separated model names",
        example="catboost,xgboost,random_forest"
    )
):
    """
    Compare predictions from multiple models
    
    Args:
        detector_id: Detector ID
        date: Date string
        time: Time string
        models: Comma-separated model names
    
    Returns:
        Comparison of predictions from different models
    """
    model_list = [m.strip() for m in models.split(',')]
    
    comparisons = []
    for model_name in model_list:
        result = prediction_loader.get_prediction(
            detector_id=detector_id,
            model_name=model_name,
            date=date,
            time_str=time
        )
        
        if result:
            comparisons.append(result)
    
    if not comparisons:
        raise HTTPException(
            status_code=404,
            detail=f"No predictions found for detector {detector_id}, date '{date}', time '{time}'"
        )
    
    # Calculate statistics
    predictions = [c['traffic_prediction'] for c in comparisons]
    avg_prediction = sum(predictions) / len(predictions)
    min_prediction = min(predictions)
    max_prediction = max(predictions)
    
    return {
        "detector_id": detector_id,
        "date": date,
        "time": time,
        "models_compared": len(comparisons),
        "predictions": comparisons,
        "statistics": {
            "average": round(avg_prediction, 2),
            "minimum": round(min_prediction, 2),
            "maximum": round(max_prediction, 2),
            "range": round(max_prediction - min_prediction, 2)
        }
    }
