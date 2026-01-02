"""
Detector Location Service

Handles loading and querying traffic detector locations in Taipei.
Provides coordinate-based search and distance calculations.
"""

import csv
import logging
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
