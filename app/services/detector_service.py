"""
Detector Location Service

Handles loading and querying traffic detector locations in Taipei.
Provides coordinate-based search and distance calculations.
"""

import csv
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger(__name__)


class Detector:
    """Represents a traffic detector with location and metadata."""
    
    def __init__(
        self,
        detid: int,
        longitude: float,
        latitude: float,
        road: str = "",
        length: float = 0.0,
        lanes: int = 1
    ):
        self.detid = detid
        self.longitude = longitude
        self.latitude = latitude
        self.road = road
        self.length = length
        self.lanes = lanes
    
    def to_dict(self) -> dict:
        """Convert detector to dictionary format."""
        return {
            "detid": self.detid,
            "longitude": self.longitude,
            "latitude": self.latitude,
            "road": self.road,
            "length": self.length,
            "lanes": self.lanes,
            "coordinates": [self.longitude, self.latitude]
        }
    
    def __repr__(self) -> str:
        return f"Detector(detid={self.detid}, road='{self.road}', coords=({self.longitude}, {self.latitude}))"


class DetectorService:
    """Service for managing detector locations and spatial queries."""
    
    def __init__(self, detectors_file: Path):
        """
        Initialize detector service.
        
        Args:
            detectors_file: Path to taipeh_detectors.csv
        """
        self.detectors_file = detectors_file
        self.detectors: Dict[int, Detector] = {}
        self._load_detectors()
    
    def _load_detectors(self) -> None:
        """Load detector locations from CSV file."""
        if not self.detectors_file.exists():
            logger.error(f"Detectors file not found: {self.detectors_file}")
            return
        
        try:
            with open(self.detectors_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    try:
                        detid = int(row['detid'])
                        longitude = float(row['long'])
                        latitude = float(row['lat'])
                        
                        detector = Detector(
                            detid=detid,
                            longitude=longitude,
                            latitude=latitude,
                            road=row.get('road', ''),
                            length=float(row.get('length', 0)),
                            lanes=int(row.get('lanes', 1))
                        )
                        
                        self.detectors[detid] = detector
                        count += 1
                    except (ValueError, KeyError) as e:
                        logger.warning(f"Skipping invalid detector row: {e}")
                        continue
            
            logger.info(f"Loaded {count} detectors from {self.detectors_file}")
        
        except Exception as e:
            logger.error(f"Error loading detectors: {e}")
    
    def get_detector_by_id(self, detid: int) -> Optional[Detector]:
        """
        Get detector by ID.
        
        Args:
            detid: Detector ID
            
        Returns:
            Detector object or None if not found
        """
        return self.detectors.get(detid)
    
    def get_all_detectors(self) -> List[Detector]:
        """
        Get all detectors.
        
        Returns:
            List of all detector objects
        """
        return list(self.detectors.values())
    
    def get_detector_ids(self) -> List[int]:
        """
        Get all detector IDs.
        
        Returns:
            Sorted list of detector IDs
        """
        return sorted(self.detectors.keys())
    
    @staticmethod
    def calculate_haversine_distance(
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calculate great-circle distance between two points using Haversine formula.
        
        Args:
            lat1: Latitude of point 1 (degrees)
            lon1: Longitude of point 1 (degrees)
            lat2: Latitude of point 2 (degrees)
            lon2: Longitude of point 2 (degrees)
            
        Returns:
            Distance in kilometers
        """
        # Convert decimal degrees to radians
        lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
        
        # Haversine formula
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def find_nearest_detectors(
        self,
        latitude: float,
        longitude: float,
        k: int = 3
    ) -> List[Tuple[Detector, float]]:
        """
        Find K nearest detectors to given coordinates.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            k: Number of nearest detectors to return (default: 3)
            
        Returns:
            List of tuples (Detector, distance_km) sorted by distance
        """
        if not self.detectors:
            logger.warning("No detectors loaded")
            return []
        
        # Calculate distances to all detectors
        distances = []
        for detector in self.detectors.values():
            distance = self.calculate_haversine_distance(
                latitude, longitude,
                detector.latitude, detector.longitude
            )
            distances.append((detector, distance))
        
        # Sort by distance and return top K
        distances.sort(key=lambda x: x[1])
        return distances[:k]
    
    def find_nearest_detector(
        self,
        latitude: float,
        longitude: float
    ) -> Optional[Tuple[Detector, float]]:
        """
        Find single nearest detector to given coordinates.
        
        Args:
            latitude: Target latitude
            longitude: Target longitude
            
        Returns:
            Tuple of (Detector, distance_km) or None
        """
        nearest = self.find_nearest_detectors(latitude, longitude, k=1)
        return nearest[0] if nearest else None
    
    def get_detectors_in_radius(
        self,
        latitude: float,
        longitude: float,
        radius_km: float
    ) -> List[Tuple[Detector, float]]:
        """
        Find all detectors within radius of given coordinates.
        
        Args:
            latitude: Center latitude
            longitude: Center longitude
            radius_km: Search radius in kilometers
            
        Returns:
            List of tuples (Detector, distance_km) within radius
        """
        detectors_in_radius = []
        
        for detector in self.detectors.values():
            distance = self.calculate_haversine_distance(
                latitude, longitude,
                detector.latitude, detector.longitude
            )
            
            if distance <= radius_km:
                detectors_in_radius.append((detector, distance))
        
        # Sort by distance
        detectors_in_radius.sort(key=lambda x: x[1])
        return detectors_in_radius
    
    def get_traffic_snapshot(
        self, 
        model: str, 
        time_str: str,
        data_dir: Optional[Path] = None
    ) -> Dict:
        """
        Get traffic snapshot for all detectors at specific time.
        
        Args:
            model: Model name (e.g., 'xgboost', 'gcn_gru')
            time_str: Time in HH:MM:SS format
            data_dir: Optional data directory path
            
        Returns:
            Dictionary with detector traffic data and statistics
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"
        
        # Convert time to prediction_chain_step (0-479, 3-minute intervals)
        time_parts = time_str.split(':')
        hour = int(time_parts[0])
        minute = int(time_parts[1])
        total_minutes = hour * 60 + minute
        interval = total_minutes // 3  # 3-minute intervals
        
        # Load prediction file
        prediction_file = data_dir / f"predictions_oct1_2017_{model}.csv"
        
        if not prediction_file.exists():
            logger.error(f"Prediction file not found: {prediction_file}")
            return {
                "success": False,
                "error": f"Model '{model}' predictions not found"
            }
        
        try:
            # Load predictions
            df = pd.read_csv(prediction_file)
            
            # Filter for specific interval
            interval_data = df[df['prediction_chain_step'] == interval]
            
            # Build detector list with traffic
            detectors_with_traffic = []
            traffic_values = []
            
            for _, row in interval_data.iterrows():
                detid = int(row['detid'])
                traffic = float(row['traffic_predict'])
                
                detector = self.get_detector_by_id(detid)
                if detector:
                    # Categorize traffic
                    if traffic < 25:
                        category = "low"
                    elif traffic < 50:
                        category = "moderate"
                    elif traffic < 100:
                        category = "high"
                    else:
                        category = "severe"
                    
                    detectors_with_traffic.append({
                        "detid": detid,
                        "lat": detector.latitude,
                        "lon": detector.longitude,
                        "traffic": round(traffic, 2),
                        "category": category,
                        "road": detector.road
                    })
                    traffic_values.append(traffic)
            
            # Calculate statistics
            if traffic_values:
                low_count = sum(1 for t in traffic_values if t < 25)
                moderate_count = sum(1 for t in traffic_values if 25 <= t < 50)
                high_count = sum(1 for t in traffic_values if 50 <= t < 100)
                severe_count = sum(1 for t in traffic_values if t >= 100)
                
                statistics = {
                    "total_detectors": len(traffic_values),
                    "avg_traffic": round(sum(traffic_values) / len(traffic_values), 2),
                    "min_traffic": round(min(traffic_values), 2),
                    "max_traffic": round(max(traffic_values), 2),
                    "low_count": low_count,
                    "moderate_count": moderate_count,
                    "high_count": high_count,
                    "severe_count": severe_count
                }
            else:
                statistics = {
                    "total_detectors": 0,
                    "avg_traffic": 0,
                    "min_traffic": 0,
                    "max_traffic": 0,
                    "low_count": 0,
                    "moderate_count": 0,
                    "high_count": 0,
                    "severe_count": 0
                }
            
            return {
                "success": True,
                "model": model,
                "time": time_str,
                "interval": interval,
                "detectors": detectors_with_traffic,
                "statistics": statistics
            }
        
        except Exception as e:
            logger.error(f"Error loading traffic snapshot: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# Global detector service instance
_detector_service: Optional[DetectorService] = None


def get_detector_service() -> DetectorService:
    """
    Get global detector service instance.
    
    Returns:
        DetectorService instance
    """
    global _detector_service
    
    if _detector_service is None:
        # Initialize with default path
        detectors_file = Path(__file__).parent.parent.parent / "data" / "taipeh_detectors.csv"
        _detector_service = DetectorService(detectors_file)
    
    return _detector_service
