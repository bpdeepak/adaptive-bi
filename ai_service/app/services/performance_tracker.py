"""
Performance tracking service for monitoring model performance improvements over time.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path
import pandas as pd
from app.utils.logger import logger


class ModelPerformanceTracker:
    """
    Tracks and compares model performance metrics over time to determine if retraining improves performance.
    """
    
    def __init__(self, storage_dir: str = "models/performance_history"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Define what constitutes improvement for each metric (higher_is_better)
        self.metric_directions = {
            # Forecasting metrics
            'rmse': False,  # Lower RMSE is better
            'r2_score': True,  # Higher R² is better
            'mae': False,  # Lower MAE is better
            'mape': False,  # Lower MAPE is better
            
            # Anomaly detection metrics
            'outlier_percentage': None,  # Stable is better (depends on contamination setting)
            'outliers_in_training_data': None,  # Depends on data quality
            
            # Dynamic pricing metrics
            'mae': False,  # Lower MAE is better
            
            # Churn prediction metrics
            'auc_score': True,  # Higher AUC is better
            'accuracy': True,  # Higher accuracy is better
            'precision': True,  # Higher precision is better
            'recall': True,  # Higher recall is better
            'f1-score': True,  # Higher F1 is better
            
            # Recommendation metrics (could be added)
            'precision_at_k': True,  # Higher precision@k is better
            'recall_at_k': True,  # Higher recall@k is better
            'ndcg': True,  # Higher NDCG is better
        }
    
    def save_model_performance(self, model_name: str, metrics: Dict[str, Any], 
                             additional_info: Optional[Dict[str, Any]] = None) -> None:
        """
        Save model performance metrics with timestamp.
        
        Args:
            model_name: Name of the model (e.g., 'forecasting', 'anomaly_detection')
            metrics: Dictionary of performance metrics
            additional_info: Additional information like training samples, features used, etc.
        """
        try:
            performance_record = {
                'timestamp': datetime.now().isoformat(),
                'model_name': model_name,
                'metrics': metrics,
                'additional_info': additional_info or {}
            }
            
            # Save to JSON file for the specific model
            performance_file = self.storage_dir / f"{model_name}_performance_history.json"
            
            # Load existing history
            history = []
            if performance_file.exists():
                try:
                    with open(performance_file, 'r') as f:
                        history = json.load(f)
                except json.JSONDecodeError:
                    logger.warning(f"Could not load existing performance history for {model_name}, starting fresh")
                    history = []
            
            # Add new record
            history.append(performance_record)
            
            # Keep only last 50 records to avoid file bloat
            if len(history) > 50:
                history = history[-50:]
            
            # Save updated history
            with open(performance_file, 'w') as f:
                json.dump(history, f, indent=2)
                
            logger.info(f"Performance metrics saved for {model_name}: {metrics}")
            
        except Exception as e:
            logger.error(f"Failed to save performance metrics for {model_name}: {str(e)}")
    
    def get_model_performance_history(self, model_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get performance history for a specific model.
        
        Args:
            model_name: Name of the model
            limit: Maximum number of recent records to return
            
        Returns:
            List of performance records, most recent first
        """
        try:
            performance_file = self.storage_dir / f"{model_name}_performance_history.json"
            
            if not performance_file.exists():
                return []
            
            with open(performance_file, 'r') as f:
                history = json.load(f)
            
            # Return most recent records first
            return history[-limit:][::-1]
            
        except Exception as e:
            logger.error(f"Failed to load performance history for {model_name}: {str(e)}")
            return []
    
    def compare_with_previous_performance(self, model_name: str, current_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare current performance with the previous training result.
        
        Args:
            model_name: Name of the model
            current_metrics: Current performance metrics
            
        Returns:
            Dictionary containing comparison results and improvement analysis
        """
        try:
            history = self.get_model_performance_history(model_name, limit=2)
            
            if len(history) < 1:
                return {
                    'comparison_available': False,
                    'reason': 'No previous performance data available',
                    'current_metrics': current_metrics
                }
            
            # Get previous metrics (second most recent, since most recent is current)
            if len(history) >= 2:
                previous_metrics = history[1]['metrics']
            else:
                return {
                    'comparison_available': False,
                    'reason': 'Only one previous record available',
                    'current_metrics': current_metrics
                }
            
            comparison_result = {
                'comparison_available': True,
                'current_metrics': current_metrics,
                'previous_metrics': previous_metrics,
                'improvements': {},
                'degradations': {},
                'overall_improvement': False,
                'improvement_summary': ''
            }
            
            improved_metrics = []
            degraded_metrics = []
            
            # Compare each metric
            for metric_name, current_value in current_metrics.items():
                if metric_name not in previous_metrics:
                    continue
                    
                previous_value = previous_metrics[metric_name]
                
                # Skip non-numeric metrics
                if not isinstance(current_value, (int, float)) or not isinstance(previous_value, (int, float)):
                    continue
                
                # Calculate percentage change
                if previous_value != 0:
                    pct_change = ((current_value - previous_value) / abs(previous_value)) * 100
                else:
                    pct_change = 0.0 if current_value == 0 else float('inf')
                
                metric_direction = self.metric_directions.get(metric_name)
                
                if metric_direction is None:
                    # For metrics where direction is unclear, just record the change
                    comparison_result['improvements'][metric_name] = {
                        'current': current_value,
                        'previous': previous_value,
                        'change': current_value - previous_value,
                        'pct_change': pct_change,
                        'direction': 'neutral'
                    }
                elif (metric_direction and current_value > previous_value) or \
                     (not metric_direction and current_value < previous_value):
                    # Improvement
                    comparison_result['improvements'][metric_name] = {
                        'current': current_value,
                        'previous': previous_value,
                        'change': current_value - previous_value,
                        'pct_change': pct_change,
                        'direction': 'improved'
                    }
                    improved_metrics.append(f"{metric_name}: {pct_change:+.2f}%")
                else:
                    # Degradation
                    comparison_result['degradations'][metric_name] = {
                        'current': current_value,
                        'previous': previous_value,
                        'change': current_value - previous_value,
                        'pct_change': pct_change,
                        'direction': 'degraded'
                    }
                    degraded_metrics.append(f"{metric_name}: {pct_change:+.2f}%")
            
            # Determine overall improvement
            # Consider it an improvement if more metrics improved than degraded, 
            # or if key metrics improved significantly
            if len(improved_metrics) > len(degraded_metrics):
                comparison_result['overall_improvement'] = True
            elif len(improved_metrics) == len(degraded_metrics) and improved_metrics:
                # Check if improvements are more significant than degradations
                avg_improvement = sum(comp['pct_change'] for comp in comparison_result['improvements'].values() if comp['direction'] == 'improved')
                avg_degradation = sum(abs(comp['pct_change']) for comp in comparison_result['degradations'].values() if comp['direction'] == 'degraded')
                comparison_result['overall_improvement'] = avg_improvement > avg_degradation
            
            # Create summary
            if comparison_result['overall_improvement']:
                comparison_result['improvement_summary'] = f"✅ Model performance IMPROVED! Improvements: {', '.join(improved_metrics)}"
                if degraded_metrics:
                    comparison_result['improvement_summary'] += f" | Degradations: {', '.join(degraded_metrics)}"
            else:
                comparison_result['improvement_summary'] = f"⚠️ Model performance mixed or degraded. Improvements: {', '.join(improved_metrics) or 'None'} | Degradations: {', '.join(degraded_metrics) or 'None'}"
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Failed to compare performance for {model_name}: {str(e)}")
            return {
                'comparison_available': False,
                'reason': f'Error during comparison: {str(e)}',
                'current_metrics': current_metrics
            }
    
    def log_performance_comparison(self, model_name: str, comparison_result: Dict[str, Any]) -> None:
        """
        Log the performance comparison in a human-readable format.
        
        Args:
            model_name: Name of the model
            comparison_result: Result from compare_with_previous_performance
        """
        try:
            if not comparison_result['comparison_available']:
                logger.info(f"🔄 {model_name.upper()} RETRAINING: {comparison_result['reason']}")
                return
            
            logger.info(f"📊 {model_name.upper()} PERFORMANCE COMPARISON:")
            logger.info(f"   {comparison_result['improvement_summary']}")
            
            if comparison_result['improvements']:
                logger.info(f"   📈 Improved metrics:")
                for metric, data in comparison_result['improvements'].items():
                    if data['direction'] == 'improved':
                        logger.info(f"      • {metric}: {data['previous']:.4f} → {data['current']:.4f} ({data['pct_change']:+.2f}%)")
            
            if comparison_result['degradations']:
                logger.info(f"   📉 Degraded metrics:")
                for metric, data in comparison_result['degradations'].items():
                    if data['direction'] == 'degraded':
                        logger.info(f"      • {metric}: {data['previous']:.4f} → {data['current']:.4f} ({data['pct_change']:+.2f}%)")
                        
        except Exception as e:
            logger.error(f"Failed to log performance comparison for {model_name}: {str(e)}")
    
    def get_performance_trends(self, model_name: str) -> Dict[str, Any]:
        """
        Analyze performance trends over the last several training cycles.
        
        Args:
            model_name: Name of the model
            
        Returns:
            Dictionary containing trend analysis
        """
        try:
            history = self.get_model_performance_history(model_name, limit=10)
            
            if len(history) < 3:
                return {
                    'trend_available': False,
                    'reason': 'Insufficient data for trend analysis (need at least 3 training cycles)'
                }
            
            # Extract metrics over time
            metrics_over_time = {}
            timestamps = []
            
            for record in reversed(history):  # Reverse to get chronological order
                timestamps.append(record['timestamp'])
                for metric_name, value in record['metrics'].items():
                    if isinstance(value, (int, float)):
                        if metric_name not in metrics_over_time:
                            metrics_over_time[metric_name] = []
                        metrics_over_time[metric_name].append(value)
            
            # Analyze trends
            trend_analysis = {
                'trend_available': True,
                'training_cycles': len(history),
                'metric_trends': {}
            }
            
            for metric_name, values in metrics_over_time.items():
                if len(values) < 3:
                    continue
                
                # Simple trend analysis - compare first third vs last third
                first_third = values[:len(values)//3] if len(values) > 3 else values[:1]
                last_third = values[-len(values)//3:] if len(values) > 3 else values[-1:]
                
                avg_first = sum(first_third) / len(first_third)
                avg_last = sum(last_third) / len(last_third)
                
                metric_direction = self.metric_directions.get(metric_name)
                
                if metric_direction is None:
                    trend_direction = 'stable'
                elif (metric_direction and avg_last > avg_first) or (not metric_direction and avg_last < avg_first):
                    trend_direction = 'improving'
                elif (metric_direction and avg_last < avg_first) or (not metric_direction and avg_last > avg_first):
                    trend_direction = 'declining'
                else:
                    trend_direction = 'stable'
                
                pct_change = ((avg_last - avg_first) / abs(avg_first)) * 100 if avg_first != 0 else 0
                
                trend_analysis['metric_trends'][metric_name] = {
                    'direction': trend_direction,
                    'avg_first_third': avg_first,
                    'avg_last_third': avg_last,
                    'overall_change_pct': pct_change,
                    'values': values
                }
            
            return trend_analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze trends for {model_name}: {str(e)}")
            return {
                'trend_available': False,
                'reason': f'Error during trend analysis: {str(e)}'
            }


# Global instance
performance_tracker = ModelPerformanceTracker()
