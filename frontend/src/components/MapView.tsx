import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, Popup, useMap, Circle } from 'react-leaflet';
import L from 'leaflet';
import { Location, RouteResponse } from '../types';
import './MapView.css';

// Fix Leaflet default marker icon issue
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

// Create custom icons for start and end markers
const startIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

const endIcon = new L.Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

interface MapViewProps {
  startLocation: Location | null;
  endLocation: Location | null;
  routeData: RouteResponse | null;
  showDetectors: boolean;
  onLocationSelect: (location: Location, type: 'start' | 'end') => void;
}

// Component to handle map events
function MapEvents({ onLocationSelect, startLocation, endLocation }: {
  onLocationSelect: (location: Location, type: 'start' | 'end') => void;
  startLocation: Location | null;
  endLocation: Location | null;
}) {
  const map = useMap();

  useEffect(() => {
    const handleClick = (e: L.LeafletMouseEvent) => {
      // Default to 'end' (like Google Maps), but use 'start' if Shift key is held or if start is empty
      const type = (e.originalEvent.shiftKey || !startLocation) ? 'start' : 'end';
      onLocationSelect({
        lat: e.latlng.lat,
        lng: e.latlng.lng,
        name: `Selected Point (${e.latlng.lat.toFixed(4)}, ${e.latlng.lng.toFixed(4)})`
      }, type);
    };

    map.on('click', handleClick);
    return () => {
      map.off('click', handleClick);
    };
  }, [map, onLocationSelect, startLocation, endLocation]);

  return null;
}

// Component to animate map view
function MapAnimator({ startLocation }: { startLocation: Location | null }) {
  const map = useMap();

  useEffect(() => {
    if (startLocation) {
      map.flyTo([startLocation.lat, startLocation.lng], 13, {
        duration: 1.5,
      });
    }
  }, [map, startLocation]);

  return null;
}

