import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, LayersControl, useMap } from 'react-leaflet';
import { LatLngTuple } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import './TrafficView.css';

// Import plugins
import 'leaflet.heat';
import 'leaflet.markercluster';
import L from 'leaflet';

interface TrafficDetector {
  detid: number;
  lat: number;
  lon: number;
  traffic: number;
  category: 'low' | 'moderate' | 'high' | 'severe';
  road: string;
}

interface TrafficStatistics {
  total_detectors: number;
  avg_traffic: number;
  min_traffic: number;
  max_traffic: number;
  low_count: number;
  moderate_count: number;
  high_count: number;
  severe_count: number;
}

interface TrafficViewProps {
  selectedModel: string;
}

// Heat map layer component
const HeatmapLayer = ({ detectors }: { detectors: TrafficDetector[] }) => {
  const map = useMap();

  useEffect(() => {
    if (!map || !detectors.length) return;

    // Remove existing heatmap layers
    map.eachLayer((layer: any) => {
      if (layer instanceof (L as any).HeatLayer) {
        map.removeLayer(layer);
      }
    });

    // Create heat map data
    const heatData = detectors.map(d => [d.lat, d.lon, d.traffic / 100]);

    // Add heat map layer with dynamic gradient
    const heat = (L as any).heatLayer(heatData, {
      radius: 25,
      blur: 35,
      maxZoom: 18,
      max: 1.0,
      gradient: {
        0.0: 'blue',
        0.25: 'cyan',
        0.5: 'yellow',
        0.75: 'orange',
        1.0: 'red'
      }
    }).addTo(map);

    return () => {
      if (map.hasLayer(heat)) {
        map.removeLayer(heat);
      }
    };
  }, [map, detectors]);

  return null;
};

// Marker cluster component
const MarkerClusterGroup = ({ detectors, getMarkerColor }: { detectors: TrafficDetector[], getMarkerColor: (category: string) => string }) => {
  const map = useMap();
  const clusterGroupRef = useRef<any>(null);

  useEffect(() => {
    if (!map) return;

    // Remove existing cluster group
    if (clusterGroupRef.current) {
      map.removeLayer(clusterGroupRef.current);
    }

    // Create new marker cluster group
    const markers = (L as any).markerClusterGroup({
      maxClusterRadius: 80,
      spiderfyOnMaxZoom: true,
      showCoverageOnHover: false,
      zoomToBoundsOnClick: true,
      iconCreateFunction: function(cluster: any) {
        const childCount = cluster.getChildCount();
        let c = ' marker-cluster-';
        if (childCount < 10) {
          c += 'small';
        } else if (childCount < 50) {
          c += 'medium';
        } else {
          c += 'large';
        }
        
        return L.divIcon({
          html: '<div><span>' + childCount + '</span></div>',
          className: 'marker-cluster' + c,
          iconSize: L.point(40, 40)
        });
      }
    });

    // Add markers to cluster group
    detectors.forEach((detector) => {
      const color = getMarkerColor(detector.category);
      
      const marker = L.circleMarker([detector.lat, detector.lon], {
        radius: 6,
        fillColor: color,
        color: color,
        weight: 2,
        opacity: 0.8,
        fillOpacity: 0.7,
      });

      const popupContent = `
        <div class="detector-popup">
          <h4>Detector ${detector.detid}</h4>
          <div class="popup-row">
            <span>Traffic:</span>
            <strong>${detector.traffic.toFixed(1)}</strong>
          </div>
          <div class="popup-row">
            <span>Category:</span>
            <strong style="color: ${color}">${detector.category.toUpperCase()}</strong>
          </div>
          ${detector.road ? `
          <div class="popup-row">
            <span>Road:</span>
            <span>${detector.road}</span>
          </div>
          ` : ''}
          <div class="popup-row">
            <span>Location:</span>
            <span>${detector.lat.toFixed(4)}, ${detector.lon.toFixed(4)}</span>
          </div>
        </div>
      `;

      marker.bindPopup(popupContent);
      markers.addLayer(marker);
    });

    map.addLayer(markers);
    clusterGroupRef.current = markers;

    return () => {
      if (clusterGroupRef.current && map.hasLayer(clusterGroupRef.current)) {
        map.removeLayer(clusterGroupRef.current);
      }
    };
  }, [map, detectors, getMarkerColor]);

  return null;
};

