"""
Synthetic social media stream simulator for disaster scenarios.
Generates realistic tweet-like data with temporal patterns,
geographic info, and varying severity levels.
"""

import random
import time
import uuid
import json
from datetime import datetime, timedelta
import numpy as np
from app.data.disaster_keywords import DISASTER_CATEGORIES, URGENCY_KEYWORDS, NEGATIVE_SENTIMENT_AMPLIFIERS, POSITIVE_RECOVERY_KEYWORDS

# ── Tweet Templates ────────────────────────────────────────────────────────────
TWEET_TEMPLATES = {
    "earthquake": [
        "MAJOR {adj} earthquake {magnitude} just hit {location}! Buildings shaking! {urgency}",
        "Felt that earthquake near {location}. {adj} tremors for 30 seconds. {reaction}",
        "Earthquake alert: {magnitude} magnitude quake strikes {location}. {urgency}",
        "Oh my god {location} is having a huge earthquake right now! {reaction} {urgency}",
        "Seismic activity detected near {location}. Citizens advised to {action}.",
        "Building collapse reported at {location} after {magnitude} earthquake. {urgency}",
        "Aftershocks continue in {location} following {adj} earthquake. Stay alert!",
        "Just survived an earthquake in {location}. {adj} experience. Need help at {landmark}.",
    ],
    "flood": [
        "Flash flood warnings issued for {location}. {adj} rainfall causing rapid water rise. {urgency}",
        "Cars submerged, streets flooded in {location}. {urgency}",
        "Flood emergency in {location}! Residents stranded on rooftops. {urgency}",
        "{location} flooded after dam breach upstream. {urgency} evacuate now!",
        "Water levels rising fast at {location}. {adj} flooding. {reaction}",
        "Rescue boats deployed in {location} for flood victims. {urgency}",
        "Major flood event unfolding in {location}. {adj} rainfall unprecedented. {urgency}",
        "Neighborhoods in {location} underwater. {urgency} immediate help needed.",
    ],
    "wildfire": [
        "{adj} wildfire burning near {location}. Fire spreading rapidly. {urgency}",
        "Mandatory evacuation ordered for {location} due to {adj} wildfire. Leave NOW!",
        "Fire crews battling {adj} blaze near {location}. {urgency}",
        "Smoke visible from miles away. Wildfire approaching {location}. {urgency}",
        "Hundreds of homes threatened by wildfire in {location}. {urgency}",
        "Air quality hazardous in {location} due to {adj} wildfire smoke.",
        "Wildfire jumping containment lines near {location}. {adj} wind conditions. {urgency}",
    ],
    "hurricane": [
        "Hurricane {name} making landfall near {location}. Category {cat} storm. {urgency}",
        "{adj} Hurricane {name} bringing {speed} mph winds to {location}. {urgency}",
        "Storm surge up to 15 feet expected at {location} from Hurricane {name}. Evacuate!",
        "Hurricane warning issued for {location}. {adj} conditions expected. {urgency}",
        "Hurricane {name} eye approaching {location}. {urgency} seek shelter!",
    ],
    "tornado": [
        "Tornado spotted near {location}! Take shelter immediately! {urgency}",
        "{adj} tornado touching down in {location}. {urgency}",
        "Tornado warning issued for {location} county. {urgency} shelter in place!",
        "EF-4 tornado destroys neighborhoods in {location}. {urgency}",
        "Multiple tornadoes reported in {location} area. {adj} conditions. {urgency}",
    ],
    "tsunami": [
        "TSUNAMI WARNING issued for {location} coastline! {urgency} Move to high ground!",
        "{adj} tsunami triggered by {magnitude} earthquake approaching {location}. {urgency}",
        "Tsunami waves reported hitting {location}. {urgency} devastating!",
        "Ocean receding rapidly at {location} beach — possible tsunami imminent! {urgency}",
    ],
    "normal": [
        "Beautiful day in {location} today! Loving the weather. #sunshine",
        "Great local event happening in {location} this weekend! #community",
        "Traffic congestion on main road in {location}. Plan alternative routes.",
        "New restaurant opened in {location}. Amazing food! #dining",
        "Sports team from {location} wins championship! #celebration",
        "Local election results from {location} are in. Close race.",
        "Concert tonight in {location}. Can't wait! #music",
        "Power outage in parts of {location} due to maintenance. Scheduled to resume tonight.",
        "Road work on highway near {location} causing delays. #traffic",
        "Community cleanup event in {location} this Saturday. Join us! #volunteer",
    ]
}

LOCATIONS = [
    "Miami", "Houston", "Los Angeles", "New York", "Chicago", "Phoenix", "Seattle",
    "New Orleans", "Tampa", "Charleston", "San Francisco", "Denver", "Atlanta",
    "Dallas", "San Diego", "Portland", "Nashville", "Memphis", "Galveston", "Key West",
    "downtown district", "north side", "coastal area", "riverside district", "uptown"
]

LANDMARKS = [
    "Main Street shelter", "City Hall area", "Central Park", "downtown bridge",
    "community center", "local hospital", "fire station #3", "university campus"
]

ADJECTIVES_SEVERE = ["massive", "catastrophic", "devastating", "severe", "extreme", "deadly", "major", "powerful"]
ADJECTIVES_MILD = ["minor", "small", "moderate", "slight"]
MAGNITUDES = ["M5.2", "M6.1", "M6.8", "M7.0", "M7.4", "M7.9", "M8.1"]
HURRICANE_NAMES = ["Alex", "Bertha", "Cristobal", "Delta", "Eta", "Fred", "Grace", "Henri"]
URGENCY_PHRASES = ["SOS!", "HELP NEEDED!", "Emergency response required!", "URGENT!", "Lives at risk!"]
REACTIONS = ["Terrifying!", "Unbelievable!", "Stay safe everyone!", "So scared right now.", "Praying for everyone."]
ACTIONS = ["evacuate immediately", "take shelter", "avoid the area", "call emergency services", "move to high ground"]

