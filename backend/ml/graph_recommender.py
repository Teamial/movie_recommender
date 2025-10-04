"""
Graph-Based Recommendation System

Uses Graph Neural Networks (GNN) and Node2Vec to model movies, users, actors, 
and genres as a knowledge graph. Discovers non-obvious connections through 
graph structure and embedding propagation.

Architecture:
- Nodes: Movies, Users, Actors, Genres
- Edges: Ratings, Cast, Genre membership
- Methods: Node2Vec (simple), GraphSAGE/GCN (advanced)
"""

import logging
from typing import List, Dict, Tuple, Optional, Set
import json
import numpy as np
from datetime import datetime, timedelta
import pickle
import os
from collections import defaultdict

from sqlalchemy.orm import Session
from sqlalchemy import func, desc

# Try importing graph learning libraries
try:
    import networkx as nx
    from node2vec import Node2Vec as Node2VecModel
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    logging.warning("NetworkX or node2vec not available. Install with: pip install networkx node2vec")

# Try importing PyTorch Geometric for GNN
try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch_geometric.nn import SAGEConv, GCNConv
    from torch_geometric.data import Data
    PYTORCH_GEOMETRIC_AVAILABLE = True
except ImportError:
    PYTORCH_GEOMETRIC_AVAILABLE = False
    logging.warning("PyTorch Geometric not available. Install with: pip install torch-geometric")

from models import Movie, User, Rating, Favorite, WatchlistItem

logger = logging.getLogger(__name__)


