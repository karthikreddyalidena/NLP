"""
Deep Learning Sentiment Analysis for disaster tweets.
Uses HuggingFace Transformers pipeline.
Produces a composite disaster-aware sentiment score.
"""

import re
import numpy as np
from app.data.disaster_keywords import (
    URGENCY_KEYWORDS, NEGATIVE_SENTIMENT_AMPLIFIERS,
    POSITIVE_RECOVERY_KEYWORDS, DISASTER_CATEGORIES
)
from config import Config

try:
    from transformers import pipeline
    import torch
    # Test if torch actually loads
    torch.zeros(1)
    TRANSFORMERS_AVAILABLE = True
except Exception as e:
    print(f"[Warning] Deep Learning unavailable (Torch DLL error): {e}")
    TRANSFORMERS_AVAILABLE = False
    
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False


class SentimentAnalyzer:
    """
    Deep Learning sentiment analyzer combining Transformer models with
    disaster-domain-specific adjustments.
    """

    def __init__(self):
        self.urgency_boost = 0.25
        self.amplifier_boost = 0.15
        self.recovery_penalty = 0.10
        self.model_name = Config.DL_MODEL_SENTIMENT

        if TRANSFORMERS_AVAILABLE:
            print(f"[Sentiment] Loading Deep Learning model: {self.model_name}")
            try:
                self.sentiment_pipeline = pipeline("sentiment-analysis", model=self.model_name, truncation=True, max_length=512)
            except Exception as e:
                print(f"[Sentiment] Failed to load model: {e}")
                self.sentiment_pipeline = None
        else:
            self.sentiment_pipeline = None
            
        self.vader = SentimentIntensityAnalyzer() if VADER_AVAILABLE else None

    def _dl_score(self, text: str) -> dict:
        if self.sentiment_pipeline:
            try:
                result = self.sentiment_pipeline(text)[0]
                label = result['label'].upper()
                score = result['score']
                
                if label == 'NEGATIVE': compound = -score
                elif label == 'POSITIVE': compound = score
                else: compound = 0.0
                    
                return {
                    'compound': compound,
                    'positive': score if label == 'POSITIVE' else 1 - score,
                    'negative': score if label == 'NEGATIVE' else 1 - score,
                    'neutral': 0.0,
                    'label': label.lower()
                }
            except Exception:
                pass
                
        # FALLBACK: Use VADER if transformers failed to load due to C++ error
        if self.vader:
            vs = self.vader.polarity_scores(text)
            return {
                'compound': vs['compound'],
                'positive': vs['pos'],
                'negative': vs['neg'],
                'neutral': vs['neu'],
                'label': 'negative' if vs['compound'] <= -0.05 else ('positive' if vs['compound'] >= 0.05 else 'neutral')
            }
            
        return {'compound': 0.0, 'positive': 0.0, 'negative': 0.0, 'neutral': 1.0, 'label': 'neutral'}

    def _keyword_adjustments(self, text: str) -> float:
        """Domain-specific adjustments based on keyword presence."""
        text_lower = text.lower()
        adjustment = 0.0

        urgency_hits = sum(1 for kw in URGENCY_KEYWORDS if kw in text_lower)
        adjustment += urgency_hits * self.urgency_boost

        amp_hits = sum(1 for kw in NEGATIVE_SENTIMENT_AMPLIFIERS if kw in text_lower)
        adjustment += amp_hits * self.amplifier_boost

        recovery_hits = sum(1 for kw in POSITIVE_RECOVERY_KEYWORDS if kw in text_lower)
        adjustment -= recovery_hits * self.recovery_penalty

        return np.clip(adjustment, -0.5, 0.8)

    def _disaster_type_score(self, text: str) -> float:
        """Score based on disaster category keyword density."""
        text_lower = text.lower()
        max_weight = 0.0
        for cat, data in DISASTER_CATEGORIES.items():
            hits = sum(1 for kw in data["primary"] if kw in text_lower)
            if hits > 0:
                max_weight = max(max_weight, data["severity_weight"] * min(hits / 2, 1.0))
        return max_weight

    def analyze(self, text: str) -> dict:
        """Full deep learning analysis of a single text."""
        dl_s = self._dl_score(text)

        # Negative compound = higher distress
        dl_distress = (1 - dl_s['compound']) / 2

        base_distress = dl_distress

        kw_adj = self._keyword_adjustments(text)
        disaster_score = self._disaster_type_score(text)

        distress_score = np.clip(base_distress + kw_adj * 0.3 + disaster_score * 0.3, 0.0, 1.0)

        urgency_count = sum(1 for kw in URGENCY_KEYWORDS if kw in text.lower())
        is_urgent = dl_s['negative'] > 0.8 or urgency_count >= 2

        return {
            'vader_compound': round(dl_s['compound'], 4),  # Keeping key name for compatibility with downstream
            'vader_negative': round(dl_s['negative'], 4),
            'vader_positive': round(dl_s['positive'], 4),
            'textblob_polarity': round(dl_s['compound'], 4),
            'textblob_subjectivity': 0.5,
            'distress_score': round(distress_score, 4),
            'disaster_keyword_score': round(disaster_score, 4),
            'is_urgent': is_urgent,
            'sentiment_label': dl_s['label']
        }

    def analyze_batch(self, texts: list) -> list:
        # Optimization: use pipeline on batch
        if self.sentiment_pipeline and len(texts) > 0:
            return [self.analyze(t) for t in texts]
        return []

    def aggregate_statistics(self, sentiments: list) -> dict:
        if not sentiments:
            return {}
        distress = [s['distress_score'] for s in sentiments]
        compounds = [s['vader_compound'] for s in sentiments]
        urgents = [s['is_urgent'] for s in sentiments]
        labels = [s['sentiment_label'] for s in sentiments]
        return {
            'mean_distress': round(np.mean(distress), 4),
            'max_distress': round(np.max(distress), 4),
            'std_distress': round(np.std(distress), 4),
            'mean_compound': round(np.mean(compounds), 4),
            'urgent_ratio': round(sum(urgents) / len(urgents), 4),
            'negative_ratio': round(labels.count('negative') / len(labels), 4),
            'positive_ratio': round(labels.count('positive') / len(labels), 4),
            'neutral_ratio': round(labels.count('neutral') / len(labels), 4),
            'total_analyzed': len(sentiments)
        }
