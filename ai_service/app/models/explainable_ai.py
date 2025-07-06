import os
import numpy as np
import pandas as pd
import shap
import lime
import lime.lime_tabular
from typing import Dict, List, Tuple, Optional, Any
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
import joblib
import logging
from sklearn.base import BaseEstimator
import json
import base64
from io import BytesIO
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class ExplainableAI:
    """Explainable AI module using SHAP and LIME for model interpretability."""
    
    def __init__(self):
        self.shap_explainers = {}
        self.lime_explainers = {}
        self.feature_names = {}
        
    def setup_explainer(self, model: Any, X_train: pd.DataFrame, 
                       model_name: str, explainer_type: str = 'both') -> Dict:
        """Setup SHAP and/or LIME explainers for a model."""
        try:
            logger.info(f"Setting up explainer for {model_name}")
            
            if X_train.empty:
                return {'status': 'error', 'message': 'X_train data is empty, cannot setup explainer.'}

            # Clean and prepare data for explainers
            X_clean = self._clean_data_for_explainer(X_train.copy())
            
            if X_clean.empty:
                return {'status': 'error', 'message': 'No valid features after data cleaning'}

            self.feature_names[model_name] = list(X_clean.columns)
            
            if explainer_type in ['shap', 'both']:
                # Setup SHAP explainer
                if hasattr(model, 'predict_proba') and hasattr(model, 'predict'):
                    try:
                        predictions = model.predict(X_train)
                        if len(np.unique(predictions)) == 2:
                            # For binary classification models, use TreeExplainer or KernelExplainer based on model type
                            try:
                                self.shap_explainers[model_name] = shap.TreeExplainer(model)
                            except Exception:
                                # Fallback to KernelExplainer if TreeExplainer fails (e.g., non-tree model or complex input)
                                self.shap_explainers[model_name] = shap.KernelExplainer(model.predict_proba, X_train)
                        else:
                            # For multi-class classification
                            self.shap_explainers[model_name] = shap.KernelExplainer(model.predict_proba, X_train)
                    except Exception as e:
                        logger.warning(f"Could not create SHAP explainer for {model_name}: {e}")
                elif hasattr(model, 'predict'):
                    # For regression models, use TreeExplainer or KernelExplainer
                    try:
                        self.shap_explainers[model_name] = shap.TreeExplainer(model)
                    except Exception:
                        # Fallback to KernelExplainer if TreeExplainer fails
                        self.shap_explainers[model_name] = shap.KernelExplainer(model.predict, X_train)
                else:
                    # For regression models or multi-class where predict_proba might not be direct for TreeExplainer
                    try:
                        self.shap_explainers[model_name] = shap.TreeExplainer(model)
                    except Exception:
                        self.shap_explainers[model_name] = shap.KernelExplainer(model.predict, X_train)

            if explainer_type in ['lime', 'both']:
                # Setup LIME explainer
                mode = 'classification' if hasattr(model, 'predict_proba') else 'regression'
                self.lime_explainers[model_name] = lime.lime_tabular.LimeTabularExplainer(
                    training_data=X_train.values, # LIME expects numpy array
                    feature_names=list(X_train.columns),
                    class_names=model.classes_.tolist() if hasattr(model, 'classes_') else ['output'] , # For classification
                    mode=mode,
                    discretize_continuous=True
                )
            
            return {
                'status': 'success',
                'model_name': model_name,
                'explainer_type': explainer_type,
                'feature_count': len(X_train.columns)
            }
            
        except Exception as e:
            logger.error(f"Error setting up explainer: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def explain_prediction_shap(self, model: Any, X_instance: pd.DataFrame, 
                               model_name: str) -> Dict:
        """Generate SHAP explanations for a single prediction."""
        try:
            if model_name not in self.shap_explainers:
                return {'status': 'error', 'message': 'SHAP explainer not setup for this model'}
            
            explainer = self.shap_explainers[model_name]
            
            if X_instance.empty:
                return {'status': 'error', 'message': 'X_instance is empty, cannot generate SHAP explanation.'}

            # Ensure we only have a single row for SHAP explanation
            if len(X_instance) > 1:
                X_instance = X_instance.iloc[:1]  # Take only the first row
            elif len(X_instance) == 0:
                return {'status': 'error', 'message': 'X_instance has no rows, cannot generate SHAP explanation.'}

            # Get SHAP values
            shap_values = explainer.shap_values(X_instance)
            
            # Handle multi-class output and ensure shap_values is a single array for contributions
            if isinstance(shap_values, list):
                # For classification, often shap_values is a list of arrays (one for each class)
                # For binary, use the shap values for the positive class (index 1)
                if len(shap_values) == 2:
                    shap_values_arr = shap_values[1] 
                else: # For multi-class, sum absolute shap values across classes or choose a class
                    shap_values_arr = np.sum(np.abs(np.array(shap_values)), axis=0)
            else:
                shap_values_arr = shap_values
            
            # Ensure shap_values_arr is 1D (for single instance)
            if shap_values_arr.ndim > 1:
                shap_values_arr = shap_values_arr.flatten() if shap_values_arr.shape[0] == 1 else shap_values_arr[0]
            
            # Get feature contributions
            feature_contributions = []
            for i, feature in enumerate(self.feature_names[model_name]):
                # Ensure index is within bounds of shap_values_arr
                if i < len(shap_values_arr):
                    # Safely extract contribution value, handling multi-dimensional arrays
                    contribution_value = shap_values_arr[i]
                    if isinstance(contribution_value, np.ndarray):
                        contribution = float(contribution_value.item()) if contribution_value.size == 1 else float(contribution_value.flatten()[0])
                    else:
                        contribution = float(contribution_value)
                    
                    # Safely extract feature value
                    try:
                        feature_value = X_instance.iloc[0, i]
                        if isinstance(feature_value, np.ndarray):
                            value = float(feature_value.item()) if feature_value.size == 1 else float(feature_value.flatten()[0])
                        elif pd.isna(feature_value) or feature_value is None:
                            value = 0.0
                        elif isinstance(feature_value, (int, float, np.integer, np.floating)):
                            value = float(feature_value)
                        elif isinstance(feature_value, bool):
                            value = float(feature_value)
                        else:
                            # For strings, dates, or other types, try to convert to float via string
                            value = float(str(feature_value))
                    except (ValueError, TypeError, AttributeError):
                        value = 0.0
                        
                    feature_contributions.append({
                        'feature': feature,
                        'value': value,
                        'contribution': contribution,
                        'abs_contribution': abs(contribution)
                    })
            
            # Sort by absolute contribution
            feature_contributions.sort(key=lambda x: x['abs_contribution'], reverse=True)
            
            # Get base value and prediction
            try:
                if isinstance(explainer.expected_value, np.ndarray):
                    # For binary classification, typically use expected value of the positive class
                    if len(explainer.expected_value) == 2:
                        base_value = float(explainer.expected_value[1])
                    else:
                        base_value = float(explainer.expected_value[0])
                else:
                    base_value = float(explainer.expected_value)
            except (ValueError, TypeError, IndexError):
                base_value = 0.0
            
            prediction = getattr(model, 'predict')(X_instance)[0]
            prediction_proba = None
            if hasattr(model, 'predict_proba'):
                prediction_proba = getattr(model, 'predict_proba')(X_instance)[0]
            
            return {
                'status': 'success',
                'model_name': model_name,
                'prediction': float(prediction),
                'prediction_proba': prediction_proba.tolist() if prediction_proba is not None else None,
                'base_value': base_value,
                'feature_contributions': feature_contributions,
                'top_positive_features': [f for f in feature_contributions if f['contribution'] > 0][:5],
                'top_negative_features': [f for f in feature_contributions if f['contribution'] < 0][:5]
            }
            
        except Exception as e:
            logger.error(f"Error generating SHAP explanation: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def explain_prediction_lime(self, model: Any, X_instance: pd.DataFrame, 
                               model_name: str, num_features: int = 10) -> Dict:
        """Generate LIME explanations for a single prediction."""
        try:
            if model_name not in self.lime_explainers:
                return {'status': 'error', 'message': 'LIME explainer not setup for this model'}
            
            explainer = self.lime_explainers[model_name]
            
            if X_instance.empty:
                return {'status': 'error', 'message': 'X_instance is empty, cannot generate LIME explanation.'}

            # Generate explanation
            # LIME expects a 1D numpy array for a single instance
            if hasattr(model, 'predict_proba'):
                explanation = explainer.explain_instance(
                    X_instance.values[0], 
                    model.predict_proba, 
                    num_features=num_features
                )
            else:
                explanation = explainer.explain_instance(
                    X_instance.values[0], 
                    model.predict, 
                    num_features=num_features
                )
            
            # Extract feature contributions
            feature_contributions = []
            # LIME's explanation.as_list() returns a list of (feature, weight) tuples
            for feature_name_or_idx, contribution in explanation.as_list():
                # Ensure feature_name is a string and not an index
                if isinstance(feature_name_or_idx, int):
                    feature_name = self.feature_names[model_name][feature_name_or_idx]
                else:
                    feature_name = feature_name_or_idx # Already a string (e.g., for categorical features)

                feature_contributions.append({
                    'feature': feature_name,
                    'contribution': float(contribution),
                    'abs_contribution': abs(float(contribution))
                })
            
            # Get prediction
            prediction = model.predict(X_instance)[0]
            prediction_proba = None
            if hasattr(model, 'predict_proba'):
                prediction_proba = model.predict_proba(X_instance)[0]
            
            return {
                'status': 'success',
                'model_name': model_name,
                'prediction': float(prediction),
                'prediction_proba': prediction_proba.tolist() if prediction_proba is not None else None,
                'feature_contributions': feature_contributions,
                'explanation_score': explanation.score, # LIME's faithfulness score
                'local_accuracy': explanation.local_exp # The linear model's local explanation
            }
            
        except Exception as e:
            logger.error(f"Error generating LIME explanation: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def explain_prediction(self, model: Any, X_instance: pd.DataFrame, 
                          model_name: str, method: str = 'shap') -> Dict:
        """Unified method to explain a single prediction using either SHAP or LIME."""
        try:
            if method == 'shap':
                return self.explain_prediction_shap(model, X_instance, model_name)
            elif method == 'lime':
                return self.explain_prediction_lime(model, X_instance, model_name)
            else:
                return {'status': 'error', 'message': f'Unsupported explanation method: {method}'}
        except Exception as e:
            logger.error(f"Error in explain_prediction: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def generate_global_explanations(self, model: Any, X_data: pd.DataFrame, 
                                   model_name: str, sample_size: int = 100) -> Dict:
        """Generate global model explanations using SHAP."""
        try:
            if model_name not in self.shap_explainers:
                return {'status': 'error', 'message': 'SHAP explainer not setup for this model'}
            
            # Sample data for efficiency
            if len(X_data) > sample_size:
                X_sample = X_data.sample(n=sample_size, random_state=42)
            else:
                X_sample = X_data
            
            if X_sample.empty:
                return {'status': 'error', 'message': 'Sampled data is empty, cannot generate global explanations.'}

            explainer = self.shap_explainers[model_name]
            shap_values = explainer.shap_values(X_sample)
            
            # Handle multi-class output and ensure shap_values is a single array for contributions
            if isinstance(shap_values, list):
                # For classification, often shap_values is a list of arrays (one for each class)
                # For binary, use the shap values for the positive class (index 1)
                if len(shap_values) == 2:
                    shap_values_arr = shap_values[1] 
                else: # For multi-class, sum absolute shap values across classes or choose a class
                    shap_values_arr = np.sum(np.abs(np.array(shap_values)), axis=0)
            else:
                shap_values_arr = shap_values
            
            # Calculate feature importance (mean absolute SHAP value)
            feature_importance = np.abs(shap_values_arr).mean(axis=0)
            
            # Create feature importance ranking
            feature_ranking = []
            for i, feature in enumerate(self.feature_names[model_name]):
                if i < len(feature_importance): # Ensure index is within bounds
                    feature_ranking.append({
                        'feature': feature,
                        'importance': float(feature_importance[i]),
                        'mean_impact': float(np.mean(shap_values_arr[:, i])),
                        'impact_std': float(np.std(shap_values_arr[:, i]))
                    })
            
            feature_ranking.sort(key=lambda x: x['importance'], reverse=True)
            
            # Generate summary statistics
            summary_stats = {}
            if feature_ranking: # Ensure feature_ranking is not empty
                summary_stats = {
                    'most_important_feature': feature_ranking[0]['feature'],
                    'least_important_feature': feature_ranking[-1]['feature'],
                    'total_features': len(feature_ranking),
                    'top_5_features': [f['feature'] for f in feature_ranking[:5]],
                    'feature_importance_distribution': {
                        'mean': float(np.mean(feature_importance)) if len(feature_importance) > 0 else 0,
                        'std': float(np.std(feature_importance)) if len(feature_importance) > 0 else 0,
                        'min': float(np.min(feature_importance)) if len(feature_importance) > 0 else 0,
                        'max': float(np.max(feature_importance)) if len(feature_importance) > 0 else 0
                    }
                }
            
            return {
                'status': 'success',
                'model_name': model_name,
                'feature_ranking': feature_ranking,
                'summary_stats': summary_stats,
                'sample_size': len(X_sample)
            }
            
        except Exception as e:
            logger.error(f"Error generating global explanations: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def generate_feature_importance(self, model: Any, X_data: pd.DataFrame, 
                                   model_name: str, method: str = 'shap') -> Dict:
        """Generate global feature importance for the model."""
        try:
            if method == 'shap':
                # Use global explanations to generate feature importance
                global_explanation = self.generate_global_explanations(model, X_data, model_name)
                if global_explanation['status'] == 'success':
                    feature_importance = global_explanation.get('feature_importance', [])
                    return {
                        'status': 'success',
                        'method': 'shap',
                        'feature_importance': feature_importance,
                        'model_name': model_name
                    }
                else:
                    return global_explanation
            elif method == 'permutation':
                # Fallback to model's built-in feature importance if available
                if hasattr(model, 'feature_importances_'):
                    feature_names = self.feature_names.get(model_name, [f'feature_{i}' for i in range(len(model.feature_importances_))])
                    importance_scores = model.feature_importances_
                    
                    feature_importance = [
                        {
                            'feature': feature_names[i],
                            'importance': float(importance_scores[i]),
                            'rank': i + 1
                        }
                        for i in range(len(feature_names))
                    ]
                    
                    # Sort by importance
                    feature_importance.sort(key=lambda x: x['importance'], reverse=True)
                    
                    # Update ranks
                    for i, item in enumerate(feature_importance):
                        item['rank'] = i + 1
                    
                    return {
                        'status': 'success',
                        'method': 'model_builtin',
                        'feature_importance': feature_importance,
                        'model_name': model_name
                    }
                else:
                    return {'status': 'error', 'message': 'Model does not have built-in feature importance'}
            else:
                return {'status': 'error', 'message': f'Unsupported importance method: {method}'}
        except Exception as e:
            logger.error(f"Error generating feature importance: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def create_visualization(self, explanation_data: Dict, 
                           visualization_type: str = 'feature_importance') -> Dict:
        """Create visualizations for explanations."""
        try:
            if visualization_type == 'feature_importance':
                if 'feature_importance' in explanation_data:
                    feature_importance = explanation_data['feature_importance'][:10]  # Top 10 features
                    
                    features = [item['feature'] for item in feature_importance]
                    importances = [item['importance'] for item in feature_importance]
                    
                    # Create plotly bar chart
                    fig = go.Figure(data=[
                        go.Bar(
                            x=importances,
                            y=features,
                            orientation='h',
                            marker_color='steelblue'
                        )
                    ])
                    
                    fig.update_layout(
                        title=f"Top 10 Feature Importance - {explanation_data.get('model_name', 'Model')}",
                        xaxis_title="Importance Score",
                        yaxis_title="Features",
                        height=400,
                        margin=dict(l=200)
                    )
                    
                    # Convert to JSON for API response
                    fig_json = fig.to_json()
                    
                    return {
                        'status': 'success',
                        'visualization_type': visualization_type,
                        'chart_data': fig_json,
                        'chart_type': 'plotly_bar'
                    }
                    
            elif visualization_type == 'prediction_explanation':
                if 'feature_contributions' in explanation_data:
                    contributions = explanation_data['feature_contributions'][:10]  # Top 10 contributors
                    
                    features = [item['feature'] for item in contributions]
                    values = [item['contribution'] for item in contributions]
                    colors = ['red' if v < 0 else 'green' for v in values]
                    
                    fig = go.Figure(data=[
                        go.Bar(
                            x=values,
                            y=features,
                            orientation='h',
                            marker_color=colors
                        )
                    ])
                    
                    fig.update_layout(
                        title=f"Feature Contributions - {explanation_data.get('model_name', 'Model')}",
                        xaxis_title="Contribution",
                        yaxis_title="Features",
                        height=400,
                        margin=dict(l=200)
                    )
                    
                    # Convert to JSON for API response
                    fig_json = fig.to_json()
                    
                    return {
                        'status': 'success',
                        'visualization_type': visualization_type,
                        'chart_data': fig_json,
                        'chart_type': 'plotly_bar'
                    }
            else:
                return {'status': 'error', 'message': f'Unsupported visualization type: {visualization_type}'}
                
            return {'status': 'error', 'message': 'Required data not found in explanation_data'}
            
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def create_explanation_visualizations(self, explanation_data: Dict, 
                                        viz_type: str = 'feature_importance') -> Dict:
        """Create visualization for explanations."""
        try:
            if viz_type == 'feature_importance':
                return self._create_feature_importance_viz(explanation_data)
            elif viz_type == 'contribution_waterfall':
                return self._create_waterfall_viz(explanation_data)
            elif viz_type == 'feature_comparison':
                return self._create_feature_comparison_viz(explanation_data)
            else:
                return {'status': 'error', 'message': 'Unsupported visualization type'}
                
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _create_feature_importance_viz(self, explanation_data: Dict) -> Dict:
        """Create feature importance bar chart."""
        if 'feature_ranking' not in explanation_data or not explanation_data['feature_ranking']:
            return {'status': 'error', 'message': 'No feature ranking data available for visualization'}
        
        features = [f['feature'] for f in explanation_data['feature_ranking'][:10]]
        importance = [f['importance'] for f in explanation_data['feature_ranking'][:10]]
        
        fig = go.Figure(data=[
            go.Bar(
                x=importance,
                y=features,
                orientation='h',
                marker_color='skyblue'
            )
        ])
        
        fig.update_layout(
            title='Top 10 Feature Importance',
            xaxis_title='Importance Score',
            yaxis_title='Features',
            height=500,
            # Ensure y-axis labels are readable, especially for longer feature names
            yaxis={'automargin': True, 'categoryorder': 'total ascending'} 
        )
        
        return {
            'status': 'success',
            'chart_data': fig.to_dict(),
            'chart_type': 'feature_importance'
        }
    
    def _create_waterfall_viz(self, explanation_data: Dict) -> Dict:
        """Create waterfall chart for feature contributions."""
        if 'feature_contributions' not in explanation_data or not explanation_data['feature_contributions']:
            return {'status': 'error', 'message': 'No feature contributions data available for visualization'}
        
        contributions = explanation_data['feature_contributions'][:8]  # Top 8 features
        
        features = [f['feature'] for f in contributions]
        values = [f['contribution'] for f in contributions]
        
        # Add base value and prediction
        base_value = explanation_data.get('base_value', 0)
        prediction_value = explanation_data.get('prediction', base_value + sum(values))

        x_labels = ['Base Value'] + features + ['Prediction']
        # The 'y' values for plotly.graph_objs.Waterfall are the *change* values, not cumulative
        # We need to explicitly define the `measure` to dictate if it's absolute, relative, or total
        measures = ["absolute"] + ["relative"] * len(values) + ["total"]
        
        fig = go.Figure(data=[
            go.Waterfall(
                name="Feature Contributions",
                orientation="v",
                measure=measures,
                x=x_labels,
                textposition="outside",
                text=[f"{val:.3f}" for val in [base_value] + values + [prediction_value]], # Display actual values for text
                y=[base_value] + values + [prediction_value], # These are the values from which changes are calculated
                connector={"line": {"color": "rgb(63, 63, 63)"}},
            )
        ])
        
        fig.update_layout(
            title="Feature Contribution Waterfall",
            showlegend=True,
            height=500,
            # Ensure x-axis labels are readable
            xaxis={'automargin': True, 'tickangle': 45} 
        )
        
        return {
            'status': 'success',
            'chart_data': fig.to_dict(),
            'chart_type': 'waterfall'
        }
    
    def _create_feature_comparison_viz(self, explanation_data: Dict) -> Dict:
        """Create feature comparison visualization."""
        if 'feature_contributions' not in explanation_data or not explanation_data['feature_contributions']:
            return {'status': 'error', 'message': 'No feature contributions data available for visualization'}
        
        contributions = explanation_data['feature_contributions'][:10]
        
        features = [f['feature'] for f in contributions]
        values = [f['value'] for f in contributions]
        contributions_vals = [f['contribution'] for f in contributions]
        
        # Create subplot with feature values and contributions
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Feature Values', 'Feature Contributions'),
            horizontal_spacing=0.1
        )
        
        # Feature values
        fig.add_trace(
            go.Bar(x=features, y=values, name='Values', marker_color='lightblue'),
            row=1, col=1
        )
        
        # Feature contributions
        colors = ['green' if c > 0 else 'red' for c in contributions_vals]
        fig.add_trace(
            go.Bar(x=features, y=contributions_vals, name='Contributions', 
                  marker_color=colors),
            row=1, col=2
        )
        
        fig.update_layout(
            title='Feature Values vs Contributions',
            height=500,
            showlegend=False
        )
        
        fig.update_xaxes(tickangle=45)
        
        return {
            'status': 'success',
            'chart_data': fig.to_dict(),
            'chart_type': 'feature_comparison'
        }
    
    def batch_explain_predictions(self, model: Any, X_batch: pd.DataFrame, 
                                 model_name: str, method: str = 'shap') -> Dict:
        """Generate explanations for a batch of predictions."""
        try:
            explanations = []
            
            if X_batch.empty:
                return {'status': 'success', 'explanations': [], 'batch_size': 0, 'method': method, 'message': 'Input batch is empty.'}

            for idx, row in X_batch.iterrows():
                X_instance = pd.DataFrame([row]) # Create a DataFrame for single row
                
                explanation = {'status': 'error', 'message': 'Explanation method not supported or failed'}
                if method == 'shap':
                    explanation = self.explain_prediction_shap(model, X_instance, model_name)
                elif method == 'lime':
                    explanation = self.explain_prediction_lime(model, X_instance, model_name)
                
                if explanation['status'] == 'success':
                    explanation['instance_id'] = str(idx) # Ensure ID is string for consistent JSON
                    explanations.append(explanation)
                else:
                    logger.warning(f"Failed to explain instance {idx} with {method}: {explanation.get('message', 'Unknown error')}")
            
            return {
                'status': 'success',
                'explanations': explanations,
                'batch_size': len(explanations),
                'method': method
            }
            
        except Exception as e:
            logger.error(f"Error in batch explanation: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def save_explainer(self, model_name: str, filepath: str) -> Dict:
        """Save explainer configuration."""
        try:
            # SHAP and LIME explainers themselves are often not directly serializable like joblib.
            # Here, we save the configuration and rely on re-initializing the explainer.
            explainer_data = {
                'model_name': model_name,
                'feature_names': self.feature_names.get(model_name, []),
                'has_shap': model_name in self.shap_explainers,
                'has_lime': model_name in self.lime_explainers,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
            os.makedirs(os.path.dirname(filepath), exist_ok=True) # Ensure directory exists
            with open(filepath, 'w') as f:
                json.dump(explainer_data, f, indent=2)
            
            return {'status': 'success', 'filepath': filepath}
            
        except Exception as e:
            logger.error(f"Error saving explainer config: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def load_explainer(self, filepath: str) -> Dict:
        """Load explainer configuration."""
        try:
            if not os.path.exists(filepath):
                return {'status': 'error', 'message': f'Explainer config file not found: {filepath}'}

            with open(filepath, 'r') as f:
                explainer_data = json.load(f)
            
            model_name = explainer_data['model_name']
            self.feature_names[model_name] = explainer_data['feature_names']
            
            # Note: SHAP/LIME explainer objects themselves are not loaded here.
            # They need to be re-initialized using `setup_explainer` with the trained model and data.
            
            return {'status': 'success', 'model_name': model_name, 'loaded_config': explainer_data}
            
        except Exception as e:
            logger.error(f"Error loading explainer config: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def save_explainers(self, path: str = 'models/saved_models/explainable_ai.pkl'):
        """Save explainers to disk."""
        try:
            explainer_data = {
                'feature_names': self.feature_names,
                # Note: SHAP and LIME explainers contain complex objects that may not serialize well
                # We'll save the metadata and rebuild explainers as needed
                'available_models': list(self.feature_names.keys()),
                'shap_model_types': {name: type(explainer).__name__ 
                                   for name, explainer in self.shap_explainers.items()},
                'lime_model_types': {name: type(explainer).__name__ 
                                   for name, explainer in self.lime_explainers.items()}
            }
            joblib.dump(explainer_data, path)
            logger.info(f"ExplainableAI metadata saved to {path}")
            return True
        except Exception as e:
            logger.error(f"Error saving explainers: {e}")
            return False
    
    def load_explainers(self, path: str = 'models/saved_models/explainable_ai.pkl'):
        """Load explainer metadata from disk."""
        try:
            if os.path.exists(path):
                explainer_data = joblib.load(path)
                self.feature_names = explainer_data.get('feature_names', {})
                logger.info(f"ExplainableAI metadata loaded from {path}")
                logger.info(f"Available models: {explainer_data.get('available_models', [])}")
                return True
            else:
                logger.info(f"No saved explainer metadata found at {path}")
                return False
        except Exception as e:
            logger.error(f"Error loading explainers: {e}")
            return False
    
    def _clean_data_for_explainer(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and prepare data for explainers by handling string/object types."""
        try:
            df_clean = df.copy()
            
            # Remove ID-like columns that are strings and other problematic columns
            string_cols_to_remove = []
            for col in df_clean.columns:
                if df_clean[col].dtype == 'object':
                    # Check if it's likely an ID column (all unique or mostly unique strings)
                    unique_ratio = df_clean[col].nunique() / len(df_clean) 
                    if unique_ratio > 0.9:  # If more than 90% unique, likely an ID
                        string_cols_to_remove.append(col)
                        continue
                    
                    # Try to convert to numeric first
                    try:
                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                        if df_clean[col].isna().all():
                            # If all values became NaN, try category codes
                            df_clean[col] = df[col].astype('category').cat.codes
                    except:
                        # If all conversions fail, remove the column
                        string_cols_to_remove.append(col)
            
            # Remove problematic columns
            df_clean = df_clean.drop(columns=string_cols_to_remove)
            
            # Handle datetime columns
            for col in df_clean.columns:
                if pd.api.types.is_datetime64_any_dtype(df_clean[col]):
                    # Convert to timestamp (numeric)
                    try:
                        df_clean[col] = df_clean[col].astype('int64') // 10**9  # Convert to seconds
                    except:
                        # If conversion fails, use ordinal
                        df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce').map(pd.Timestamp.toordinal)
                        df_clean[col] = df_clean[col].fillna(0)
            
            # Fill NaN values
            df_clean = df_clean.fillna(0)
            
            # Ensure all remaining columns are numeric
            numeric_cols = []
            for col in df_clean.columns:
                try:
                    # Force conversion to numeric, coercing errors to NaN
                    df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
                    if not df_clean[col].isna().all():  # Keep column if it has some valid numeric data
                        numeric_cols.append(col)
                except:
                    continue
            
            df_clean = df_clean[numeric_cols].fillna(0)
            
            # Ensure we have at least some columns
            if df_clean.empty or len(df_clean.columns) == 0:
                logger.warning("All columns removed during cleaning, creating dummy features")
                # Create minimal dummy features
                df_clean = pd.DataFrame({
                    'feature_1': [1.0] * len(df),
                    'feature_2': [2.0] * len(df)
                })
            
            return df_clean
            
        except Exception as e:
            logger.warning(f"Error cleaning data for explainer: {e}")
            # Return minimal dummy DataFrame
            return pd.DataFrame({
                'feature_1': [1.0] * min(100, len(df) if not df.empty else 100),
                'feature_2': [2.0] * min(100, len(df) if not df.empty else 100)
            })
