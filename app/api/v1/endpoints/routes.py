"""
Route optimization API endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Optional, List, Dict, Any
from pathlib import Path

from app.schemas.route import (
    RouteRequest,
    RouteResponse,
    NearestDetectorsRequest,
    NearestDetectorsResponse,
    GraphStatsResponse,
    AvailableModelsResponse,
    DetectorInfo,
    DetectorTrafficInfo,
    PathInfo,
    RouteCoordinate
)
from app.services.routing_service import get_routing_service
from app.services.detector_service import get_detector_service

router = APIRouter()


def get_detector_info(detector_id: int, detector_service, distance_km: Optional[float] = None) -> DetectorInfo:
    """Helper to get detector info."""
    det = detector_service.get_detector(detector_id)
    if det:
        return DetectorInfo(
            detector_id=detector_id,
            name=det.get('name', f'Detector {detector_id}'),
            lat=det['lat'],
            lon=det['long'],
            highway=det.get('highway'),
            distance_km=distance_km
        )
    return None


@router.post("/optimize", response_model=RouteResponse)
async def optimize_route(request: RouteRequest) -> RouteResponse:
    """
    Calculate both shortest and fastest routes between two points.
    
    - **start_lat, start_lon**: Starting coordinates
    - **end_lat, end_lon**: Destination coordinates
    - **model**: ML model for traffic prediction (catboost, xgboost, lightgbm, etc.)
    - **departure_time**: Time of departure in HH:MM:SS format
    
    Returns both shortest path (by distance) and fastest path (considering traffic).
    """
    routing_service = get_routing_service()
    detector_service = get_detector_service()
    
    # Validate model
    stats = routing_service.get_graph_stats()
    if request.model not in stats['available_models']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model '{request.model}'. Available models: {stats['available_models']}"
        )
    
    # Find nearest detectors to start and end points (returns List[Tuple[Detector, distance]])
    start_nearest = detector_service.find_nearest_detectors(
        latitude=request.start_lat,
        longitude=request.start_lon,
        k=1
    )
    
    end_nearest = detector_service.find_nearest_detectors(
        latitude=request.end_lat,
        longitude=request.end_lon,
        k=1
    )
    
    if not start_nearest:
        return RouteResponse(
            success=False,
            message="Could not find detector near starting point",
            start_input={"lat": request.start_lat, "lon": request.start_lon},
            end_input={"lat": request.end_lat, "lon": request.end_lon},
            model=request.model,
            departure_time=request.departure_time
        )
    
    if not end_nearest:
        return RouteResponse(
            success=False,
            message="Could not find detector near destination",
            start_input={"lat": request.start_lat, "lon": request.start_lon},
            end_input={"lat": request.end_lat, "lon": request.end_lon},
            model=request.model,
            departure_time=request.departure_time
        )
    
    # Unpack Tuple[Detector, distance]
    start_det, start_dist = start_nearest[0]
    end_det, end_dist = end_nearest[0]
    
    start_detector_id = start_det.detid
    end_detector_id = end_det.detid
    
    # Calculate time interval
    time_interval = routing_service.time_to_interval(request.departure_time)
    
    # Find shortest path (Dijkstra) - also get traffic info for comparison
    shortest_result = routing_service.find_shortest_path(
        start_detector_id,
        end_detector_id,
        model_name=request.model,
        departure_time=request.departure_time
    )
    
    # Find fastest path (A* with traffic)
    fastest_result = routing_service.find_fastest_path(
        start_detector_id,
        end_detector_id,
        model_name=request.model,
        departure_time=request.departure_time
    )
    
    # Helper function to build route coordinates and formats
    def build_path_coordinates(
        path: List[int], 
        traffic_levels: Optional[List[float]] = None,
        departure_time: str = "00:00:00",
        road_geometry: Optional[List[tuple]] = None
    ) -> tuple:
        """Build coordinates, polyline, and route_json for a path."""
        coordinates = []
        
        # Parse departure time
        parts = departure_time.split(":")
        base_hours = int(parts[0])
        base_minutes = int(parts[1])
        
        for i, det_id in enumerate(path):
            det = detector_service.get_detector_by_id(det_id)
            if det:
                # Calculate estimated time at this point (3 min per step)
                total_minutes = base_hours * 60 + base_minutes + (i * 3)
                hours = (total_minutes // 60) % 24
                minutes = total_minutes % 60
                time_str = f"{hours:02d}:{minutes:02d}:00"
                
                traffic = traffic_levels[i] if traffic_levels and i < len(traffic_levels) else None
                
                coordinates.append(RouteCoordinate(
                    lat=det.latitude,
                    lon=det.longitude,
                    detector_id=det_id,
                    name=det.road or f"Detector {det_id}",
                    traffic=round(traffic, 2) if traffic else None,
                    time=time_str
                ))
        
        # Use road geometry if available, otherwise use detector coordinates
        if road_geometry and len(road_geometry) > 0:
            polyline = [[lon, lat] for lon, lat in road_geometry]
        else:
            polyline = [[coord.lon, coord.lat] for coord in coordinates]
        
        # Build standard route JSON (similar to OSRM/Mapbox format)
        route_json = {
            "type": "route",
            "properties": {
                "distance_weight": None,  # Will be set by caller
                "duration_estimate": f"{len(path) * 3} minutes",
                "waypoints": len(path),
                "uses_road_network": bool(road_geometry and len(road_geometry) > 0),
                "geometry_points": len(polyline)
            },
            "geometry": {
                "type": "LineString",
                "coordinates": polyline
            },
            "waypoints": [
                {
                    "location": [coord.lon, coord.lat],
                    "name": coord.name,
                    "detector_id": coord.detector_id
                }
                for coord in coordinates
            ]
        }
        
        return coordinates, polyline, route_json
    
    # Build path info for shortest
    shortest_path_info = None
    if shortest_result.success:
        # Convert traffic_levels dict to list in path order
        shortest_traffic_list = []
        if shortest_result.traffic_levels and isinstance(shortest_result.traffic_levels, dict):
            for det_id in shortest_result.path:
                if det_id in shortest_result.traffic_levels:
                    shortest_traffic_list.append(shortest_result.traffic_levels[det_id])
        
        coords, polyline, route_json = build_path_coordinates(
            shortest_result.path, 
            traffic_levels=shortest_traffic_list if shortest_traffic_list else None,
            departure_time=request.departure_time,
            road_geometry=shortest_result.geometry if hasattr(shortest_result, 'geometry') else None
        )
        route_json["properties"]["distance_weight"] = round(shortest_result.total_weight, 4)
        route_json["properties"]["algorithm"] = "astar"
        if hasattr(shortest_result, 'distance_meters') and shortest_result.distance_meters:
            route_json["properties"]["distance_meters"] = round(shortest_result.distance_meters, 2)
        
        shortest_path_info = PathInfo(
            path=shortest_result.path,
            path_length=len(shortest_result.path),
            total_weight=round(shortest_result.total_weight, 4),
            algorithm="astar",
            traffic_levels=shortest_result.traffic_levels if shortest_result.traffic_levels else None,
            avg_traffic=round(sum(shortest_traffic_list) / len(shortest_traffic_list), 1) if shortest_traffic_list else None,
            max_traffic=round(max(shortest_traffic_list), 1) if shortest_traffic_list else None,
            min_traffic=round(min(shortest_traffic_list), 1) if shortest_traffic_list else None,
            distance_meters=round(shortest_result.distance_meters, 2) if hasattr(shortest_result, 'distance_meters') and shortest_result.distance_meters else None,
            coordinates=coords,
            polyline=polyline,
            route_json=route_json
        )
    
    # Build path info for fastest
    fastest_path_info = None
    if fastest_result.success:
        # Convert traffic_levels dict to list in path order
        fastest_traffic_list = []
        if fastest_result.traffic_levels and isinstance(fastest_result.traffic_levels, dict):
            for det_id in fastest_result.path:
                if det_id in fastest_result.traffic_levels:
                    fastest_traffic_list.append(fastest_result.traffic_levels[det_id])
        elif isinstance(fastest_result.traffic_levels, list):
            fastest_traffic_list = fastest_result.traffic_levels
        
        coords, polyline, route_json = build_path_coordinates(
            fastest_result.path,
            traffic_levels=fastest_traffic_list if fastest_traffic_list else None,
            departure_time=request.departure_time,
            road_geometry=fastest_result.geometry if hasattr(fastest_result, 'geometry') else None
        )
        route_json["properties"]["distance_weight"] = round(fastest_result.total_weight, 4)
        route_json["properties"]["algorithm"] = "astar"
        route_json["properties"]["avg_traffic"] = round(sum(fastest_traffic_list) / len(fastest_traffic_list), 1) if fastest_traffic_list else None
        
        fastest_path_info = PathInfo(
            path=fastest_result.path,
            path_length=len(fastest_result.path),
            total_weight=round(fastest_result.total_weight, 4),
            algorithm="astar",
            traffic_levels=fastest_result.traffic_levels,  # Keep as dict for detailed view
            avg_traffic=round(sum(fastest_traffic_list) / len(fastest_traffic_list), 1) if fastest_traffic_list else None,
            max_traffic=round(max(fastest_traffic_list), 1) if fastest_traffic_list else None,
            min_traffic=round(min(fastest_traffic_list), 1) if fastest_traffic_list else None,
            distance_meters=round(fastest_result.distance_meters, 2) if hasattr(fastest_result, 'distance_meters') and fastest_result.distance_meters else None,
            coordinates=coords,
            polyline=polyline,
            route_json=route_json
        )
    
    # Build comparison
    comparison = None
    if shortest_path_info and fastest_path_info:
        comparison = {
            "shortest_detectors": shortest_path_info.path_length,
            "fastest_detectors": fastest_path_info.path_length,
            "shortest_weight": shortest_path_info.total_weight,
            "fastest_weight": fastest_path_info.total_weight,
            "same_path": shortest_path_info.path == fastest_path_info.path,
            "weight_difference": round(fastest_path_info.total_weight - shortest_path_info.total_weight, 4)
        }
    
    # Build GeoJSON for visualization
    geojson = build_geojson(
        detector_service,
        shortest_result.path if shortest_result.success else [],
        fastest_result.path if fastest_result.success else [],
        {"lat": request.start_lat, "lon": request.start_lon},
        {"lat": request.end_lat, "lon": request.end_lon},
        shortest_geometry=shortest_result.geometry if shortest_result.success and hasattr(shortest_result, 'geometry') else None,
        fastest_geometry=fastest_result.geometry if fastest_result.success and hasattr(fastest_result, 'geometry') else None
    )
    
    # Get all detectors with traffic levels for map visualization
    all_detectors_data = routing_service.get_all_detectors_with_traffic(
        model_name=request.model,
        departure_time=request.departure_time
    )
    
    # Convert to DetectorTrafficInfo objects
    all_detectors = [
        DetectorTrafficInfo(
            detector_id=d["detector_id"],
            name=d["name"],
            lat=d["lat"],
            lon=d["lon"],
            highway=d["highway"],
            traffic=d["traffic"],
            traffic_level=d["traffic_level"]
        )
        for d in all_detectors_data
    ]
    
    return RouteResponse(
        success=True,
        message="Routes calculated successfully",
        start_input={"lat": request.start_lat, "lon": request.start_lon},
        start_detector=DetectorInfo(
            detector_id=start_detector_id,
            name=start_det.road or f'Detector {start_detector_id}',
            lat=start_det.latitude,
            lon=start_det.longitude,
            highway=start_det.road,
            distance_km=round(start_dist, 3)
        ),
        end_input={"lat": request.end_lat, "lon": request.end_lon},
        end_detector=DetectorInfo(
            detector_id=end_detector_id,
            name=end_det.road or f'Detector {end_detector_id}',
            lat=end_det.latitude,
            lon=end_det.longitude,
            highway=end_det.road,
            distance_km=round(end_dist, 3)
        ),
        model=request.model,
        departure_time=request.departure_time,
        time_interval=time_interval,
        shortest_path=shortest_path_info,
        fastest_path=fastest_path_info,
        all_detectors=all_detectors,
        comparison=comparison,
        geojson=geojson
    )


def build_geojson(
    detector_service,
    shortest_path: List[int],
    fastest_path: List[int],
    start_point: Dict[str, float],
    end_point: Dict[str, float],
    shortest_geometry: Optional[List[tuple]] = None,
    fastest_geometry: Optional[List[tuple]] = None
) -> Dict[str, Any]:
    """Build GeoJSON FeatureCollection for visualization."""
    features = []
    
    # Start point marker
    features.append({
        "type": "Feature",
        "properties": {
            "type": "start_point",
            "label": "Start"
        },
        "geometry": {
            "type": "Point",
            "coordinates": [start_point["lon"], start_point["lat"]]
        }
    })
    
    # End point marker
    features.append({
        "type": "Feature",
        "properties": {
            "type": "end_point",
            "label": "End"
        },
        "geometry": {
            "type": "Point",
            "coordinates": [end_point["lon"], end_point["lat"]]
        }
    })
    
    # Shortest path line - use road geometry if available
    if shortest_path:
        if shortest_geometry and len(shortest_geometry) > 0:
            # Use actual road network geometry
            coords = [[lon, lat] for lon, lat in shortest_geometry]
        else:
            # Fallback to detector coordinates
            coords = []
            for det_id in shortest_path:
                det = detector_service.get_detector_by_id(det_id)
                if det:
                    coords.append([det.longitude, det.latitude])
        
        if coords:
            features.append({
                "type": "Feature",
                "properties": {
                    "type": "shortest_path",
                    "label": "Shortest Route",
                    "stroke": "#3388ff",
                    "stroke-width": 4,
                    "detectors": len(shortest_path),
                    "uses_road_network": bool(shortest_geometry and len(shortest_geometry) > 0)
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                }
            })
    
    # Fastest path line - use road geometry if available
    if fastest_path:
        if fastest_geometry and len(fastest_geometry) > 0:
            # Use actual road network geometry
            coords = [[lon, lat] for lon, lat in fastest_geometry]
        else:
            # Fallback to detector coordinates
            coords = []
            for det_id in fastest_path:
                det = detector_service.get_detector_by_id(det_id)
                if det:
                    coords.append([det.longitude, det.latitude])
        
        if coords:
            features.append({
                "type": "Feature",
                "properties": {
                    "type": "fastest_path",
                    "label": "Fastest Route",
                    "stroke": "#33cc33",
                    "stroke-width": 4,
                    "detectors": len(fastest_path),
                    "uses_road_network": bool(fastest_geometry and len(fastest_geometry) > 0)
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords
                }
            })
    
    # Detector markers along paths
    all_detectors = set(shortest_path + fastest_path)
    for det_id in all_detectors:
        det = detector_service.get_detector_by_id(det_id)
        if det:
            in_shortest = det_id in shortest_path
            in_fastest = det_id in fastest_path
            
            features.append({
                "type": "Feature",
                "properties": {
                    "type": "detector",
                    "detector_id": det_id,
                    "name": det.road or f'Detector {det_id}',
                    "in_shortest": in_shortest,
                    "in_fastest": in_fastest
                },
                "geometry": {
                    "type": "Point",
                    "coordinates": [det.longitude, det.latitude]
                }
            })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


@router.post("/nearest-detectors", response_model=NearestDetectorsResponse)
async def find_nearest_detectors(request: NearestDetectorsRequest) -> NearestDetectorsResponse:
    """
    Find the nearest traffic detectors to a given point.
    
    - **lat**: Latitude of the query point
    - **lon**: Longitude of the query point
    - **k**: Number of nearest detectors to return (default: 5, max: 50)
    """
    detector_service = get_detector_service()
    
    # Returns List[Tuple[Detector, distance]]
    detectors = detector_service.find_nearest_detectors(
        latitude=request.lat,
        longitude=request.lon,
        k=request.k
    )
    
    detector_list = [
        DetectorInfo(
            detector_id=det.detid,
            name=det.road or f"Detector {det.detid}",
            lat=det.latitude,
            lon=det.longitude,
            highway=det.road,
            distance_km=round(dist, 3)
        )
        for det, dist in detectors
    ]
    
    return NearestDetectorsResponse(
        success=True,
        query_point={"lat": request.lat, "lon": request.lon},
        detectors=detector_list,
        total_count=len(detector_list)
    )


@router.get("/graph-stats", response_model=GraphStatsResponse)
async def get_graph_stats() -> GraphStatsResponse:
    """
    Get statistics about the routing graph.
    
    Returns information about the number of detectors, edges, and available models.
    """
    routing_service = get_routing_service()
    stats = routing_service.get_graph_stats()
    
    return GraphStatsResponse(
        total_detectors=stats['total_detectors'],
        total_edges=stats['total_edges'],
        detector_ids_sample=stats['detector_ids_sample'],
        available_models=stats['available_models']
    )


@router.get("/available-models", response_model=AvailableModelsResponse)
async def get_available_models() -> AvailableModelsResponse:
    """
    Get list of available ML models for traffic prediction.
    """
    routing_service = get_routing_service()
    stats = routing_service.get_graph_stats()
    
    return AvailableModelsResponse(
        models=stats['available_models'],
        total_count=len(stats['available_models']),
        default_model="catboost"
    )


@router.get("/detector/{detector_id}")
async def get_detector_by_id_endpoint(detector_id: int) -> Dict[str, Any]:
    """
    Get information about a specific detector by ID.
    """
    detector_service = get_detector_service()
    detector = detector_service.get_detector_by_id(detector_id)
    
    if not detector:
        raise HTTPException(
            status_code=404,
            detail=f"Detector with ID {detector_id} not found"
        )
    
    return {
        "detector_id": detector_id,
        "name": detector.road or f'Detector {detector_id}',
        "lat": detector.latitude,
        "lon": detector.longitude,
        "highway": detector.road,
        "lane": detector.lanes,
        "length": detector.length
    }


@router.get("/traffic-prediction/{detector_id}")
async def get_traffic_prediction(
    detector_id: int,
    model: str = "catboost",
    departure_time: str = "08:00:00"
) -> Dict[str, Any]:
    """
    Get traffic prediction for a specific detector at a given time.
    
    - **detector_id**: The detector ID
    - **model**: ML model to use for prediction
    - **departure_time**: Time in HH:MM:SS format
    """
    routing_service = get_routing_service()
    detector_service = get_detector_service()
    
    # Validate model
    stats = routing_service.get_graph_stats()
    if model not in stats['available_models']:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model '{model}'. Available models: {stats['available_models']}"
        )
    
    # Check detector exists
    detector = detector_service.get_detector_by_id(detector_id)
    if not detector:
        raise HTTPException(
            status_code=404,
            detail=f"Detector with ID {detector_id} not found"
        )
    
    # Get time interval
    interval = routing_service.time_to_interval(departure_time)
    
    # Get traffic prediction
    traffic = routing_service.get_traffic_prediction(detector_id, model, interval)
    
    return {
        "detector_id": detector_id,
        "model": model,
        "departure_time": departure_time,
        "time_interval": interval,
        "traffic_prediction": round(traffic, 2),
        "traffic_level": categorize_traffic(traffic)
    }


def categorize_traffic(traffic: float) -> str:
    """Categorize traffic level based on prediction value."""
    if traffic < 100:
        return "free_flow"
    elif traffic < 250:
        return "light"
    elif traffic < 450:
        return "moderate"
    elif traffic < 650:
        return "heavy"
    else:
        return "congested"
