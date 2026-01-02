import React, { useState } from 'react';
import { Location, RouteResponse } from '../types';
import './ControlPanel.css';

interface ModelOption {
  id: string;
  name: string;
  description: string;
}

const MODEL_OPTIONS: ModelOption[] = [
  {
    id: 'linear_regression',
    name: 'Linear Regression',
    description: 'Linear Regression - A statistical model that predicts traffic based on linear relationships between features. Fast and interpretable, works well for straightforward traffic patterns.'
  },
  {
    id: 'xgboost',
    name: 'XGBoost',
    description: 'Extreme Gradient Boosting - A powerful ensemble learning method that builds sequential decision trees. Excels at handling non-linear patterns and feature interactions in traffic data.'
  },
  {
    id: 'catboost',
    name: 'CatBoost',
    description: 'Categorical Boosting - An advanced gradient boosting algorithm optimized for categorical features. Handles complex traffic patterns with high accuracy.'
  },
  {
    id: 'lightgbm',
    name: 'LightGBM',
    description: 'Light Gradient Boosting Machine - A fast gradient boosting framework using tree-based learning. Efficient for large-scale traffic prediction.'
  },
  {
    id: 'random_forest',
    name: 'Random Forest',
    description: 'Random Forest - An ensemble method using multiple decision trees. Provides robust predictions and handles outliers well in traffic patterns.'
  },
  {
    id: 'lasso',
    name: 'Lasso Regression',
    description: 'Lasso Regression - Linear model with L1 regularization for feature selection. Good for identifying key traffic factors.'
  },
  {
    id: 'ridge',
    name: 'Ridge Regression',
    description: 'Ridge Regression - Linear model with L2 regularization to prevent overfitting. Stable predictions for traffic data.'
  },
  {
    id: 'elasticnet',
    name: 'ElasticNet',
    description: 'ElasticNet - Combines Lasso and Ridge regularization. Balanced approach for traffic prediction with many features.'
  },
  {
    id: 'gcn_gru',
    name: 'GCN-GRU',
    description: 'Graph Convolutional Network + Gated Recurrent Unit - Deep learning model that captures spatial dependencies through graph structure and temporal patterns with GRU. Advanced neural network for traffic forecasting.'
  },
  {
    id: 'gcn_lstm',
    name: 'GCN-LSTM',
    description: 'Graph Convolutional Network + Long Short-Term Memory - Combines graph-based spatial learning with LSTM temporal modeling. State-of-the-art neural architecture for complex traffic prediction.'
  }
];

interface ControlPanelProps {
  viewMode: '3d' | '2d';
  appMode: 'route' | 'traffic';
  startLocation: Location | null;
  endLocation: Location | null;
  departureTime: string;
  selectedModel: string;
  routeData: RouteResponse | null;
  isLoading: boolean;
  error: string | null;
  showDetectors: boolean;
  onAppModeChange: (mode: 'route' | 'traffic') => void;
  onDepartureTimeChange: (time: string) => void;
  onModelChange: (model: string) => void;
  onCalculateRoute: () => void;
  onReset: () => void;
  onLocationSelect: (location: Location, type: 'start' | 'end') => void;
  onToggleDetectors: (show: boolean) => void;
}

