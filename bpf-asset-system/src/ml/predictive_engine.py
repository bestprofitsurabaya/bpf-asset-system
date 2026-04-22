"""
Machine Learning Predictive Engine
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from pathlib import Path
from typing import Optional, Tuple, List, Dict

logger = logging.getLogger(__name__)

class PredictiveMaintenanceEngine:
    """Advanced Predictive Maintenance Engine with ML"""
    
    def __init__(self, mode: str = 'real', models_dir: Path = None):
        self.mode = mode
        
        if models_dir is None:
            models_dir = Path(__file__).parent.parent.parent / 'models'
        
        self.models_dir = models_dir
        self.models_dir.mkdir(exist_ok=True)
        
        self.model_path = self.models_dir / f'rf_model_{mode}.pkl'
        self.scaler_path = self.models_dir / f'scaler_{mode}.pkl'
        self.anomaly_model_path = self.models_dir / f'anomaly_model_{mode}.pkl'
        
        self.model = None
        self.scaler = None
        self.anomaly_model = None
        
        self.feature_columns = [
            'days_since_install', 'amp_kompresor', 'low_p', 'high_p',
            'delta_t', 'temp_outdoor', 'maintenance_count',
            'amp_rolling_mean_3', 'delta_t_rolling_mean_3',
            'amp_rate', 'delta_t_rate', 'month', 'is_rainy_season'
        ]
    
    def load_or_train_models(self, logs: pd.DataFrame = None):
        """Load existing models or train new ones"""
        try:
            if self.model_path.exists():
                self.model = joblib.load(self.model_path)
                self.scaler = joblib.load(self.scaler_path)
                self.anomaly_model = joblib.load(self.anomaly_model_path)
                logger.info("ML models loaded successfully")
                return True
            elif logs is not None and not logs.empty:
                return self.train_models(logs)
            else:
                logger.warning("No existing models and no training data provided")
                return False
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            if logs is not None and not logs.empty:
                return self.train_models(logs)
            return False
    
    def _create_features(self, logs: pd.DataFrame) -> pd.DataFrame:
        """Create advanced features for ML"""
        logs = logs.copy()
        
        if 'tanggal' in logs.columns:
            logs['tanggal'] = pd.to_datetime(logs['tanggal'])
            logs = logs.sort_values(['asset_id', 'tanggal'])
        
        # Days since installation (approximated)
        logs['days_since_install'] = logs.groupby('asset_id')['tanggal'].rank(method='first') * 7
        
        # Maintenance count
        logs['maintenance_count'] = logs.groupby('asset_id').cumcount()
        
        # Rolling averages
        if 'amp_kompresor' in logs.columns:
            logs['amp_rolling_mean_3'] = logs.groupby('asset_id')['amp_kompresor'].transform(
                lambda x: x.rolling(3, min_periods=1).mean()
            )
        else:
            logs['amp_rolling_mean_3'] = 15
        
        if 'delta_t' in logs.columns:
            logs['delta_t_rolling_mean_3'] = logs.groupby('asset_id')['delta_t'].transform(
                lambda x: x.rolling(3, min_periods=1).mean()
            )
        else:
            logs['delta_t_rolling_mean_3'] = 10
        
        # Rate of change
        if 'amp_kompresor' in logs.columns:
            logs['amp_rate'] = logs.groupby('asset_id')['amp_kompresor'].pct_change().fillna(0)
        else:
            logs['amp_rate'] = 0
        
        if 'delta_t' in logs.columns:
            logs['delta_t_rate'] = logs.groupby('asset_id')['delta_t'].pct_change().fillna(0)
        else:
            logs['delta_t_rate'] = 0
        
        # Seasonal features
        if 'tanggal' in logs.columns:
            logs['month'] = logs['tanggal'].dt.month
            logs['is_rainy_season'] = logs['month'].isin([10, 11, 12, 1, 2, 3]).astype(int)
        else:
            logs['month'] = datetime.now().month
            logs['is_rainy_season'] = 1 if datetime.now().month in [10, 11, 12, 1, 2, 3] else 0
        
        return logs
    
    def train_models(self, logs: pd.DataFrame) -> bool:
        """Train ML models on historical data"""
        if logs.empty or len(logs) < 50:
            logger.warning("Not enough data to train ML models")
            return False
        
        try:
            features = self._create_features(logs)
            
            available_cols = [col for col in self.feature_columns if col in features.columns]
            
            if 'health_score' not in features.columns:
                logger.error("No health_score column in data")
                return False
            
            X = features[available_cols].fillna(0)
            y = features['health_score'].fillna(70)
            
            if len(X) < 50:
                logger.warning("Not enough valid samples for training")
                return False
            
            # Train Random Forest
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                n_jobs=-1
            )
            
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X)
            self.model.fit(X_scaled, y)
            
            # Train Isolation Forest
            self.anomaly_model = IsolationForest(
                contamination=0.1,
                random_state=42,
                n_jobs=-1
            )
            self.anomaly_model.fit(X_scaled)
            
            # Save models
            joblib.dump(self.model, self.model_path)
            joblib.dump(self.scaler, self.scaler_path)
            joblib.dump(self.anomaly_model, self.anomaly_model_path)
            
            score = self.model.score(X_scaled, y)
            logger.info(f"ML models trained successfully. R2 Score: {score:.3f}")
            return True
            
        except Exception as e:
            logger.error(f"Error training models: {e}")
            return False
    
    def predict_health_score(self, asset_id: str, current_readings: Dict,
                            logs: pd.DataFrame) -> Tuple[Optional[float], Optional[List[float]], bool, float]:
        """Predict health score with ML"""
        if self.model is None or self.scaler is None:
            return None, None, False, 0
        
        try:
            asset_logs = logs[logs['asset_id'] == asset_id] if not logs.empty else pd.DataFrame()
            
            # Build feature vector
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
            
            X = pd.DataFrame([features])[self.feature_columns].fillna(0)
            
            # Ensure all feature columns exist
            for col in self.feature_columns:
                if col not in X.columns:
                    X[col] = 0
            X = X[self.feature_columns]
            
            X_scaled = self.scaler.transform(X)
            
            # Predictions
            predicted_health = float(self.model.predict(X_scaled)[0])
            predicted_health = max(0, min(100, predicted_health))
            
            # Anomaly detection
            is_anomaly = self.anomaly_model.predict(X_scaled)[0] == -1
            anomaly_score = float(self.anomaly_model.score_samples(X_scaled)[0])
            
            # Confidence interval from tree predictions
            tree_preds = np.array([tree.predict(X_scaled)[0] for tree in self.model.estimators_])
            confidence_interval = [
                float(np.percentile(tree_preds, 2.5)),
                float(np.percentile(tree_preds, 97.5))
            ]
            
            return predicted_health, confidence_interval, is_anomaly, anomaly_score
            
        except Exception as e:
            logger.error(f"Error predicting health score: {e}")
            return None, None, False, 0
    
    def predict_remaining_life(self, asset_id: str, logs: pd.DataFrame,
                               threshold: float = 65) -> Tuple[Optional[float], float, Optional[datetime]]:
        """Predict Remaining Useful Life (RUL) in days"""
        asset_logs = logs[logs['asset_id'] == asset_id].sort_values('tanggal') if not logs.empty else pd.DataFrame()
        
        if len(asset_logs) < 10:
            return None, 0, None
        
        try:
            asset_logs = asset_logs.copy()
            asset_logs['tanggal'] = pd.to_datetime(asset_logs['tanggal'])
            asset_logs['days'] = (asset_logs['tanggal'] - asset_logs['tanggal'].min()).dt.days
            
            X = asset_logs[['days']].values
            y = asset_logs['health_score'].values
            
            model = LinearRegression()
            model.fit(X, y)
            
            if model.coef_[0] < 0:
                days_to_failure = (threshold - model.intercept_) / model.coef_[0]
                confidence = model.score(X, y) * 100
                fail_date = asset_logs['tanggal'].min() + timedelta(days=int(days_to_failure))
                return max(0, days_to_failure), confidence, fail_date
            
            return float('inf'), 0, None
            
        except Exception as e:
            logger.error(f"Error predicting RUL: {e}")
            return None, 0, None
    
    def get_similar_assets_pattern(self, asset_id: str, logs: pd.DataFrame) -> List[Dict]:
        """Find similar assets with degradation patterns"""
        if logs.empty:
            return []
        
        asset_logs = logs[logs['asset_id'] == asset_id].tail(10)
        if asset_logs.empty:
            return []
        
        avg_health = asset_logs['health_score'].mean()
        avg_delta = asset_logs['delta_t'].mean() if 'delta_t' in asset_logs.columns else 10
        avg_amp = asset_logs['amp_kompresor'].mean() if 'amp_kompresor' in asset_logs.columns else 15
        
        all_assets = logs['asset_id'].unique()
        similarities = []
        
        for other_id in all_assets:
            if other_id == asset_id:
                continue
            
            other_logs = logs[logs['asset_id'] == other_id].tail(10)
            if other_logs.empty:
                continue
            
            other_avg_health = other_logs['health_score'].mean()
            other_avg_delta = other_logs['delta_t'].mean() if 'delta_t' in other_logs.columns else 10
            other_avg_amp = other_logs['amp_kompresor'].mean() if 'amp_kompresor' in other_logs.columns else 15
            
            health_diff = abs(avg_health - other_avg_health)
            delta_diff = abs(avg_delta - other_avg_delta)
            amp_diff = abs(avg_amp - other_avg_amp)
            
            similarity = 100 - (health_diff * 2 + delta_diff * 5 + amp_diff * 3)
            
            if similarity > 60:
                similarities.append({
                    'asset_id': other_id,
                    'similarity': round(similarity, 1),
                    'avg_health': round(other_avg_health, 1),
                    'trend': 'Degrading' if self._is_degrading(other_logs) else 'Stable'
                })
        
        return sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:5]
    
    def _is_degrading(self, logs: pd.DataFrame) -> bool:
        """Check if asset is degrading"""
        if len(logs) < 3:
            return False
        
        health_scores = logs['health_score'].tail(3).tolist()
        return health_scores[0] > health_scores[1] > health_scores[2]
    
    def detect_anomalies_realtime(self, readings: Dict, asset_id: str,
                                  logs: pd.DataFrame) -> Tuple[List[Dict], str]:
        """Real-time anomaly detection"""
        if logs.empty:
            return [], "Normal"
        
        asset_logs = logs[logs['asset_id'] == asset_id].tail(30)
        anomalies = []
        
        if len(asset_logs) >= 5:
            # Statistical anomaly (Z-score)
            for param in ['amp_kompresor', 'delta_t', 'low_p']:
                if param in readings and param in asset_logs.columns:
                    mean_val = asset_logs[param].mean()
                    std_val = asset_logs[param].std()
                    
                    if std_val > 0:
                        z_score = abs(readings[param] - mean_val) / std_val
                        
                        if z_score > 3:
                            anomalies.append({
                                'parameter': param,
                                'value': readings[param],
                                'expected': f"{mean_val:.2f} +/- {std_val*2:.2f}",
                                'z_score': round(z_score, 2),
                                'severity': 'High' if z_score > 4 else 'Medium',
                                'message': f'Nilai {param} di luar batas normal'
                            })
        
        # Rule-based anomaly
        if readings.get('delta_t', 0) < 6:
            anomalies.append({
                'parameter': 'delta_t',
                'value': readings['delta_t'],
                'expected': '> 8',
                'severity': 'High',
                'message': 'Efisiensi pendinginan sangat rendah - periksa filter dan freon'
            })
        elif readings.get('delta_t', 0) < 8:
            anomalies.append({
                'parameter': 'delta_t',
                'value': readings['delta_t'],
                'expected': '> 10',
                'severity': 'Medium',
                'message': 'Efisiensi pendinginan di bawah optimal'
            })
        
        if readings.get('amp_kompresor', 0) > 30:
            anomalies.append({
                'parameter': 'amp_kompresor',
                'value': readings['amp_kompresor'],
                'expected': '< 25',
                'severity': 'Critical',
                'message': 'Arus kompresor terlalu tinggi - risiko overheating!'
            })
        elif readings.get('amp_kompresor', 0) > 25:
            anomalies.append({
                'parameter': 'amp_kompresor',
                'value': readings['amp_kompresor'],
                'expected': '< 25',
                'severity': 'High',
                'message': 'Arus kompresor di atas normal'
            })
        
        if readings.get('low_p', 140) < 120:
            anomalies.append({
                'parameter': 'low_p',
                'value': readings['low_p'],
                'expected': '120-150',
                'severity': 'High',
                'message': 'Tekanan rendah - kemungkinan kebocoran freon'
            })
        elif readings.get('low_p', 140) > 160:
            anomalies.append({
                'parameter': 'low_p',
                'value': readings['low_p'],
                'expected': '120-150',
                'severity': 'Medium',
                'message': 'Tekanan tinggi - periksa kondensor'
            })
        
        # Trend-based anomaly
        if len(asset_logs) >= 3:
            recent_health = asset_logs['health_score'].tail(3).tolist()
            if len(recent_health) == 3:
                if recent_health[0] > recent_health[1] > recent_health[2]:
                    drop_rate = (recent_health[0] - recent_health[2]) / 2
                    if drop_rate > 5:
                        anomalies.append({
                            'parameter': 'health_trend',
                            'value': f"Turun {drop_rate:.1f}% per minggu",
                            'expected': 'Stabil',
                            'severity': 'High' if drop_rate > 10 else 'Medium',
                            'message': 'Penurunan performa cepat - perlu investigasi'
                        })
        
        # Determine overall severity
        severity_levels = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
        severity = "Normal"
        if anomalies:
            max_severity = max(anomalies, key=lambda x: severity_levels.get(x['severity'], 0))
            severity = max_severity['severity']
        
        return anomalies, severity