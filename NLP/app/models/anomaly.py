"""
Anomaly Detection: Isolation Forest + Local Outlier Factor.
Detects statistically unusual spikes in social media data
(volume, sentiment, keyword frequency) that signal crisis events.
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class AnomalyDetector:
    """
    Dual-engine anomaly detection:
    - Isolation Forest: tree-based, fast, global anomalies
    - LOF: density-based, local neighborhood anomalies
    Ensemble vote for final anomaly decision.
    """

    def __init__(self, contamination=0.05):
        self.contamination = contamination
        self.isolation_forest = IsolationForest(
            n_estimators=200,
            contamination=contamination,
            max_samples='auto',
            random_state=42,
            warm_start=False
        )
        self.lof = LocalOutlierFactor(
            n_neighbors=20,
            contamination=contamination,
            novelty=True,        # enable predict() on new data
            metric='euclidean'
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        self.anomaly_history = []
        self.threshold_if = 0.0    # decision function threshold
        self.threshold_lof = 0.0

    def _build_feature_vector(self, tweets_data: list) -> np.ndarray:
        """
        Build feature matrix from tweet statistics.
        Features: [distress_score, disaster_kw_score, retweets_log,
                   likes_log, followers_log, caps_ratio, exclamation,
                   is_urgent, textblob_subjectivity, vader_negative]
        """
        rows = []
        for d in tweets_data:
            sentiment = d.get('sentiment', {})
            row = [
                float(sentiment.get('distress_score', 0)),
                float(sentiment.get('disaster_keyword_score', 0)),
                np.log1p(float(d.get('retweets', 0))),
                np.log1p(float(d.get('likes', 0))),
                np.log1p(float(d.get('followers', 100))),
                float(sentiment.get('textblob_subjectivity', 0.5)),
                float(sentiment.get('vader_negative', 0)),
                float(1 if sentiment.get('is_urgent', False) else 0),
                float(len(d.get('text', '').split())),
                float(d.get('text', '').count('!'))
            ]
            rows.append(row)
        return np.array(rows, dtype=np.float32)

    def fit(self, tweets_data: list):
        """Fit both anomaly detectors on a batch of tweets."""
        if len(tweets_data) < 20:
            return self
        X = self._build_feature_vector(tweets_data)
        X_scaled = self.scaler.fit_transform(X)

        try:
            self.isolation_forest.fit(X_scaled)
            self.lof.fit(X_scaled)
            self.is_fitted = True
        except Exception as e:
            pass
        return self

    def predict(self, tweets_data: list) -> np.ndarray:
        """
        Returns anomaly scores per tweet.
        Score > 0 = anomaly (crisis signal).
        """
        if not self.is_fitted or not tweets_data:
            return np.zeros(len(tweets_data))

        X = self._build_feature_vector(tweets_data)
        X_scaled = self.scaler.transform(X)

        try:
            # Isolation Forest: score_samples returns negative → negate for anomaly score
            if_scores = -self.isolation_forest.score_samples(X_scaled)
            # LOF: decision_function < 0 is anomaly
            lof_raw = -self.lof.decision_function(X_scaled)
            lof_scores = np.clip(lof_raw, 0, None)

            # Normalize both to [0,1]
            def normalize(arr):
                mn, mx = arr.min(), arr.max()
                if mx - mn < 1e-8:
                    return np.zeros_like(arr)
                return (arr - mn) / (mx - mn)

            if_norm = normalize(if_scores)
            lof_norm = normalize(lof_scores)

            # Weighted ensemble: IF slightly stronger
            anomaly_scores = 0.55 * if_norm + 0.45 * lof_norm
            return anomaly_scores
        except Exception:
            return np.zeros(len(tweets_data))

    def detect_volume_anomaly(self, counts: list, window: int = 10) -> dict:
        """
        Detect anomaly in tweet volume time series.
        Uses Z-score on rolling window.
        """
        if len(counts) < window:
            return {'is_anomaly': False, 'z_score': 0.0, 'current': 0, 'baseline': 0}

        recent = counts[-window:]
        baseline = np.mean(counts[:-window]) if len(counts) > window else np.mean(counts)
        std = np.std(counts) + 1e-8
        z = (counts[-1] - baseline) / std

        return {
            'is_anomaly': bool(abs(z) > 2.5),
            'z_score': round(float(z), 3),
            'current': int(counts[-1]),
            'baseline': round(float(baseline), 1),
            'direction': 'spike' if z > 0 else 'drop'
        }

    def get_top_anomalies(self, tweets_data: list, scores: np.ndarray, top_n: int = 5) -> list:
        """Return the N most anomalous tweets."""
        if not tweets_data or scores is None or len(scores) == 0:
            return []
        ranked = sorted(
            zip(scores, tweets_data),
            key=lambda x: x[0],
            reverse=True
        )[:top_n]
        return [
            {**tweet, 'anomaly_score': round(float(score), 4)}
            for score, tweet in ranked
        ]

    def evaluate(self) -> dict:
        return {
            'n_estimators': 200,
            'contamination': self.contamination,
            'is_fitted': self.is_fitted,
            'algorithm': 'Isolation Forest + LOF Ensemble'
        }