# Geographic coordinates (lat, lon) for locations
LOCATION_COORDS = {
    "Miami": (25.7617, -80.1918),
    "Houston": (29.7604, -95.3698),
    "Los Angeles": (34.0522, -118.2437),
    "New York": (40.7128, -74.0060),
    "Chicago": (41.8781, -87.6298),
    "Phoenix": (33.4484, -112.0740),
    "Seattle": (47.6062, -122.3321),
    "New Orleans": (29.9511, -90.0715),
    "Tampa": (27.9506, -82.4572),
    "Charleston": (32.7765, -79.9311),
    "San Francisco": (37.7749, -122.4194),
    "Denver": (39.7392, -104.9903),
    "Atlanta": (33.7490, -84.3880),
    "Dallas": (32.7767, -96.7970),
    "San Diego": (32.7157, -117.1611),
    "Portland": (45.5231, -122.6765),
    "Nashville": (36.1627, -86.7816),
    "Memphis": (35.1495, -90.0490),
    "Galveston": (29.3013, -94.7977),
    "Key West": (24.5551, -81.7800),
}


class StreamSimulator:
    """
    Simulates a real-time social media stream with disaster events.
    Generates data in bursts to mimic viral spread of crisis info.
    """

    def __init__(self):
        self.tweet_id = 0
        self.base_time = datetime.utcnow()
        self.active_events = []   # ongoing disaster events
        self.event_probability = 0.03  # chance a new event starts per batch

    def _fill_template(self, template: str, disaster_type: str) -> str:
        location = random.choice(LOCATIONS)
        return template.format(
            adj=random.choice(ADJECTIVES_SEVERE if random.random() > 0.3 else ADJECTIVES_MILD),
            location=location,
            magnitude=random.choice(MAGNITUDES),
            urgency=random.choice(URGENCY_PHRASES) if random.random() > 0.4 else "",
            reaction=random.choice(REACTIONS),
            action=random.choice(ACTIONS),
            name=random.choice(HURRICANE_NAMES),
            cat=random.randint(1, 5),
            speed=random.randint(74, 185),
            landmark=random.choice(LANDMARKS),
        ).strip()

    def _generate_tweet(self, disaster_type: str = None, severity: float = None) -> dict:
        self.tweet_id += 1
        if disaster_type is None:
            disaster_type = random.choices(
                list(TWEET_TEMPLATES.keys()),
                weights=[2, 2, 2, 1, 1, 1, 15],  # normal = 15x more likely
                k=1
            )[0]

        templates = TWEET_TEMPLATES[disaster_type]
        template = random.choice(templates)
        text = self._fill_template(template, disaster_type)

        # Random location with some hotspot bias
        loc_name = random.choice(list(LOCATION_COORDS.keys()))
        lat, lon = LOCATION_COORDS[loc_name]
        lat += random.gauss(0, 0.05)
        lon += random.gauss(0, 0.05)

        # Engagement metrics
        is_crisis = disaster_type != "normal"
        retweets = int(np.random.lognormal(4 if is_crisis else 1.5, 1.5))
        likes = int(retweets * random.uniform(1.5, 4.0))
        replies = int(retweets * random.uniform(0.2, 0.8))

        severity = severity or (random.uniform(0.4, 1.0) if is_crisis else random.uniform(0.0, 0.3))

        tweet = {
            "id": f"tw_{self.tweet_id:06d}_{uuid.uuid4().hex[:8]}",
            "text": text,
            "timestamp": (self.base_time + timedelta(seconds=self.tweet_id * random.uniform(0.5, 3))).isoformat(),
            "user_id": f"user_{random.randint(1000, 99999)}",
            "location": loc_name,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "retweets": retweets,
            "likes": likes,
            "replies": replies,
            "disaster_type": disaster_type,
            "true_severity": round(severity, 3),
            "platform": random.choice(["twitter", "reddit", "facebook"]),
            "language": "en",
            "followers": random.randint(10, 100000),
            "verified": random.random() < 0.05,
        }
        return tweet

    def generate_batch(self, size: int = 20, force_crisis: bool = False) -> list:
        """Generate a batch of tweets, optionally forcing crisis content."""
        tweets = []

        # Check if a new disaster event starts
        if random.random() < self.event_probability or force_crisis:
            event_type = random.choice([k for k in TWEET_TEMPLATES.keys() if k != "normal"])
            severity = random.uniform(0.6, 1.0)
            burst_size = random.randint(3, 8)
            for _ in range(burst_size):
                tweets.append(self._generate_tweet(event_type, severity))

        # Fill rest with mixed content
        remaining = size - len(tweets)
        for _ in range(remaining):
            tweets.append(self._generate_tweet())

        random.shuffle(tweets)
        return tweets

    def generate_dataset(self, n: int = 2000) -> list:
        """Generate a large static dataset for training/evaluation."""
        all_tweets = []
        for i in range(0, n, 20):
            force = (i % 200 == 0)
            batch = self.generate_batch(size=min(20, n - i), force_crisis=force)
            all_tweets.extend(batch)
        return all_tweets[:n]

    def stream(self, interval: float = 2.0):
        """Continuously yield batches (generator)."""
        while True:
            yield self.generate_batch()
            time.sleep(interval)