const ControlPanel: React.FC<ControlPanelProps> = ({ viewMode, appMode, startLocation, endLocation, departureTime, selectedModel, routeData, isLoading, error, showDetectors, onAppModeChange, onDepartureTimeChange, onModelChange, onCalculateRoute, onReset, onLocationSelect, onToggleDetectors }) => {
  const [startInput, setStartInput] = useState('');
  const [endInput, setEndInput] = useState('');
  const [startSuggestions, setStartSuggestions] = useState<any[]>([]);
  const [endSuggestions, setEndSuggestions] = useState<any[]>([]);
  const [showStartSuggestions, setShowStartSuggestions] = useState(false);
  const [showEndSuggestions, setShowEndSuggestions] = useState(false);
  const [isPanelMinimized, setIsPanelMinimized] = useState(false);
  const [isSearchingStart, setIsSearchingStart] = useState(false);
  const [isSearchingEnd, setIsSearchingEnd] = useState(false);
  const [startInputFocused, setStartInputFocused] = useState(false);
  const [endInputFocused, setEndInputFocused] = useState(false);
  const [hoveredModel, setHoveredModel] = useState<string | null>(null);
  const [isModelDropdownOpen, setIsModelDropdownOpen] = useState(false);
  const [showModelInfo, setShowModelInfo] = useState(false);
  const searchTimeoutRef = React.useRef<number>();
  const modelDropdownRef = React.useRef<HTMLDivElement>(null);
  const modelInfoRef = React.useRef<HTMLDivElement>(null);

  // Update input when location is selected from map/globe
  React.useEffect(() => {
    if (startLocation) {
      const locationText = startLocation.name || `${startLocation.lat.toFixed(4)}, ${startLocation.lng.toFixed(4)}`;
      if (startInput !== locationText) {
        setStartInput(locationText);
      }
    }
  }, [startLocation]);

  React.useEffect(() => {
    if (endLocation) {
      const locationText = endLocation.name || `${endLocation.lat.toFixed(4)}, ${endLocation.lng.toFixed(4)}`;
      if (endInput !== locationText) {
        setEndInput(locationText);
      }
    }
  }, [endLocation]);

  const searchLocation = async (query: string, type: 'start' | 'end') => {
    console.log(`searchLocation called - type: ${type}, query: "${query}", length: ${query.length}`);
    
    if (query.length < 2) {
      if (type === 'start') {
        setStartSuggestions([]);
        setShowStartSuggestions(false);
        setIsSearchingStart(false);
      } else {
        setEndSuggestions([]);
        setShowEndSuggestions(false);
        setIsSearchingEnd(false);
      }
      return;
    }

    if (type === 'start') {
      setIsSearchingStart(true);
    } else {
      setIsSearchingEnd(true);
    }

    try {
      // Try multiple search strategies for better results
      let data: any[] = [];
      
      // Strategy 1: Search with Taipei context
      const searchQuery = query.includes('taipei') || query.includes('Taipei') 
        ? query 
        : `${query}, Taipei`;
      
      const url1 = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchQuery)}&countrycodes=tw&limit=10&addressdetails=1`;
      console.log('Fetching strategy 1:', url1);
      
      const response1 = await fetch(url1);
      if (response1.ok) {
        data = await response1.json();
        console.log(`Strategy 1 results for "${query}":`, data.length, 'items');
      }
      
      // Strategy 2: If no results, try without Taipei context
      if (data.length === 0) {
        const url2 = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=tw&limit=10&addressdetails=1`;
        console.log('Fetching strategy 2:', url2);
        const response2 = await fetch(url2);
        if (response2.ok) {
          data = await response2.json();
          console.log(`Strategy 2 results for "${query}":`, data.length, 'items');
        }
      }

      // Filter and sort results to prioritize Taipei area
      const taipeiResults = data.filter((item: any) => 
        item.display_name.toLowerCase().includes('taipei') ||
        item.display_name.toLowerCase().includes('臺北') ||
        item.display_name.toLowerCase().includes('台北')
      );
      
      const otherResults = data.filter((item: any) => 
        !item.display_name.toLowerCase().includes('taipei') &&
        !item.display_name.toLowerCase().includes('臺北') &&
        !item.display_name.toLowerCase().includes('台北')
      );
      
      // Combine: Taipei results first, then others
      const sortedData = [...taipeiResults, ...otherResults].slice(0, 8);

      if (type === 'start') {
        setStartSuggestions(sortedData);
        console.log('Setting showStartSuggestions to true, data:', sortedData);
        setShowStartSuggestions(true);
        setIsSearchingStart(false);
      } else {
        setEndSuggestions(sortedData);
        console.log('Setting showEndSuggestions to true, data:', sortedData);
        setShowEndSuggestions(true);
        setIsSearchingEnd(false);
      }
    } catch (error) {
      console.error('Search error:', error);
      if (type === 'start') {
        setIsSearchingStart(false);
      } else {
        setIsSearchingEnd(false);
      }
    }
  };

  const handleInputChange = (value: string, type: 'start' | 'end') => {
    console.log(`handleInputChange - type: ${type}, value: "${value}"`);
    
    if (type === 'start') {
      setStartInput(value);
      if (value.length < 2) {
        setStartSuggestions([]);
        setShowStartSuggestions(false);
      }
    } else {
      setEndInput(value);
      if (value.length < 2) {
        setEndSuggestions([]);
        setShowEndSuggestions(false);
      }
    }

    // Debounce search
    if (searchTimeoutRef.current) {
      clearTimeout(searchTimeoutRef.current);
    }

    if (value.length < 2) {
      if (type === 'start') {
        setIsSearchingStart(false);
      } else {
        setIsSearchingEnd(false);
      }
      return;
    }

    if (type === 'start') {
      setIsSearchingStart(true);
    } else {
      setIsSearchingEnd(true);
    }
    
    searchTimeoutRef.current = window.setTimeout(() => {
      console.log(`Timeout fired - calling searchLocation for ${type}`);
      searchLocation(value, type);
    }, 800);
  };

  const handleSuggestionSelect = (suggestion: any, type: 'start' | 'end') => {
    const location: Location = {
      lat: parseFloat(suggestion.lat),
      lng: parseFloat(suggestion.lon),
      name: suggestion.display_name,
    };

    onLocationSelect(location, type);

    if (type === 'start') {
      setStartInput(suggestion.display_name);
      setShowStartSuggestions(false);
      setStartSuggestions([]);
    } else {
      setEndInput(suggestion.display_name);
      setShowEndSuggestions(false);
      setEndSuggestions([]);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent<HTMLInputElement>, type: 'start' | 'end') => {
    if (e.key === 'Enter') {
      const suggestions = type === 'start' ? startSuggestions : endSuggestions;
      if (suggestions.length > 0) {
        handleSuggestionSelect(suggestions[0], type);
      }
    }
  };

  const handleReset = () => {
    setStartInput('');
    setEndInput('');
    setStartSuggestions([]);
    setEndSuggestions([]);
    setShowStartSuggestions(false);
    setShowEndSuggestions(false);
    setHoveredModel(null);
    setIsModelDropdownOpen(false);
    onReset();
  };

  // Close dropdown when clicking outside
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (modelDropdownRef.current && !modelDropdownRef.current.contains(event.target as Node)) {
        setIsModelDropdownOpen(false);
        setHoveredModel(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const formatDateTime = (dateStr: string) => {
    return dateStr.replace('T', ' ');
  };

  return (
    <div className={`control-panel ${viewMode === '3d' ? 'globe-mode' : 'map-mode'} ${isPanelMinimized ? 'minimized' : ''}`}>
      <div className="panel-header">
        <button 
          className="panel-minimize-btn" 
          onClick={() => setIsPanelMinimized(!isPanelMinimized)}
          title={isPanelMinimized ? 'Expand Panel' : 'Minimize Panel'}
        >
          {isPanelMinimized ? '◀' : '▶'}
        </button>
        <div className="logo-title">
          <img src="/logo.svg" alt="TaipeiSim Logo" className="app-logo" />
          <div>
            <h2>TaipeiSim</h2>
            <p className="chinese-subtitle">机北天练线</p>
          </div>
        </div>
        <div className="header-bottom">
          <p className="subtitle">Historical Traffic Router</p>
          <div className="detector-toggle">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={showDetectors}
                onChange={(e) => onToggleDetectors(e.target.checked)}
                className="toggle-checkbox"
              />
              <span className="toggle-slider"></span>
              <span className="toggle-text">Detectors</span>
            </label>
          </div>
        </div>
      </div>

      <div className="panel-content">
        {/* Mode Selector */}
        <div className="section mode-selector-section">
          <h3>🎯 Mode</h3>
          <div className="mode-selector">
            <button
              className={`mode-btn ${appMode === 'route' ? 'active' : ''}`}
              onClick={() => onAppModeChange('route')}
            >
              <span className="mode-icon">🚗</span>
              <span className="mode-label">Find Route</span>
            </button>
            <button
              className={`mode-btn ${appMode === 'traffic' ? 'active' : ''}`}
              onClick={() => onAppModeChange('traffic')}
            >
              <span className="mode-icon">📊</span>
              <span className="mode-label">View Traffic</span>
            </button>
          </div>
        </div>

        {/* Location Selection - Only show in route mode */}
        {appMode === 'route' && (
        <div className="section">
          <h3>📍 Locations</h3>
          {viewMode === '2d' && (
            <p className="map-hint">💡 Click map to set destination (Shift+Click for start)</p>
          )}

          <div className="location-input">
            <label>Start Location</label>
            <div className="autocomplete-wrapper">
              <input
                type="text"
                className="location-text-input"
                placeholder="Type location name or address..."
                value={startInput}
                onChange={(e) => handleInputChange(e.target.value, 'start')}
                onKeyPress={(e) => handleKeyPress(e, 'start')}
                onFocus={() => {
                  setStartInputFocused(true);
                  console.log('Start input focused, suggestions:', startSuggestions.length);
                  if (startInput.length >= 2 && startSuggestions.length > 0) {
                    setShowStartSuggestions(true);
                  }
                }}
                onBlur={() => {
                  setStartInputFocused(false);
                  setTimeout(() => {
                    console.log('Start input blurred, hiding suggestions');
                    setShowStartSuggestions(false);
                  }, 500);
                }}
              />
              {isSearchingStart && <div className="search-loading">Searching...</div>}
              {showStartSuggestions && startSuggestions.length > 0 && (
                <div className="suggestions-dropdown" onMouseDown={(e) => e.preventDefault()}>
                  {startSuggestions.map((suggestion, index) => (
                    <div key={index} className="suggestion-item" onMouseDown={(e) => {
                      e.preventDefault();
                      handleSuggestionSelect(suggestion, 'start');
                    }}>
                      <div className="suggestion-name">{suggestion.name || suggestion.display_name.split(',')[0]}</div>
                      <div className="suggestion-address">{suggestion.display_name}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div className="location-input">
            <label>Destination</label>
            <div className="autocomplete-wrapper">
              <input
                type="text"
                className="location-text-input"
                placeholder="Type location name or address..."
                value={endInput}
                onChange={(e) => handleInputChange(e.target.value, 'end')}
                onKeyPress={(e) => handleKeyPress(e, 'end')}
                onFocus={() => {
                  setEndInputFocused(true);
                  console.log('End input focused, suggestions:', endSuggestions.length);
                  if (endInput.length >= 2 && endSuggestions.length > 0) {
                    setShowEndSuggestions(true);
                  }
                }}
                onBlur={() => {
                  setEndInputFocused(false);
                  setTimeout(() => {
                    console.log('End input blurred, hiding suggestions');
                    setShowEndSuggestions(false);
                  }, 500);
                }}
              />
              {isSearchingEnd && <div className="search-loading">Searching...</div>}
              {showEndSuggestions && endSuggestions.length > 0 && (
                <div className="suggestions-dropdown" onMouseDown={(e) => e.preventDefault()}>
                  {endSuggestions.map((suggestion, index) => (
                    <div key={index} className="suggestion-item" onMouseDown={(e) => {
                      e.preventDefault();
                      handleSuggestionSelect(suggestion, 'end');
                    }}>
                      <div className="suggestion-name">{suggestion.name || suggestion.display_name.split(',')[0]}</div>
                      <div className="suggestion-address">{suggestion.display_name}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
        )}

        {/* Time Selection - Show for both modes */}
        <div className="section">
          <h3>🕐 {appMode === 'route' ? 'Departure Time' : 'View Time'}</h3>
          <div className="time-input">
            <input 
              type="time" 
              value={departureTime} 
              onChange={(e) => onDepartureTimeChange(e.target.value)} 
              onClick={(e) => {
                const target = e.target as HTMLInputElement;
                if (target.showPicker) {
                  target.showPicker();
                }
              }}
              title={appMode === 'route' ? 'Select departure time' : 'Select traffic view time'} 
            />
            <p className="time-note">Date fixed: September 19, 2017</p>
          </div>
        </div>

        {/* Model Selection */}
        <div className="section">
          <h3>🤖 Prediction Model</h3>
          <div className="model-select-container" ref={modelDropdownRef}>
            <div className="model-select-wrapper">
              <div 
                className={`custom-select ${isModelDropdownOpen ? 'open' : ''}`}
                onClick={() => setIsModelDropdownOpen(!isModelDropdownOpen)}
              >
                <div className="select-selected">
                  {MODEL_OPTIONS.find(m => m.id === selectedModel)?.name}
                </div>
                <div className={`select-arrow ${isModelDropdownOpen ? 'open' : ''}`}>▼</div>
              </div>
              <div 
                className="model-info-icon"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowModelInfo(!showModelInfo);
                }}
                title="Click to see model description"
              >
                ℹ️
              </div>
            </div>
            
            {/* Custom dropdown options */}
            {isModelDropdownOpen && (
              <div className="select-options">
                {MODEL_OPTIONS.map((model) => (
                  <div
                    key={model.id}
                    className={`select-option ${selectedModel === model.id ? 'selected' : ''}`}
                    onClick={() => {
                      onModelChange(model.id);
                      setIsModelDropdownOpen(false);
                      setHoveredModel(null);
                    }}
                  >
                    <span>{model.name}</span>
                    {selectedModel === model.id && <span className="check-mark">✓</span>}
                  </div>
                ))}
              </div>
            )}
            
            {/* Model info popup - shown when clicking info icon */}
            {showModelInfo && (
              <div className="model-info-overlay" onClick={() => setShowModelInfo(false)}>
                <div className="model-tooltip-popup" ref={modelInfoRef} onClick={(e) => e.stopPropagation()}>
                  <button 
                    className="popup-close-btn"
                    onClick={() => setShowModelInfo(false)}
                    title="Close"
                  >
                    ×
                  </button>
                  <div className="tooltip-header">
                    <strong>{MODEL_OPTIONS.find(m => m.id === selectedModel)?.name}</strong>
                    <span className="selected-indicator">Selected</span>
                  </div>
                  <p className="tooltip-description">
                    {MODEL_OPTIONS.find(m => m.id === selectedModel)?.description}
                  </p>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Calculate Button - Only in route mode */}
        {appMode === 'route' && (
        <div className="section">
          <button className="calculate-btn" onClick={onCalculateRoute} disabled={!startLocation || !endLocation || isLoading}>
            {isLoading ? (
              <>
                <span className="spinner"></span>
                Calculating...
              </>
            ) : (
              'Calculate Route'
            )}
          </button>
        </div>
        )}

        {/* Error Display */}
        {error && (
          <div className="error-box">
            <span className="error-icon">⚠️</span>
            {error}
          </div>
        )}

        {/* Route Results - Only in route mode */}
        {appMode === 'route' && routeData && (
          <div className="section results-section">
            <h3>Route Comparison</h3>
            
            {/* Shortest Path Stats */}
            <div className="route-stats-block">
              <h4 style={{ color: '#22c55e', marginBottom: '8px' }}>📏 Shortest Path</h4>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-label">Distance</span>
                  <span className="stat-value">{((routeData.shortest_path?.distance_meters || 0) / 1000).toFixed(2)} km</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Traffic Detectors</span>
                  <span className="stat-value">{routeData.shortest_path?.path?.length || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Severe Traffic</span>
                  <span className="stat-value" style={{ color: (routeData.shortest_path?.traffic_categories?.severe || 0) > 0 ? '#ef4444' : '#22c55e' }}>
                    {routeData.shortest_path?.traffic_categories?.severe || 0}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">High Traffic</span>
                  <span className="stat-value" style={{ color: (routeData.shortest_path?.traffic_categories?.high || 0) > 0 ? '#f97316' : '#22c55e' }}>
                    {routeData.shortest_path?.traffic_categories?.high || 0}
                  </span>
                </div>
              </div>
            </div>

            {/* Fastest Path Stats */}
            <div className="route-stats-block" style={{ marginTop: '16px' }}>
              <h4 style={{ color: '#3b82f6', marginBottom: '8px' }}>⚡ Fastest Path (Optimized)</h4>
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-label">Distance</span>
                  <span className="stat-value">{((routeData.fastest_path?.distance_meters || 0) / 1000).toFixed(2)} km</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Traffic Detectors</span>
                  <span className="stat-value">{routeData.fastest_path?.path?.length || 0}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Severe Traffic</span>
                  <span className="stat-value" style={{ color: (routeData.fastest_path?.traffic_categories?.severe || 0) > 0 ? '#ef4444' : '#22c55e' }}>
                    {routeData.fastest_path?.traffic_categories?.severe || 0}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">High Traffic</span>
                  <span className="stat-value" style={{ color: (routeData.fastest_path?.traffic_categories?.high || 0) > 0 ? '#f97316' : '#22c55e' }}>
                    {routeData.fastest_path?.traffic_categories?.high || 0}
                  </span>
                </div>
              </div>
            </div>

            {/* Total Detectors */}
            <div className="stat-item" style={{ marginTop: '16px', paddingTop: '16px', borderTop: '1px solid rgba(212, 197, 160, 0.2)' }}>
              <span className="stat-label">Total Detectors Monitored</span>
              <span className="stat-value">{routeData.all_detectors?.length || 0}</span>
            </div>
          </div>
        )}

        {/* Reset Button */}
        {(startLocation || endLocation) && (
          <div className="section">
            <button className="reset-btn" onClick={handleReset}>
              Reset & Return to Globe
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default ControlPanel;