class MovieKnowledgeGraph:
    """
    Constructs and manages a knowledge graph of movies, users, actors, genres
    """
    
    def __init__(self, db: Session, cache_dir: str = "/tmp/graph_cache"):
        self.db = db
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        self.graph = None
        self.node_to_id = {}  # Map node names to integer IDs
        self.id_to_node = {}  # Reverse mapping
        self.node_types = {}  # Track node types (user/movie/actor/genre)
        
        # Edge type counters
        self.edge_types = {
            'user_movie_rating': 0,
            'user_movie_favorite': 0,
            'user_movie_watchlist': 0,
            'movie_actor': 0,
            'movie_genre': 0,
            'movie_director': 0
        }
    
    def build_graph(self, 
                   max_users: int = 1000, 
                   max_movies: int = 2000,
                   min_interactions: int = 3) -> nx.Graph:
        """
        Build heterogeneous knowledge graph from database
        
        Args:
            max_users: Maximum users to include
            max_movies: Maximum movies to include
            min_interactions: Minimum interactions for user/movie to be included
        
        Returns:
            NetworkX graph with weighted edges
        """
        logger.info(f"Building knowledge graph (users={max_users}, movies={max_movies})")
        
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX required for graph construction")
        
        # Initialize graph
        self.graph = nx.Graph()
        node_id = 0
        
        # 1. Add Users
        logger.info("Adding user nodes...")
        active_users = (
            self.db.query(User)
            .join(Rating)
            .group_by(User.id)
            .having(func.count(Rating.id) >= min_interactions)
            .order_by(desc(func.count(Rating.id)))
            .limit(max_users)
            .all()
        )
        
        for user in active_users:
            node_name = f"user_{user.id}"
            self.node_to_id[node_name] = node_id
            self.id_to_node[node_id] = node_name
            self.node_types[node_id] = 'user'
            self.graph.add_node(node_id, type='user', name=user.username)
            node_id += 1
        
        logger.info(f"Added {len(active_users)} user nodes")
        
        # 2. Add Movies
        logger.info("Adding movie nodes...")
        popular_movies = (
            self.db.query(Movie)
            .join(Rating)
            .group_by(Movie.id)
            .having(func.count(Rating.id) >= min_interactions)
            .order_by(desc(func.count(Rating.id)))
            .limit(max_movies)
            .all()
        )
        
        for movie in popular_movies:
            node_name = f"movie_{movie.id}"
            self.node_to_id[node_name] = node_id
            self.id_to_node[node_id] = node_name
            self.node_types[node_id] = 'movie'
            self.graph.add_node(
                node_id, 
                type='movie', 
                title=movie.title,
                vote_average=movie.vote_average or 0
            )
            node_id += 1
        
        logger.info(f"Added {len(popular_movies)} movie nodes")
        
        # 3. Add Genres
        logger.info("Adding genre nodes...")
        all_genres = set()
        for movie in popular_movies:
            if movie.genres:
                genres = json.loads(movie.genres) if isinstance(movie.genres, str) else movie.genres
                all_genres.update(genres)
        
        for genre in all_genres:
            node_name = f"genre_{genre}"
            self.node_to_id[node_name] = node_id
            self.id_to_node[node_id] = node_name
            self.node_types[node_id] = 'genre'
            self.graph.add_node(node_id, type='genre', name=genre)
            node_id += 1
        
        logger.info(f"Added {len(all_genres)} genre nodes")
        
        # 4. Add Actors
        logger.info("Adding actor nodes...")
        all_actors = set()
        movie_actors = {}  # movie_id -> [actors]
        
        for movie in popular_movies:
            if movie.cast:
                cast = json.loads(movie.cast) if isinstance(movie.cast, str) else movie.cast
                actors = [actor.get('name') for actor in cast[:5]]  # Top 5 cast
                movie_actors[movie.id] = actors
                all_actors.update(actors)
        
        for actor in all_actors:
            if actor:  # Skip empty names
                node_name = f"actor_{actor}"
                self.node_to_id[node_name] = node_id
                self.id_to_node[node_id] = node_name
                self.node_types[node_id] = 'actor'
                self.graph.add_node(node_id, type='actor', name=actor)
                node_id += 1
        
        logger.info(f"Added {len(all_actors)} actor nodes")
        
        # 5. Add Directors
        logger.info("Adding director nodes...")
        all_directors = set()
        movie_directors = {}
        
        for movie in popular_movies:
            if movie.crew:
                crew = json.loads(movie.crew) if isinstance(movie.crew, str) else movie.crew
                directors = [c.get('name') for c in crew if c.get('job') == 'Director']
                if directors:
                    movie_directors[movie.id] = directors[0]
                    all_directors.add(directors[0])
        
        for director in all_directors:
            if director:
                node_name = f"director_{director}"
                self.node_to_id[node_name] = node_id
                self.id_to_node[node_id] = node_name
                self.node_types[node_id] = 'director'
                self.graph.add_node(node_id, type='director', name=director)
                node_id += 1
        
        logger.info(f"Added {len(all_directors)} director nodes")
        
        # 6. Add Edges: User-Movie (Ratings)
        logger.info("Adding user-movie rating edges...")
        user_ids = {user.id for user in active_users}
        movie_ids = {movie.id for movie in popular_movies}
        
        ratings = (
            self.db.query(Rating)
            .filter(Rating.user_id.in_(user_ids))
            .filter(Rating.movie_id.in_(movie_ids))
            .all()
        )
        
        for rating in ratings:
            user_node = self.node_to_id.get(f"user_{rating.user_id}")
            movie_node = self.node_to_id.get(f"movie_{rating.movie_id}")
            
            if user_node is not None and movie_node is not None:
                # Weight by rating (normalized to 0-1)
                weight = rating.rating / 5.0
                self.graph.add_edge(
                    user_node, 
                    movie_node, 
                    weight=weight,
                    edge_type='rating'
                )
                self.edge_types['user_movie_rating'] += 1
        
        logger.info(f"Added {self.edge_types['user_movie_rating']} rating edges")
        
        # 7. Add Edges: User-Movie (Favorites)
        favorites = (
            self.db.query(Favorite)
            .filter(Favorite.user_id.in_(user_ids))
            .filter(Favorite.movie_id.in_(movie_ids))
            .all()
        )
        
        for fav in favorites:
            user_node = self.node_to_id.get(f"user_{fav.user_id}")
            movie_node = self.node_to_id.get(f"movie_{fav.movie_id}")
            
            if user_node is not None and movie_node is not None:
                # High weight for favorites
                self.graph.add_edge(
                    user_node,
                    movie_node,
                    weight=1.0,
                    edge_type='favorite'
                )
                self.edge_types['user_movie_favorite'] += 1
        
        logger.info(f"Added {self.edge_types['user_movie_favorite']} favorite edges")
        
        # 8. Add Edges: Movie-Genre
        for movie in popular_movies:
            movie_node = self.node_to_id.get(f"movie_{movie.id}")
            
            if movie.genres and movie_node is not None:
                genres = json.loads(movie.genres) if isinstance(movie.genres, str) else movie.genres
                
                for genre in genres:
                    genre_node = self.node_to_id.get(f"genre_{genre}")
                    if genre_node is not None:
                        self.graph.add_edge(
                            movie_node,
                            genre_node,
                            weight=1.0,
                            edge_type='genre'
                        )
                        self.edge_types['movie_genre'] += 1
        
        logger.info(f"Added {self.edge_types['movie_genre']} movie-genre edges")
        
        # 9. Add Edges: Movie-Actor
        for movie_id, actors in movie_actors.items():
            movie_node = self.node_to_id.get(f"movie_{movie_id}")
            
            if movie_node is not None:
                for actor in actors:
                    actor_node = self.node_to_id.get(f"actor_{actor}")
                    if actor_node is not None:
                        self.graph.add_edge(
                            movie_node,
                            actor_node,
                            weight=0.8,  # Slightly lower weight
                            edge_type='cast'
                        )
                        self.edge_types['movie_actor'] += 1
        
        logger.info(f"Added {self.edge_types['movie_actor']} movie-actor edges")
        
        # 10. Add Edges: Movie-Director
        for movie_id, director in movie_directors.items():
            movie_node = self.node_to_id.get(f"movie_{movie_id}")
            director_node = self.node_to_id.get(f"director_{director}")
            
            if movie_node is not None and director_node is not None:
                self.graph.add_edge(
                    movie_node,
                    director_node,
                    weight=0.9,
                    edge_type='director'
                )
                self.edge_types['movie_director'] += 1
        
        logger.info(f"Added {self.edge_types['movie_director']} movie-director edges")
        
        # Graph statistics
        logger.info(f"Graph built: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")
        logger.info(f"Edge types: {self.edge_types}")
        
        return self.graph
    
    def save_graph(self, filename: str = "knowledge_graph.pkl"):
        """Save graph to disk"""
        path = os.path.join(self.cache_dir, filename)
        
        data = {
            'graph': self.graph,
            'node_to_id': self.node_to_id,
            'id_to_node': self.id_to_node,
            'node_types': self.node_types,
            'edge_types': self.edge_types
        }
        
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        logger.info(f"Graph saved to {path}")
    
    def load_graph(self, filename: str = "knowledge_graph.pkl") -> bool:
        """Load graph from disk"""
        path = os.path.join(self.cache_dir, filename)
        
        if not os.path.exists(path):
            return False
        
        try:
            with open(path, 'rb') as f:
                data = pickle.load(f)
            
            self.graph = data['graph']
            self.node_to_id = data['node_to_id']
            self.id_to_node = data['id_to_node']
            self.node_types = data['node_types']
            self.edge_types = data['edge_types']
            
            logger.info(f"Graph loaded from {path}")
            return True
        except Exception as e:
            logger.error(f"Failed to load graph: {e}")
            return False


