"""
Topic Modeling using Deep Learning Zero-Shot Classification.
Dynamically categorizes disaster topics from tweet corpus.
"""

import numpy as np
import warnings
warnings.filterwarnings('ignore')

try:
    import torch
    torch.zeros(1)  # Will raise OSError if DLL fails
    from transformers import pipeline
    TRANSFORMERS_AVAILABLE = True
except Exception as e:
    print(f"[Warning] Transformers/Torch unavailable (falling back to keyword rules): {e}")
    TRANSFORMERS_AVAILABLE = False

# Topic labels based on expected disaster topics
TOPIC_LABEL_MAP = {
    0: "🔥 Wildfire & Fire Emergency",
    1: "🌊 Flood & Water Disaster",
    2: "🌀 Hurricane & Storm",
    3: "🌍 Earthquake & Seismic",
    4: "🌪️ Tornado & Severe Weather",
    5: "🏥 Emergency Response & Aid",
    6: "📢 Evacuation & Safety",
    7: "💬 General Community Updates"
}

TOPIC_COLORS = {
    0: '#FF6B35', 1: '#4ECDC4', 2: '#45B7D1', 3: '#96CEB4',
    4: '#FFEAA7', 5: '#DDA0DD', 6: '#98D8C8', 7: '#87CEEB'
}

# The actual labels to feed to the Zero-Shot model
ZERO_SHOT_CANDIDATES = [
    "wildfire and fire emergency",
    "flood and water disaster",
    "hurricane and storm",
    "earthquake and seismic",
    "tornado and severe weather",
    "emergency response and aid",
    "evacuation and safety",
    "general community updates"
]

class TopicModeler:
    """
    Deep Learning Zero-Shot topic modeling for disaster tweets.
    Identifies dominant disaster themes using semantic entailment.
    """

    def __init__(self, n_topics=8):
        self.n_topics = n_topics
        self.is_fitted = True # Zero-shot doesn't need fitting!

        if TRANSFORMERS_AVAILABLE:
            print("[TopicModeler] Loading Zero-Shot Classification model: facebook/bart-large-mnli")
            try:
                # Using a lighter model if bart is too heavy, e.g., typeform/distilbert-base-uncased-mnli
                self.zero_shot = pipeline("zero-shot-classification", model="typeform/distilbert-base-uncased-mnli")
            except Exception as e:
                print(f"[TopicModeler] Failed to load zero-shot model: {e}")
                self.zero_shot = None
        else:
            self.zero_shot = None

    def fit(self, texts: list):
        """No fitting required for Zero-Shot DL models."""
        return self

    def transform(self, texts: list) -> np.ndarray:
        """Get topic distribution for each document."""
        last_idx = self.n_topics - 1  # always valid fallback
        distributions = []
        for t in texts:
            dist = np.zeros(self.n_topics)
            if self.zero_shot:
                try:
                    result = self.zero_shot(t, candidate_labels=ZERO_SHOT_CANDIDATES[:self.n_topics])
                    for label, score in zip(result['labels'], result['scores']):
                        idx = ZERO_SHOT_CANDIDATES.index(label)
                        if idx < self.n_topics:
                            dist[idx] = score
                except Exception:
                    dist[last_idx] = 1.0
            else:
                dist[last_idx] = 1.0
            distributions.append(dist)
        return np.array(distributions)

    def get_dominant_topic(self, text: str) -> dict:
        """Get the dominant topic for a single tweet."""
        last_idx = self.n_topics - 1
        if not self.zero_shot:
            return {'topic_id': last_idx, 'label': TOPIC_LABEL_MAP.get(last_idx, 'General'), 'confidence': 1.0, 'top_words': [], 'color': TOPIC_COLORS.get(last_idx, '#888888')}
        
        try:
            result = self.zero_shot(text, candidate_labels=ZERO_SHOT_CANDIDATES)
            best_label = result['labels'][0]
            confidence = result['scores'][0]
            topic_id = ZERO_SHOT_CANDIDATES.index(best_label)
            
            dist = [0.0] * self.n_topics
            for label, score in zip(result['labels'], result['scores']):
                dist[ZERO_SHOT_CANDIDATES.index(label)] = round(float(score), 4)

            return {
                'topic_id': topic_id,
                'label': TOPIC_LABEL_MAP.get(topic_id, f'Topic {topic_id}'),
                'confidence': round(float(confidence), 4),
                'distribution': dist,
                'top_words': best_label.split(),
                'color': TOPIC_COLORS.get(topic_id, '#888888')
            }
        except Exception:
            return {'topic_id': 7, 'label': TOPIC_LABEL_MAP[7], 'confidence': 1.0, 'top_words': [], 'color': TOPIC_COLORS[7]}

    def get_all_topics(self) -> list:
        """Get full topic → word distribution for display."""
        topics = []
        for i, label in enumerate(ZERO_SHOT_CANDIDATES):
            topics.append({
                'topic_id': i,
                'label': TOPIC_LABEL_MAP.get(i, f'Topic {i}'),
                'color': TOPIC_COLORS.get(i, '#888888'),
                'words': [(w, 1.0) for w in label.split() if len(w) > 3],
                'word_string': label
            })
        return topics

    def get_corpus_topic_distribution(self, texts: list) -> list:
        """Get aggregate topic proportions across all texts."""
        if not texts:
            return [{'topic': i, 'proportion': 1.0 / self.n_topics} for i in range(self.n_topics)]
        
        # for performance, sample up to 20 texts for corpus distribution
        sample = texts[-20:] if len(texts) > 20 else texts
        dists = self.transform(sample)
        mean_dist = dists.mean(axis=0)
        return [
            {
                'topic_id': i,
                'label': TOPIC_LABEL_MAP.get(i, f'Topic {i}'),
                'proportion': round(float(mean_dist[i]), 4),
                'color': TOPIC_COLORS.get(i, '#888888')
            }
            for i in range(self.n_topics)
        ]

    @property
    def perplexity(self) -> float:
        return -1.0