const MapView: React.FC<MapViewProps> = ({
  startLocation,
  endLocation,
  routeData,
  showDetectors,
  onLocationSelect,
}) => {
  const TAIPEI_CENTER: [number, number] = [25.0330, 121.5654];

  // Extract route coordinates for polyline - use fastest path by default
  // Backend returns polyline as [[lon, lat], ...], we need [lat, lon] for Leaflet
  const shortestRoute: [number, number][] = routeData?.shortest_path?.polyline
    ? routeData.shortest_path.polyline.map(coord => [coord[1], coord[0]]) // [lon, lat] -> [lat, lon]
    : routeData?.shortest_path?.geometry
    ? routeData.shortest_path.geometry.map(coord => [coord[1], coord[0]])
    : [];

  const fastestRoute: [number, number][] = routeData?.fastest_path?.polyline
    ? routeData.fastest_path.polyline.map(coord => [coord[1], coord[0]])
    : routeData?.fastest_path?.geometry
    ? routeData.fastest_path.geometry.map(coord => [coord[1], coord[0]])
    : [];

  // Get traffic level color
  const getTrafficColor = (level: string) => {
    switch (level) {
      case 'low': return '#22c55e'; // green
      case 'moderate': return '#eab308'; // yellow
      case 'high': return '#f97316'; // orange
      case 'severe': return '#ef4444'; // red
      default: return '#9ca3af'; // gray
    }
  };

  return (
    <div className="map-container fade-in">
      <MapContainer
        center={TAIPEI_CENTER}
        zoom={12}
        style={{ height: '100%', width: '100%' }}
        zoomControl={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          maxZoom={20}
        />
        
        <MapEvents
          onLocationSelect={onLocationSelect}
          startLocation={startLocation}
          endLocation={endLocation}
        />
        
        <MapAnimator startLocation={startLocation} />
        
        {/* Start and End Markers */}
        {startLocation && (
          <Marker position={[startLocation.lat, startLocation.lng]} icon={startIcon}>
            <Popup>
              <strong>Start Location</strong>
              <br />
              {startLocation.name || `${startLocation.lat.toFixed(4)}, ${startLocation.lng.toFixed(4)}`}
            </Popup>
          </Marker>
        )}
        
        {endLocation && (
          <Marker position={[endLocation.lat, endLocation.lng]} icon={endIcon}>
            <Popup>
              <strong>Destination</strong>
              <br />
              {endLocation.name || `${endLocation.lat.toFixed(4)}, ${endLocation.lng.toFixed(4)}`}
            </Popup>
          </Marker>
        )}
        
        {/* Fastest Path (Blue) - Render first (bottom layer) */}
        {fastestRoute.length > 0 && (
          <Polyline
            positions={fastestRoute}
            color="#3b82f6"
            weight={6}
            opacity={0.85}
          >
            <Popup>
              <strong>⚡ Fastest Path (Traffic-Optimized)</strong>
              <br />
              Distance: {((routeData?.fastest_path?.distance_meters || 0) / 1000).toFixed(2)} km
              <br />
              Detectors: {routeData?.fastest_path?.path?.length || 0}
              <br />
              High Traffic: {routeData?.fastest_path?.traffic_categories?.high || 0}
              <br />
              Severe Traffic: {routeData?.fastest_path?.traffic_categories?.severe || 0}
            </Popup>
          </Polyline>
        )}
        
        {/* Shortest Path (Green) - Render second (top layer) */}
        {shortestRoute.length > 0 && (
          <Polyline
            positions={shortestRoute}
            color="#22c55e"
            weight={4}
            opacity={0.75}
            dashArray="8, 12"
            dashOffset="0"
          >
            <Popup>
              <strong>📏 Shortest Path</strong>
              <br />
              Distance: {((routeData?.shortest_path?.distance_meters || 0) / 1000).toFixed(2)} km
              <br />
              Detectors: {routeData?.shortest_path?.path?.length || 0}
              <br />
              High Traffic: {routeData?.shortest_path?.traffic_categories?.high || 0}
              <br />
              Severe Traffic: {routeData?.shortest_path?.traffic_categories?.severe || 0}
            </Popup>
          </Polyline>
        )}
        
        {/* Traffic Detectors */}
        {showDetectors && routeData?.all_detectors && routeData.all_detectors.map((detector) => (
          <Circle
            key={detector.detector_id}
            center={[detector.lat, detector.lon]}
            radius={100}
            fillColor={getTrafficColor(detector.traffic_level)}
            fillOpacity={0.6}
            color={getTrafficColor(detector.traffic_level)}
            weight={2}
          >
            <Popup>
              <strong>Detector {detector.detector_id}</strong>
              <br />
              Traffic: {detector.traffic?.toFixed(2) || 'N/A'}
              <br />
              Level: <span style={{ 
                color: getTrafficColor(detector.traffic_level),
                fontWeight: 'bold',
                textTransform: 'uppercase'
              }}>
                {detector.traffic_level}
              </span>
            </Popup>
          </Circle>
        ))}
      </MapContainer>
      
      <div className="map-legend">
        <div className="legend-item">
          <span className="legend-dot start"></span>
          <span>Start</span>
        </div>
        <div className="legend-item">
          <span className="legend-dot end"></span>
          <span>Destination</span>
        </div>
        {routeData && (
          <>
            <div className="legend-title" style={{ marginTop: '10px' }}>Routes:</div>
            <div className="legend-item">
              <span className="legend-line" style={{ 
                backgroundColor: '#22c55e', 
                height: '3px', 
                width: '30px',
                backgroundImage: 'repeating-linear-gradient(90deg, #22c55e 0px, #22c55e 8px, transparent 8px, transparent 20px)'
              }}></span>
              <span>📏 Shortest (by distance)</span>
            </div>
            <div className="legend-item">
              <span className="legend-line" style={{ backgroundColor: '#3b82f6', height: '4px', width: '30px' }}></span>
              <span>⚡ Fastest (avoids traffic)</span>
            </div>
          </>
        )}
        {showDetectors && routeData && (
          <>
            <div className="legend-title">Traffic Levels:</div>
            <div className="legend-item">
              <span className="legend-circle" style={{ backgroundColor: '#22c55e' }}></span>
              <span>Low (&lt;25)</span>
            </div>
            <div className="legend-item">
              <span className="legend-circle" style={{ backgroundColor: '#eab308' }}></span>
              <span>Moderate (25-50)</span>
            </div>
            <div className="legend-item">
              <span className="legend-circle" style={{ backgroundColor: '#f97316' }}></span>
              <span>High (50-100)</span>
            </div>
            <div className="legend-item">
              <span className="legend-circle" style={{ backgroundColor: '#ef4444' }}></span>
              <span>Severe (≥100)</span>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default MapView;