const TrafficView: React.FC<TrafficViewProps> = ({ selectedModel }) => {
  const [detectors, setDetectors] = useState<TrafficDetector[]>([]);
  const [statistics, setStatistics] = useState<TrafficStatistics | null>(null);
  const [currentTime, setCurrentTime] = useState<string>('09:00:00');
  const [timeInterval, setTimeInterval] = useState<number>(18); // 09:00 in 30-min intervals
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isStatsMinimized, setIsStatsMinimized] = useState(false);

  // Center of Taipei
  const center: LatLngTuple = [25.0330, 121.5654];

  // Load traffic data
  const loadTrafficData = async (time: string) => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `https://taipeisim-be.ruangopini.app/api/v1/detectors/traffic?model=${selectedModel}&time=${time}`
      );

      if (!response.ok) {
        throw new Error('Failed to load traffic data');
      }

      const data = await response.json();
      setDetectors(data.detectors);
      setStatistics(data.statistics);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Traffic data load error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Load initial data
  useEffect(() => {
    loadTrafficData(currentTime);
  }, [selectedModel]);

  // Convert interval (0-47) to time string
  const intervalToTime = (interval: number): string => {
    const totalMinutes = interval * 30; // 30-minute intervals
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:00`;
  };

  // Format time for display
  const formatTime = (time: string): string => {
    const [hours, minutes] = time.split(':');
    return `${hours}:${minutes}`;
  };

  // Handle time slider change
  const handleTimeChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const interval = parseInt(event.target.value);
    setTimeInterval(interval);
    const newTime = intervalToTime(interval);
    setCurrentTime(newTime);
    loadTrafficData(newTime);
  };

  // Get marker color based on traffic category
  const getMarkerColor = (category: string): string => {
    switch (category) {
      case 'low':
        return '#22c55e'; // green
      case 'moderate':
        return '#facc15'; // yellow
      case 'high':
        return '#f97316'; // orange
      case 'severe':
        return '#dc2626'; // red
      default:
        return '#6b7280'; // gray
    }
  };

  return (
    <div className="traffic-view">
      {/* Statistics Panel */}
      <div className={`statistics-panel ${isStatsMinimized ? 'minimized' : ''}`}>
        <div className="statistics-header">
          <h3>Traffic Statistics</h3>
          <button 
            className="minimize-btn" 
            onClick={() => setIsStatsMinimized(!isStatsMinimized)}
            title={isStatsMinimized ? 'Expand' : 'Minimize'}
          >
            {isStatsMinimized ? '▼' : '▲'}
          </button>
        </div>
        {statistics && (
          <div className="stats-content">
            <div className="stat-item">
              <span className="stat-label">Total Detectors:</span>
              <span className="stat-value">{statistics.total_detectors}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Average Traffic:</span>
              <span className="stat-value">{statistics.avg_traffic.toFixed(1)}</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">Range:</span>
              <span className="stat-value">
                {statistics.min_traffic.toFixed(0)} - {statistics.max_traffic.toFixed(0)}
              </span>
            </div>
            <div className="stat-divider"></div>
            <div className="stat-item">
              <span className="stat-dot low"></span>
              <span className="stat-label">Low:</span>
              <span className="stat-value">{statistics.low_count}</span>
            </div>
            <div className="stat-item">
              <span className="stat-dot moderate"></span>
              <span className="stat-label">Moderate:</span>
              <span className="stat-value">{statistics.moderate_count}</span>
            </div>
            <div className="stat-item">
              <span className="stat-dot high"></span>
              <span className="stat-label">High:</span>
              <span className="stat-value">{statistics.high_count}</span>
            </div>
            <div className="stat-item">
              <span className="stat-dot severe"></span>
              <span className="stat-label">Severe:</span>
              <span className="stat-value">{statistics.severe_count}</span>
            </div>
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="traffic-legend">
        <h4>Traffic Levels</h4>
        <div className="legend-items">
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#22c55e' }}></span>
            <span>Low (&lt; 25)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#facc15' }}></span>
            <span>Moderate (25-50)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#f97316' }}></span>
            <span>High (50-100)</span>
          </div>
          <div className="legend-item">
            <span className="legend-color" style={{ backgroundColor: '#dc2626' }}></span>
            <span>Severe (≥ 100)</span>
          </div>
        </div>
      </div>

      {/* Map */}
      <MapContainer
        center={center}
        zoom={12}
        className="traffic-map"
      >
        <LayersControl position="topright">
          {/* Base Layers */}
          <LayersControl.BaseLayer name="Light Map (CartoDB Positron)">
            <TileLayer
              attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
              url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
            />
          </LayersControl.BaseLayer>
          
          <LayersControl.BaseLayer name="OpenStreetMap">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          </LayersControl.BaseLayer>
          
          <LayersControl.BaseLayer checked name="Dark Map (CartoDB Dark Matter)">
            <TileLayer
              attribution='&copy; <a href="https://carto.com/">CartoDB</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
          </LayersControl.BaseLayer>
        </LayersControl>

        {/* Marker Clusters and Heatmap */}
        <MarkerClusterGroup detectors={detectors} getMarkerColor={getMarkerColor} />
        <HeatmapLayer detectors={detectors} />
      </MapContainer>

      {/* Time Slider */}
      <div className="time-slider-container">
        <div className="time-slider-header">
          <span className="time-label">Time:</span>
          <span className="time-display">{formatTime(currentTime)}</span>
        </div>
        <input
          type="range"
          min="0"
          max="47"
          value={timeInterval}
          onChange={handleTimeChange}
          className="time-slider"
          disabled={isLoading}
        />
        <div className="time-markers">
          <span>00:00</span>
          <span>06:00</span>
          <span>12:00</span>
          <span>18:00</span>
          <span>23:59</span>
        </div>
      </div>

      {/* Loading overlay */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Loading traffic data...</p>
        </div>
      )}

      {/* Error message */}
      {error && (
        <div className="error-message">
          {error}
        </div>
      )}
    </div>
  );
};

export default TrafficView;
