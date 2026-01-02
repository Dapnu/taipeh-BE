"""
Route schemas for route optimization API.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ================================
# REQUEST SCHEMAS
# ================================

class RouteRequest(BaseModel):
    """Request model for route optimization."""
    start_lat: float = Field(..., description="Starting point latitude", ge=-90, le=90)
    start_lon: float = Field(..., description="Starting point longitude", ge=-180, le=180)
    end_lat: float = Field(..., description="Destination latitude", ge=-90, le=90)
    end_lon: float = Field(..., description="Destination longitude", ge=-180, le=180)
    model: str = Field(
        default="catboost",
        description="ML model for traffic prediction"
    )
    departure_time: str = Field(
        default="08:00:00",
        description="Departure time in HH:MM:SS format",
        pattern=r"^([01]?[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]$"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_lat": 25.047924,
                "start_lon": 121.517081,
                "end_lat": 25.033493,
                "end_lon": 121.564101,
                "model": "catboost",
                "departure_time": "08:30:00"
            }
        }


class NearestDetectorsRequest(BaseModel):
    """Request to find nearest detectors."""
    lat: float = Field(..., description="Latitude", ge=-90, le=90)
    lon: float = Field(..., description="Longitude", ge=-180, le=180)
    k: int = Field(default=5, description="Number of nearest detectors", ge=1, le=50)
    
    class Config:
        json_schema_extra = {
            "example": {
                "lat": 25.047924,
                "lon": 121.517081,
                "k": 5
            }
        }


# ================================
# RESPONSE SCHEMAS
# ================================

class DetectorInfo(BaseModel):
    """Information about a traffic detector."""
    detector_id: int = Field(..., description="Detector ID")
    name: Optional[str] = Field(None, description="Detector name")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    highway: Optional[str] = Field(None, description="Highway name")
    distance_km: Optional[float] = Field(None, description="Distance from query point in km")


class DetectorTrafficInfo(BaseModel):
    """Information about a detector with its current traffic level."""
    detector_id: int = Field(..., description="Detector ID")
    name: Optional[str] = Field(None, description="Detector name")
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    highway: Optional[str] = Field(None, description="Highway/road type")
    traffic: float = Field(..., description="Traffic level (0-800+)")
    traffic_level: str = Field(..., description="Traffic level category (low/moderate/high/severe)")


class Coordinate(BaseModel):
    """A single coordinate point."""
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")


class RouteCoordinate(BaseModel):
    """Coordinate with additional route info."""
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    detector_id: int = Field(..., description="Detector ID at this point")
    name: Optional[str] = Field(None, description="Location name")
    traffic: Optional[float] = Field(None, description="Traffic level at this point")
    time: Optional[str] = Field(None, description="Estimated time at this point")


class PathInfo(BaseModel):
    """Information about a path."""
    path: List[int] = Field(..., description="List of detector IDs in path order")
    path_length: int = Field(..., description="Number of detectors in path")
    total_weight: float = Field(..., description="Total path weight/cost")
    algorithm: str = Field(..., description="Algorithm used (dijkstra/astar)")
    traffic_levels: Optional[Dict[int, float]] = Field(None, description="Traffic levels by detector ID")
    avg_traffic: Optional[float] = Field(None, description="Average traffic along path")
    max_traffic: Optional[float] = Field(None, description="Maximum traffic along path")
    min_traffic: Optional[float] = Field(None, description="Minimum traffic along path")
    distance_meters: Optional[float] = Field(None, description="Total distance in meters")
    
    # Route coordinates for mapping
    coordinates: Optional[List[RouteCoordinate]] = Field(None, description="Coordinates along the route")
    
    # Standard route formats
    polyline: Optional[List[List[float]]] = Field(None, description="Route as [[lon, lat], ...] for mapping libraries")
    route_json: Optional[Dict[str, Any]] = Field(None, description="Route in standard routing format")


class RouteResponse(BaseModel):
    """Response model for route optimization."""
    success: bool = Field(..., description="Whether routing was successful")
    message: Optional[str] = Field(None, description="Status or error message")
    
    # Starting point info
    start_input: Dict[str, float] = Field(..., description="Original start coordinates")
    start_detector: Optional[DetectorInfo] = Field(None, description="Nearest detector to start")
    
    # Ending point info
    end_input: Dict[str, float] = Field(..., description="Original end coordinates")
    end_detector: Optional[DetectorInfo] = Field(None, description="Nearest detector to end")
    
    # Model and time info
    model: str = Field(..., description="ML model used")
    departure_time: str = Field(..., description="Departure time")
    time_interval: Optional[int] = Field(None, description="Time interval (0-479)")
    
    # Routes
    shortest_path: Optional[PathInfo] = Field(None, description="Shortest path by distance")
    fastest_path: Optional[PathInfo] = Field(None, description="Fastest path considering traffic")
    
    # All detectors with traffic levels (for map visualization)
    all_detectors: Optional[List[DetectorTrafficInfo]] = Field(
        None, 
        description="All detectors with their traffic levels at departure time"
    )
    
    # Comparison
    comparison: Optional[Dict[str, Any]] = Field(None, description="Comparison between routes")
    
    # GeoJSON for visualization
    geojson: Optional[Dict[str, Any]] = Field(None, description="GeoJSON FeatureCollection of routes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Routes calculated successfully",
                "start_input": {"lat": 25.047924, "lon": 121.517081},
                "start_detector": {
                    "detector_id": 51,
                    "name": "Detector 51",
                    "lat": 25.0479,
                    "lon": 121.5171,
                    "distance_km": 0.05
                },
                "end_input": {"lat": 25.033493, "lon": 121.564101},
                "end_detector": {
                    "detector_id": 907,
                    "name": "Detector 907",
                    "lat": 25.0335,
                    "lon": 121.5641,
                    "distance_km": 0.03
                },
                "model": "catboost",
                "departure_time": "08:30:00",
                "time_interval": 170,
                "shortest_path": {
                    "path": [51, 623, 302, 907],
                    "path_length": 4,
                    "total_weight": 0.384,
                    "algorithm": "dijkstra"
                },
                "fastest_path": {
                    "path": [51, 338, 907],
                    "path_length": 3,
                    "total_weight": 0.497,
                    "algorithm": "astar",
                    "avg_traffic": 268.9,
                    "max_traffic": 400.0,
                    "min_traffic": 6.7
                }
            }
        }


class NearestDetectorsResponse(BaseModel):
    """Response for nearest detectors query."""
    success: bool = Field(..., description="Whether query was successful")
    query_point: Dict[str, float] = Field(..., description="Query coordinates")
    detectors: List[DetectorInfo] = Field(..., description="List of nearest detectors")
    total_count: int = Field(..., description="Number of detectors returned")


class GraphStatsResponse(BaseModel):
    """Response for graph statistics."""
    total_detectors: int = Field(..., description="Total number of detectors in graph")
    total_edges: int = Field(..., description="Total number of edges in graph")
    detector_ids_sample: List[int] = Field(..., description="Sample of detector IDs")
    available_models: List[str] = Field(..., description="Available ML models")


class AvailableModelsResponse(BaseModel):
    """Response for available models."""
    models: List[str] = Field(..., description="List of available model names")
    total_count: int = Field(..., description="Number of models")
    default_model: str = Field(..., description="Default model if not specified")