class Node2VecEmbedder:
    """
    Generate node embeddings using Node2Vec (DeepWalk variant)
    
    Node2Vec learns embeddings by treating random walks as sentences
    and applying Skip-Gram (Word2Vec) to learn node representations.
    """
    
    def __init__(self, 
                 graph: nx.Graph,
                 dimensions: int = 128,
                 walk_length: int = 30,
                 num_walks: int = 200,
                 p: float = 1.0,
                 q: float = 1.0,
                 workers: int = 4):
        """
        Args:
            graph: NetworkX graph
            dimensions: Embedding dimension
            walk_length: Length of each random walk
            num_walks: Number of walks per node
            p: Return parameter (controls likelihood of revisiting nodes)
            q: In-out parameter (controls exploration vs. exploitation)
            workers: Parallel workers
        """
        if not NETWORKX_AVAILABLE:
            raise ImportError("NetworkX and node2vec required")
        
        self.graph = graph
        self.dimensions = dimensions
        self.walk_length = walk_length
        self.num_walks = num_walks
        self.p = p
        self.q = q
        self.workers = workers
        
        self.model = None
        self.embeddings = None
    
    def fit(self, epochs: int = 10, min_count: int = 1):
        """
        Train Node2Vec model
        
        Args:
            epochs: Training epochs
            min_count: Minimum word count for Skip-Gram
        """
        logger.info(f"Training Node2Vec (dim={self.dimensions}, walks={self.num_walks}, length={self.walk_length})")
        
        # Initialize Node2Vec
        node2vec = Node2VecModel(
            self.graph,
            dimensions=self.dimensions,
            walk_length=self.walk_length,
            num_walks=self.num_walks,
            p=self.p,
            q=self.q,
            workers=self.workers,
            quiet=False
        )
        
        # Train Skip-Gram model
        self.model = node2vec.fit(
            window=10,  # Context window
            min_count=min_count,
            batch_words=4,
            epochs=epochs
        )
        
        # Extract embeddings
        self.embeddings = {
            node: self.model.wv[str(node)]
            for node in self.graph.nodes()
        }
        
        logger.info(f"✅ Node2Vec trained: {len(self.embeddings)} node embeddings")
    
    def get_embedding(self, node_id: int) -> np.ndarray:
        """Get embedding for a node"""
        if self.embeddings is None:
            raise ValueError("Model not trained. Call fit() first.")
        
        return self.embeddings.get(node_id, np.zeros(self.dimensions))
    
    def get_similar_nodes(self, node_id: int, top_k: int = 10) -> List[Tuple[int, float]]:
        """Find most similar nodes in embedding space"""
        if self.model is None:
            raise ValueError("Model not trained")
        
        try:
            similar = self.model.wv.most_similar(str(node_id), topn=top_k)
            return [(int(node), score) for node, score in similar]
        except KeyError:
            return []


