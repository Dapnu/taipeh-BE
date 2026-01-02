"""
Service for loading and querying pre-computed predictions from CSV files
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, time
import logging

logger = logging.getLogger(__name__)


class PredictionDataLoader:
    """Loads and manages pre-computed prediction data from CSV files"""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.predictions_cache: Dict[str, pd.DataFrame] = {}
        self.available_models: List[str] = []
        self.available_dates: List[str] = []
        
    def load_predictions(self, model_name: str, date: str) -> Optional[pd.DataFrame]:
        """
        Load predictions for a specific model and date
        
        Args:
            model_name: Name of the model (e.g., 'catboost', 'xgboost')
            date: Date in format 'oct1_2017' or 'YYYY-MM-DD'
        
        Returns:
            DataFrame with predictions or None if not found
        """
        cache_key = f"{model_name}_{date}"
        
        # Check cache first
        if cache_key in self.predictions_cache:
            logger.info(f"Returning cached predictions for {cache_key}")
            return self.predictions_cache[cache_key]
        
        # Try to find the file
        # Format: predictions_oct1_2017_catboost.csv
        date_formatted = date.replace("-", "_").lower()
        file_pattern = f"predictions_{date_formatted}_{model_name}.csv"
        file_path = self.data_dir / file_pattern
        
        if not file_path.exists():
            logger.warning(f"Prediction file not found: {file_path}")
            return None
        
        try:
            # Load CSV
            df = pd.read_csv(file_path)
            
            # Validate required columns
            required_cols = ['detid', 'date', 'interval', 'time', 'traffic_predict']
            if not all(col in df.columns for col in required_cols):
                logger.error(f"Missing required columns in {file_path}")
                return None
            
            # Convert date column to datetime
            df['date'] = pd.to_datetime(df['date'])
            
            # Cache the dataframe
            self.predictions_cache[cache_key] = df
            logger.info(f"Loaded predictions from {file_path}: {len(df)} records")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading predictions from {file_path}: {str(e)}")
            return None
    
    def get_prediction(
        self,
        detector_id: int,
        model_name: str,
        date: str,
        time_str: str
    ) -> Optional[Dict]:
        """
        Get prediction for specific detector, model, date, and time
        
        Args:
            detector_id: Detector ID
            model_name: Model name (e.g., 'catboost')
            date: Date string (e.g., 'oct1_2017' or '2017-10-01')
            time_str: Time string (e.g., '08:00:00' or '08:00')
        
        Returns:
            Dictionary with prediction data or None if not found
        """
        df = self.load_predictions(model_name, date)
        
        if df is None:
            return None
        
        # Query the dataframe
        result = df[
            (df['detid'] == detector_id) &
            (df['time'] == time_str)
        ]
        
        if result.empty:
            return None
        
        # Return first match as dict
        record = result.iloc[0]
        return {
            'detector_id': int(record['detid']),
            'date': str(record['date'].date()),
            'interval': int(record['interval']),
            'time': str(record['time']),
            'traffic_prediction': float(record['traffic_predict']),
            'model': model_name
        }
    
    def get_predictions_by_detector(
        self,
        detector_id: int,
        model_name: str,
        date: str,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all predictions for a detector within a time range
        
        Args:
            detector_id: Detector ID
            model_name: Model name
            date: Date string
            start_time: Start time (optional)
            end_time: End time (optional)
        
        Returns:
            List of prediction dictionaries
        """
        df = self.load_predictions(model_name, date)
        
        if df is None:
            return []
        
        # Filter by detector
        result = df[df['detid'] == detector_id].copy()
        
        # Filter by time range if provided
        if start_time:
            result = result[result['time'] >= start_time]
        if end_time:
            result = result[result['time'] <= end_time]
        
        # Convert to list of dicts
        predictions = []
        for _, row in result.iterrows():
            predictions.append({
                'detector_id': int(row['detid']),
                'date': str(row['date'].date()),
                'interval': int(row['interval']),
                'time': str(row['time']),
                'traffic_prediction': float(row['traffic_predict']),
                'model': model_name
            })
        
        return predictions
    
    def get_available_models(self) -> List[str]:
        """
        Scan data directory and return list of available models
        
        Returns:
            List of model names
        """
        if self.available_models:
            return self.available_models
        
        models = set()
        for file_path in self.data_dir.glob("predictions_*.csv"):
            # Extract model name from filename
            # Format: predictions_oct1_2017_catboost.csv
            parts = file_path.stem.split('_')
            if len(parts) >= 4:
                model_name = '_'.join(parts[3:])  # Handle models with underscores
                models.add(model_name)
        
        self.available_models = sorted(list(models))
        return self.available_models
    
    def get_available_dates(self) -> List[str]:
        """
        Scan data directory and return list of available dates
        
        Returns:
            List of date strings
        """
        if self.available_dates:
            return self.available_dates
        
        dates = set()
        for file_path in self.data_dir.glob("predictions_*.csv"):
            # Extract date from filename
            # Format: predictions_oct1_2017_catboost.csv
            parts = file_path.stem.split('_')
            if len(parts) >= 4:
                # Get date part (e.g., 'oct1', '2017')
                date_str = f"{parts[1]}_{parts[2]}"
                dates.add(date_str)
        
        self.available_dates = sorted(list(dates))
        return self.available_dates
    
    def get_unique_detectors(self, model_name: str, date: str) -> List[int]:
        """
        Get list of unique detector IDs for a specific model and date
        
        Args:
            model_name: Model name
            date: Date string
        
        Returns:
            List of detector IDs
        """
        df = self.load_predictions(model_name, date)
        
        if df is None:
            return []
        
        return sorted(df['detid'].unique().tolist())
    
    def clear_cache(self):
        """Clear the predictions cache"""
        self.predictions_cache.clear()
        logger.info("Predictions cache cleared")


# Global instance
prediction_loader = PredictionDataLoader(data_dir="data")
