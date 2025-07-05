"""
Reasoning Service - Exposes knowledge graph reasoning capabilities
Provides cognitive AI insights, pattern recognition, and strategic recommendations
"""

import logging
import asyncio
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import networkx as nx

from app.models.knowledge_graph import CustomerBehaviorGraph # Corrected import path
from app.model_configs.model_config import PRICING_CONFIG # Import the config instance instead
# from app.models.explainable_ai import ExplainableAI # Not directly used in ReasoningService, more for specific model explanations
# from app.utils.feature_engineering import AdvancedFeatureProcessor # Not directly used here, features are for models

logger = logging.getLogger(__name__)

class ReasoningService:
    def __init__(self, mongodb_client):
        self.db = mongodb_client
        self.knowledge_graph = CustomerBehaviorGraph()
        self.config = PRICING_CONFIG # Use the pre-configured instance
        self._graph_built = False
        self.last_built_time: Optional[datetime] = None # To track last graph build time
        self.kg_graph = None # Initialize the in-memory graph representation

    async def initialize(self):
        """Initialize reasoning service and build knowledge graph."""
        try:
            await self._build_knowledge_graph()
            logger.info("Reasoning service initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize reasoning service: {e}")
            raise

    async def _build_knowledge_graph(self):
        """Build and populate knowledge graph with latest data."""
        try:
            # Load data from database using _get methods
            users = await self._get_users()
            products = await self._get_products()
            transactions = await self._get_transactions()
            feedback = await self._get_feedback()
            activities = await self._get_activities()

            # Ensure essential columns are correctly formatted and present for graph building
            # Schema mapping and data cleaning:
            # Users: userId, username, email, registrationDate, lastLogin, address (nested)
            # Products: productId, name, category, price, stock, description, addedDate
            # Transactions: transactionId, userId, productId, quantity, totalPrice, transactionDate, status, paymentMethod, shippingAddress
            # Feedback: feedbackId, userId, productId, rating, comment, feedbackDate
            # User Activities: activityId, userId, activityType, timestamp, ipAddress, device, searchTerm

            # Ensure transactionDate is datetime for transactions
            if not transactions.empty and 'transactionDate' in transactions.columns:
                transactions['transactionDate'] = pd.to_datetime(transactions['transactionDate'], errors='coerce')
                transactions.dropna(subset=['transactionDate'], inplace=True)
            else:
                logger.warning("Transactions DataFrame is empty or missing 'transactionDate'. Knowledge graph will be limited.")
                self._graph_built = False
                return

            # Ensure necessary user and product data is available
            if users.empty or products.empty:
                logger.warning("Users or Products DataFrame is empty. Knowledge graph will be incomplete.")
                self._graph_built = False
                return
            
            # Map totalPrice to 'amount' for consistency if needed by graph builder
            if 'totalPrice' in transactions.columns and 'amount' not in transactions.columns:
                transactions['amount'] = transactions['totalPrice']
            elif 'amount' not in transactions.columns: # Fallback if totalPrice also missing
                transactions['amount'] = transactions['quantity'] * transactions.get('price', 1.0) # Estimate if price is available

            # Ensure 'price' is available in transactions for graph edge attributes
            if 'price' not in transactions.columns:
                # Derive price from amount and quantity since products don't have a price column
                transactions['price'] = transactions['amount'] / transactions['quantity'].replace(0,1)
                transactions['price'] = pd.to_numeric(transactions['price'], errors='coerce').fillna(0)

            # Ensure 'category' is available in transactions (from product merge or schema) for graph node attributes
            if 'category' not in transactions.columns:
                transactions = transactions.merge(
                    products[['productId', 'category']], on='productId', how='left'
                )
                transactions['category'].fillna('unknown', inplace=True) # Fill missing categories

            # Build the knowledge graph using the prepared data
            build_result = self.knowledge_graph.build_graph_from_data(transactions, products, users)
            
            if build_result['status'] == 'success':
                self._graph_built = True
                self.last_built_time = datetime.utcnow()
                logger.info(f"Knowledge graph built with {build_result.get('nodes', 0)} nodes and {build_result.get('edges', 0)} edges.")
                # Save the graph after successful build
                graph_save_path = os.path.join(self.config.BASE_MODEL_DIR, "knowledge_graph.gml")
                self.knowledge_graph.save_graph(graph_save_path)
                self.kg_graph = build_result.get('graph') # Update in-memory graph reference
            else:
                logger.error(f"Knowledge graph building failed: {build_result['message']}")
                self._graph_built = False
        except Exception as e:
            logger.error(f"Error in building knowledge graph: {e}", exc_info=True)
            self._graph_built = False
            raise

    async def get_customer_insights(
        self, user_id: str, insight_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get comprehensive insights about a customer."""
        if not self._graph_built:
            # Attempt to load from disk if not built in current session (e.g., app restart)
            graph_load_path = os.path.join(self.config.BASE_MODEL_DIR, "knowledge_graph.gml")
            try:
                load_result = self.knowledge_graph.load_graph(graph_load_path)
                if load_result:  # load_graph now returns boolean
                    self._graph_built = True
                    logger.info("Knowledge graph loaded for insights.")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph from disk: {e}. Attempting to build.")
                await self._build_knowledge_graph() # Attempt to build if not loaded
                if not self._graph_built:
                    return {'status': 'error', 'message': 'Knowledge graph not built and cannot be loaded/built.'}

        try:
            insights_result = self.knowledge_graph.get_customer_insights(user_id)
            
            if insights_result['status'] == 'success':
                # Further refine or add meta-insights if needed
                insights = {
                    'user_id': user_id,
                    'customer_profile': insights_result.get('profile', {}),
                    'purchase_history': insights_result.get('purchase_history', []),
                    'similar_customers': insights_result.get('similar_customers', []),
                    'product_recommendations': insights_result.get('graph_recommendations', []), # Use graph recommendations
                    'behavioral_insights': insights_result.get('insights', []), # Textual insights
                    'timestamp': datetime.utcnow().isoformat()
                }
                # Example of adding meta-insights
                profile = insights.get('customer_profile', {})
                total_spent = profile.get('total_spent_lifetime', 0)
                transaction_count = profile.get('total_orders_lifetime', 0)

                meta_insights = []
                if total_spent > 1000 and transaction_count > 5:
                    meta_insights.append("High-value, frequent customer.")
                elif total_spent > 300:
                    meta_insights.append("Mid-value customer with growing engagement.")
                
                if insights['similar_customers']:
                    meta_insights.append(f"Has {len(insights['similar_customers'])} similar customers in the network.")

                insights['meta_insights'] = meta_insights if meta_insights else ["Standard customer profile."]

                return {'status': 'success', 'data': insights}
            else:
                return insights_result # Propagate error from knowledge graph

        except Exception as e:
            logger.error(f"Failed to get customer insights for {user_id}: {e}", exc_info=True)
            raise

    async def get_product_intelligence(
        self, product_id: str, analysis_depth: str = 'comprehensive'
    ) -> Dict[str, Any]:
        """Get comprehensive insights about a product."""
        if not self._graph_built:
            # Attempt to load from disk if not built in current session (e.g., app restart)
            graph_load_path = os.path.join(self.config.BASE_MODEL_DIR, "knowledge_graph.gml")
            try:
                load_result = self.knowledge_graph.load_graph(graph_load_path)
                if load_result:  # load_graph now returns boolean
                    self._graph_built = True
                    logger.info("Knowledge graph loaded for product intelligence.")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph from disk: {e}. Attempting to build.")
                await self._build_knowledge_graph() # Attempt to build if not loaded
                if not self._graph_built:
                    return {'status': 'error', 'message': 'Knowledge graph not built and cannot be loaded/built.'}

        try:
            intelligence_result = self.knowledge_graph.get_product_intelligence(product_id)

            if intelligence_result['status'] == 'success':
                insights = {
                    'product_id': product_id,
                    'product_profile': intelligence_result.get('profile', {}),
                    'purchasing_customers': intelligence_result.get('purchasing_customers', []),
                    'categories': intelligence_result.get('categories', []),
                    'co_purchased_products': intelligence_result.get('co_purchased_products', []),
                    'market_insights': intelligence_result.get('insights', []), # Textual insights
                    'timestamp': datetime.utcnow().isoformat()
                }
                # Example of adding strategic recommendations based on intelligence
                profile = insights.get('product_profile', {})
                total_sales = profile.get('total_sales', 0) # Assuming this attribute is added in KG
                units_sold = profile.get('units_sold', 0) # Assuming this attribute is added in KG

                strategic_recommendations = []
                if total_sales > 10000 or units_sold > 500:
                    strategic_recommendations.append("Promote as a best-seller.")
                    if insights['co_purchased_products']:
                        strategic_recommendations.append("Explore cross-promotions with frequently co-purchased items.")
                elif total_sales < 1000:
                    strategic_recommendations.append("Review pricing strategy.")
                    strategic_recommendations.append("Enhance product description and visibility.")
                
                insights['strategic_recommendations'] = strategic_recommendations
                return {'status': 'success', 'data': insights}
            else:
                return intelligence_result
        except Exception as e:
            logger.error(f"Failed to get product insights for {product_id}: {e}", exc_info=True)
            raise

    async def get_market_intelligence(
        self, market_segment: str = 'overall', time_horizon: str = 'quarterly'
    ) -> Dict[str, Any]:
        """Get market intelligence and trend analysis."""
        if not self._graph_built:
            # Attempt to load from disk if not built in current session (e.g., app restart)
            graph_load_path = os.path.join(self.config.BASE_MODEL_DIR, "knowledge_graph.gml")
            try:
                load_result = self.knowledge_graph.load_graph(graph_load_path)
                if load_result:  # load_graph now returns boolean
                    self._graph_built = True
                    logger.info("Knowledge graph loaded for market intelligence.")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph from disk: {e}. Attempting to build.")
                await self._build_knowledge_graph() # Attempt to build if not loaded
                if not self._graph_built:
                    return {'status': 'error', 'message': 'Knowledge graph not built and cannot be loaded/built.'}

        try:
            # This method would typically aggregate insights from graph data
            # For demonstration, we'll return a simplified structure.
            # Real implementation would involve extensive graph queries and aggregation.
            
            # Example: Analyze overall trends from transactions
            transactions = await self._get_transactions()
            if transactions.empty:
                return {'status': 'error', 'message': 'No transaction data available for market intelligence.'}

            transactions['transactionDate'] = pd.to_datetime(transactions['transactionDate'], errors='coerce')
            transactions.dropna(subset=['transactionDate'], inplace=True)
            
            # Filter by time horizon if specified
            end_date = datetime.utcnow()
            if time_horizon == 'quarterly':
                start_date = end_date - timedelta(days=90)
            elif time_horizon == 'monthly':
                start_date = end_date - timedelta(days=30)
            elif time_horizon == 'yearly':
                start_date = end_date - timedelta(days=365)
            else: # overall
                start_date = transactions['transactionDate'].min()

            filtered_transactions = transactions[transactions['transactionDate'] >= start_date]
            
            if filtered_transactions.empty:
                return {'status': 'info', 'message': 'No transactions in the specified time horizon.', 'data': {}}


            # Category performance (from transactions, assume category is merged)
            category_sales = filtered_transactions.groupby('category')['totalPrice'].sum().to_dict()
            
            # Top products
            top_products = filtered_transactions.groupby('productId')['totalPrice'].sum().nlargest(5).to_dict()

            intelligence = {
                'market_segment': market_segment,
                'time_horizon': time_horizon,
                'trend_analysis': {
                    'overall_revenue': float(filtered_transactions['totalPrice'].sum()),
                    'category_performance': {k: float(v) for k, v in category_sales.items()},
                    'top_products': {k: float(v) for k, v in top_products.items()},
                    'recent_growth_rate': 'N/A' # Placeholder for actual calculation
                },
                'customer_behavior_trends': {
                    'avg_transaction_value': float(filtered_transactions['totalPrice'].mean()),
                    'avg_quantity_per_transaction': float(filtered_transactions['quantity'].mean())
                },
                'growth_opportunities': ["Identify new product categories based on emerging trends.", "Expand into underserved customer segments."],
                'risk_factors': ["Increasing competition.", "Supply chain disruptions."],
                'strategic_recommendations': ["Invest in R&D for innovative products.", "Strengthen customer loyalty programs."],
                'timestamp': datetime.utcnow().isoformat()
            }
            return {'status': 'success', 'data': intelligence}
        except Exception as e:
            logger.error(f"Failed to get market intelligence: {e}", exc_info=True)
            raise

    async def perform_causal_analysis(
        self, target_metric: str, analysis_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Perform causal analysis to understand what drives key metrics."""
        if not self._graph_built:
            # Attempt to load from disk if not built in current session (e.g., app restart)
            graph_load_path = os.path.join(self.config.BASE_MODEL_DIR, "knowledge_graph.gml")
            try:
                load_result = self.knowledge_graph.load_graph(graph_load_path)
                if load_result:  # load_graph now returns boolean
                    self._graph_built = True
                    logger.info("Knowledge graph loaded for causal analysis.")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph from disk: {e}. Attempting to build.")
                await self._build_knowledge_graph() # Attempt to build if not loaded
                if not self._graph_built:
                    return {'status': 'error', 'message': 'Knowledge graph not built and cannot be loaded/built.'}

        try:
            # Causal analysis is complex and often involves specialized libraries (e.g., DoWhy, CausalForest).
            # For this context, we will provide a conceptual output based on common factors
            # and potentially leverage graph relationships for causal paths.
            
            # A real implementation would require a proper causal inference engine
            # and perhaps a defined causal graph structure.
            
            causal_factors = {}
            intervention_recommendations = []

            if target_metric == 'total_revenue':
                # Example: Factors that could cause changes in total revenue
                causal_factors = {
                    'product_price_changes': {'impact': 'positive', 'strength': 'high', 'reason': 'Directly affects sales volume and revenue per unit.'},
                    'marketing_spend_increase': {'impact': 'positive', 'strength': 'medium', 'reason': 'Increases product visibility and customer acquisition.'},
                    'customer_satisfaction_rating': {'impact': 'positive', 'strength': 'medium', 'reason': 'Higher satisfaction leads to repeat purchases and referrals.'},
                    'website_traffic_volume': {'impact': 'positive', 'strength': 'high', 'reason': 'More visitors correlate with more potential transactions.'},
                    'competitor_pricing_strategies': {'impact': 'negative', 'strength': 'high', 'reason': 'Aggressive competitor pricing can draw customers away.'}
                }
                intervention_recommendations = [
                    "Implement A/B testing on pricing strategies to find optimal points.",
                    "Increase investment in targeted digital marketing campaigns.",
                    "Enhance customer support and post-purchase follow-ups to boost satisfaction."
                ]
            elif target_metric == 'customer_churn_rate':
                # Example: Factors influencing churn rate
                causal_factors = {
                    'recency_of_last_purchase': {'impact': 'positive', 'strength': 'high', 'reason': 'Longer inactivity often precedes churn.'}, # Higher recency -> higher churn
                    'negative_feedback_count': {'impact': 'positive', 'strength': 'medium', 'reason': 'Customer dissatisfaction is a strong churn indicator.'},
                    'customer_support_response_time': {'impact': 'negative', 'strength': 'medium', 'reason': 'Faster resolution of issues improves retention.'},
                    'product_return_rate_by_user': {'impact': 'positive', 'strength': 'low', 'reason': 'Frequent returns may indicate dissatisfaction or poor fit.'}
                }
                intervention_recommendations = [
                    "Implement proactive churn prevention campaigns based on inactivity triggers.",
                    "Improve product quality and accurately describe products to reduce returns.",
                    "Optimize customer service workflows for quicker issue resolution."
                ]
            else:
                causal_factors = {"message": f"Causal analysis for metric '{target_metric}' is not pre-defined in this example."}

            return {
                'status': 'success',
                'target_metric': target_metric,
                'causal_factors': causal_factors,
                'intervention_recommendations': intervention_recommendations,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Causal analysis failed for {target_metric}: {e}", exc_info=True)
            raise

    async def get_strategic_recommendations(
        self, business_context: Dict[str, Any], priority_areas: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get high-level strategic recommendations based on comprehensive analysis."""
        if not self._graph_built:
            # Attempt to load from disk if not built in current session (e.g., app restart)
            graph_load_path = os.path.join(self.config.BASE_MODEL_DIR, "knowledge_graph.gml")
            try:
                load_result = self.knowledge_graph.load_graph(graph_load_path)
                if load_result:  # load_graph now returns boolean
                    self._graph_built = True
                    logger.info("Knowledge graph loaded for strategic recommendations.")
            except Exception as e:
                logger.warning(f"Could not load knowledge graph from disk: {e}. Attempting to build.")
                await self._build_knowledge_graph() # Attempt to build if not loaded
                if not self._graph_built:
                    return {'status': 'error', 'message': 'Knowledge graph not built and cannot be loaded/built.'}

        try:
            if priority_areas is None:
                priority_areas = ['revenue_growth', 'customer_retention', 'market_expansion', 'operational_efficiency', 'product_innovation']

            strategic_initiatives = {}
            for area in priority_areas:
                if area == 'revenue_growth':
                    strategic_initiatives[area] = [
                        "Implement dynamic pricing across all product categories to maximize profit margins.",
                        "Launch targeted up-selling and cross-selling campaigns leveraging AI recommendations.",
                        "Explore new monetization models, such as subscription services or premium features.",
                        "Optimize marketing spend by allocating budget to channels with highest ROI based on predictive analytics."
                    ]
                elif area == 'customer_retention':
                    strategic_initiatives[area] = [
                        "Enhance personalized customer engagement strategies, especially for medium/high-risk churn customers.",
                        "Develop a tiered loyalty program with exclusive benefits to reward and retain valuable customers.",
                        "Improve post-purchase customer support and establish robust feedback loops to address dissatisfaction promptly.",
                        "Proactively identify and re-engage dormant customers with tailored incentives."
                    ]
                elif area == 'market_expansion':
                    strategic_initiatives[area] = [
                        "Identify untapped geographic markets or niche customer segments using demographic and behavioral data.",
                        "Introduce new product lines or adapt existing ones based on market intelligence and identified gaps.",
                        "Form strategic partnerships or collaborations to enter new customer segments or distribution channels."
                    ]
                elif area == 'operational_efficiency':
                    strategic_initiatives[area] = [
                        "Automate inventory management and order fulfillment processes using AI-driven forecasts and demand prediction.",
                        "Optimize supply chain logistics with predictive analytics to reduce costs and improve delivery times.",
                        "Streamline customer service workflows with AI-powered chatbots and intelligent routing for common queries.",
                        "Implement anomaly detection in operational data to quickly identify and resolve inefficiencies."
                    ]
                elif area == 'product_innovation':
                    strategic_initiatives[area] = [
                        "Utilize AI to analyze customer feedback and market trends for identifying unmet needs and new product opportunities.",
                        "Develop predictive models for product success based on historical data and market signals.",
                        "Leverage A/B testing and experimentation to rapidly iterate on new product features and designs.",
                        "Integrate explainable AI to understand which product features drive customer satisfaction and sales."
                    ]
                else:
                    strategic_initiatives[area] = [f"No specific initiatives defined for {area} yet."]
            
            # Example of combining insights for overall recommendations based on business context
            overall_recommendations = []
            if business_context.get('ecommerce_platform_stability', True) == False:
                overall_recommendations.append("Prioritize platform stability and performance improvements before aggressively scaling new AI initiatives.")
            if business_context.get('current_market_growth') == 'high':
                overall_recommendations.append("Capitalize on high market growth by accelerating customer acquisition and product launch efforts.")
            if business_context.get('resource_availability') == 'limited':
                overall_recommendations.append("Focus on high-impact, low-cost AI initiatives first to maximize ROI with limited resources.")

            return {
                'status': 'success',
                'business_context': business_context,
                'priority_areas': priority_areas,
                'strategic_initiatives': strategic_initiatives,
                'overall_recommendations': overall_recommendations,
                'timestamp': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to generate strategic recommendations: {e}", exc_info=True)
            raise

    async def query_knowledge_graph(self, query_string: str) -> Dict[str, Any]:
        """Query the knowledge graph with natural language or structured queries."""
        try:
            if not self.kg_graph:
                await self._build_knowledge_graph()
            
            if not self.kg_graph:
                return {
                    'status': 'error',
                    'message': 'Knowledge graph is not available',
                    'results': []
                }
            
            # Simple query processing - in real implementation, this would use NLP
            query_lower = query_string.lower()
            results = []
            
            # Search for entities and relationships based on query keywords
            if 'customer' in query_lower or 'user' in query_lower:
                # Find customer-related nodes
                customer_nodes = [node for node in self.kg_graph.nodes() if 'customer' in str(node).lower()]
                for node in customer_nodes[:5]:  # Limit results
                    neighbors = list(self.kg_graph.neighbors(node))
                    results.append({
                        'entity': str(node),
                        'type': 'customer',
                        'connections': [str(n) for n in neighbors[:3]],
                        'properties': self.kg_graph.nodes[node] if node in self.kg_graph.nodes else {}
                    })
            
            if 'product' in query_lower:
                # Find product-related nodes
                product_nodes = [node for node in self.kg_graph.nodes() if 'product' in str(node).lower()]
                for node in product_nodes[:5]:  # Limit results
                    neighbors = list(self.kg_graph.neighbors(node))
                    results.append({
                        'entity': str(node),
                        'type': 'product',
                        'connections': [str(n) for n in neighbors[:3]],
                        'properties': self.kg_graph.nodes[node] if node in self.kg_graph.nodes else {}
                    })
            
            if 'relationship' in query_lower or 'connection' in query_lower:
                # Find interesting relationships
                edges = list(self.kg_graph.edges(data=True))[:10]
                for edge in edges:
                    results.append({
                        'relationship': f"{edge[0]} -> {edge[1]}",
                        'type': 'relationship',
                        'weight': edge[2].get('weight', 1.0),
                        'properties': edge[2]
                    })
            
            # If no specific results found, return general graph statistics
            if not results:
                results = [{
                    'type': 'graph_stats',
                    'nodes': self.kg_graph.number_of_nodes(),
                    'edges': self.kg_graph.number_of_edges(),
                    'density': nx.density(self.kg_graph),
                    'message': f"Knowledge graph contains {self.kg_graph.number_of_nodes()} entities and {self.kg_graph.number_of_edges()} relationships"
                }]
            
            return {
                'status': 'success',
                'query': query_string,
                'results': results,
                'result_count': len(results)
            }
            
        except Exception as e:
            logger.error(f"Error querying knowledge graph: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e),
                'results': []
            }

    async def build_knowledge_graph(self) -> Dict[str, Any]:
        """Trigger a rebuild of the knowledge graph from raw data."""
        try:
            logger.info("Starting knowledge graph rebuild...")
            
            # Clear existing graph
            self.kg_graph = nx.Graph()
            
            # Rebuild the knowledge graph
            await self._build_knowledge_graph()
            
            # Check if graph was built successfully
            if not self.kg_graph:
                return {
                    'status': 'error',
                    'message': 'Failed to build knowledge graph'
                }
            
            stats = {
                'nodes': self.kg_graph.number_of_nodes(),
                'edges': self.kg_graph.number_of_edges(),
                'density': nx.density(self.kg_graph),
                'components': nx.number_connected_components(self.kg_graph)
            }
            
            logger.info(f"Knowledge graph rebuilt successfully: {stats}")
            
            return {
                'status': 'success',
                'message': 'Knowledge graph rebuilt successfully',
                'statistics': stats
            }
            
        except Exception as e:
            logger.error(f"Error building knowledge graph: {e}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    # Helper methods to fetch data from MongoDB (similar to other services)
    async def _get_users(self) -> pd.DataFrame:
        try:
            users_cursor = self.db.users.find({})
            users_list = await users_cursor.to_list(length=None)
            df = pd.DataFrame(users_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure proper datetime parsing for relevant columns
            if 'registrationDate' in df.columns:
                df['registrationDate'] = pd.to_datetime(df['registrationDate'], errors='coerce')
            if 'lastLogin' in df.columns:
                df['lastLogin'] = pd.to_datetime(df['lastLogin'], errors='coerce')

            logger.info(f"Fetched {len(df)} users for reasoning service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching users for reasoning service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_products(self) -> pd.DataFrame:
        try:
            products_cursor = self.db.products.find({})
            products_list = await products_cursor.to_list(length=None)
            df = pd.DataFrame(products_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure numeric types
            if 'price' in df.columns:
                df['price'] = pd.to_numeric(df['price'], errors='coerce')
            if 'stock' in df.columns:
                df['stock'] = pd.to_numeric(df['stock'], errors='coerce')

            logger.info(f"Fetched {len(df)} products for reasoning service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching products for reasoning service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_transactions(self) -> pd.DataFrame:
        try:
            transactions_cursor = self.db.transactions.find({})
            transactions_list = await transactions_cursor.to_list(length=None)
            df = pd.DataFrame(transactions_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Ensure datetime parsing and numeric types
            if 'transactionDate' in df.columns:
                df['transactionDate'] = pd.to_datetime(df['transactionDate'], errors='coerce')
            if 'totalPrice' in df.columns:
                df['totalPrice'] = pd.to_numeric(df['totalPrice'], errors='coerce')
            if 'quantity' in df.columns:
                df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')

            logger.info(f"Fetched {len(df)} transactions for reasoning service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching transactions for reasoning service: {e}", exc_info=True)
            return pd.DataFrame()
            
    async def _get_feedback(self) -> pd.DataFrame:
        try:
            feedback_cursor = self.db.feedback.find({})
            feedback_list = await feedback_cursor.to_list(length=None)
            df = pd.DataFrame(feedback_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            if 'feedbackDate' in df.columns:
                df['feedbackDate'] = pd.to_datetime(df['feedbackDate'], errors='coerce')
            if 'rating' in df.columns:
                df['rating'] = pd.to_numeric(df['rating'], errors='coerce')

            logger.info(f"Fetched {len(df)} feedback entries for reasoning service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching feedback for reasoning service: {e}", exc_info=True)
            return pd.DataFrame()

    async def _get_activities(self) -> pd.DataFrame:
        try:
            activities_cursor = self.db.user_activities.find({})
            activities_list = await activities_cursor.to_list(length=None)
            df = pd.DataFrame(activities_list)
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            logger.info(f"Fetched {len(df)} activities for reasoning service.")
            return df
        except Exception as e:
            logger.error(f"Error fetching activities for reasoning service: {e}", exc_info=True)
            return pd.DataFrame()

