import os
import networkx as nx
import pandas as pd
import numpy as np
import gc
from typing import Dict, List, Tuple, Optional, Any
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
import joblib # For saving/loading graph

logger = logging.getLogger(__name__)

class MemoryMonitor:
    """Simple memory monitoring utility"""
    @staticmethod
    def get_memory_usage_mb():
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0
    
    @staticmethod
    def log_memory_usage(operation=""):
        """Log current memory usage"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            logger.info(f"Memory usage {operation}: {memory_mb:.1f} MB")
        except ImportError:
            pass
    
    @staticmethod
    def cleanup_memory():
        """Force garbage collection"""
        gc.collect()
        logger.debug("Forced garbage collection")

class CustomerBehaviorGraph:
    """Knowledge graph for customer behavior analysis and reasoning."""
    
    def __init__(self):
        self.graph = nx.MultiDiGraph() # Use MultiDiGraph to allow multiple edges between nodes (e.g., multiple purchases)
        self.node_attributes = {} # Cache for quick attribute lookup
        self.edge_attributes = {} # Cache for quick attribute lookup
        self._is_built = False # Flag to indicate if graph has been built
        
    def build_graph_from_data(self, transactions: pd.DataFrame, 
                            products: pd.DataFrame, 
                            users: pd.DataFrame) -> Dict:
        """Build knowledge graph from transaction, product, and user data with memory optimization."""
        try:
            logger.info("Building customer behavior knowledge graph...")
            MemoryMonitor.log_memory_usage("before graph building")
            
            # Reset graph before rebuilding
            self.graph = nx.MultiDiGraph()
            self.node_attributes = {}
            self.edge_attributes = {}

            if transactions.empty or products.empty or users.empty:
                logger.warning("One or more input DataFrames are empty. Cannot build graph.")
                self._is_built = False
                return {'status': 'error', 'message': 'Insufficient data to build graph.'}

            # Debug: Log column names to understand data structure
            logger.info(f"Users DataFrame columns: {list(users.columns)}")
            logger.info(f"Products DataFrame columns: {list(products.columns)}")
            logger.info(f"Transactions DataFrame columns: {list(transactions.columns)}")
            logger.info(f"Users shape: {users.shape}, Products shape: {products.shape}, Transactions shape: {transactions.shape}")

            # Limit data size for memory management
            max_users = 5000  # Limit users to prevent memory explosion
            max_transactions = 100000  # Limit transactions
            
            if len(users) > max_users:
                logger.warning(f"Limiting users to {max_users} (found {len(users)}) to manage memory")
                users = users.head(max_users)
            
            if len(transactions) > max_transactions:
                logger.warning(f"Limiting transactions to {max_transactions} (found {len(transactions)}) to manage memory")
                transactions = transactions.head(max_transactions)

            # --- Add Customer Nodes ---
            try:
                for _, user_row in users.iterrows():
                    # Handle both renamed (user_id) and original (userId) column names
                    user_id = user_row.get('user_id') or user_row.get('userId')
                    if user_id is None:
                        logger.warning(f"User row missing user ID: {user_row.to_dict()}")
                        continue
                        
                    attrs = {
                        'type': 'customer',
                        'username': user_row.get('username'),
                        'email': user_row.get('email'),
                        'registrationDate': user_row.get('registrationDate'),
                        'lastLogin': user_row.get('lastLogin'),
                        'country': user_row.get('address', {}).get('country', 'unknown') if isinstance(user_row.get('address'), dict) else 'unknown',
                        'total_spent_lifetime': user_row.get('total_spent', 0), # From data_generator User Schema
                        'total_orders_lifetime': user_row.get('total_orders', 0) # From data_generator User Schema
                    }
                    self.graph.add_node(f"customer_{user_id}", **attrs)
                    self.node_attributes[f"customer_{user_id}"] = attrs
                logger.info(f"Added {len(users)} customer nodes.")
            except Exception as e:
                logger.error(f"Error adding customer nodes: {str(e)}")
                raise
            MemoryMonitor.log_memory_usage("after adding customer nodes")
            
            # --- Add Product Nodes ---
            for _, product_row in products.iterrows():
                # Handle both renamed (product_id) and original (productId) column names
                product_id = product_row.get('product_id') or product_row.get('productId')
                if product_id is None:
                    logger.warning(f"Product row missing product ID: {product_row.to_dict()}")
                    continue
                    
                attrs = {
                    'type': 'product',
                    'name': product_row.get('name'),
                    'category': product_row.get('category'),
                    'price': product_row.get('price'), # This is base price from product schema
                    'stock': product_row.get('stock'),
                    'addedDate': product_row.get('addedDate')
                }
                self.graph.add_node(f"product_{product_id}", **attrs)
                self.node_attributes[f"product_{product_id}"] = attrs
            logger.info(f"Added {len(products)} product nodes.")

            # --- Add Category Nodes (if not implicitly added through products) ---
            # Ensure categories from products are added as distinct nodes
            for category in products['category'].unique():
                attrs = {
                    'type': 'category',
                    'category_name': category
                }
                self.graph.add_node(f"category_{category}", **attrs)
                self.node_attributes[f"category_{category}"] = attrs
            logger.info(f"Added {len(products['category'].unique())} category nodes.")
            
            # --- Add Transaction Nodes and Relationships ---
            # It's good to add transaction nodes if each transaction needs to be a distinct entity
            # and have properties itself. Or, just use them to create direct relationships.
            # For simplicity, we'll create direct relationships for now (user-product)
            # You could add transaction nodes later if needed.

            for _, tx_row in transactions.iterrows():
                # Handle both renamed and original column names
                transaction_id = tx_row.get('transaction_id') or tx_row.get('transactionId')
                user_id = tx_row.get('user_id') or tx_row.get('userId')
                product_id = tx_row.get('product_id') or tx_row.get('productId')
                
                if not all([transaction_id, user_id, product_id]):
                    logger.warning(f"Transaction row missing required IDs: {tx_row.to_dict()}")
                    continue
                
                # Get category from product data
                product_col = 'product_id' if 'product_id' in products.columns else 'productId'
                category = products[products[product_col] == product_id]['category'].iloc[0] if product_id in products[product_col].values else 'unknown'

                customer_node = f"customer_{user_id}"
                product_node = f"product_{product_id}"
                category_node = f"category_{category}"

                # Add nodes if they don't exist (e.g., if transactions have users/products not in initial population)
                if customer_node not in self.graph:
                    self.graph.add_node(customer_node, type='customer', user_id=user_id, status='uninitialized')
                if product_node not in self.graph:
                    self.graph.add_node(product_node, type='product', product_id=product_id, status='uninitialized')
                if category_node not in self.graph:
                    self.graph.add_node(category_node, type='category', category_name=category)
                
                # Purchase relationship: Customer -> Product
                purchase_edge_attrs = {
                    'type': 'PURCHASED',
                    'quantity': tx_row.get('quantity', 0),
                    'amount': tx_row.get('amount') or tx_row.get('totalAmount') or tx_row.get('totalPrice', 0), # Handle renamed columns
                    'timestamp': tx_row.get('timestamp') or tx_row.get('transactionDate'), # Handle renamed columns
                    'status': tx_row.get('status', 'completed'),
                    'transaction_id': transaction_id # Link to the transaction itself
                }
                self.graph.add_edge(customer_node, product_node, key=transaction_id, **purchase_edge_attrs)
                self.edge_attributes[(customer_node, product_node, transaction_id)] = purchase_edge_attrs

                # Belongs_to relationship: Product -> Category
                if not self.graph.has_edge(product_node, category_node, key='belongs_to'): # Avoid duplicate 'belongs_to' edges
                     self.graph.add_edge(product_node, category_node, key='belongs_to', type='BELONGS_TO')

            logger.info(f"Added {len(transactions)} transaction relationships.")
            
            # --- Add Similar-to Relationships (Customers by shared purchases) ---
            self._add_customer_similarity_relationships(transactions)
            logger.info("Added customer similarity relationships.")

            self._is_built = True
            logger.info(f"Knowledge graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
            
            return {
                'status': 'success',
                'nodes': self.graph.number_of_nodes(),
                'edges': self.graph.number_of_edges(),
                'node_types': self._get_node_type_counts(),
                'edge_types': self._get_edge_type_counts()
            }
            
        except Exception as e:
            logger.error(f"Error building knowledge graph: {str(e)}", exc_info=True)
            self._is_built = False
            return {'status': 'error', 'message': str(e)}

    def _add_customer_similarity_relationships(self, transactions: pd.DataFrame, min_shared_products: int = 2, max_customers: int = 1000):
        """
        Memory-optimized version that limits similarity calculations to prevent RAM overload.
        Only processes the most active customers to reduce memory usage.
        """
        # Create a mapping of user to the set of products they purchased
        user_products = defaultdict(set)
        for _, tx_row in transactions.iterrows():
            # Handle both renamed and original column names
            user_id = tx_row.get('user_id') or tx_row.get('userId')
            product_id = tx_row.get('product_id') or tx_row.get('productId')
            
            if user_id and product_id:
                user_products[user_id].add(product_id)

        # Limit to most active customers to reduce memory usage
        customer_activity = [(user_id, len(products)) for user_id, products in user_products.items()]
        customer_activity.sort(key=lambda x: x[1], reverse=True)  # Sort by activity
        
        # Limit customers processed for similarity
        limited_customers = [user_id for user_id, _ in customer_activity[:max_customers]]
        logger.info(f"Processing similarity for top {len(limited_customers)} active customers (out of {len(customer_activity)} total)")
        
        similarity_count = 0
        max_similarities = 10000  # Limit total similarity edges to prevent memory explosion
        
        # Process in batches to avoid memory issues
        batch_size = 100
        for i in range(0, len(limited_customers), batch_size):
            batch_customers = limited_customers[i:i + batch_size]
            
            for idx1, user1_id in enumerate(batch_customers):
                # Only compare with remaining customers in current batch and some future customers
                compare_with = batch_customers[idx1 + 1:] + limited_customers[i + batch_size:i + batch_size + 50]
                
                for user2_id in compare_with:
                    if similarity_count >= max_similarities:
                        logger.info(f"Reached maximum similarity relationships ({max_similarities}), stopping...")
                        return
                    
                    products1 = user_products[user1_id]
                    products2 = user_products[user2_id]
                    
                    shared_products = products1.intersection(products2)
                    
                    if len(shared_products) >= min_shared_products:
                        # Calculate Jaccard similarity as strength of similarity
                        union_products = products1.union(products2)
                        similarity_score = len(shared_products) / len(union_products) if len(union_products) > 0 else 0
                        
                        if similarity_score > 0.2:  # Increased threshold to reduce edges
                            edge_attrs = {
                                'type': 'SIMILAR_TO',
                                'similarity_score': similarity_score,
                                'shared_product_count': len(shared_products)
                            }
                            # Add a non-directional edge for similarity
                            self.graph.add_edge(f"customer_{user1_id}", f"customer_{user2_id}", **edge_attrs)
                            similarity_count += 1
            
            # Clear batch data to save memory
            del batch_customers
            
            # Log progress
            if i % (batch_size * 5) == 0:
                logger.info(f"Processed similarity batch {i//batch_size + 1}/{(len(limited_customers) + batch_size - 1)//batch_size}")
        
        logger.info(f"Added {similarity_count} similarity relationships")

    def get_customer_insights(self, user_id: str) -> Dict:
        """Get comprehensive insights for a specific customer from the graph."""
        if not self._is_built:
            return {'status': 'error', 'message': 'Knowledge graph not built. Please build it first.'}

        customer_node = f"customer_{user_id}"
        if customer_node not in self.graph:
            return {'status': 'error', 'message': f'Customer {user_id} not found in graph.'}
        
        try:
            # Basic customer profile from node attributes
            customer_profile = self.graph.nodes[customer_node]

            # Purchase history (products purchased by this customer)
            purchase_history = []
            for u, v, k, data in self.graph.edges(customer_node, data=True, keys=True):
                if data.get('type') == 'PURCHASED':
                    purchase_history.append({
                        'transactionId': k, # The key for multi-edge (transaction ID)
                        'product_id': v.replace('product_', ''),
                        'quantity': data.get('quantity'),
                        'totalPrice': data.get('amount') or data.get('totalPrice', 0), # Handle both column names
                        'transactionDate': data.get('timestamp') or data.get('transactionDate')
                    })
            
            # Find similar customers
            similar_customers = []
            for u, v, data in self.graph.edges(customer_node, data=True):
                if data.get('type') == 'SIMILAR_TO' and v.startswith('customer_'):
                    similar_customers.append({
                        'userId': v.replace('customer_', ''),
                        'similarity_score': data.get('similarity_score')
                    })
            
            # Products frequently bought together (by this user, or by similar users)
            # This is more complex, typically needs a separate recommendation logic or graph projection
            frequently_bought_together = self._get_frequently_bought_together(user_id)
            
            # Recommendations based on graph traversal (e.g., from similar customers or co-purchased patterns)
            graph_recommendations = self._recommend_products_from_graph(user_id)

            return {
                'status': 'success',
                'user_id': user_id,
                'profile': customer_profile,
                'purchase_history': purchase_history,
                'similar_customers': similar_customers,
                'frequently_bought_together': frequently_bought_together,
                'graph_recommendations': graph_recommendations,
                'insights': self._generate_customer_insights_text(customer_profile, purchase_history)
            }
        except Exception as e:
            logger.error(f"Error getting customer insights for {user_id}: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def _get_frequently_bought_together(self, user_id: str, top_n: int = 5) -> List[Dict]:
        """
        Identifies products frequently bought together by the given user.
        This is a simplified approach, a more robust one uses market basket analysis.
        """
        customer_node = f"customer_{user_id}"
        if customer_node not in self.graph:
            return []

        purchased_products = set()
        for u, v, data in self.graph.edges(customer_node, data=True):
            if data.get('type') == 'PURCHASED' and v.startswith('product_'):
                purchased_products.add(v)
        
        co_purchase_counts = defaultdict(int)
        for prod1_node in purchased_products:
            # Find all users who bought prod1
            for u, v, data in self.graph.in_edges(prod1_node, data=True):
                if data.get('type') == 'PURCHASED':
                    customer_of_prod1 = u
                    # Find other products bought by this user
                    for u2, v2, data2 in self.graph.edges(customer_of_prod1, data=True):
                        if data2.get('type') == 'PURCHASED' and v2.startswith('product_') and v2 != prod1_node:
                            co_purchase_counts[v2] += 1
                            
        sorted_co_purchased = sorted(co_purchase_counts.items(), key=lambda item: item[1], reverse=True)
        
        result = []
        for product_node, count in sorted_co_purchased[:top_n]:
            product_id = product_node.replace('product_', '')
            product_attrs = self.graph.nodes.get(product_node, {})
            result.append({
                'product_id': product_id,
                'name': product_attrs.get('name'),
                'category': product_attrs.get('category'),
                'co_purchase_count': count
            })
        return result

    def _recommend_products_from_graph(self, user_id: str, top_n: int = 5) -> List[Dict]:
        """
        Generates product recommendations for a user based on similar customers' purchases.
        """
        customer_node = f"customer_{user_id}"
        if customer_node not in self.graph:
            return []
        
        # Get products already purchased by the user
        user_purchased_products = {v for u, v, data in self.graph.edges(customer_node, data=True) if data.get('type') == 'PURCHASED'}

        # Aggregate products from similar customers
        product_scores = defaultdict(float)
        for u, v, data in self.graph.edges(customer_node, data=True):
            if data.get('type') == 'SIMILAR_TO' and v.startswith('customer_'):
                similar_customer_node = v
                similarity_score = data.get('similarity_score', 0)
                
                # Iterate through products purchased by the similar customer
                for u2, v2, data2 in self.graph.edges(similar_customer_node, data=True):
                    if data2.get('type') == 'PURCHASED' and v2.startswith('product_') and v2 not in user_purchased_products:
                        product_node = v2
                        # Score by similarity * transaction total (or some other metric)
                        amount = data2.get('amount') or data2.get('totalPrice', 1.0)
                        product_scores[product_node] += similarity_score * amount
        
        sorted_recommendations = sorted(product_scores.items(), key=lambda item: item[1], reverse=True)
        
        recommendations = []
        for product_node, score in sorted_recommendations[:top_n]:
            product_id = product_node.replace('product_', '')
            product_attrs = self.graph.nodes.get(product_node, {})
            recommendations.append({
                'product_id': product_id,
                'name': product_attrs.get('name'),
                'category': product_attrs.get('category'),
                'score': score
            })
        return recommendations

    def _generate_customer_insights_text(self, profile: Dict, purchase_history: List) -> List[str]:
        """Generates human-readable insights based on customer profile and purchase history."""
        insights = []
        
        # Engagement insights
        if profile.get('total_orders_lifetime', 0) > 10 and profile.get('total_spent_lifetime', 0) > 500:
            insights.append("This is a high-value and frequent customer.")
        elif profile.get('total_orders_lifetime', 0) > 3:
            insights.append("This customer shows good engagement with multiple purchases.")
        else:
            insights.append("This customer is relatively new or has made few purchases.")
            
        # Recency insight
        if profile.get('lastLogin') and isinstance(profile['lastLogin'], datetime):
            days_since_last_login = (datetime.now() - profile['lastLogin']).days
            if days_since_last_login > 30:
                insights.append(f"Last logged in {days_since_last_login} days ago, potentially becoming inactive.")
            elif days_since_last_login < 7:
                insights.append("Recently active, showing good current engagement.")
        
        # Product category preference (from overall purchase history)
        if purchase_history:
            df_history = pd.DataFrame(purchase_history)
            if not df_history.empty and 'category' in df_history.columns:
                most_bought_category = df_history['category'].mode().iloc[0] if not df_history['category'].mode().empty else None
                if most_bought_category:
                    insights.append(f"Shows a strong preference for products in the '{most_bought_category}' category.")
            
        return insights if insights else ["Standard customer profile, no specific patterns identified yet."]


    def get_product_intelligence(self, product_id: str) -> Dict:
        """Get intelligence on a specific product from the graph."""
        if not self._is_built:
            return {'status': 'error', 'message': 'Knowledge graph not built. Please build it first.'}

        product_node = f"product_{product_id}"
        if product_node not in self.graph:
            return {'status': 'error', 'message': f'Product {product_id} not found in graph.'}
        
        try:
            # Basic product profile from node attributes
            product_profile = self.graph.nodes[product_node]

            # Customers who purchased this product
            purchasing_customers = []
            for u, v, k, data in self.graph.edges(data=True, keys=True):
                if v == product_node and data.get('type') == 'PURCHASED':
                    purchasing_customers.append({
                        'userId': u.replace('customer_', ''),
                        'quantity': data.get('quantity'),
                        'totalPrice': data.get('amount') or data.get('totalPrice', 0), # Handle both column names
                        'transactionDate': data.get('timestamp') or data.get('transactionDate'),
                        'transactionId': k
                    })
            
            # Categories this product belongs to
            categories_belonging_to = []
            for u, v, data in self.graph.edges(data=True):
                if u == product_node and data.get('type') == 'BELONGS_TO':
                    categories_belonging_to.append(v.replace('category_', ''))

            # Products frequently bought together with this product
            co_purchased_products = self._get_frequently_bought_together_product(product_id)

            return {
                'status': 'success',
                'product_id': product_id,
                'profile': product_profile,
                'purchasing_customers': purchasing_customers,
                'categories': categories_belonging_to,
                'co_purchased_products': co_purchased_products,
                'insights': self._generate_product_insights_text(product_profile, purchasing_customers)
            }
        except Exception as e:
            logger.error(f"Error getting product intelligence for {product_id}: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}

    def _get_frequently_bought_together_product(self, product_id: str, top_n: int = 5) -> List[Dict]:
        """Identifies products frequently co-purchased with the given product."""
        product_node = f"product_{product_id}"
        if product_node not in self.graph:
            return []

        co_purchase_counts = defaultdict(int)
        
        # Find all customers who bought the product_id
        customers_who_bought = {u for u, v, data in self.graph.in_edges(product_node, data=True) if data.get('type') == 'PURCHASED'}
        
        # For each customer, find other products they bought
        for customer_node in customers_who_bought:
            for u, v, data in self.graph.out_edges(customer_node, data=True):
                if data.get('type') == 'PURCHASED' and v.startswith('product_') and v != product_node:
                    co_purchase_counts[v] += 1
        
        sorted_co_purchased = sorted(co_purchase_counts.items(), key=lambda item: item[1], reverse=True)
        
        result = []
        for co_product_node, count in sorted_co_purchased[:top_n]:
            co_product_id = co_product_node.replace('product_', '')
            co_product_attrs = self.graph.nodes.get(co_product_node, {})
            result.append({
                'product_id': co_product_id,
                'name': co_product_attrs.get('name'),
                'category': co_product_attrs.get('category'),
                'co_purchase_count': count
            })
        return result

    def _generate_product_insights_text(self, profile: Dict, purchasing_customers: List) -> List[str]:
        """Generates human-readable insights for a product."""
        insights = []
        
        total_units_sold = sum(p.get('quantity', 0) for p in purchasing_customers)
        total_revenue = sum(p.get('totalPrice', 0) for p in purchasing_customers)  # Already handled above
        unique_buyers = len({p['userId'] for p in purchasing_customers})
        
        if total_units_sold > 100:
            insights.append(f"This product is a strong seller with {total_units_sold} units sold.")
        if total_revenue > 5000:
            insights.append(f"It generates significant revenue, totaling ${total_revenue:.2f}.")
        if unique_buyers > 50:
            insights.append(f"The product has broad appeal, purchased by {unique_buyers} unique customers.")
        
        category = profile.get('category')
        if category:
            insights.append(f"It belongs to the '{category}' category, a key segment.")
            
        if profile.get('stock') is not None and profile['stock'] < 20:
            insights.append(f"Current stock is low ({profile['stock']} units), consider restocking soon.")
            
        if profile.get('rating') is not None and profile['rating'] >= 4.0:
            insights.append(f"High customer satisfaction with an average rating of {profile['rating']}.")
            
        return insights if insights else ["Standard product performance."]

    def get_graph_summary(self) -> Dict:
        """Get summary statistics of the knowledge graph."""
        if not self._is_built:
            return {'status': 'error', 'message': 'Knowledge graph not built. Please build it first.'}
        try:
            return {
                'status': 'success',
                'node_count': self.graph.number_of_nodes(),
                'edge_count': self.graph.number_of_edges(),
                'node_types': self._get_node_type_counts(),
                'edge_types': self._get_edge_type_counts(),
                'graph_density': nx.density(self.graph) if self.graph.number_of_nodes() > 1 else 0
            }
        except Exception as e:
            logger.error(f"Error getting graph summary: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
            
    def _get_node_type_counts(self) -> Dict:
        """Helper to count nodes by type."""
        counts = defaultdict(int)
        for node, attrs in self.graph.nodes(data=True):
            counts[attrs.get('type', 'unknown')] += 1
        return dict(counts)
        
    def _get_edge_type_counts(self) -> Dict:
        """Helper to count edges by type."""
        counts = defaultdict(int)
        for u, v, key, attrs in self.graph.edges(data=True, keys=True):
            counts[attrs.get('type', 'unknown')] += 1
        return dict(counts)
        
    def save_graph(self, path: str = 'models/knowledge_graph.gml'):
        """Save the knowledge graph to a file."""
        if not self._is_built:
            logger.warning("Graph not built, cannot save.")
            return {'status': 'error', 'message': 'Graph not built.'}
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            
            # Create a copy of the graph and convert all non-string attributes to strings
            graph_copy = self.graph.copy()
            
            def convert_to_string(value):
                """Convert any value to a string that's safe for GML serialization."""
                if isinstance(value, str):
                    return value
                elif hasattr(value, 'isoformat'):  # datetime/timestamp objects
                    return value.isoformat()
                elif isinstance(value, (pd.Timestamp, pd.Timedelta)):
                    return str(value)
                elif isinstance(value, (int, float)):
                    return str(value)
                elif value is None:
                    return "None"
                else:
                    return str(value)
            
            # Convert node attributes
            for node, data in graph_copy.nodes(data=True):
                for key, value in list(data.items()):
                    data[key] = convert_to_string(value)
                        
            # Convert edge attributes
            for u, v, data in graph_copy.edges(data=True):
                for attr_key, value in list(data.items()):
                    data[attr_key] = convert_to_string(value)
            
            nx.write_gml(graph_copy, path)
            logger.info(f"Knowledge graph saved to {path}")
            return {'status': 'success', 'path': path}
        except Exception as e:
            logger.error(f"Error saving knowledge graph: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': str(e)}
            
    def load_graph(self, path: str = 'models/saved_models/knowledge_graph.gml'):
        """Load the knowledge graph from a file."""
        try:
            if not os.path.exists(path):
                logger.warning(f"Knowledge graph file not found at {path}. Will attempt to rebuild on next request.")
                self._is_built = False
                return False

            self.graph = nx.read_gml(path)
            # Re-populate node and edge attributes cache for easier access if needed
            self.node_attributes = {node: data for node, data in self.graph.nodes(data=True)}
            self.edge_attributes = {(u, v, k): data for u, v, k, data in self.graph.edges(data=True, keys=True)} # Include key for MultiDiGraph
            self._is_built = True
            logger.info(f"Knowledge graph loaded from {path}")
            return True
        except Exception as e:
            logger.warning(f"Could not load knowledge graph from {path}: {e}")
            self._is_built = False
            return False

class ReasoningEngine:
    """Cognitive reasoning engine for business intelligence."""
    
    def __init__(self):
        self.knowledge_graph = CustomerBehaviorGraph()
        self.rules = self._load_business_rules()
    
    def _load_business_rules(self) -> Dict:
        """Load business rules for reasoning."""
        return {
            'churn_risk_rules': [
                {'condition': 'recency_days > 60', 'risk_level': 'high', 'reason': 'Long time since last purchase'},
                {'condition': 'frequency < 3', 'risk_level': 'medium', 'reason': 'Low purchase frequency'},
                {'condition': 'avg_order_value < 30', 'risk_level': 'low', 'reason': 'Low average order value'},
            ],
            'pricing_rules': [
                {'condition': 'demand_ratio > 1.5', 'action': 'increase_price', 'factor': 1.1},
                {'condition': 'inventory_turnover > 2', 'action': 'discount', 'factor': 0.9},
                {'condition': 'competitive_index < -1', 'action': 'premium_pricing', 'factor': 1.15},
            ],
            'recommendation_rules': [
                {'condition': 'customer_lifetime_value > 1000', 'strategy': 'premium_products'},
                {'condition': 'purchase_frequency > 10', 'strategy': 'loyalty_rewards'},
                {'condition': 'category_diversity > 3', 'strategy': 'cross_sell'},
            ]
        }
    
    def analyze_customer_journey(self, customer_id: str, transactions: pd.DataFrame) -> Dict:
        """Analyze and reason about customer journey."""
        try:
            customer_data = transactions[transactions['user_id'] == customer_id].copy()
            customer_data = customer_data.sort_values('timestamp')
            
            if customer_data.empty:
                return {'status': 'error', 'message': 'No data found for customer'}
            
            journey_stages = []
            
            # Analyze transaction patterns
            for i, (_, transaction) in enumerate(customer_data.iterrows()):
                if i == 0:
                    stage = 'first_purchase'
                elif i < 3:
                    stage = 'exploration'
                elif customer_data[:i+1]['amount'].sum() > 500:
                    stage = 'loyal_customer'
                else:
                    stage = 'regular_customer'
                
                journey_stages.append({
                    'transaction_id': transaction.get('transaction_id', f'tx_{i}'),
                    'stage': stage,
                    'category': transaction.get('category', 'unknown'),
                    'amount': transaction.get('amount', 0),
                    'timestamp': transaction.get('timestamp')
                })
            
            # Reasoning about journey
            insights = self._reason_about_journey(journey_stages, customer_data)
            
            # Predict next best action
            next_action = self._predict_next_action(customer_data)
            
            return {
                'status': 'success',
                'customer_id': customer_id,
                'journey_stages': journey_stages,
                'insights': insights,
                'next_action': next_action,
                'customer_summary': {
                    'total_spent': customer_data['amount'].sum(),
                    'transaction_count': len(customer_data),
                    'avg_order_value': customer_data['amount'].mean(),
                    'categories_purchased': customer_data['category'].nunique() if 'category' in customer_data.columns else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing customer journey: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _reason_about_journey(self, journey_stages: List[Dict], customer_data: pd.DataFrame) -> List[str]:
        """Generate reasoning about customer journey."""
        insights = []
        
        # Journey progression analysis
        stages = [stage['stage'] for stage in journey_stages]
        
        if 'loyal_customer' in stages:
            insights.append("Customer has progressed to loyal status with high-value purchases")
        
        if len(set(stage['category'] for stage in journey_stages)) > 2:
            insights.append("Customer shows cross-category exploration behavior")
        
        # Purchase pattern analysis
        amounts = [stage['amount'] for stage in journey_stages]
        if len(amounts) > 1:
            trend = np.polyfit(range(len(amounts)), amounts, 1)[0]
            if trend > 0:
                insights.append("Increasing purchase value trend indicates growing engagement")
            elif trend < -5:
                insights.append("Declining purchase values may indicate disengagement risk")
        
        # Frequency analysis
        if len(journey_stages) > 5:
            insights.append("High purchase frequency indicates strong engagement")
        elif len(journey_stages) < 3:
            insights.append("Low purchase frequency suggests potential churn risk")
        
        return insights
    
    def _predict_next_action(self, customer_data: pd.DataFrame) -> Dict:
        """Predict next best action for customer."""
        total_spent = customer_data['amount'].sum()
        transaction_count = len(customer_data)
        last_category = customer_data['category'].iloc[-1] if 'category' in customer_data.columns and not customer_data.empty else 'unknown'
        
        # Rule-based next action prediction
        if total_spent > 1000 and transaction_count > 10:
            action = {
                'type': 'premium_offer',
                'description': 'Offer premium products or VIP status',
                'expected_impact': 'Increase customer lifetime value'
            }
        elif transaction_count < 3:
            action = {
                'type': 'onboarding_campaign',
                'description': 'Send targeted onboarding emails with product recommendations',
                'expected_impact': 'Increase engagement and repeat purchases'
            }
        else:
            action = {
                'type': 'cross_sell',
                'description': f'Recommend products from categories other than {last_category}',
                'expected_impact': 'Increase order value and category diversity'
            }
        
        return action
    
    def generate_business_insights(self, data: pd.DataFrame) -> Dict:
        """Generate comprehensive business insights using reasoning."""
        try:
            insights = {
                'revenue_insights': self._analyze_revenue_patterns(data),
                'customer_insights': self._analyze_customer_behavior(data),
                'product_insights': self._analyze_product_performance(data),
                'operational_insights': self._analyze_operational_metrics(data)
            }
            
            # Meta-insights (insights about insights)
            meta_insights = self._generate_meta_insights(insights)
            insights['meta_insights'] = meta_insights  # type: ignore
            
            return {'status': 'success', 'insights': insights}
            
        except Exception as e:
            logger.error(f"Error generating business insights: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _analyze_revenue_patterns(self, data: pd.DataFrame) -> Dict:
        """Analyze revenue patterns with reasoning."""
        if data.empty or 'amount' not in data.columns:
            return {'error': 'No revenue data available'}
            
        daily_revenue = data.groupby(data['timestamp'].dt.date)['amount'].sum()
        
        # Trend analysis
        x = np.arange(len(daily_revenue))
        trend = float(np.polyfit(x, daily_revenue.values.astype(float), 1)[0]) if len(daily_revenue) > 1 else 0.0
        
        # Seasonality detection
        peak_day = None
        if len(daily_revenue) >= 7:
            weekly_pattern = data.groupby(data['timestamp'].dt.dayofweek)['amount'].mean()
            peak_day = weekly_pattern.idxmax()
            
        insights = {
            'total_revenue': data['amount'].sum(),
            'avg_daily_revenue': daily_revenue.mean(),
            'revenue_trend': 'increasing' if trend > 0 else 'decreasing',
            'trend_strength': abs(trend),
            'peak_day': peak_day,
            'revenue_volatility': daily_revenue.std() / daily_revenue.mean() if daily_revenue.mean() > 0 else 0
        }
        
        return insights
    
    def _analyze_customer_behavior(self, data: pd.DataFrame) -> Dict:
        """Analyze customer behavior patterns."""
        if data.empty or 'user_id' not in data.columns:
            return {'error': 'No customer data available'}
            
        customer_metrics = data.groupby('user_id').agg({
            'amount': ['sum', 'mean', 'count'],
            'category': 'nunique' if 'category' in data.columns else lambda x: 1,
            'timestamp': lambda x: (x.max() - x.min()).days
        }).round(2)
        
        customer_metrics.columns = ['total_spent', 'avg_order_value', 'frequency', 'categories', 'lifetime_days']
        
        insights = {
            'total_customers': len(customer_metrics),
            'avg_customer_value': customer_metrics['total_spent'].mean(),
            'avg_order_value': customer_metrics['avg_order_value'].mean(),
            'avg_purchase_frequency': customer_metrics['frequency'].mean(),
            'high_value_customers': len(customer_metrics[customer_metrics['total_spent'] > customer_metrics['total_spent'].quantile(0.8)]),
            'cross_category_shoppers': len(customer_metrics[customer_metrics['categories'] > 1]),
            'customer_retention_risk': len(customer_metrics[customer_metrics['frequency'] < 3])
        }
        
        return insights
    
    def _analyze_product_performance(self, data: pd.DataFrame) -> Dict:
        """Analyze product performance with reasoning."""
        if data.empty or 'product_id' not in data.columns:
            return {'error': 'No product data available'}
            
        product_metrics = data.groupby('product_id').agg({
            'amount': ['sum', 'mean'],
            'quantity': 'sum' if 'quantity' in data.columns else lambda x: len(x),
            'user_id': 'nunique'
        }).round(2)
        
        product_metrics.columns = ['total_revenue', 'avg_price', 'units_sold', 'unique_customers']
        
        # Category performance
        category_metrics = {}
        if 'category' in data.columns:
            category_metrics = data.groupby('category').agg({
                'amount': 'sum',
                'product_id': 'nunique',
                'user_id': 'nunique'
            }).round(2)
        
        insights = {
            'total_products': len(product_metrics),
            'best_selling_product': product_metrics['total_revenue'].idxmax() if not product_metrics.empty else None,
            'most_popular_product': product_metrics['unique_customers'].idxmax() if not product_metrics.empty else None,
            'top_category': category_metrics['amount'].idxmax() if len(category_metrics) > 0 else None,
            'category_diversity': len(category_metrics),
            'avg_products_per_category': len(product_metrics) / len(category_metrics) if len(category_metrics) > 0 else 0,
            'underperforming_products': len(product_metrics[product_metrics['unique_customers'] < 2])
        }
        
        return insights
    
    def _analyze_operational_metrics(self, data: pd.DataFrame) -> Dict:
        """Analyze operational metrics."""
        if data.empty:
            return {'error': 'No operational data available'}
            
        # Time-based analysis
        hourly_sales = data.groupby(data['timestamp'].dt.hour)['amount'].sum()
        daily_sales = data.groupby(data['timestamp'].dt.dayofweek)['amount'].sum()
        
        insights = {
            'peak_hour': hourly_sales.idxmax() if not hourly_sales.empty else None,
            'peak_day': daily_sales.idxmax() if not daily_sales.empty else None,
            'avg_transaction_value': data['amount'].mean(),
            'transaction_volume': len(data),
            'sales_concentration': (data['amount'].quantile(0.8) - data['amount'].quantile(0.2)) / data['amount'].mean() if data['amount'].mean() > 0 else 0
        }
        
        return insights
    
    def _generate_meta_insights(self, insights: Dict) -> List[str]:
        """Generate high-level insights about the business."""
        meta_insights = []
        
        revenue = insights.get('revenue_insights', {})
        customers = insights.get('customer_insights', {})
        products = insights.get('product_insights', {})
        
        # Business health assessment
        if revenue.get('revenue_trend') == 'increasing' and customers.get('avg_customer_value', 0) > 100:
            meta_insights.append("Business shows strong growth with increasing revenue and healthy customer values")
        
        # Customer portfolio analysis
        total_customers = customers.get('total_customers', 1)
        high_value_customers = customers.get('high_value_customers', 0)
        if high_value_customers / total_customers > 0.2:
            meta_insights.append("Strong high-value customer segment indicates good market positioning")
        
        # Product portfolio insights
        if products.get('category_diversity', 0) > 5:
            meta_insights.append("Diverse product portfolio reduces market risk")
        
        # Operational efficiency
        customer_retention_risk = customers.get('customer_retention_risk', 0)
        if customer_retention_risk / total_customers > 0.3:
            meta_insights.append("High customer retention risk requires immediate attention to engagement strategies")
        
        return meta_insights

