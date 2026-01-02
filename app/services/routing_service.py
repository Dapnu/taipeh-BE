"""
Routing Service

Handles route calculation using graph algorithms with traffic prediction data.
Supports shortest path (distance-based) and fastest path (traffic-aware).
Uses actual road network from OSMnx GraphML file for realistic routing.
"""

import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set, Any, Union
from dataclasses import dataclass, field
import heapq
import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class RouteResult:
    """Result of a route calculation."""
    path: List[int]  # Sequence of detector IDs
    total_weight: float  # Total path weight (distance or traffic cost)
    edge_weights: List[float]  # Individual edge weights
    traffic_levels: Union[Dict[int, float], List[float]]  # Traffic prediction at each detector (dict or list)
    geometry: List[Tuple[float, float]] = field(default_factory=list)  # Road geometry (lon, lat) points
    distance_meters: float = 0.0  # Total distance in meters
    success: bool = True
    error_message: str = ""


@dataclass
class DetectorInfo:
    """Information about a detector."""
    detid: int
    lat: float
    lon: float
    nearest_node: Optional[int] = None  # OSM node ID


class RoutingService:
    """
    Service for calculating optimal routes through detector network.
    
    Uses OSMnx road network graph for realistic shortest path routing
    and traffic predictions for fastest path calculation.
    """
    
    # Time interval constants
    INTERVAL_MINUTES = 3
    INTERVALS_PER_DAY = 480  # 24 * 60 / 3
    
    def __init__(
        self,
        adjacency_file: Path,
        predictions_dir: Path,
        graphml_file: Optional[Path] = None,
        detectors_file: Optional[Path] = None
    ):
        """
        Initialize routing service.
        
        Args:
            adjacency_file: Path to taipeh_adjacency_matrix_transposed_normalized.csv
            predictions_dir: Directory containing prediction CSV files
            graphml_file: Path to taipei.graphml (OSMnx road network)
            detectors_file: Path to taipeh_detectors.csv
        """
        self.adjacency_file = adjacency_file
        self.predictions_dir = predictions_dir
        self.graphml_file = graphml_file
        self.detectors_file = detectors_file
        
        # Graph structure from adjacency matrix: {from_detector: {to_detector: weight}}
        self.graph: Dict[int, Dict[int, float]] = {}
        self.detector_ids: List[int] = []
        
        # OSMnx road network graph
        self.road_network: Optional[nx.MultiDiGraph] = None
        
        # Detector information with coordinates
        self.detectors: Dict[int, DetectorInfo] = {}
        
        # Predictions cache: {model: {detector_id: {interval: traffic_predict}}}
        self.predictions_cache: Dict[str, Dict[int, Dict[int, float]]] = {}
        
        # Load graph structures
        self._load_adjacency_matrix()
        self._load_detectors()
        self._load_road_network()
    
    def _load_adjacency_matrix(self) -> None:
        """Load adjacency matrix and build graph structure."""
        if not self.adjacency_file.exists():
            logger.error(f"Adjacency file not found: {self.adjacency_file}")
            return
        
        try:
            with open(self.adjacency_file, 'r') as f:
                reader = csv.reader(f)
                
                # First row contains column headers (detector IDs)
                header = next(reader)
                # Remove 'detid_Y' or first column header, parse detector IDs
                col_detector_ids = []
                for col in header[1:]:
                    try:
                        # Parse detector ID (might be like "51.00")
                        det_id = int(float(col))
                        col_detector_ids.append(det_id)
                    except ValueError:
                        continue
                
                self.detector_ids = col_detector_ids
                logger.info(f"Found {len(self.detector_ids)} detectors in adjacency matrix")
                
                # Initialize graph structure
                for det_id in self.detector_ids:
                    self.graph[det_id] = {}
                
                # Parse each row
                for row in reader:
                    if not row:
                        continue
                    
                    try:
                        # First column is row detector ID
                        row_det_id = int(float(row[0]))
                        
                        # Parse edge weights to other detectors
                        for i, weight_str in enumerate(row[1:]):
                            if i >= len(col_detector_ids):
                                break
                            
                            col_det_id = col_detector_ids[i]
                            weight = float(weight_str)
                            
                            # Only add edge if weight > 0 (connected)
                            # Also filter out very small weights (noise)
                            if weight > 0.01 and row_det_id != col_det_id:
                                self.graph[row_det_id][col_det_id] = weight
                    
                    except (ValueError, IndexError) as e:
                        continue
                
                # Count edges
                total_edges = sum(len(neighbors) for neighbors in self.graph.values())
                logger.info(f"Built graph with {len(self.graph)} nodes and {total_edges} edges")
        
        except Exception as e:
            logger.error(f"Error loading adjacency matrix: {e}")
    
    def _load_detectors(self) -> None:
        """Load detector information with coordinates from CSV."""
        if not self.detectors_file or not self.detectors_file.exists():
            logger.warning(f"Detectors file not found: {self.detectors_file}")
            return
        
        try:
            with open(self.detectors_file, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        detid = int(row['detid'])
                        lat = float(row['lat'])
                        lon = float(row['long'])
                        
                        self.detectors[detid] = DetectorInfo(
                            detid=detid,
                            lat=lat,
                            lon=lon
                        )
                    except (ValueError, KeyError) as e:
                        continue
                
            logger.info(f"Loaded {len(self.detectors)} detectors with coordinates")
        
        except Exception as e:
            logger.error(f"Error loading detectors: {e}")
    
    def _load_road_network(self) -> None:
        """Load OSMnx road network from GraphML file."""
        if not self.graphml_file or not self.graphml_file.exists():
            logger.warning(f"GraphML file not found: {self.graphml_file}")
            return
        
        try:
            logger.info(f"Loading road network from {self.graphml_file}...")
            self.road_network = nx.read_graphml(self.graphml_file)
            
            # Convert to MultiDiGraph if needed
            if not isinstance(self.road_network, nx.MultiDiGraph):
                self.road_network = nx.MultiDiGraph(self.road_network)
            
            logger.info(f"Road network loaded: {self.road_network.number_of_nodes()} nodes, {self.road_network.number_of_edges()} edges")
            
            # Map detectors to nearest road network nodes
            self._map_detectors_to_nodes()
            
        except Exception as e:
            logger.error(f"Error loading road network: {e}")
            self.road_network = None
    
    def _map_detectors_to_nodes(self) -> None:
        """Map each detector to its nearest node in the road network."""
        if self.road_network is None:
            return
        
        # Build a list of nodes with their coordinates
        nodes_with_coords = []
        for node_id, data in self.road_network.nodes(data=True):
            if 'y' in data and 'x' in data:
                try:
                    lat = float(data['y'])
                    lon = float(data['x'])
                    nodes_with_coords.append((node_id, lat, lon))
                except (ValueError, TypeError):
                    continue
        
        if not nodes_with_coords:
            logger.warning("No nodes with coordinates found in road network")
            return
        
        logger.info(f"Mapping {len(self.detectors)} detectors to {len(nodes_with_coords)} road network nodes...")
        
        # For each detector, find nearest node
        mapped_count = 0
        for detid, det_info in self.detectors.items():
            min_dist = float('inf')
            nearest_node = None
            
            for node_id, node_lat, node_lon in nodes_with_coords:
                # Simple Euclidean distance (good enough for nearby points)
                dist = ((det_info.lat - node_lat) ** 2 + (det_info.lon - node_lon) ** 2) ** 0.5
                
                if dist < min_dist:
                    min_dist = dist
                    nearest_node = node_id
            
            if nearest_node is not None:
                det_info.nearest_node = nearest_node
                mapped_count += 1
        
        logger.info(f"Mapped {mapped_count} detectors to road network nodes")
    
    @staticmethod
    def time_to_interval(time_str: str) -> int:
        """
        Convert time string to interval index.
        
        Args:
            time_str: Time in format "HH:MM:SS" or "HH:MM"
            
        Returns:
            Interval index (0-479)
        """
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            
            total_minutes = hours * 60 + minutes
            interval = total_minutes // 3
            
            # Ensure within valid range
            return min(max(interval, 0), 479)
        
        except (ValueError, IndexError):
            logger.warning(f"Invalid time format: {time_str}, using interval 0")
            return 0
    
    @staticmethod
    def interval_to_time(interval: int) -> str:
        """
        Convert interval index to time string.
        
        Args:
            interval: Interval index (0-479)
            
        Returns:
            Time string "HH:MM:SS"
        """
        total_minutes = interval * 3
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02d}:{minutes:02d}:00"
    
    def _load_predictions(self, model_name: str) -> Dict[int, Dict[int, float]]:
        """
        Load predictions for a specific model.
        
        Args:
            model_name: Model name (e.g., "catboost", "xgboost")
            
        Returns:
            Dict mapping detector_id -> interval -> traffic_predict
        """
        if model_name in self.predictions_cache:
            return self.predictions_cache[model_name]
        
        # Find prediction file
        prediction_file = None
        for f in self.predictions_dir.glob(f"predictions_*_{model_name}.csv"):
            prediction_file = f
            break
        
        if not prediction_file or not prediction_file.exists():
            logger.error(f"Prediction file not found for model: {model_name}")
            return {}
        
        predictions: Dict[int, Dict[int, float]] = {}
        
        try:
            with open(prediction_file, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        det_id = int(row['detid'])
                        # Use prediction_chain_step (0-479) as the interval key
                        # This aligns with time_to_interval() which returns 0-479
                        # The 'interval' column (0-7) represents 3-hour periods
                        interval = int(row['prediction_chain_step'])
                        traffic = float(row['traffic_predict'])
                        
                        if det_id not in predictions:
                            predictions[det_id] = {}
                        
                        predictions[det_id][interval] = traffic
                    
                    except (ValueError, KeyError):
                        continue
            
            self.predictions_cache[model_name] = predictions
            logger.info(f"Loaded predictions for {len(predictions)} detectors from {model_name}")
            
        except Exception as e:
            logger.error(f"Error loading predictions: {e}")
        
        return predictions
    
    def get_traffic_prediction(
        self,
        detector_id: int,
        model_name: str,
        interval: int
    ) -> float:
        """
        Get traffic prediction for a detector at specific time interval.
        
        Args:
            detector_id: Detector ID
            model_name: Prediction model name
            interval: Time interval (0-479)
            
        Returns:
            Traffic prediction value (0-800), default 400 if not found
        """
        predictions = self._load_predictions(model_name)
        
        if detector_id in predictions:
            if interval in predictions[detector_id]:
                return predictions[detector_id][interval]
        
        # Return moderate traffic if not found
        return 400.0
    
    def get_all_detectors_with_traffic(
        self,
        model_name: str,
        departure_time: str
    ) -> List[Dict]:
        """
        Get all detectors with their traffic levels at a specific time.
        
        Args:
            model_name: ML model name for predictions
            departure_time: Departure time "HH:MM:SS"
            
        Returns:
            List of dicts with detector info and traffic level
        """
        # Convert time to interval
        interval = self.time_to_interval(departure_time)
        
        # Load predictions
        predictions = self._load_predictions(model_name)
        
        # Calculate average traffic for fallback (same as used in path calculation)
        fallback_traffic = self._get_average_traffic(predictions, interval)
        
        # Load detector details from CSV for name and highway info
        detector_details = {}
        if self.detectors_file and self.detectors_file.exists():
            try:
                import csv
                with open(self.detectors_file, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        det_id = int(row['detid'])
                        detector_details[det_id] = {
                            'name': row.get('fclass', f'Detector {det_id}'),
                            'highway': row.get('fclass', '')
                        }
            except Exception as e:
                logger.warning(f"Could not load detector details: {e}")
        
        result = []
        
        for det_id, det_info in self.detectors.items():
            # Get traffic prediction for this detector
            # Use average traffic as fallback for consistency with path calculation
            traffic = predictions.get(det_id, {}).get(interval, fallback_traffic)
            
            # Determine traffic level category
            # Traffic level categories (adjusted for actual traffic conditions)
            # < 25: low (lancar)
            # 25-50: moderate (ramai lancar)  
            # 50-100: high (padat)
            # >= 100: severe (macet parah)
            if traffic < 25:
                traffic_level = "low"
            elif traffic < 50:
                traffic_level = "moderate"
            elif traffic < 100:
                traffic_level = "high"
            else:
                traffic_level = "severe"
            
            # Get name and highway from details
            details = detector_details.get(det_id, {})
            name = details.get('name', f'Detector {det_id}')
            highway = details.get('highway', '')
            
            result.append({
                "detector_id": det_id,
                "name": name,
                "lat": det_info.lat,
                "lon": det_info.lon,
                "highway": highway,
                "traffic": round(traffic, 2),
                "traffic_level": traffic_level
            })
        
        return result
    
    def find_shortest_path(
        self,
        start_detector: int,
        end_detector: int,
        model_name: str = None,
        departure_time: str = None
    ) -> RouteResult:
        """
        Find shortest path using actual road network from OSMnx.
        Falls back to adjacency matrix if road network not available.
        
        Args:
            start_detector: Starting detector ID
            end_detector: Destination detector ID
            model_name: Optional - prediction model for traffic info display
            departure_time: Optional - departure time for traffic info display
            
        Returns:
            RouteResult with path, geometry, detectors along route, and traffic levels
        """
        # Check if detectors exist
        if start_detector not in self.graph:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message=f"Start detector {start_detector} not in network"
            )
        
        if end_detector not in self.graph:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message=f"End detector {end_detector} not in network"
            )
        
        # Try to use road network for actual shortest path
        if self.road_network is not None and start_detector in self.detectors and end_detector in self.detectors:
            result = self._find_road_network_path(start_detector, end_detector, model_name, departure_time)
            if result.success:
                return result
            # Fall through to adjacency-based if road network fails
            logger.warning(f"Road network path failed, falling back to adjacency: {result.error_message}")
        
        # Fallback: use adjacency matrix with Dijkstra
        return self._find_adjacency_shortest_path(start_detector, end_detector)
    
    def _find_road_network_path(
        self,
        start_detector: int,
        end_detector: int,
        model_name: str = None,
        departure_time: str = None
    ) -> RouteResult:
        """
        Find shortest path using OSMnx road network.
        Also detects all detectors along the route and their traffic levels.
        
        Args:
            start_detector: Starting detector ID
            end_detector: Destination detector ID
            model_name: Optional - prediction model for traffic info
            departure_time: Optional - departure time for traffic info
            
        Returns:
            RouteResult with actual road geometry, detectors along route, and traffic levels
        """
        start_info = self.detectors.get(start_detector)
        end_info = self.detectors.get(end_detector)
        
        if not start_info or not start_info.nearest_node:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message=f"Start detector {start_detector} not mapped to road network"
            )
        
        if not end_info or not end_info.nearest_node:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message=f"End detector {end_detector} not mapped to road network"
            )
        
        def get_edge_length(u, v, data):
            """Custom weight function to handle string length values from GraphML."""
            length = data.get('length', 1)
            try:
                return float(length)
            except (ValueError, TypeError):
                return 1.0
        
        def heuristic(u, v):
            """
            Admissible heuristic: straight-line distance in meters.
            Always underestimates actual road distance (roads are never shorter than straight line).
            """
            try:
                u_data = self.road_network.nodes[u]
                v_data = self.road_network.nodes[v]
                u_lat = float(u_data.get('y', 0))
                u_lon = float(u_data.get('x', 0))
                v_lat = float(v_data.get('y', 0))
                v_lon = float(v_data.get('x', 0))
                
                # Haversine approximation for small distances (Taipei area)
                # At latitude ~25°, 1 degree ≈ 111km lat, 100km lon
                lat_diff = (u_lat - v_lat) * 111000  # meters
                lon_diff = (u_lon - v_lon) * 100000  # meters (cos(25°) ≈ 0.9)
                
                return (lat_diff**2 + lon_diff**2) ** 0.5
            except:
                return 0  # Fallback: no heuristic = Dijkstra behavior
        
        try:
            # Find shortest path in road network using A* algorithm
            # A* with admissible heuristic guarantees optimal path and is faster than Dijkstra
            node_path = nx.astar_path(
                self.road_network,
                source=start_info.nearest_node,
                target=end_info.nearest_node,
                heuristic=heuristic,
                weight=get_edge_length
            )
            
            # Extract geometry (coordinates) from path
            geometry = []
            total_distance = 0.0
            edge_weights = []
            
            # Build set of nodes in the path for quick lookup
            path_nodes_set = set(node_path)
            
            for i, node_id in enumerate(node_path):
                node_data = self.road_network.nodes[node_id]
                if 'y' in node_data and 'x' in node_data:
                    try:
                        lat = float(node_data['y'])
                        lon = float(node_data['x'])
                        geometry.append((lon, lat))
                    except (ValueError, TypeError):
                        pass
                
                # Get edge length to next node
                if i < len(node_path) - 1:
                    next_node = node_path[i + 1]
                    # Get edge data (MultiDiGraph may have multiple edges)
                    edge_data = self.road_network.get_edge_data(node_id, next_node)
                    if edge_data:
                        # Get first edge's length
                        first_edge = list(edge_data.values())[0] if isinstance(edge_data, dict) else edge_data
                        if isinstance(first_edge, dict):
                            length_val = first_edge.get('length', 0)
                            # Convert to float (may be string from graphml)
                            try:
                                length = float(length_val) if length_val else 0
                            except (ValueError, TypeError):
                                length = 0
                        else:
                            length = 0
                        edge_weights.append(length)
                        total_distance += length
            
            # Find all detectors along the route
            detectors_along_route = []
            traffic_levels = {}
            
            # Load predictions if model and time provided
            predictions = None
            departure_interval = None
            if model_name and departure_time:
                predictions = self._load_predictions(model_name)
                departure_interval = self.time_to_interval(departure_time)
            
            # Get average traffic for fallback
            avg_traffic = 400.0
            if predictions and departure_interval is not None:
                avg_traffic = self._get_average_traffic(predictions, departure_interval)
            
            # Check each detector if its nearest node is on the path
            for det_id, det_info in self.detectors.items():
                if det_info.nearest_node and det_info.nearest_node in path_nodes_set:
                    # Find position in path for ordering
                    try:
                        path_index = node_path.index(det_info.nearest_node)
                        detectors_along_route.append((path_index, det_id))
                        
                        # Get traffic level if predictions available
                        if predictions and departure_interval is not None:
                            traffic = predictions.get(det_id, {}).get(departure_interval, avg_traffic)
                            traffic_levels[det_id] = traffic
                    except ValueError:
                        pass
            
            # Sort by path order and extract detector IDs
            detectors_along_route.sort(key=lambda x: x[0])
            detector_path = [det_id for _, det_id in detectors_along_route]
            
            # Ensure start and end are included with their traffic levels
            if start_detector not in detector_path:
                detector_path.insert(0, start_detector)
            if start_detector not in traffic_levels and predictions and departure_interval is not None:
                traffic_levels[start_detector] = predictions.get(start_detector, {}).get(departure_interval, avg_traffic)
            
            if end_detector not in detector_path:
                detector_path.append(end_detector)
            if end_detector not in traffic_levels and predictions and departure_interval is not None:
                traffic_levels[end_detector] = predictions.get(end_detector, {}).get(departure_interval, avg_traffic)
            
            return RouteResult(
                path=detector_path,
                total_weight=total_distance,
                edge_weights=edge_weights,
                traffic_levels=traffic_levels,
                geometry=geometry,
                distance_meters=total_distance,
                success=True
            )
            
        except nx.NetworkXNoPath:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message="No path found in road network"
            )
        except Exception as e:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message=f"Road network error: {str(e)}"
            )
    
    def _find_adjacency_shortest_path(
        self,
        start_detector: int,
        end_detector: int
    ) -> RouteResult:
        """
        Find shortest path using adjacency matrix (fallback).
        Uses Dijkstra's algorithm.
        
        Args:
            start_detector: Starting detector ID
            end_detector: Destination detector ID
            
        Returns:
            RouteResult with path and metrics
        """
        # Dijkstra's algorithm
        distances: Dict[int, float] = {det: float('inf') for det in self.graph}
        distances[start_detector] = 0
        previous: Dict[int, Optional[int]] = {det: None for det in self.graph}
        
        # Priority queue: (distance, detector_id)
        pq = [(0, start_detector)]
        visited: Set[int] = set()
        
        while pq:
            current_dist, current = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == end_detector:
                break
            
            if current not in self.graph:
                continue
            
            for neighbor, weight in self.graph[current].items():
                if neighbor in visited:
                    continue
                
                new_dist = current_dist + weight
                
                if new_dist < distances[neighbor]:
                    distances[neighbor] = new_dist
                    previous[neighbor] = current
                    heapq.heappush(pq, (new_dist, neighbor))
        
        # Reconstruct path
        if distances[end_detector] == float('inf'):
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message="No path found between detectors"
            )
        
        path = []
        current = end_detector
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        
        # Calculate edge weights and generate simple geometry from detector coords
        edge_weights = []
        geometry = []
        
        for i, det_id in enumerate(path):
            # Add detector coordinates to geometry
            if det_id in self.detectors:
                det = self.detectors[det_id]
                geometry.append((det.lon, det.lat))
            
            # Get edge weight to next detector
            if i < len(path) - 1:
                weight = self.graph[path[i]].get(path[i + 1], 0)
                edge_weights.append(weight)
        
        return RouteResult(
            path=path,
            total_weight=distances[end_detector],
            edge_weights=edge_weights,
            traffic_levels=[],
            geometry=geometry,
            success=True
        )
    
    def find_fastest_path(
        self,
        start_detector: int,
        end_detector: int,
        model_name: str,
        departure_time: str
    ) -> RouteResult:
        """
        Find fastest path considering traffic predictions.
        Uses A* algorithm with traffic-based edge weights.
        
        Higher traffic_predict = more congested = higher cost to traverse
        
        Args:
            start_detector: Starting detector ID
            end_detector: Destination detector ID
            model_name: Prediction model to use
            departure_time: Departure time string "HH:MM:SS"
            
        Returns:
            RouteResult with path, traffic levels, and metrics
        """
        if start_detector not in self.graph:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message=f"Start detector {start_detector} not in network"
            )
        
        if end_detector not in self.graph:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message=f"End detector {end_detector} not in network"
            )
        
        # Convert departure time to interval
        departure_interval = self.time_to_interval(departure_time)
        
        # Load predictions
        predictions = self._load_predictions(model_name)
        
        # Try to use road network for traffic-aware routing
        if self.road_network is not None and start_detector in self.detectors and end_detector in self.detectors:
            result = self._find_road_network_fastest_path(
                start_detector, end_detector, predictions, departure_interval
            )
            if result.success:
                return result
            logger.warning(f"Road network fastest path failed, falling back: {result.error_message}")
        
        # Fallback: use adjacency matrix with traffic weighting
        return self._find_adjacency_fastest_path(
            start_detector, end_detector, predictions, departure_interval
        )
    
    def _find_road_network_fastest_path(
        self,
        start_detector: int,
        end_detector: int,
        predictions: Dict[int, Dict[int, float]],
        departure_interval: int
    ) -> RouteResult:
        """
        Find fastest path using road network with traffic-aware weighting.
        
        Uses actual road network from GraphML and applies traffic predictions
        to weight the edges - higher traffic = higher cost.
        
        This method also finds ALL detectors along the route path and uses
        their traffic predictions for accurate weighting.
        """
        start_info = self.detectors.get(start_detector)
        end_info = self.detectors.get(end_detector)
        
        if not start_info or not start_info.nearest_node:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message=f"Start detector {start_detector} not mapped to road network"
            )
        
        if not end_info or not end_info.nearest_node:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message=f"End detector {end_detector} not mapped to road network"
            )
        
        # Build a mapping of road network nodes to nearby detectors for traffic lookup
        # This allows us to apply traffic predictions based on nearby detectors
        node_to_detector = self._build_node_to_detector_map()
        
        # Build reverse mapping: detector -> node for finding detectors along path
        detector_to_node = {det_id: det_info.nearest_node 
                          for det_id, det_info in self.detectors.items() 
                          if det_info.nearest_node is not None}
        
        # Get average traffic for the departure time from all detectors
        avg_traffic = self._get_average_traffic(predictions, departure_interval)
        
        def get_traffic_weighted_length(u, v, data):
            """
            Calculate edge cost based on road length and traffic conditions.
            
            Higher traffic at nearby detectors = higher cost to traverse
            """
            # Get base length
            length = data.get('length', 1)
            try:
                base_length = float(length)
            except (ValueError, TypeError):
                base_length = 1.0
            
            # Find traffic level from nearby detector
            traffic = avg_traffic  # Default to average
            
            # Check if destination node has a nearby detector
            if v in node_to_detector:
                det_id = node_to_detector[v]
                if det_id in predictions and departure_interval in predictions[det_id]:
                    traffic = predictions[det_id][departure_interval]
            elif u in node_to_detector:
                det_id = node_to_detector[u]
                if det_id in predictions and departure_interval in predictions[det_id]:
                    traffic = predictions[det_id][departure_interval]
            
            # ============================================================
            # TRAFFIC WEIGHT CONFIGURATION - MAXIMUM AVOIDANCE
            # ============================================================
            # Goal: ABSOLUTELY AVOID HIGH TRAFFIC (>= 50)
            #
            # Strategy: EXTREME exponential penalty
            # - Low traffic (< 25): minimal penalty (~1x)
            # - Moderate traffic (25-50): moderate penalty (~2-5x)
            # - High traffic (50-100): MASSIVE penalty (100x-500x)
            # - Severe traffic (>= 100): PROHIBITIVE penalty (1000x+)
            # ============================================================
            
            # ULTRA-AGGRESSIVE configuration
            if traffic < 25:
                # Low traffic: minimal penalty
                traffic_multiplier = 1.0 + (traffic / 100.0)  # 1.0x - 1.25x
            elif traffic < 50:
                # Moderate traffic: noticeable penalty
                # 25 → 2x, 50 → 5x
                traffic_multiplier = 1.0 + ((traffic - 25) / 10.0)  # 1.0x - 3.5x
            elif traffic < 100:
                # HIGH traffic: MASSIVE penalty to force A* to find alternatives
                # 50 → 100x, 75 → 300x, 100 → 500x
                traffic_multiplier = 100.0 + ((traffic - 50) * 8.0)
            else:
                # SEVERE traffic: PROHIBITIVE penalty (make it almost impossible)
                # 100 → 500x, 200 → 1500x, 400 → 3500x
                traffic_multiplier = 500.0 + ((traffic - 100) * 10.0)
            
            # Cap at 5000x
            MAX_MULTIPLIER = 5000.0
            traffic_multiplier = min(traffic_multiplier, MAX_MULTIPLIER)
            
            return base_length * traffic_multiplier
        
        try:
            # Find fastest path with traffic weighting using A* algorithm
            # A* requires an admissible heuristic: h(n) <= actual cost from n to goal
            # 
            # Note: With aggressive traffic penalties, heuristic is still admissible
            # because we're only increasing edge costs, not reducing them.
            # 
            # Using h(n) = euclidean_distance (straight-line) is ADMISSIBLE because:
            # - euclidean_distance <= road_distance (roads are never shorter than straight line)
            # - road_distance <= weighted_cost (multiplier >= 1)
            # Therefore: h(n) <= actual_cost ✓
            
            def heuristic(u, v):
                """Admissible heuristic: straight-line distance in meters"""
                try:
                    u_data = self.road_network.nodes[u]
                    v_data = self.road_network.nodes[v]
                    u_lat = float(u_data.get('y', 0))
                    u_lon = float(u_data.get('x', 0))
                    v_lat = float(v_data.get('y', 0))
                    v_lon = float(v_data.get('x', 0))
                    
                    # Haversine approximation for small distances (Taipei area)
                    # At latitude ~25°, 1 degree ≈ 111km lat, 100km lon
                    lat_diff = (u_lat - v_lat) * 111000  # meters
                    lon_diff = (u_lon - v_lon) * 100000  # meters (cos(25°) ≈ 0.9)
                    
                    return (lat_diff**2 + lon_diff**2) ** 0.5
                except:
                    return 0  # Fallback: no heuristic = Dijkstra behavior
            
            try:
                node_path = nx.astar_path(
                    self.road_network,
                    source=start_info.nearest_node,
                    target=end_info.nearest_node,
                    heuristic=heuristic,
                    weight=get_traffic_weighted_length
                )
            except nx.NetworkXNoPath:
                raise ValueError(f"No path found between detectors {start_detector} and {end_detector}")
            
            # Convert node_path to a set for O(1) lookup
            path_nodes_set = set(node_path)
            
            # Find ALL detectors along the path
            # A detector is "along the path" if its nearest_node is in the path
            detectors_along_path = []
            detector_traffic_map = {}  # detector_id -> traffic level
            
            for det_id, node_id in detector_to_node.items():
                if node_id in path_nodes_set:
                    # Get traffic prediction for this detector
                    traffic = predictions.get(det_id, {}).get(departure_interval, avg_traffic)
                    
                    # Find the index in the path for ordering
                    try:
                        path_index = node_path.index(node_id)
                        detectors_along_path.append((path_index, det_id, traffic))
                        detector_traffic_map[det_id] = traffic
                    except ValueError:
                        continue
            
            # Sort detectors by their order in the path
            detectors_along_path.sort(key=lambda x: x[0])
            
            # Extract ordered detector IDs and their traffic levels
            ordered_detector_ids = [det_id for _, det_id, _ in detectors_along_path]
            ordered_traffic_levels = [traffic for _, _, traffic in detectors_along_path]
            
            # Ensure start and end detectors are included
            if start_detector not in ordered_detector_ids:
                ordered_detector_ids.insert(0, start_detector)
                start_traffic = predictions.get(start_detector, {}).get(departure_interval, avg_traffic)
                ordered_traffic_levels.insert(0, start_traffic)
                detector_traffic_map[start_detector] = start_traffic
            
            if end_detector not in ordered_detector_ids:
                ordered_detector_ids.append(end_detector)
                end_traffic = predictions.get(end_detector, {}).get(departure_interval, avg_traffic)
                ordered_traffic_levels.append(end_traffic)
                detector_traffic_map[end_detector] = end_traffic
            
            # Extract geometry and calculate metrics
            geometry = []
            total_distance = 0.0
            total_weighted_cost = 0.0
            edge_weights = []
            segment_traffic_levels = []
            
            for i, node_id in enumerate(node_path):
                node_data = self.road_network.nodes[node_id]
                if 'y' in node_data and 'x' in node_data:
                    try:
                        lat = float(node_data['y'])
                        lon = float(node_data['x'])
                        geometry.append((lon, lat))
                    except (ValueError, TypeError):
                        pass
                
                # Get edge data to next node
                if i < len(node_path) - 1:
                    next_node = node_path[i + 1]
                    edge_data = self.road_network.get_edge_data(node_id, next_node)
                    if edge_data:
                        first_edge = list(edge_data.values())[0] if isinstance(edge_data, dict) else edge_data
                        if isinstance(first_edge, dict):
                            try:
                                length = float(first_edge.get('length', 0))
                            except (ValueError, TypeError):
                                length = 0
                            
                            # Get traffic for this segment
                            traffic = avg_traffic
                            if next_node in node_to_detector:
                                det_id = node_to_detector[next_node]
                                if det_id in predictions and departure_interval in predictions[det_id]:
                                    traffic = predictions[det_id][departure_interval]
                            
                            traffic_multiplier = 1.0 + (traffic / 400.0)
                            weighted_cost = length * traffic_multiplier
                            
                            edge_weights.append(length)
                            total_distance += length
                            total_weighted_cost += weighted_cost
                            segment_traffic_levels.append(traffic)
            
            logger.info(f"Fastest path found: {len(ordered_detector_ids)} detectors along route, "
                       f"{len(node_path)} nodes, {total_distance:.0f}m")
            
            return RouteResult(
                path=ordered_detector_ids,
                total_weight=total_weighted_cost,
                edge_weights=edge_weights,
                traffic_levels=detector_traffic_map,  # Dict format: {det_id: traffic_level}
                geometry=geometry,
                distance_meters=total_distance,
                success=True
            )
            
        except nx.NetworkXNoPath:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message="No path found in road network"
            )
        except Exception as e:
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message=f"Road network error: {str(e)}"
            )
    
    def _build_node_to_detector_map(self) -> Dict[Any, int]:
        """
        Build mapping from road network nodes to nearby detector IDs.
        Uses the nearest_node already computed for each detector.
        """
        node_to_detector = {}
        for det_id, det_info in self.detectors.items():
            if det_info.nearest_node is not None:
                node_to_detector[det_info.nearest_node] = det_id
        return node_to_detector
    
    def _get_average_traffic(
        self,
        predictions: Dict[int, Dict[int, float]],
        interval: int
    ) -> float:
        """Get average traffic across all detectors for a given interval."""
        traffic_values = []
        for det_id, intervals in predictions.items():
            if interval in intervals:
                traffic_values.append(intervals[interval])
        
        if traffic_values:
            return sum(traffic_values) / len(traffic_values)
        return 400.0  # Default moderate traffic
    
    def _find_adjacency_fastest_path(
        self,
        start_detector: int,
        end_detector: int,
        predictions: Dict[int, Dict[int, float]],
        departure_interval: int
    ) -> RouteResult:
        """
        Find fastest path using adjacency matrix with traffic weighting (fallback).
        """
        def get_edge_cost(from_det: int, to_det: int, current_interval: int) -> float:
            """Calculate edge cost based on adjacency weight and traffic."""
            base_weight = self.graph.get(from_det, {}).get(to_det, 1.0)
            
            # Get traffic at destination detector
            traffic = 400.0  # Default moderate traffic
            if to_det in predictions and current_interval in predictions[to_det]:
                traffic = predictions[to_det][current_interval]
            
            # Normalize traffic (0-800) to multiplier (1.0 - 3.0)
            # Low traffic (0-200): multiplier ~1.0
            # High traffic (600-800): multiplier ~3.0
            traffic_multiplier = 1.0 + (traffic / 400.0)
            
            return base_weight * traffic_multiplier
        
        # A* algorithm with traffic-aware costs
        g_scores: Dict[int, float] = {det: float('inf') for det in self.graph}
        g_scores[start_detector] = 0
        
        previous: Dict[int, Optional[int]] = {det: None for det in self.graph}
        
        # Priority queue: (f_score, g_score, detector_id, current_interval)
        pq = [(0, 0, start_detector, departure_interval)]
        visited: Set[int] = set()
        
        while pq:
            _, current_g, current, current_interval = heapq.heappop(pq)
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current == end_detector:
                break
            
            if current not in self.graph:
                continue
            
            for neighbor in self.graph[current]:
                if neighbor in visited:
                    continue
                
                # Calculate traffic-aware edge cost
                edge_cost = get_edge_cost(current, neighbor, current_interval)
                new_g = current_g + edge_cost
                
                if new_g < g_scores[neighbor]:
                    g_scores[neighbor] = new_g
                    previous[neighbor] = current
                    
                    # Estimate time to traverse edge (roughly 1 interval per edge)
                    next_interval = min(current_interval + 1, 479)
                    
                    # Simple heuristic: assume remaining edges have moderate traffic
                    h_score = 0  # Could add heuristic based on detector positions
                    f_score = new_g + h_score
                    
                    heapq.heappush(pq, (f_score, new_g, neighbor, next_interval))
        
        # Reconstruct path
        if g_scores[end_detector] == float('inf'):
            return RouteResult(
                path=[], total_weight=0, edge_weights=[], traffic_levels=[],
                success=False, error_message="No path found between detectors"
            )
        
        path = []
        current = end_detector
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        
        # Calculate edge weights and traffic levels along path
        edge_weights = []
        traffic_levels = []
        geometry = []
        
        current_interval = departure_interval
        for i, det_id in enumerate(path):
            # Get traffic at this detector
            traffic = 400.0
            if det_id in predictions and current_interval in predictions[det_id]:
                traffic = predictions[det_id][current_interval]
            traffic_levels.append(traffic)
            
            # Add detector coordinates to geometry
            if det_id in self.detectors:
                det = self.detectors[det_id]
                geometry.append((det.lon, det.lat))
            
            # Get edge weight to next detector
            if i < len(path) - 1:
                weight = self.graph[det_id].get(path[i + 1], 0)
                edge_weights.append(weight)
                # Advance time by roughly 1 interval per edge
                current_interval = min(current_interval + 1, 479)
        
        # Try to get actual road geometry between start and end detectors
        road_geometry = []
        if self.road_network is not None and len(path) >= 2:
            start_det = path[0]
            end_det = path[-1]
            if start_det in self.detectors and end_det in self.detectors:
                start_info = self.detectors[start_det]
                end_info = self.detectors[end_det]
                if start_info.nearest_node and end_info.nearest_node:
                    try:
                        node_path = nx.shortest_path(
                            self.road_network,
                            source=start_info.nearest_node,
                            target=end_info.nearest_node,
                            weight='length'
                        )
                        for node_id in node_path:
                            node_data = self.road_network.nodes[node_id]
                            if 'y' in node_data and 'x' in node_data:
                                try:
                                    lat = float(node_data['y'])
                                    lon = float(node_data['x'])
                                    road_geometry.append((lon, lat))
                                except (ValueError, TypeError):
                                    pass
                    except:
                        pass
        
        # Use road geometry if available, otherwise use detector coordinates
        final_geometry = road_geometry if road_geometry else geometry
        
        return RouteResult(
            path=path,
            total_weight=g_scores[end_detector],
            edge_weights=edge_weights,
            traffic_levels=traffic_levels,
            geometry=final_geometry,
            success=True
        )
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available prediction models.
        
        Returns:
            List of model names
        """
        models = []
        for f in self.predictions_dir.glob("predictions_*_*.csv"):
            # Extract model name from filename: predictions_oct1_2017_MODEL.csv
            # For multi-word models like gcn_gru: predictions_oct1_2017_gcn_gru.csv
            parts = f.stem.split('_')
            if len(parts) >= 4:
                # Join everything after date parts (oct1, 2017) as model name
                # predictions_oct1_2017_gcn_gru -> ['predictions', 'oct1', '2017', 'gcn', 'gru']
                model_name = '_'.join(parts[3:])  # Join from index 3 onwards
                if model_name not in models:
                    models.append(model_name)
        return sorted(models)
    
    def get_graph_stats(self) -> dict:
        """
        Get graph statistics.
        
        Returns:
            Dictionary with graph stats
        """
        total_edges = sum(len(neighbors) for neighbors in self.graph.values())
        
        road_network_stats = {}
        if self.road_network is not None:
            road_network_stats = {
                "road_network_nodes": self.road_network.number_of_nodes(),
                "road_network_edges": self.road_network.number_of_edges(),
                "detectors_mapped": sum(1 for d in self.detectors.values() if d.nearest_node is not None)
            }
        
        return {
            "total_detectors": len(self.graph),
            "total_edges": total_edges,
            "detector_ids_sample": self.detector_ids[:10] if self.detector_ids else [],
            "available_models": self.get_available_models(),
            "road_network_available": self.road_network is not None,
            **road_network_stats
        }


# Global routing service instance
_routing_service: Optional[RoutingService] = None


def get_routing_service() -> RoutingService:
    """
    Get global routing service instance.
    
    Returns:
        RoutingService instance
    """
    global _routing_service
    
    if _routing_service is None:
        base_path = Path(__file__).parent.parent.parent / "data"
        adjacency_file = base_path / "taipeh_adjacency_matrix_transposed_normalized.csv"
        graphml_file = base_path / "taipei.graphml"
        detectors_file = base_path / "taipeh_detectors.csv"
        
        _routing_service = RoutingService(
            adjacency_file=adjacency_file,
            predictions_dir=base_path,
            graphml_file=graphml_file,
            detectors_file=detectors_file
        )
    
    return _routing_service
