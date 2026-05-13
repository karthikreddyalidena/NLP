"""
Clustering module: Deep Learning Embeddings + K-Means + DBSCAN.
Identifies semantic clusters using SentenceTransformers.
"""

import numpy as np
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from sklearn.decomposition import PCA
from config import Config
import warnings
warnings.filterwarnings('ignore')

try:
    import torch
    torch.zeros(1)
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except Exception as e:
    print(f"[Warning] SentenceTransformers unavailable: {e}")
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    TFIDF_AVAILABLE = True
except ImportError:
    TFIDF_AVAILABLE = False


class ClusteringEngine:
    """
    Deep Learning clustering using SentenceTransformers + K-Means/DBSCAN.
    """

    def __init__(self, n_clusters=Config.N_CLUSTERS, dbscan_eps=Config.DBSCAN_EPS, dbscan_min_samples=Config.DBSCAN_MIN_SAMPLES):
        self.n_clusters = n_clusters
        self.dbscan_eps = dbscan_eps
        self.dbscan_min_samples = dbscan_min_samples

        self.kmeans = KMeans(
            n_clusters=n_clusters,
            init='k-means++',
            n_init=10,
            max_iter=300,
            random_state=42
        )
        self.dbscan = DBSCAN(
            eps=dbscan_eps,
            min_samples=dbscan_min_samples,
            metric='euclidean'
        )
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=2, random_state=42)
        self.is_fitted = False
        self.cluster_profiles = {}   # per-cluster stats
        self.silhouette = -1.0
        self.davies_bouldin = 99.0
        
        self.model_name = Config.DL_MODEL_EMBEDDING
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            print(f"[Clustering] Loading Embedding model: {self.model_name}")
            try:
                self.embedder = SentenceTransformer(self.model_name)
            except Exception as e:
                print(f"[Clustering] Failed to load embedder: {e}")
                self.embedder = None
        else:
            self.embedder = None
            
        self.tfidf = TfidfVectorizer(max_features=384, stop_words='english') if TFIDF_AVAILABLE else None
        self.tfidf_fitted = False

    def get_embeddings(self, texts: list) -> np.ndarray:
        if self.embedder and texts:
            try:
                return self.embedder.encode(texts, convert_to_numpy=True)
            except Exception:
                pass
                
        # FALLBACK: TF-IDF
        if self.tfidf and texts:
            if not self.tfidf_fitted:
                self.tfidf.fit(texts)
                self.tfidf_fitted = True
            return self.tfidf.transform(texts).toarray()
            
        return np.random.rand(len(texts), 384)

    def fit_kmeans(self, X: np.ndarray) -> np.ndarray:
        """Fit K-Means and return cluster labels."""
        if len(X) < self.n_clusters:
            return np.zeros(len(X), dtype=int)
        X_scaled = self.scaler.fit_transform(X)
        labels = self.kmeans.fit_predict(X_scaled)
        self.is_fitted = True

        if len(set(labels)) > 1:
            try:
                self.silhouette = silhouette_score(X_scaled, labels)
                self.davies_bouldin = davies_bouldin_score(X_scaled, labels)
            except:
                pass
        return labels

    def predict_kmeans(self, X: np.ndarray) -> np.ndarray:
        """Predict cluster for new points."""
        if not self.is_fitted:
            return np.zeros(len(X), dtype=int)
        X_scaled = self.scaler.transform(X)
        return self.kmeans.predict(X_scaled)

    def fit_dbscan(self, coords: np.ndarray) -> np.ndarray:
        """
        Fit DBSCAN on (lat, lon) coordinates scaled for km distance.
        Returns cluster labels (-1 = noise/isolated).
        """
        if len(coords) < self.dbscan_min_samples:
            return np.full(len(coords), -1, dtype=int)
        # Convert degrees to approximate km
        coords_km = coords * np.array([111.0, 85.0])
        labels = self.dbscan.fit_predict(coords_km)
        return labels

    def get_pca_projection(self, X: np.ndarray) -> np.ndarray:
        """Reduce to 2D for visualization."""
        if X.shape[0] < 2:
            return np.zeros((X.shape[0], 2))
        if X.shape[1] > 2:
            return self.pca.fit_transform(X)
        return X

    def compute_cluster_profiles(self, labels: np.ndarray, distress_scores: np.ndarray,
                                  disaster_types: list) -> dict:
        """Compute per-cluster crisis profile statistics."""
        profiles = {}
        unique_labels = set(labels)
        for lbl in unique_labels:
            mask = labels == lbl
            cluster_distress = distress_scores[mask]
            cluster_types = [t for t, m in zip(disaster_types, mask) if m]

            type_counts = {}
            for t in cluster_types:
                type_counts[t] = type_counts.get(t, 0) + 1
            dominant_type = max(type_counts, key=type_counts.get) if type_counts else 'unknown'

            profiles[int(lbl)] = {
                'size': int(mask.sum()),
                'mean_distress': round(float(cluster_distress.mean()), 4) if len(cluster_distress) else 0.0,
                'max_distress': round(float(cluster_distress.max()), 4) if len(cluster_distress) else 0.0,
                'dominant_type': dominant_type,
                'type_distribution': type_counts,
                'crisis_ratio': round(float((cluster_distress > 0.60).mean()), 4) if len(cluster_distress) else 0.0
            }
        self.cluster_profiles = profiles
        return profiles

    def get_crisis_clusters(self, threshold: float = 0.65) -> list:
        """Return cluster IDs exceeding crisis threshold."""
        return [
            cid for cid, prof in self.cluster_profiles.items()
            if prof.get('mean_distress', 0) >= threshold and prof.get('dominant_type', 'normal') != 'normal'
        ]

    def evaluate(self) -> dict:
        return {
            'silhouette_score': round(self.silhouette, 4),
            'davies_bouldin_score': round(self.davies_bouldin, 4),
            'n_clusters': self.n_clusters,
            'is_fitted': self.is_fitted
        }
