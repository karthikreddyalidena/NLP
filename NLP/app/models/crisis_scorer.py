"""
Crisis Scoring Engine — Composite threat assessment.
Combines clustering, anomaly, sentiment, keyword, volume, and
geographic spread signals into a single crisis score [0, 1].
Generates structured alerts with severity levels.
"""

import numpy as np
from datetime import datetime
import uuid
from config import Config


SEVERITY_LEVELS = {
    'CRITICAL': {'min': 0.90, 'color': '#FF0000', 'icon': '🚨', 'action': 'IMMEDIATE RESPONSE'},
    'HIGH':     {'min': 0.75, 'color': '#FF6600', 'icon': '⚠️',  'action': 'PRIORITIZE RESPONSE'},
    'MODERATE': {'min': 0.55, 'color': '#FFB300', 'icon': '⚡',  'action': 'MONITOR CLOSELY'},
    'LOW':      {'min': 0.30, 'color': '#2196F3', 'icon': 'ℹ️',  'action': 'OBSERVE'},
    'NONE':     {'min': 0.00, 'color': '#4CAF50', 'icon': '✅',  'action': 'NO ACTION'}
}


class CrisisScorer:
    """
    Weighted composite crisis index using 6 signals:
      w1 * sentiment_distress   (0.25)
      w2 * anomaly_score        (0.25)
      w3 * cluster_crisis_ratio (0.20)
      w4 * keyword_density      (0.15)
      w5 * volume_spike         (0.10)
      w6 * engagement_signal    (0.05)
    """

    WEIGHTS = {
        'sentiment': 0.25,
        'anomaly': 0.25,
        'cluster': 0.20,
        'keyword': 0.15,
        'volume': 0.10,
        'engagement': 0.05
    }

    def __init__(self):
        self.alert_history = []
        self.last_alert_time = {}
        self.score_history = []
        self.total_alerts = {'CRITICAL': 0, 'HIGH': 0, 'MODERATE': 0, 'LOW': 0}

    def compute_score(self,
                      mean_distress: float,
                      anomaly_scores: np.ndarray,
                      cluster_crisis_ratio: float,
                      keyword_density: float,
                      volume_z_score: float,
                      mean_engagement: float) -> dict:
        """Compute composite crisis score."""
        s1 = float(np.clip(mean_distress, 0, 1))
        s2 = float(np.clip(anomaly_scores.mean() if len(anomaly_scores) > 0 else 0, 0, 1))
        s3 = float(np.clip(cluster_crisis_ratio, 0, 1))
        s4 = float(np.clip(keyword_density, 0, 1))
        s5 = float(np.clip(abs(volume_z_score) / 5.0, 0, 1))  # z > 5 = max
        s6 = float(np.clip(mean_engagement / 1000.0, 0, 1))   # engagement saturation

        w = self.WEIGHTS
        score = (
            w['sentiment']   * s1 +
            w['anomaly']     * s2 +
            w['cluster']     * s3 +
            w['keyword']     * s4 +
            w['volume']      * s5 +
            w['engagement']  * s6
        )
        score = float(np.clip(score, 0.0, 1.0))

        self.score_history.append({'score': score, 'time': datetime.utcnow().isoformat()})
        if len(self.score_history) > 1000:
            self.score_history = self.score_history[-500:]

        return {
            'crisis_score': round(score, 4),
            'components': {
                'sentiment': round(s1, 4),
                'anomaly': round(s2, 4),
                'cluster': round(s3, 4),
                'keyword': round(s4, 4),
                'volume': round(s5, 4),
                'engagement': round(s6, 4)
            },
            'severity': self._get_severity(score),
            'timestamp': datetime.utcnow().isoformat()
        }

    def _get_severity(self, score: float) -> dict:
        for level, meta in SEVERITY_LEVELS.items():
            if score >= meta['min']:
                return {
                    'level': level,
                    'color': meta['color'],
                    'icon': meta['icon'],
                    'action': meta['action'],
                    'score': round(score, 4)
                }
        return {**SEVERITY_LEVELS['NONE'], 'level': 'NONE', 'score': round(score, 4)}

    def should_alert(self, severity_level: str, location: str = 'global') -> bool:
        """Rate-limit alerts per location."""
        key = f"{severity_level}_{location}"
        now = datetime.utcnow().timestamp()
        last = self.last_alert_time.get(key, 0)
        cooldown = Config.ALERT_COOLDOWN
        if severity_level == 'CRITICAL':
            cooldown = 10
        if now - last > cooldown:
            self.last_alert_time[key] = now
            return True
        return False

    def generate_alert(self, score_result: dict, top_tweets: list,
                       location: str, disaster_type: str) -> dict:
        """Create a structured crisis alert."""
        severity = score_result['severity']
        level = severity['level']

        if level in ('NONE', 'LOW') or not self.should_alert(level, location):
            return None

        self.total_alerts[level] = self.total_alerts.get(level, 0) + 1

        alert = {
            'alert_id': str(uuid.uuid4())[:8].upper(),
            'timestamp': datetime.utcnow().isoformat(),
            'location': location,
            'disaster_type': disaster_type,
            'crisis_score': score_result['crisis_score'],
            'severity_level': level,
            'severity_color': severity['color'],
            'severity_icon': severity['icon'],
            'recommended_action': severity['action'],
            'top_signals': score_result['components'],
            'sample_tweets': [t.get('text', '')[:120] for t in top_tweets[:3]],
            'total_alerts_today': sum(self.total_alerts.values())
        }
        self.alert_history.append(alert)
        if len(self.alert_history) > 200:
            self.alert_history = self.alert_history[-100:]
        return alert

    def get_recent_alerts(self, n: int = 20) -> list:
        return list(reversed(self.alert_history[-n:]))

    def get_score_trend(self, n: int = 50) -> list:
        return self.score_history[-n:]

    def get_statistics(self) -> dict:
        scores = [s['score'] for s in self.score_history] or [0]
        return {
            'current_score': round(scores[-1], 4) if scores else 0,
            'mean_score_1h': round(np.mean(scores[-180:]), 4),
            'peak_score': round(max(scores), 4),
            'total_alerts': sum(self.total_alerts.values()),
            'alerts_by_severity': self.total_alerts.copy(),
            'score_trend': self.get_score_trend(30)
        }
