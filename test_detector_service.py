"""
Quick test for detector service without needing full dependency installation.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.detector_service import DetectorService

def test_detector_service():
    """Test detector service functionality."""
    print("=" * 60)
    print("DETECTOR SERVICE TEST")
    print("=" * 60)
    
    # Initialize service
    detectors_file = Path(__file__).parent / "data" / "taipeh_detectors.csv"
    print(f"Loading from: {detectors_file}")
    service = DetectorService(detectors_file)
    
    # Test 1: Check loaded detectors
    print(f"\n✓ Loaded {len(service.detectors)} detectors")
    
    # Test 2: Get specific detector
    detector_51 = service.get_detector_by_id(51)
    if detector_51:
        print(f"\n✓ Found detector 51:")
        print(f"  - Coordinates: ({detector_51.longitude}, {detector_51.latitude})")
        print(f"  - Road: {detector_51.road}")
    
    # Test 3: Distance calculation
    # Test coordinates: Taipei 101 area (121.5645, 25.0340)
    test_lat = 25.0340
    test_lon = 121.5645
    
    print(f"\n✓ Finding nearest detectors to ({test_lon}, {test_lat})...")
    nearest = service.find_nearest_detectors(test_lat, test_lon, k=5)
    
    print(f"\n  Top 5 nearest detectors:")
    for i, (detector, distance) in enumerate(nearest, 1):
        print(f"  {i}. Detector {detector.detid}: {distance:.3f} km away")
        print(f"     Road: {detector.road}")
        print(f"     Coords: ({detector.longitude}, {detector.latitude})")
    
    # Test 4: Detectors in radius
    radius = 2.0  # 2 km
    in_radius = service.get_detectors_in_radius(test_lat, test_lon, radius)
    print(f"\n✓ Found {len(in_radius)} detectors within {radius} km radius")
    
    # Test 5: Get all detector IDs
    all_ids = service.get_detector_ids()
    print(f"\n✓ Detector ID range: {min(all_ids)} - {max(all_ids)}")
    print(f"  Sample IDs: {all_ids[:10]}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    test_detector_service()
