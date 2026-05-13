import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'crisis-detection-secret-2024')
    DEBUG = True
    
    # Streaming
    STREAM_INTERVAL = 3          # seconds between polls (faster real-time)
    BATCH_SIZE = 25              # tweets per clustering batch
    BUFFER_SIZE = 800            # max tweets kept in memory
    
    # Data Sources Configuration
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY', '') # Optional: Add your NewsAPI key here
    ENABLE_REDDIT = True
    ENABLE_NEWSAPI = True        # Falls back to RSS if no key provided
    ENABLE_USGS = True
    ENABLE_GDELT = True
    
    # ML Model Parameters
    DL_MODEL_SENTIMENT = "distilbert-base-uncased-finetuned-sst-2-english"
    DL_MODEL_EMBEDDING = "all-MiniLM-L6-v2"
    N_CLUSTERS = 8               # K-Means clusters
    DBSCAN_EPS = 0.5
    DBSCAN_MIN_SAMPLES = 5
    N_TOPICS = 8                 # Topics (Zero-Shot) — must match TOPIC_LABEL_MAP
    ANOMALY_CONTAMINATION = 0.05
    
    # Crisis Thresholds
    CRISIS_SCORE_THRESHOLD = 0.65
    HIGH_SEVERITY_THRESHOLD = 0.80
    CRITICAL_THRESHOLD = 0.90
    
    # Alert Rate Limiting (seconds)
    ALERT_COOLDOWN = 30
