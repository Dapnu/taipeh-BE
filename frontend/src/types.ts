export interface Location {
  lat: number;
  lng: number;
  name?: string;
}

export interface DetectorWithTraffic {
  detector_id: number;
  name: string;
  lat: number;
  lon: number;
  highway: string;
  traffic: number;
  traffic_level: 'low' | 'moderate' | 'high' | 'severe';
}

export interface PathInfo {
  path: number[];
  total_weight: number;
  edge_weights?: number[];
  traffic_levels?: { [key: string]: number }; // detector_id -> traffic value
  traffic_categories?: { // Count by category
    low: number;
    moderate: number;
    high: number;
    severe: number;
  };
  polyline?: [number, number][]; // [[lon, lat], ...]
  geometry?: [number, number][]; // Alternative name for polyline
  distance_meters: number;
  success?: boolean;
}

export interface RouteResponse {
  shortest_path: PathInfo;
  fastest_path: PathInfo;
  model_used: string;
  departure_time: string;
  all_detectors?: DetectorWithTraffic[];
}

export interface SearchResult {
  display_name: string;
  lat: string;
  lon: string;
}
