"""
Machine Learning Engine for Predictive Maintenance
"""

import pandas as pd
import numpy as np
import logging
from pathlib import Path
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import warnings
warnings.filterwarnings('ignore')

from config.settings import MODEL_DIR
import database.crud_ac as db_ac

logger = logging.getLogger(__name__)


class PredictiveMaintenanceEngine:
    """Advanced Predictive Maintenance Engine with ML"""
    
    def __init__(self, mode='real'):
        self.mode = mode
        self.model_path = MODEL_DIR / f'rf_model_{mode}.pkl'
        self.scaler_path = MODEL_DIR / f'scaler_{mode}.pkl'
        self.anomaly_model_path = MODEL_DIR / f'anomaly_model_{mode}.pkl'
        self.model = None
        self.scaler = None
        self.anomaly_model = None
        self.load_or_train_models()
    
    def load_or_train_models(self):
        """Load existing models or train new ones"""
        try:
            if self.model_path.exists():
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.anomaly_model = joblib.load(self.anomaly_model_path)
                logger.info("ML models loaded successfully")
            else:
                self.train_models()
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.train_models()
    
    def _create_features(self, logs):
        """Create advanced features for ML"""
        logs = logs.copy()
        logs['tanggal'] = pd.to_datetime(logs['tanggal'])
        logs = logs.sort_values(['asset_id', 'tanggal'])
        
        logs['days_since_install'] = logs.groupby('asset_id')['tanggal'].rank(method='first') * 7
        logs['maintenance_count'] = logs.groupby('asset_id').cumcount()
        
        logs['amp_rolling_mean_3'] = logs.groupby('asset_id')['amp_kompresor'].transform(
            lambda x: x.rolling(3, min_periods=1).mean()
        )
        logs['delta_t_rolling_mean_3'] = logs.groupby('asset_id')['delta_t'].transform(
            lambda x: x.rolling(3, min_periods=1).mean()
        )
        
        logs['amp_rate'] = logs.groupby('asset_id')['amp_kompresor'].pct_change().fillna(0)
        logs['delta_t_rate'] = logs.groupby('asset_id')['delta_t'].pct_change().fillna(0)
        
        logs['month'] = logs['tanggal'].dt.month
        logs['is_rainy_season'] = logs['month'].isin([10, 11, 12, 1, 2, 3]).astype(int)
        
        return logs
    
    def train_models(self):
        """Train ML models on historical data"""
        logs = db_ac.get_all_logs(mode=self.mode)
        
        if logs.empty or len(logs) < 50:
            logger.warning("Not enough data to train ML models")
            self.model = None
            self.anomaly_model = None
            return
        
        try:
            features = self._create_features(logs)
            
            feature_cols = ['days_since_install', 'amp_kompresor', 'low_p', 'high_p',
                          'delta_t', 'temp_outdoor', 'maintenance_count',
                          'amp_rolling_mean_3', 'delta_t_rolling_mean_3',
                          'amp_rate', 'delta_t_rate', 'month', 'is_rainy_season']
            
            available_cols = [col for col in feature_cols if col in features.columns]
            X = features[available_cols].fillna(0)
            y = features['health_score'].fillna(70)
            
            self.model = RandomForestRegressor(
                n_estimators=100, max_depth=10, random_state=42, n_jobs=-1
            )
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            
            self.anomaly_model = IsolationForest(
                contamination=0.1, random_state=42, n_jobs=-1
            )
            self.anomaly_model.fit(X_scaled)
            
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            joblib.dump(self.anomaly_model, self.anomaly_model_path)
            
            score = self.model.score(X_scaled, y)
            logger.info(f"ML models trained successfully. R2 Score: {score:.3f}")
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            self.model = None
            self.anomaly_model = None
    
    def predict_health_score(self, asset_id, current_readings):
        """Predict health score with ML"""
        if self.model is None:
            return None, None, None, None
        
        try:
            logs = db_ac.get_all_logs(mode=self.mode)
            asset_logs = logs[logs['asset_id'] == asset_id]
            
            features = {
                'days_since_install': len(asset_logs) * 7,
                'amp_kompresor': current_readings.get('amp', 15),
                'low_p': current_readings.get('low_p', 140),
                'high_p': current_readings.get('high_p', 350),
                'delta_t': current_readings.get('delta_t', 10),
                'temp_outdoor': current_readings.get('temp_outdoor', 32),
                'maintenance_count': len(asset_logs),
                'amp_rolling_mean_3': current_readings.get('amp', 15),
                'delta_t_rolling_mean_3': current_readings.get('delta_t', 10),
                'amp_rate': 0,
                'delta_t_rate': 0,
                'month': datetime.now().month,
                'is_rainy_season': 1 if datetime.now().month in [10, 11, 12, 1, 2, 3] else 0
            }
            
            feature_cols = ['days_since_install', 'amp_kompresor', 'low_p', 'high_p',
                          'delta_t', 'temp_outdoor', 'maintenance_count',
                          'amp_rolling_mean_3', 'delta_t_rolling_mean_3',
                          'amp_rate', 'delta_t_rate', 'month', 'is_rainy_season']
            
            X = pd.DataFrame([features])[feature_cols].fillna(0)
            X_scaled = self.scaler.transform(X)
            
            predicted_health = self.model.predict(X_scaled)[0]
            is_anomaly = self.anomaly_model.predict(X_scaled)[0] == -1
            anomaly_score = self.anomaly_model.score_samples(X_scaled)[0]
            
            tree_preds = np.array([tree.predict(X_scaled)[0] for tree in self.model.estimators_])
            confidence_interval = np.percentile(tree_preds, [2.5, 97.5])
            
            return predicted_health, confidence_interval, is_anomaly, anomaly_score
            
        except Exception as e:
            logger.error(f"Error predicting health score: {e}")
            return None, None, None, None
    
    def predict_remaining_life(self, asset_id):
        """Predict Remaining Useful Life (RUL) in days"""
        logs = db_ac.get_all_logs(mode=self.mode)
        asset_logs = logs[logs['asset_id'] == asset_id].sort_values('tanggal')
        
        if len(asset_logs) < 10:
            return None, None, None
        
        try:
            asset_logs['tanggal'] = pd.to_datetime(asset_logs['tanggal'])
            asset_logs['days'] = (asset_logs['tanggal'] - asset_logs['tanggal'].min()).dt.days
            
            X = asset_logs[['days']].values
            y = asset_logs['health_score'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            threshold = 65
            if model.coef_[0] < 0:
                days_to_failure = (threshold - model.intercept_) / model.coef_[0]
                confidence = model.score(X, y) * 100
                fail_date = asset_logs['tanggal'].min() + timedelta(days=int(days_to_failure))
                return max(0, days_to_failure), confidence, fail_date
            
            return float('inf'), 0, None
            
        except Exception as e:
            logger.error(f"Error predicting RUL: {e}")
            return None, None, None
    
    def get_similar_assets_pattern(self, asset_id):
        """Find similar assets with degradation patterns"""
        logs = db_ac.get_all_logs(mode=self.mode)
        
        if logs.empty:
            return []
        
        asset_logs = logs[logs['asset_id'] == asset_id].tail(10)
        if asset_logs.empty:
            return []
        
        avg_health = asset_logs['health_score'].mean()
        avg_delta = asset_logs['delta_t'].mean()
        avg_amp = asset_logs['amp_kompresor'].mean()
        
        all_assets = logs['asset_id'].unique()
        similarities = []
        
        for other_id in all_assets:
            if other_id == asset_id:
                continue
            
            other_logs = logs[logs['asset_id'] == other_id].tail(10)
            if other_logs.empty:
                continue
            
            health_diff = abs(avg_health - other_logs['health_score'].mean())
            delta_diff = abs(avg_delta - other_logs['delta_t'].mean())
            amp_diff = abs(avg_amp - other_logs['amp_kompresor'].mean())
            
            similarity = 100 - (health_diff * 2 + delta_diff * 5 + amp_diff * 3)
            
            if similarity > 60:
                similarities.append({
                    'asset_id': other_id,
                    'similarity': round(similarity, 1),
                    'avg_health': round(other_logs['health_score'].mean(), 1),
                    'trend': 'Degrading' if other_logs['health_score'].is_monotonic_decreasing else 'Stable'
                })
        
        return sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:5]