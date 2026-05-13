"""
Flask Application Factory with Socket.IO real-time engine.
Orchestrates all ML pipelines and streams data to the dashboard.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import threading
import time
import numpy as np
from collections import deque
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_socketio import SocketIO, emit

from config import Config
from app.data.realtime_stream import RealTimeStreamer
from app.data.preprocessor import TextPreprocessor
from app.models.sentiment import SentimentAnalyzer
from app.models.clustering import ClusteringEngine
from app.models.topic_model import TopicModeler
from app.models.anomaly import AnomalyDetector
from app.models.crisis_scorer import CrisisScorer
from app.utils.alert_system import AlertManager

import os
# ── Flask + SocketIO setup ─────────────────────────────────────────────────────
flask_app = Flask(__name__, template_folder="../templates", static_folder="../static")
flask_app.config.from_object(Config)
flask_app.secret_key = 'crisis-sentinel-v2-super-secret-key-forced-logout'
socketio_mode = 'threading' if os.name == 'nt' else 'eventlet'
socketio = SocketIO(flask_app, cors_allowed_origins="*", async_mode=socketio_mode)

# ── Global ML Pipeline ────────────────────────────────────────────────────────
simulator   = RealTimeStreamer()
preprocessor = TextPreprocessor()
sentiment_analyzer = SentimentAnalyzer()
clustering  = ClusteringEngine(n_clusters=Config.N_CLUSTERS)
topic_model = TopicModeler(n_topics=Config.N_TOPICS)
anomaly_det = AnomalyDetector(contamination=Config.ANOMALY_CONTAMINATION)
crisis_scorer = CrisisScorer()
alert_mgr   = AlertManager()

# ── In-memory buffers ─────────────────────────────────────────────────────────
tweet_buffer     = deque(maxlen=Config.BUFFER_SIZE)
processed_buffer = deque(maxlen=Config.BUFFER_SIZE)
volume_history   = deque(maxlen=200)
sentiment_trend  = deque(maxlen=100)
crisis_trend     = deque(maxlen=100)
geo_points       = deque(maxlen=300)

# Boot state
_is_bootstrapped = False
_stream_active   = False
_lock            = threading.Lock()


def _bootstrap():
    """Pre-train models on synthetic data before live streaming."""
    global _is_bootstrapped
    print("[BOOTSTRAP] Generating initial dataset...")
    initial_data = simulator.generate_dataset(n=500)
    texts = [t['text'] for t in initial_data]

    print("[BOOTSTRAP] Fitting TF-IDF vectorizer...")
    preprocessor.fit_tfidf(texts)

    print("[BOOTSTRAP] Running sentiment analysis...")
    for tw in initial_data:
        tw['sentiment'] = sentiment_analyzer.analyze(tw['text'])

    print("[BOOTSTRAP] Fitting anomaly detector...")
    anomaly_det.fit(initial_data)

    print("[BOOTSTRAP] Fitting topic model...")
    processed_texts = preprocessor.preprocess_batch(texts)
    topic_model.fit(processed_texts)

    print("[BOOTSTRAP] Fitting K-Means clusters...")
    X = clustering.get_embeddings(texts)
    clustering.fit_kmeans(X)

    # Seed buffers
    for tw in initial_data[-100:]:
        tweet_buffer.append(tw)

    _is_bootstrapped = True
    print("[BOOTSTRAP] Bootstrap complete!")


def _process_batch(batch: list) -> dict:
    """Full ML pipeline for one streaming batch."""
    if not batch:
        return {}

    texts = [t['text'] for t in batch]

    # 1. Sentiment
    for tw in batch:
        tw['sentiment'] = sentiment_analyzer.analyze(tw['text'])

    # 2. TF-IDF → Clustering
    try:
        X = clustering.get_embeddings(texts)
        labels = clustering.predict_kmeans(X) if clustering.is_fitted else np.zeros(len(batch), dtype=int)
        for tw, lbl in zip(batch, labels):
            tw['cluster'] = int(lbl)
    except:
        for tw in batch:
            tw['cluster'] = 0
        labels = np.zeros(len(batch), dtype=int)

    # 3. Topic modeling
    try:
        for tw in batch:
            tw['topic'] = topic_model.get_dominant_topic(tw['text'])
    except:
        for tw in batch:
            tw['topic'] = {'topic_id': 0, 'label': 'General', 'confidence': 0.5}

    # 4. Anomaly detection
    try:
        anomaly_scores = anomaly_det.predict(batch)
        for tw, sc in zip(batch, anomaly_scores):
            tw['anomaly_score'] = round(float(sc), 4)
    except:
        anomaly_scores = np.zeros(len(batch))
        for tw in batch:
            tw['anomaly_score'] = 0.0

    # 5. Crisis scoring
    distress_vals = np.array([tw['sentiment']['distress_score'] for tw in batch])
    kw_scores = np.array([tw['sentiment']['disaster_keyword_score'] for tw in batch])
    engagement = np.array([tw.get('retweets', 0) + tw.get('likes', 0) for tw in batch], dtype=float)

    volume_history.append(len(batch))
    vol_anomaly = anomaly_det.detect_volume_anomaly(list(volume_history))

    # Cluster crisis ratio
    distress_ser = distress_vals
    non_normal_mask = np.array([tw.get('disaster_type', 'normal') != 'normal' for tw in batch])
    cluster_ratio = float(non_normal_mask.mean())

    score_result = crisis_scorer.compute_score(
        mean_distress=float(distress_vals.mean()),
        anomaly_scores=anomaly_scores,
        cluster_crisis_ratio=cluster_ratio,
        keyword_density=float(kw_scores.mean()),
        volume_z_score=vol_anomaly.get('z_score', 0),
        mean_engagement=float(engagement.mean())
    )

    # 6. Alert generation
    top_distress_tweets = sorted(batch, key=lambda t: t['sentiment']['distress_score'], reverse=True)
    dominant_type = max(set(t.get('disaster_type', 'normal') for t in batch[:5]),
                        key=list(t.get('disaster_type', 'normal') for t in batch[:5]).count)
    dominant_location = max(set(t.get('location', 'Unknown') for t in batch[:5]),
                            key=list(t.get('location', 'Unknown') for t in batch[:5]).count)

    alert = crisis_scorer.generate_alert(
        score_result, top_distress_tweets, dominant_location, dominant_type
    )
    if alert:
        alert_mgr.add_alert(alert)

    # Update trend buffers
    ts = datetime.utcnow().strftime('%H:%M:%S')
    sentiment_trend.append({
        'time': ts,
        'distress': round(float(distress_vals.mean()), 4),
        'negative_ratio': round(float((distress_vals > 0.5).mean()), 4)
    })
    crisis_trend.append({'time': ts, 'score': score_result['crisis_score']})

    # Geo points
    for tw in batch:
        geo_points.append({
            'lat': tw.get('lat', 0), 'lon': tw.get('lon', 0),
            'distress': tw['sentiment']['distress_score'],
            'location': tw.get('location', ''),
            'type': tw.get('disaster_type', 'normal')
        })

    # Store in buffer
    with _lock:
        for tw in batch:
            tweet_buffer.append(tw)

    return {
        'batch': batch,
        'score_result': score_result,
        'alert': alert,
        'vol_anomaly': vol_anomaly,
        'batch_size': len(batch),
        'timestamp': ts
    }


def _streaming_loop():
    """Background thread: generate, process, emit via Socket.IO."""
    global _stream_active
    _stream_active = True
    print("[STREAM] Starting real-time stream...")

    while _stream_active:
        try:
            batch = simulator.generate_batch(size=Config.BATCH_SIZE)
            result = _process_batch(batch)

            if result:
                # Serialize for JSON
                payload = {
                    'tweets': _serialize_tweets(result['batch'][:8]),
                    'crisis_score': result['score_result'].get('crisis_score', 0),
                    'severity': result['score_result'].get('severity', {}),
                    'components': result['score_result'].get('components', {}),
                    'alert': result.get('alert'),
                    'vol_anomaly': result.get('vol_anomaly', {}),
                    'sentiment_trend': list(sentiment_trend)[-20:],
                    'crisis_trend': list(crisis_trend)[-20:],
                    'geo_points': list(geo_points)[-50:],
                    'stats': crisis_scorer.get_statistics(),
                    'topic_distribution': topic_model.get_corpus_topic_distribution(
                        [t['text'] for t in list(tweet_buffer)[-100:]]
                    ),
                    'top_anomalies': anomaly_det.get_top_anomalies(
                        result['batch'], 
                        np.array([t.get('anomaly_score', 0) for t in result['batch']]),
                        top_n=3
                    ),
                    'alert_counts': alert_mgr.get_counts_by_severity(),
                    'timestamp': result['timestamp']
                }
                socketio.emit('stream_update', payload)

        except Exception as e:
            print(f"[STREAM ERROR] {e}")

        time.sleep(Config.STREAM_INTERVAL)


def _serialize_tweets(tweets: list) -> list:
    """Make tweets JSON-safe."""
    safe = []
    for t in tweets:
        safe.append({
            'id': t.get('id', ''),
            'text': t.get('text', '')[:200],
            'location': t.get('location', ''),
            'lat': t.get('lat', 0),
            'lon': t.get('lon', 0),
            'platform': t.get('platform', 'twitter'),
            'disaster_type': t.get('disaster_type', 'normal'),
            'retweets': int(t.get('retweets', 0)),
            'likes': int(t.get('likes', 0)),
            'cluster': int(t.get('cluster', 0)),
            'anomaly_score': round(float(t.get('anomaly_score', 0)), 4),
            'sentiment': {
                'distress_score': t.get('sentiment', {}).get('distress_score', 0),
                'sentiment_label': t.get('sentiment', {}).get('sentiment_label', 'neutral'),
                'is_urgent': t.get('sentiment', {}).get('is_urgent', False),
                'vader_compound': t.get('sentiment', {}).get('vader_compound', 0),
            },
            'topic': {
                'label': t.get('topic', {}).get('label', 'General'),
                'color': t.get('topic', {}).get('color', '#888'),
            }
        })
    return safe


# ── Auth Decorator ────────────────────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ── Routes ────────────────────────────────────────────────────────────────────
@flask_app.route('/')
@login_required
def index():
    return render_template('dashboard.html')

@flask_app.route('/analytics')
@login_required
def analytics():
    return render_template('analytics.html')

@flask_app.route('/alerts')
@login_required
def alerts_page():
    return render_template('alerts.html')

@flask_app.route('/login')
def login():
    if 'user' in session:
        return redirect(url_for('index'))
    return render_template('login.html')

@flask_app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    remember = data.get('remember', False)
    
    # Mock authentication check
    if username == 'admin' and password == 'crisis2024':
        session.permanent = remember
        session['user'] = username
        return jsonify({'success': True})
    
    # Google mock auth
    if data.get('google_auth'):
        session.permanent = True
        session['user'] = data.get('email', 'google_user@gmail.com')
        return jsonify({'success': True})
        
    return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@flask_app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@flask_app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user', None)
    return jsonify({'success': True})

@flask_app.route('/api/status')
def api_status():
    return jsonify({
        'bootstrapped': _is_bootstrapped,
        'streaming': _stream_active,
        'buffer_size': len(tweet_buffer),
        'total_alerts': len(alert_mgr.alerts),
        'models': {
            'clustering': clustering.evaluate(),
            'anomaly': anomaly_det.evaluate(),
            'topic_model': {'fitted': topic_model.is_fitted, 'n_topics': topic_model.n_topics}
        }
    })

@flask_app.route('/api/alerts')
def api_alerts():
    return jsonify(alert_mgr.get_recent(50))

@flask_app.route('/api/crisis_stats')
def api_crisis_stats():
    return jsonify(crisis_scorer.get_statistics())

@flask_app.route('/api/topics')
def api_topics():
    return jsonify(topic_model.get_all_topics())

@flask_app.route('/api/geo')
def api_geo():
    return jsonify(list(geo_points)[-200:])

@flask_app.route('/api/simulate_crisis', methods=['POST'])
def simulate_crisis():
    """Inject a forced crisis event for demonstration."""
    batch = simulator.generate_batch(size=15, force_crisis=True)
    result = _process_batch(batch)
    return jsonify({'status': 'crisis_injected', 'score': result.get('score_result', {}).get('crisis_score', 0)})

@flask_app.route('/api/cluster_profiles')
def api_cluster_profiles():
    if not tweet_buffer:
        return jsonify({})
    recent = list(tweet_buffer)[-200:]
    texts  = [t['text'] for t in recent]
    try:
        X = clustering.get_embeddings(texts)
        labels = clustering.predict_kmeans(X)
        distress = np.array([t.get('sentiment', {}).get('distress_score', 0) for t in recent])
        types = [t.get('disaster_type', 'normal') for t in recent]
        profiles = clustering.compute_cluster_profiles(labels, distress, types)
        return jsonify(profiles)
    except Exception as e:
        return jsonify({'error': str(e)})


# ── Socket.IO events ──────────────────────────────────────────────────────────
@socketio.on('connect')
def on_connect():
    print(f"[WS] Client connected: {request.sid}")
    # Send current state immediately
    emit('init_data', {
        'bootstrapped': _is_bootstrapped,
        'alerts': alert_mgr.get_recent(10),
        'topics': topic_model.get_all_topics(),
        'stats': crisis_scorer.get_statistics()
    })

@socketio.on('disconnect')
def on_disconnect():
    print(f"[WS] Client disconnected: {request.sid}")

@socketio.on('request_crisis_simulation')
def on_simulate():
    batch = simulator.generate_batch(size=15, force_crisis=True)
    result = _process_batch(batch)
    emit('crisis_simulated', {'score': result.get('score_result', {}).get('crisis_score', 0)})


def start_background_stream():
    _bootstrap()
    socketio.start_background_task(_streaming_loop)
