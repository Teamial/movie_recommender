"""
Graph-Based Recommendation Demo

Demonstrates the power of knowledge graphs and Node2Vec for movie recommendations.
Shows how the system discovers non-obvious connections through graph structure.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from database import SessionLocal
from models import User, Movie, Rating
from ml.graph_recommender import (
    GRAPH_LEARNING_AVAILABLE,
    MovieKnowledgeGraph,
    Node2VecEmbedder,
    GraphRecommender
)
from ml.recommender import MovieRecommender

import json
from collections import Counter


def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def check_dependencies():
    """Check if graph learning dependencies are available"""
    print_header("1. Checking Dependencies")
    
    if not GRAPH_LEARNING_AVAILABLE:
        print("❌ Graph learning dependencies not available")
        print("\nPlease install:")
        print("  pip install networkx node2vec")
        print("\nOptional (for GNN):")
        print("  pip install torch-geometric")
        return False
    
    print("✅ NetworkX available")
    print("✅ Node2Vec available")
    
    try:
        import torch
        from torch_geometric.nn import SAGEConv
        print("✅ PyTorch Geometric available (GNN support)")
    except ImportError:
        print("⚠️  PyTorch Geometric not available (optional)")
    
    return True


def demo_graph_construction(db):
    """Demonstrate knowledge graph construction"""
    print_header("2. Building Knowledge Graph")
    
    kg = MovieKnowledgeGraph(db)
    
    print("Building graph from database...")
    print("  - Extracting users, movies, actors, directors, genres")
    print("  - Creating edges for ratings, cast, genres")
    
    graph = kg.build_graph(
        max_users=200,      # Small demo graph
        max_movies=500,
        min_interactions=3
    )
    
    print(f"\n✅ Graph built successfully!")
    print(f"   Nodes: {graph.number_of_nodes()}")
    print(f"   Edges: {graph.number_of_edges()}")
    
    # Show node type distribution
    print(f"\n📊 Node Types:")
    node_counts = Counter(kg.node_types.values())
    for node_type, count in node_counts.items():
        print(f"   {node_type.capitalize()}: {count}")
    
    # Show edge type distribution
    print(f"\n🔗 Edge Types:")
    for edge_type, count in kg.edge_types.items():
        print(f"   {edge_type}: {count}")
    
    # Calculate graph statistics
    import networkx as nx
    
    density = nx.density(graph)
    avg_degree = sum(dict(graph.degree()).values()) / graph.number_of_nodes()
    
    print(f"\n📈 Graph Statistics:")
    print(f"   Density: {density:.4f}")
    print(f"   Average degree: {avg_degree:.2f}")
    print(f"   Connected: {nx.is_connected(graph)}")
    
    return kg, graph


def demo_node_embeddings(kg, graph):
    """Demonstrate Node2Vec embedding training"""
    print_header("3. Training Node2Vec Embeddings")
    
    print("Initializing Node2Vec...")
    print("  Parameters:")
    print("    - Dimensions: 64 (embedding size)")
    print("    - Walk length: 20 (steps per walk)")
    print("    - Num walks: 100 (walks per node)")
    print("    - p=1.0, q=1.0 (balanced exploration)")
    
    node2vec = Node2VecEmbedder(
        graph,
        dimensions=64,
        walk_length=20,
        num_walks=100,
        p=1.0,
        q=1.0,
        workers=4
    )
    
    print("\nTraining Skip-Gram model...")
    node2vec.fit(epochs=5)
    
    print(f"\n✅ Embeddings trained!")
    print(f"   Embedding dimension: {node2vec.dimensions}")
    print(f"   Total embeddings: {len(node2vec.embeddings)}")
    
    # Show example embedding
    user_node = list(kg.node_to_id.values())[0]
    emb = node2vec.get_embedding(user_node)
    print(f"\n📐 Example Embedding (first node):")
    print(f"   Shape: {emb.shape}")
    print(f"   Norm: {emb.dot(emb)**0.5:.3f}")
    print(f"   First 5 dims: {emb[:5]}")
    
    return node2vec


def demo_graph_similarity(kg, graph, node2vec):
    """Demonstrate finding similar nodes in graph space"""
    print_header("4. Finding Similar Nodes in Graph Space")
    
    # Pick a movie node
    movie_nodes = [
        (node_id, node_name) 
        for node_name, node_id in kg.node_to_id.items() 
        if node_name.startswith('movie_')
    ]
    
    if len(movie_nodes) < 10:
        print("Not enough movie nodes for demo")
        return
    
    sample_node_id, sample_node_name = movie_nodes[5]
    movie_id = int(sample_node_name.split('_')[1])
    
    # Get the movie
    db = SessionLocal()
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    
    if not movie:
        print("Sample movie not found")
        return
    
    print(f"Finding movies similar to: {movie.title}")
    print(f"  Genres: {movie.genres}")
    
    # Find similar nodes
    similar_nodes = node2vec.get_similar_nodes(sample_node_id, top_k=20)
    
    # Filter to movies only
    similar_movies = [
        (node_id, score) 
        for node_id, score in similar_nodes 
        if kg.node_types.get(node_id) == 'movie'
    ][:5]
    
    print(f"\n🎬 Top 5 Similar Movies (by graph embeddings):")
    for i, (node_id, score) in enumerate(similar_movies, 1):
        node_name = kg.id_to_node[node_id]
        sim_movie_id = int(node_name.split('_')[1])
        sim_movie = db.query(Movie).filter(Movie.id == sim_movie_id).first()
        
        if sim_movie:
            print(f"   {i}. {sim_movie.title} (similarity: {score:.3f})")
            print(f"      Genres: {sim_movie.genres}")
    
    db.close()


def demo_graph_recommendations(db):
    """Demonstrate graph-based recommendations"""
    print_header("5. Graph-Based Recommendations")
    
    # Get a user with ratings
    user = db.query(User).join(Rating).group_by(User.id).first()
    
    if not user:
        print("No users with ratings found")
        return
    
    print(f"Generating recommendations for: {user.username}")
    
    # Show user's rated movies
    ratings = db.query(Rating).filter(Rating.user_id == user.id).order_by(Rating.rating.desc()).limit(5).all()
    
    print(f"\n📝 User's Top Rated Movies:")
    for rating in ratings:
        movie = rating.movie
        print(f"   {movie.title}: {rating.rating}/5.0")
    
    # Initialize graph recommender
    print(f"\n🔄 Generating graph-based recommendations...")
    graph_rec = GraphRecommender(db)
    
    # Build/load graph
    graph_rec.build_or_load_graph()
    
    # Train embeddings
    graph_rec.train_embeddings(dimensions=64)
    
    # Get recommendations
    recommendations = graph_rec.get_graph_recommendations(
        user_id=user.id,
        n_recommendations=10
    )
    
    print(f"\n✅ Graph-Based Recommendations:")
    for i, movie in enumerate(recommendations, 1):
        genres = json.loads(movie.genres) if isinstance(movie.genres, str) else movie.genres
        print(f"   {i}. {movie.title} ({movie.vote_average}/10)")
        print(f"      Genres: {', '.join(genres[:3])}")


def demo_recommendation_explanation(db):
    """Demonstrate recommendation explanations via graph paths"""
    print_header("6. Explaining Recommendations (Graph Paths)")
    
    # Get a user
    user = db.query(User).join(Rating).group_by(User.id).first()
    if not user:
        print("No users found")
        return
    
    # Get a recommended movie
    graph_rec = GraphRecommender(db)
    graph_rec.build_or_load_graph()
    
    recommendations = graph_rec.get_graph_recommendations(user.id, n_recommendations=5)
    
    if not recommendations:
        print("No recommendations found")
        return
    
    movie = recommendations[0]
    
    print(f"Why was '{movie.title}' recommended to {user.username}?")
    
    # Get explanation
    explanation = graph_rec.explain_graph_recommendation(user.id, movie.id)
    
    if 'explanation_paths' in explanation:
        print(f"\n🔍 Connection Paths Found: {explanation['paths_found']}")
        print(f"   Distance: {explanation['distance']} hops")
        
        print(f"\n📍 Example Paths:")
        for i, path in enumerate(explanation['explanation_paths'][:3], 1):
            print(f"   {i}. {path}")
    else:
        print(f"\n⚠️  {explanation.get('explanation', 'No path found')}")


def demo_hybrid_comparison(db):
    """Compare different recommendation strategies"""
    print_header("7. Hybrid Strategy Comparison")
    
    # Get a user
    user = db.query(User).join(Rating).group_by(User.id).first()
    if not user:
        print("No users found")
        return
    
    recommender = MovieRecommender(db)
    
    print(f"Comparing recommendation strategies for: {user.username}\n")
    
    # SVD only
    print("Strategy 1: SVD (Matrix Factorization)")
    svd_recs = recommender.get_svd_recommendations(user.id, n_recommendations=5)
    for i, movie in enumerate(svd_recs, 1):
        print(f"   {i}. {movie.title}")
    
    # Graph only
    print("\nStrategy 2: Graph (Node2Vec)")
    try:
        graph_recs = recommender.get_graph_recommendations(user.id, n_recommendations=5)
        for i, movie in enumerate(graph_recs, 1):
            print(f"   {i}. {movie.title}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # Hybrid (Graph + SVD)
    print("\nStrategy 3: Hybrid (Graph + SVD + Item-CF)")
    hybrid_recs = recommender.get_hybrid_recommendations(
        user.id,
        n_recommendations=5,
        use_graph=True,
        use_context=False
    )
    for i, movie in enumerate(hybrid_recs, 1):
        print(f"   {i}. {movie.title}")
    
    # Check overlap
    svd_ids = {m.id for m in svd_recs}
    graph_ids = {m.id for m in graph_recs} if graph_recs else set()
    hybrid_ids = {m.id for m in hybrid_recs}
    
    print(f"\n📊 Overlap Analysis:")
    print(f"   SVD ∩ Graph: {len(svd_ids & graph_ids)} movies")
    print(f"   SVD ∩ Hybrid: {len(svd_ids & hybrid_ids)} movies")
    print(f"   Graph ∩ Hybrid: {len(graph_ids & hybrid_ids)} movies")
    print(f"   Unique to Hybrid: {len(hybrid_ids - svd_ids - graph_ids)} movies")


def demo_graph_metrics(db):
    """Show comprehensive graph metrics"""
    print_header("8. Graph Quality Metrics")
    
    graph_rec = GraphRecommender(db)
    graph_rec.build_or_load_graph()
    
    metrics = graph_rec.get_graph_metrics()
    
    print("📊 Knowledge Graph Metrics:\n")
    
    print(f"Graph Structure:")
    print(f"   Total nodes: {metrics['total_nodes']}")
    print(f"   Total edges: {metrics['total_edges']}")
    print(f"   Density: {metrics['density']:.4f}")
    print(f"   Avg degree: {metrics['average_degree']:.2f}")
    
    print(f"\nNode Types:")
    for node_type, count in metrics['node_types'].items():
        percentage = (count / metrics['total_nodes']) * 100
        print(f"   {node_type.capitalize()}: {count} ({percentage:.1f}%)")
    
    print(f"\nEdge Types:")
    for edge_type, count in metrics['edge_types'].items():
        percentage = (count / metrics['total_edges']) * 100
        print(f"   {edge_type}: {count} ({percentage:.1f}%)")
    
    print(f"\nEmbeddings:")
    print(f"   Trained: {'Yes' if metrics['embeddings_trained'] else 'No'}")
    if metrics.get('embedding_dimension'):
        print(f"   Dimensions: {metrics['embedding_dimension']}")


def main():
    """Run all demos"""
    print("=" * 70)
    print("  GRAPH-BASED RECOMMENDATION SYSTEM DEMO")
    print("  Showcasing Knowledge Graphs & Node2Vec")
    print("=" * 70)
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Connect to database
    db = SessionLocal()
    
    try:
        # 1. Build knowledge graph
        kg, graph = demo_graph_construction(db)
        
        # 2. Train node embeddings
        node2vec = demo_node_embeddings(kg, graph)
        
        # 3. Find similar nodes
        demo_graph_similarity(kg, graph, node2vec)
        
        # 4. Generate recommendations
        demo_graph_recommendations(db)
        
        # 5. Explain recommendations
        demo_recommendation_explanation(db)
        
        # 6. Compare strategies
        demo_hybrid_comparison(db)
        
        # 7. Show metrics
        demo_graph_metrics(db)
        
        print_header("Demo Complete!")
        print("✅ All demonstrations completed successfully")
        print("\nNext steps:")
        print("  1. Read GRAPH_RECOMMENDATIONS.md for full documentation")
        print("  2. Try graph recommendations in your app")
        print("  3. Monitor performance and A/B test")
        print("  4. Experiment with hybrid weights")
        
    except Exception as e:
        print(f"\n❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
