import React, { useState, useEffect } from 'react';
import { Location, SearchResult } from '../types';
import './LocationSearch.css';

interface LocationSearchProps {
  onSelect: (location: Location) => void;
  onClose: () => void;
  searchType: 'start' | 'end';
}

const LocationSearch: React.FC<LocationSearchProps> = ({ onSelect, onClose, searchType }) => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      if (query.length > 2) {
        searchLocation();
      } else {
        setResults([]);
      }
    }, 500);

    return () => clearTimeout(timeoutId);
  }, [query]);

  const searchLocation = async () => {
    setIsSearching(true);
    setError(null);

    try {
      // Add Taipei as context for better results
      const searchQuery = query.includes('Taipei') ? query : `${query}, Taipei, Taiwan`;

      const response = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(searchQuery)}&format=json&limit=5`);

      if (!response.ok) {
        throw new Error('Search failed');
      }

      const data: SearchResult[] = await response.json();

      // Filter results to be near Taipei (rough bounding box)
      const taipeiResults = data.filter((result) => {
        const lat = parseFloat(result.lat);
        const lon = parseFloat(result.lon);
        return lat >= 24.95 && lat <= 25.15 && lon >= 121.45 && lon <= 121.65;
      });

      setResults(taipeiResults);

      if (taipeiResults.length === 0 && data.length > 0) {
        // If no results in Taipei area, show all results
        setResults(data);
      }
    } catch (err) {
      setError('Failed to search locations. Please try again.');
      console.error('Search error:', err);
    } finally {
      setIsSearching(false);
    }
  };

  const handleSelect = (result: SearchResult) => {
    onSelect({
      lat: parseFloat(result.lat),
      lng: parseFloat(result.lon),
      name: result.display_name,
    });
  };

  const handleOverlayClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  return (
    <div className="search-overlay" onClick={handleOverlayClick}>
      <div className="search-modal">
        <div className="search-header">
          <h3>Search {searchType === 'start' ? 'Start' : 'Destination'} Location</h3>
          <button className="close-btn" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="search-body">
          <div className="search-input-container">
            <input type="text" className="search-input" placeholder="Enter location name or address..." value={query} onChange={(e) => setQuery(e.target.value)} autoFocus />
            {isSearching && <span className="search-spinner">🔄</span>}
          </div>

          {error && <div className="search-error">{error}</div>}

          <div className="search-results">
            {results.length > 0 ? (
              results.map((result, index) => (
                <div key={index} className="result-item" onClick={() => handleSelect(result)}>
                  <div className="result-name">{result.display_name.split(',')[0]}</div>
                  <div className="result-address">{result.display_name}</div>
                </div>
              ))
            ) : query.length > 2 && !isSearching ? (
              <div className="no-results">No locations found. Try a different search term.</div>
            ) : query.length <= 2 ? (
              <div className="search-hint">Type at least 3 characters to search for locations in Taipei.</div>
            ) : null}
          </div>

          <div className="search-footer">
            <p>Examples: "Taipei 101", "National Taiwan University", "Shilin Night Market"</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LocationSearch;
