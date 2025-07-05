import networkx as nx
import pandas as pd
from typing import List, Dict, Any, Tuple, Optional, Union
from datetime import datetime
import numpy as np
import logging

logger = logging.getLogger(__name__)

def create_bipartite_graph(df: pd.DataFrame, left_col: str, right_col: str, edge_attrs: Optional[List[str]] = None) -> nx.Graph:
    """
    Creates a bipartite graph from a DataFrame representing relationships.
    Nodes from `left_col` form one set, `right_col` forms the other.
    Args:
        df: Input DataFrame containing the relationships.
        left_col: Column for the 'left' set of nodes (e.g., 'user_id').
        right_col: Column for the 'right' set of nodes (e.g., 'product_id').
        edge_attrs: List of columns from df to be included as edge attributes.
    Returns:
        A NetworkX bipartite graph.
    """
    G = nx.Graph()
    # Add nodes with 'bipartite' attribute to distinguish the sets
    left_nodes = df[left_col].unique()
    right_nodes = df[right_col].unique()
    G.add_nodes_from(left_nodes, bipartite=0) # Assign 0 to the left set
    G.add_nodes_from(right_nodes, bipartite=1) # Assign 1 to the right set

    # Add edges with attributes
    for idx, row in df.iterrows():
        u = row[left_col]
        v = row[right_col]
        
        # Collect specified edge attributes
        attrs = {}
        if edge_attrs:
            for attr in edge_attrs:
                if attr in row:
                    # Handle potential non-serializable types for attributes if needed
                    val = row[attr]
                    if isinstance(val, (datetime, pd.Timestamp)):
                        attrs[attr] = val.isoformat()
                    elif pd.isna(val):
                        attrs[attr] = None # Handle NaN values
                    else:
                        attrs[attr] = val
                else:
                    attrs[attr] = None # Attribute not found in row

        G.add_edge(u, v, **attrs)
    logger.info(f"Created bipartite graph with {len(left_nodes)} {left_col} nodes and {len(right_nodes)} {right_col} nodes.")
    return G

def project_bipartite_graph(G: nx.Graph, nodes: List[Any], bipartite_set: int = 0) -> nx.Graph:
    """
    Projects a bipartite graph onto one set of nodes. This creates a unipartite graph
    where connections represent shared neighbors in the original bipartite graph.
    Args:
        G: The bipartite graph.
        nodes: A list of nodes from one bipartite set to project onto.
        bipartite_set: 0 for the 'left' set (e.g., users), 1 for the 'right' set (e.g., products).
                       Nodes in the `nodes` list should belong to this set.
    Returns:
        The projected graph.
    """
    if bipartite_set not in [0, 1]:
        raise ValueError("bipartite_set must be 0 or 1.")
    
    # Filter nodes to ensure they belong to the specified bipartite set
    valid_nodes = [n for n in nodes if n in G and G.nodes[n].get('bipartite') == bipartite_set]
    
    if not valid_nodes:
        logger.warning(f"No valid nodes found in the graph for projection for bipartite set {bipartite_set}. Returning empty graph.")
        return nx.Graph()

    # Use networkx's built-in projection
    projected_G = nx.bipartite.projected_graph(G, valid_nodes)
    
    # Add 'weight' to edges based on number of common neighbors (if applicable)
    # This is a common practice for projected graphs
    for u, v, data in projected_G.edges(data=True):
        common_neighbors = len(list(nx.common_neighbors(G, u, v)))
        projected_G.edges[u,v]['weight'] = common_neighbors
        projected_G.edges[u,v]['type'] = 'co_occurrence' # Add a type for clarity

    logger.info(f"Projected graph created with {projected_G.number_of_nodes()} nodes and {projected_G.number_of_edges()} edges.")
    return projected_G

