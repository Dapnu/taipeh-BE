"""
Quick test for routing service.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.routing_service import RoutingService

def test_routing_service():
    """Test routing service functionality."""
    print("=" * 60)
    print("ROUTING SERVICE TEST")
    print("=" * 60)
    
    # Initialize service
    base_path = Path(__file__).parent / "data"
    adjacency_file = base_path / "taipeh_adjacency_matrix_transposed_normalized.csv"
    
    print(f"\nLoading from: {adjacency_file}")
    service = RoutingService(
        adjacency_file=adjacency_file,
        predictions_dir=base_path
    )
    
    # Test 1: Graph stats
    stats = service.get_graph_stats()
    print(f"\n✓ Graph Statistics:")
    print(f"  - Total detectors: {stats['total_detectors']}")
    print(f"  - Total edges: {stats['total_edges']}")
    print(f"  - Sample detector IDs: {stats['detector_ids_sample']}")
    print(f"  - Available models: {stats['available_models']}")
    
    # Test 2: Time conversion
    print(f"\n✓ Time Conversion Tests:")
    test_times = ["00:00:00", "08:30:00", "12:00:00", "17:45:00", "23:59:00"]
    for t in test_times:
        interval = service.time_to_interval(t)
        back_time = service.interval_to_time(interval)
        print(f"  {t} -> interval {interval} -> {back_time}")
    
    # Test 3: Shortest path
    print(f"\n✓ Shortest Path Test (Dijkstra):")
    start_det = 51
    end_det = 907
    
    result = service.find_shortest_path(start_det, end_det)
    if result.success:
        print(f"  From detector {start_det} to {end_det}:")
        print(f"  - Path length: {len(result.path)} detectors")
        print(f"  - Total weight: {result.total_weight:.4f}")
        print(f"  - Path (first 10): {result.path[:10]}...")
        print(f"  - Path (last 5): ...{result.path[-5:]}")
    else:
        print(f"  FAILED: {result.error_message}")
    
    # Test 4: Fastest path with traffic
    print(f"\n✓ Fastest Path Test (Traffic-Aware):")
    model_name = "catboost"
    departure_time = "08:30:00"
    
    result = service.find_fastest_path(start_det, end_det, model_name, departure_time)
    if result.success:
        print(f"  From detector {start_det} to {end_det}:")
        print(f"  - Model: {model_name}")
        print(f"  - Departure: {departure_time}")
        print(f"  - Path length: {len(result.path)} detectors")
        print(f"  - Total cost: {result.total_weight:.4f}")
        print(f"  - Path (first 10): {result.path[:10]}...")
        
        if result.traffic_levels:
            avg_traffic = sum(result.traffic_levels) / len(result.traffic_levels)
            max_traffic = max(result.traffic_levels)
            min_traffic = min(result.traffic_levels)
            print(f"  - Traffic stats: avg={avg_traffic:.1f}, min={min_traffic:.1f}, max={max_traffic:.1f}")
    else:
        print(f"  FAILED: {result.error_message}")
    
    # Test 5: Compare different times
    print(f"\n✓ Traffic Variation by Time:")
    times = ["06:00:00", "08:30:00", "12:00:00", "18:00:00", "22:00:00"]
    
    for t in times:
        result = service.find_fastest_path(start_det, end_det, model_name, t)
        if result.success and result.traffic_levels:
            avg_traffic = sum(result.traffic_levels) / len(result.traffic_levels)
            print(f"  {t}: avg traffic = {avg_traffic:.1f}, total cost = {result.total_weight:.2f}")
    
    # Test 6: Get traffic prediction for specific detector
    print(f"\n✓ Traffic Prediction Lookup:")
    test_detector = 51
    test_interval = service.time_to_interval("08:30:00")
    traffic = service.get_traffic_prediction(test_detector, "catboost", test_interval)
    print(f"  Detector {test_detector} at 08:30:00 (interval {test_interval}): {traffic:.1f}")
    
    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED!")
    print("=" * 60)

if __name__ == "__main__":
    test_routing_service()
