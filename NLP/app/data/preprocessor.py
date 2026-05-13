"""
NLP Preprocessing pipeline for social media text.
Handles cleaning, tokenization, stopword removal, lemmatization, TF-IDF vectorization.
"""

import re
import string
import numpy as np
import pandas as pd
from datetime import datetime

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
    from nltk.tokenize import word_tokenize
    for pkg in ['punkt', 'stopwords', 'wordnet', 'punkt_tab']:
        try:
            nltk.download(pkg, quiet=True)
        except:
            pass
    NLTK_AVAILABLE = True
except Exception:
    NLTK_AVAILABLE = False

from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer


class TextPreprocessor:
    def __init__(self):
        self.lemmatizer = WordNetLemmatizer() if NLTK_AVAILABLE else None
        try:
            self.stop_words = set(stopwords.words('english')) if NLTK_AVAILABLE else set()
        except:
            self.stop_words = set()
        # Domain-specific stopwords to keep (they matter for disaster detection)
        domain_keep = {'not', 'no', 'very', 'too', 'more', 'most', 'need', 'help', 'urgent'}
        self.stop_words -= domain_keep
        
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=500,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True
        )
        self.count_vectorizer = CountVectorizer(
            max_features=300,
            ngram_range=(1, 1),
            min_df=1
        )
        self.is_fitted = False
        self._texts_buffer = []

    def clean_text(self, text: str) -> str:
        """Remove URLs, mentions, hashtag symbols, special chars, lowercase."""
        if not isinstance(text, str):
            return ""
        text = re.sub(r'http\S+|www\S+', '', text)
        text = re.sub(r'@\w+', '', text)
        text = re.sub(r'#(\w+)', r'\1', text)
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\d+', '', text)
        text = text.lower().strip()
        text = re.sub(r'\s+', ' ', text)
        return text

    def tokenize(self, text: str) -> list:
        """Tokenize and remove stopwords & short tokens."""
        cleaned = self.clean_text(text)
        if NLTK_AVAILABLE:
            try:
                tokens = word_tokenize(cleaned)
            except:
                tokens = cleaned.split()
        else:
            tokens = cleaned.split()
        tokens = [t for t in tokens if t not in self.stop_words and len(t) > 2]
        return tokens

    def lemmatize(self, tokens: list) -> list:
        """Apply lemmatization."""
        if self.lemmatizer:
            return [self.lemmatizer.lemmatize(t) for t in tokens]
        return tokens

    def preprocess(self, text: str) -> str:
        """Full pipeline: clean → tokenize → lemmatize → rejoin."""
        tokens = self.tokenize(text)
        tokens = self.lemmatize(tokens)
        return ' '.join(tokens)

    def preprocess_batch(self, texts: list) -> list:
        """Preprocess a list of texts."""
        return [self.preprocess(t) for t in texts]

    def fit_tfidf(self, texts: list):
        """Fit TF-IDF on a corpus."""
        processed = self.preprocess_batch(texts)
        # Filter out empty strings
        processed = [t if t.strip() else 'unknown' for t in processed]
        self.tfidf_vectorizer.fit(processed)
        self.count_vectorizer.fit(processed)
        self.is_fitted = True
        return self

    def transform_tfidf(self, texts: list) -> np.ndarray:
        """Transform texts to TF-IDF matrix."""
        processed = self.preprocess_batch(texts)
        processed = [t if t.strip() else 'unknown' for t in processed]
        if not self.is_fitted:
            return self.tfidf_vectorizer.fit_transform(processed).toarray()
        return self.tfidf_vectorizer.transform(processed).toarray()

    def get_vocabulary(self) -> list:
        """Return TF-IDF vocabulary."""
        if self.is_fitted:
            return list(self.tfidf_vectorizer.vocabulary_.keys())
        return []

    def get_count_matrix(self, texts: list) -> np.ndarray:
        """Return raw count matrix for LDA."""
        processed = self.preprocess_batch(texts)
        processed = [t if t.strip() else 'unknown' for t in processed]
        try:
            return self.count_vectorizer.fit_transform(processed)
        except:
            return None

    def extract_features(self, tweet: dict) -> dict:
        """Extract numeric features from a tweet dict."""
        text = tweet.get('text', '')
        features = {
            'text_length': len(text),
            'word_count': len(text.split()),
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'caps_ratio': sum(1 for c in text if c.isupper()) / max(len(text), 1),
            'hashtag_count': text.count('#'),
            'mention_count': text.count('@'),
            'url_count': len(re.findall(r'http\S+', text)),
        }
        return features