def calculate_graph_metrics(G: Union[nx.Graph, nx.DiGraph]) -> Dict[str, Any]:
    """
    Calculates common graph-theoretic metrics for a given graph.
    Args:
        G: The input NetworkX graph.
    Returns:
        A dictionary of graph metrics.
    """
    if not isinstance(G, (nx.Graph, nx.DiGraph, nx.MultiGraph, nx.MultiDiGraph)):
        logger.error(f"Expected NetworkX graph, got {type(G)}")
        return {"error": "Invalid graph type"}
        
    metrics = {
        "num_nodes": G.number_of_nodes(),
        "num_edges": G.number_of_edges(),
        "is_empty": G.number_of_nodes() == 0,
        "density": nx.density(G) if G.number_of_nodes() > 1 else 0
    }

    if G.number_of_nodes() > 1:
        if nx.is_connected(G):
            metrics["is_connected"] = True
            try: # Try to calculate path length and diameter, can fail for large graphs
                metrics["avg_shortest_path_length"] = nx.average_shortest_path_length(G)
                metrics["diameter"] = nx.diameter(G)
            except (nx.NetworkXError, nx.NetworkXNoPath):
                metrics["avg_shortest_path_length"] = None
                metrics["diameter"] = None
                logger.warning("Could not calculate avg_shortest_path_length or diameter (graph not strongly connected or too large).")
        else:
            metrics["is_connected"] = False
            metrics["num_connected_components"] = nx.number_connected_components(G)
            metrics["largest_component_nodes"] = len(max(nx.connected_components(G), key=len, default=set()))

    # Handle cases for empty graph or single node graph for degree calculations
    if G.number_of_nodes() > 0:
        try:
            # Calculate average degree with type ignore to handle NetworkX typing issues
            degree_list = list(G.degree())  # type: ignore
            if degree_list:
                degrees = [d for n, d in degree_list]
                metrics["avg_degree"] = float(sum(degrees)) / len(degrees)
            else:
                metrics["avg_degree"] = 0.0
            
            if isinstance(G, nx.DiGraph):
                in_degree_list = list(G.in_degree())  # type: ignore
                out_degree_list = list(G.out_degree())  # type: ignore
                
                if in_degree_list:
                    in_degrees = [d for n, d in in_degree_list]
                    metrics["avg_in_degree"] = float(sum(in_degrees)) / len(in_degrees)
                else:
                    metrics["avg_in_degree"] = 0.0
                    
                if out_degree_list:
                    out_degrees = [d for n, d in out_degree_list]
                    metrics["avg_out_degree"] = float(sum(out_degrees)) / len(out_degrees)
                else:
                    metrics["avg_out_degree"] = 0.0
        except Exception as e:
            logger.warning(f"Error calculating degree metrics: {e}")
            metrics["avg_degree"] = 0.0
            if isinstance(G, nx.DiGraph):
                metrics["avg_in_degree"] = 0.0
                metrics["avg_out_degree"] = 0.0
    else:
        metrics["avg_degree"] = 0.0
        if isinstance(G, nx.DiGraph):
            metrics["avg_in_degree"] = 0.0
            metrics["avg_out_degree"] = 0.0

    return metrics

def find_k_shortest_paths(G: nx.Graph, source: Any, target: Any, k: int = 1, weight: Optional[str] = None) -> List[List[Any]]:
    """
    Finds k shortest paths between a source and target node.
    Args:
        G: The graph.
        source: Source node.
        target: Target node.
        k: Number of shortest paths to find.
        weight: Edge attribute to use as weight (e.g., 'distance', 'cost').
    Returns:
        A list of lists, where each inner list is a path.
    """
    try:
        paths = list(nx.shortest_simple_paths(G, source, target, weight=weight))
        return paths[:k]
    except nx.NetworkXNoPath:
        logger.warning(f"No path found between {source} and {target}.")
        return []
    except Exception as e:
        logger.error(f"Error finding shortest paths between {source} and {target}: {str(e)}", exc_info=True)
        return []

def recommend_by_proximity(G: nx.Graph, start_node: Any, max_distance: int = 2) -> List[Any]:
    """
    Recommends nodes based on their proximity in the graph (e.g., "friends of friends" for users,
    or "related products" for products).
    Args:
        G: The graph.
        start_node: The node from which to start recommendations.
        max_distance: Maximum distance (number of hops) from the start_node to consider.
    Returns:
        A list of recommended nodes (excluding the start_node itself and immediate neighbors).
    """
    if start_node not in G:
        logger.warning(f"Start node {start_node} not found in graph. Cannot recommend by proximity.")
        return []

    recommended_nodes = set()
    # Use BFS to find nodes within max_distance
    for node, distance in nx.shortest_path_length(G, source=start_node).items():
        # Exclude the start_node itself and immediate neighbors (distance 1)
        # Recommend nodes at distance > 1 up to max_distance
        if 1 < distance <= max_distance:
            recommended_nodes.add(node)
            
    # Optionally, you can filter out nodes of specific types if the graph contains mixed node types
    # For example, if you want to recommend only 'product_' nodes
    clean_recommendations = [
        str(node).replace('customer_', '').replace('product_', '').replace('category_', '') 
        for node in recommended_nodes
        # if str(node).startswith('product_') # Example: filter for only product recommendations
    ]
    
    return list(set(clean_recommendations)) # Use set to remove duplicates, then convert to list