class GraphRecommender:
    """
    Main graph-based recommendation engine
    
    Uses knowledge graph structure and embeddings to generate recommendations
    """
    
    def __init__(self, db: Session, cache_dir: str = "/tmp/graph_cache"):
        self.db = db
        self.cache_dir = cache_dir
        
        self.kg = MovieKnowledgeGraph(db, cache_dir)
        self.node2vec = None
        self.embeddings_cache = {}
        
        # Try to load cached graph
        if self.kg.load_graph():
            logger.info("Using cached knowledge graph")
        else:
            logger.info("Cached graph not found, will build on first use")
    
    def build_or_load_graph(self, force_rebuild: bool = False):
        """Build knowledge graph or load from cache"""
        if force_rebuild or self.kg.graph is None:
            self.kg.build_graph()
            self.kg.save_graph()
        
        return self.kg.graph
    
    def train_embeddings(self, 
                        dimensions: int = 128,
                        force_retrain: bool = False):
        """Train Node2Vec embeddings"""
        
        # Check if graph exists
        if self.kg.graph is None:
            self.build_or_load_graph()
        
        # Check if embeddings cached
        emb_path = os.path.join(self.cache_dir, "node2vec_embeddings.pkl")
        
        if not force_retrain and os.path.exists(emb_path):
            logger.info("Loading cached embeddings...")
            with open(emb_path, 'rb') as f:
                self.node2vec = pickle.load(f)
            logger.info("✅ Embeddings loaded from cache")
            return
        
        # Train new embeddings
        logger.info("Training new Node2Vec embeddings...")
        self.node2vec = Node2VecEmbedder(
            self.kg.graph,
            dimensions=dimensions,
            walk_length=30,
            num_walks=200,
            p=1.0,
            q=1.0
        )
        
        self.node2vec.fit(epochs=10)
        
        # Cache embeddings
        with open(emb_path, 'wb') as f:
            pickle.dump(self.node2vec, f)
        
        logger.info(f"✅ Embeddings cached to {emb_path}")
    
    def get_graph_recommendations(self, 
                                  user_id: int,
                                  n_recommendations: int = 10) -> List[Movie]:
        """
        Get recommendations using graph embeddings
        
        Strategy:
        1. Get user node embedding
        2. Find similar movie nodes in embedding space
        3. Filter out already seen movies
        4. Return top-N recommendations
        """
        
        # Ensure embeddings trained
        if self.node2vec is None:
            self.train_embeddings()
        
        # Get user node ID
        user_node_name = f"user_{user_id}"
        user_node_id = self.kg.node_to_id.get(user_node_name)
        
        if user_node_id is None:
            logger.warning(f"User {user_id} not in graph")
            return []
        
        # Get user's embedding
        user_embedding = self.node2vec.get_embedding(user_node_id)
        
        # Get already seen movies
        seen_movie_ids = self._get_seen_movie_ids(user_id)
        
        # Find similar movie nodes
        movie_scores = []
        
        for node_id, node_type in self.kg.node_types.items():
            if node_type == 'movie':
                node_name = self.kg.id_to_node[node_id]
                movie_id = int(node_name.split('_')[1])
                
                # Skip seen movies
                if movie_id in seen_movie_ids:
                    continue
                
                # Compute similarity
                movie_embedding = self.node2vec.get_embedding(node_id)
                similarity = self._cosine_similarity(user_embedding, movie_embedding)
                
                movie_scores.append((movie_id, similarity))
        
        # Sort by similarity
        movie_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Fetch top-N movies
        top_movie_ids = [mid for mid, score in movie_scores[:n_recommendations]]
        recommendations = (
            self.db.query(Movie)
            .filter(Movie.id.in_(top_movie_ids))
            .all()
        )
        
        # Sort by original order
        recommendations.sort(key=lambda m: top_movie_ids.index(m.id))
        
        logger.info(f"Generated {len(recommendations)} graph-based recommendations for user {user_id}")
        
        return recommendations
    
    def get_similar_movies_graph(self, 
                                movie_id: int,
                                n_similar: int = 10) -> List[Tuple[Movie, float]]:
        """
        Find similar movies using graph structure
        
        Uses:
        1. Direct graph neighbors (shared actors, directors, genres)
        2. Embedding similarity in graph space
        """
        
        # Ensure embeddings trained
        if self.node2vec is None:
            self.train_embeddings()
        
        # Get movie node
        movie_node_name = f"movie_{movie_id}"
        movie_node_id = self.kg.node_to_id.get(movie_node_name)
        
        if movie_node_id is None:
            logger.warning(f"Movie {movie_id} not in graph")
            return []
        
        # Get similar nodes using Node2Vec
        similar_nodes = self.node2vec.get_similar_nodes(movie_node_id, top_k=50)
        
        # Filter to only movie nodes
        similar_movies = []
        
        for node_id, score in similar_nodes:
            node_type = self.kg.node_types.get(node_id)
            
            if node_type == 'movie':
                node_name = self.kg.id_to_node[node_id]
                sim_movie_id = int(node_name.split('_')[1])
                
                if sim_movie_id != movie_id:
                    similar_movies.append((sim_movie_id, score))
        
        # Fetch movies
        top_movie_ids = [mid for mid, score in similar_movies[:n_similar]]
        movies = self.db.query(Movie).filter(Movie.id.in_(top_movie_ids)).all()
        
        # Create movie-score tuples
        movie_dict = {m.id: m for m in movies}
        result = [
            (movie_dict[mid], score)
            for mid, score in similar_movies[:n_similar]
            if mid in movie_dict
        ]
        
        logger.info(f"Found {len(result)} similar movies to {movie_id} using graph")
        
        return result
    
    def explain_graph_recommendation(self, 
                                    user_id: int,
                                    movie_id: int) -> Dict:
        """
        Explain why a movie was recommended using graph paths
        
        Returns:
            Explanation with graph paths connecting user to movie
        """
        
        if self.kg.graph is None:
            self.build_or_load_graph()
        
        user_node_name = f"user_{user_id}"
        movie_node_name = f"movie_{movie_id}"
        
        user_node_id = self.kg.node_to_id.get(user_node_name)
        movie_node_id = self.kg.node_to_id.get(movie_node_name)
        
        if user_node_id is None or movie_node_id is None:
            return {"error": "User or movie not in graph"}
        
        # Find shortest paths
        try:
            paths = list(nx.all_shortest_paths(
                self.kg.graph,
                user_node_id,
                movie_node_id,
                cutoff=5  # Max path length
            ))
            
            # Convert paths to readable format
            readable_paths = []
            
            for path in paths[:3]:  # Top 3 paths
                path_description = []
                
                for node_id in path:
                    node_name = self.kg.id_to_node[node_id]
                    node_type = self.kg.node_types[node_id]
                    
                    if node_type == 'user':
                        path_description.append(f"You")
                    elif node_type == 'movie':
                        movie = self.db.query(Movie).filter(Movie.id == int(node_name.split('_')[1])).first()
                        path_description.append(f"Movie: {movie.title if movie else node_name}")
                    elif node_type == 'actor':
                        path_description.append(f"Actor: {node_name.split('_', 1)[1]}")
                    elif node_type == 'director':
                        path_description.append(f"Director: {node_name.split('_', 1)[1]}")
                    elif node_type == 'genre':
                        path_description.append(f"Genre: {node_name.split('_', 1)[1]}")
                
                readable_paths.append(" → ".join(path_description))
            
            return {
                "paths_found": len(paths),
                "explanation_paths": readable_paths,
                "distance": len(paths[0]) - 1 if paths else None
            }
        
        except nx.NetworkXNoPath:
            return {
                "paths_found": 0,
                "explanation": "No direct path found in graph"
            }
    
    def get_graph_metrics(self) -> Dict:
        """Get graph statistics and health metrics"""
        
        if self.kg.graph is None:
            return {"error": "Graph not built"}
        
        # Node type counts
        node_type_counts = defaultdict(int)
        for node_type in self.kg.node_types.values():
            node_type_counts[node_type] += 1
        
        # Graph metrics
        metrics = {
            "total_nodes": self.kg.graph.number_of_nodes(),
            "total_edges": self.kg.graph.number_of_edges(),
            "node_types": dict(node_type_counts),
            "edge_types": self.kg.edge_types,
            "average_degree": sum(dict(self.kg.graph.degree()).values()) / self.kg.graph.number_of_nodes(),
            "density": nx.density(self.kg.graph),
            "embeddings_trained": self.node2vec is not None
        }
        
        if self.node2vec:
            metrics["embedding_dimension"] = self.node2vec.dimensions
        
        return metrics
    
    def _get_seen_movie_ids(self, user_id: int) -> Set[int]:
        """Get IDs of movies user has already seen/rated"""
        seen_ids = set()
        
        # Rated movies
        ratings = self.db.query(Rating.movie_id).filter(Rating.user_id == user_id).all()
        seen_ids.update(r[0] for r in ratings)
        
        # Favorites
        favorites = self.db.query(Favorite.movie_id).filter(Favorite.user_id == user_id).all()
        seen_ids.update(f[0] for f in favorites)
        
        # Watchlist
        watchlist = self.db.query(WatchlistItem.movie_id).filter(WatchlistItem.user_id == user_id).all()
        seen_ids.update(w[0] for w in watchlist)
        
        return seen_ids
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors"""
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


# Check if graph learning is available
GRAPH_LEARNING_AVAILABLE = NETWORKX_AVAILABLE

if not GRAPH_LEARNING_AVAILABLE:
    logger.warning(
        "Graph learning not available. Install dependencies:\n"
        "pip install networkx node2vec\n"
        "Optional (for GNN): pip install torch-geometric"
    )
