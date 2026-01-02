"""
Detectors endpoint - Traffic detector information and snapshots
"""

from fastapi import APIRouter, Query, HTTPException, status
from typing import Optional
from app.services.detector_service import get_detector_service

router = APIRouter()


@router.get(
    "/traffic",
    status_code=status.HTTP_200_OK,
    summary="Get Traffic Snapshot",
    description="Get traffic conditions for all detectors at a specific time using a selected prediction model"
)
async def get_traffic_snapshot(
    model: str = Query(
        ...,
        description="Prediction model name (e.g., 'xgboost', 'gcn_gru', 'lightgbm')",
        example="xgboost"
    ),
    time: str = Query(
        ...,
        description="Time in HH:MM:SS format (00:00:00 - 23:59:59)",
        example="09:00:00",
        regex="^([0-1][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$"
    )
):
    """
    Get traffic snapshot for all detectors at a specific time.
    
    This endpoint returns traffic predictions for all 242 detectors in Taipei
    at the specified time, using the selected ML model. Traffic is categorized
    into four levels:
    - Low: < 25
    - Moderate: 25-50
    - High: 50-100
    - Severe: >= 100
    
    Args:
        model: ML model name for predictions
        time: Time in HH:MM:SS format
        
    Returns:
        Dictionary containing:
        - success: Whether the request was successful
        - model: Model name used
        - time: Time requested
        - interval: Prediction interval (0-479)
        - detectors: List of detectors with traffic data
        - statistics: Aggregate statistics
    """
    detector_service = get_detector_service()
    result = detector_service.get_traffic_snapshot(model, time)
    
    if not result.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Failed to load traffic snapshot")
        )
    
    return result
