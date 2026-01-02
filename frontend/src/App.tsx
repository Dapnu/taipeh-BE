import React, { useState } from 'react';
import GlobeView from './components/GlobeView';
import MapView from './components/MapView';
import TrafficView from './components/TrafficView';
import ControlPanel from './components/ControlPanel';
import { Location, RouteResponse } from './types';
import './App.css';

type ViewMode = '3d' | '2d';
type AppMode = 'route' | 'traffic';

function App() {
  const [viewMode, setViewMode] = useState<ViewMode>('3d');
  const [appMode, setAppMode] = useState<AppMode>('route');
  const [startLocation, setStartLocation] = useState<Location | null>(null);
  const [endLocation, setEndLocation] = useState<Location | null>(null);
  const [departureTime, setDepartureTime] = useState<string>('09:00:00');
  const [selectedModel, setSelectedModel] = useState<string>('linear_regression');
  const [showDetectors, setShowDetectors] = useState<boolean>(false);
  const [routeData, setRouteData] = useState<RouteResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAppModeChange = (mode: AppMode) => {
    setAppMode(mode);
    // Switch to 2D view when entering traffic mode
    if (mode === 'traffic') {
      setViewMode('2d');
    }
    // Clear errors when switching modes
    setError(null);
  };

  const handleLocationSelect = (location: Location, type: 'start' | 'end') => {
    if (type === 'start') {
      setStartLocation(location);
      // Transition to 2D view when start location is filled
      if (viewMode === '3d') {
        setTimeout(() => {
          setViewMode('2d');
        }, 300);
      }
    } else {
      setEndLocation(location);
    }
  };

  const handleCalculateRoute = async () => {
    if (!startLocation || !endLocation) {
      setError('Please select both start and end locations');
      return;
    }

    setIsLoading(true);
    setError(null);
    setRouteData(null);

    try {
      // Call our backend API
      const response = await fetch('https://taipeisim-be.ruangopini.app/api/v1/routes/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          start_lat: startLocation.lat,
          start_lon: startLocation.lng,
          end_lat: endLocation.lat,
          end_lon: endLocation.lng,
          model: selectedModel,
          departure_time: departureTime,
        }),
      });

      if (!response.ok) {
        let errorMessage = 'Failed to calculate route';
        try {
          const errorData = await response.json();
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = `Server error: ${response.status} ${response.statusText}`;
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      setRouteData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
      console.error('Route calculation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReset = () => {
    setStartLocation(null);
    setEndLocation(null);
    setRouteData(null);
    setError(null);
    setViewMode('3d');
  };

  return (
    <div className="app">
      {viewMode === '3d' ? (
        <GlobeView onLocationSelect={(loc) => handleLocationSelect(loc, 'start')} />
      ) : appMode === 'route' ? (
        <MapView startLocation={startLocation} endLocation={endLocation} routeData={routeData} showDetectors={showDetectors} onLocationSelect={handleLocationSelect} />
      ) : (
        <TrafficView selectedModel={selectedModel} />
      )}

      <ControlPanel
        viewMode={viewMode}
        appMode={appMode}
        startLocation={startLocation}
        endLocation={endLocation}
        departureTime={departureTime}
        selectedModel={selectedModel}
        showDetectors={showDetectors}
        routeData={routeData}
        isLoading={isLoading}
        error={error}
        onAppModeChange={handleAppModeChange}
        onDepartureTimeChange={setDepartureTime}
        onModelChange={setSelectedModel}
        onToggleDetectors={setShowDetectors}
        onCalculateRoute={handleCalculateRoute}
        onReset={handleReset}
        onLocationSelect={handleLocationSelect}
      />
    </div>
  );
}

export default App;
