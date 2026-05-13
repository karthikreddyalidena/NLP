"""
Multi-Source Real-Time stream pulling from Reddit, USGS, GDELT, and Google News RSS.
Synchronizes and interleaves data into a uniform format for the CrisisAI ML pipeline.
Includes per-source cooldowns and full synthetic fallback to prevent startup blocking.
"""

import time
import json
import urllib.request
import uuid
import random
from datetime import datetime
import re
from xml.etree import ElementTree as ET
import feedparser
import requests
from config import Config

# ── Synthetic fallback data ────────────────────────────────────────
SYNTHETIC_TEXTS = [
    ("Wildfire spreading rapidly towards residential areas in California, thousands evacuated", "wildfire", "United States"),
    ("Major earthquake magnitude 6.8 strikes coastal region of Japan, tsunami warning issued", "earthquake", "Japan"),
    ("Severe flooding affecting southern provinces of China, thousands displaced", "flood", "China"),
    ("Tropical storm makes landfall in Philippines with 150mph winds", "hurricane", "Philippines"),
    ("Drought emergency declared in parts of Kenya as crops fail", "normal", "Kenya"),
    ("Chemical plant explosion near Mumbai, emergency response teams deployed", "explosion", "India"),
    ("Record snowstorm paralyses transport across northern Europe", "normal", "Europe"),
    ("Emergency declared after dam breach in Brazil, evacuation underway", "flood", "Brazil"),
    ("Australia bushfire season begins early, multiple fronts active in Queensland", "wildfire", "Australia"),
    ("Strong aftershocks continue in Turkey following yesterday's 5.9 magnitude quake", "earthquake", "Turkey"),
    ("Volcanic eruption on Indonesian island forces evacuation of 10,000 residents", "normal", "Indonesia"),
    ("Flash floods threaten Pakistan's Khyber Pakhtunkhwa province", "flood", "Pakistan"),
    ("Hurricane warning issued for Gulf Coast as category 3 system approaches", "hurricane", "United States"),
    ("Red Cross appeals for aid after cyclone devastates Mozambique coastline", "normal", "Africa"),
    ("Emergency services respond to multiple wildfires in Canadian province of British Columbia", "wildfire", "Canada"),
    ("Rescue teams search for survivors after landslide buries village in Peru", "normal", "Peru"),
    ("Severe thunderstorms and tornadoes reported across US midwest states", "tornado", "United States"),
    ("Pandemic preparedness alert issued by WHO following disease outbreak in DRC", "pandemic", "Africa"),
    ("Power grid failure leaves millions without electricity in Venezuela", "normal", "South America"),
    ("Emergency shelters opened as winter storm strikes South Korea", "normal", "South Korea"),
]

# Global mappings for basic geolocation
GLOBAL_LOCATIONS = {
    "United States": (37.0902, -95.7129), "China": (35.8617, 104.1954),
    "India": (20.5937, 78.9629), "Brazil": (-14.2350, -51.9253),
    "Russia": (61.5240, 105.3188), "Japan": (36.2048, 138.2529),
    "Germany": (51.1657, 10.4515), "France": (46.2276, 2.2137),
    "UK": (55.3781, -3.4360), "United Kingdom": (55.3781, -3.4360),
    "Italy": (41.8719, 12.5674), "Canada": (56.1304, -106.3468),
    "Australia": (-25.2744, 133.7751), "Spain": (40.4637, -3.7492),
    "Mexico": (23.6345, -102.5528), "Indonesia": (-0.7893, 113.9213),
    "Turkey": (38.9637, 35.2433), "Iran": (32.4279, 53.6880),
    "Pakistan": (30.3753, 69.3451), "Nigeria": (9.0820, 8.6753),
    "South Africa": (-30.5595, 22.9375), "Argentina": (-38.4161, -63.6167),
    "Egypt": (26.8206, 30.8025), "Vietnam": (14.0583, 108.2772),
    "Philippines": (12.8797, 121.7740), "Taiwan": (23.6978, 120.9605),
    "South Korea": (35.9078, 127.7669), "Ukraine": (48.3794, 31.1656),
    "Peru": (-9.1900, -75.0152), "Chile": (-35.6751, -71.5430),
    "Colombia": (4.5709, -74.2973), "Saudi Arabia": (23.8859, 45.0792),
    "Kenya": (-0.0236, 37.9062), "Global": (0.0, 0.0),
    "Europe": (54.5260, 15.2551), "Africa": (8.7832, 34.5085),
    "Asia": (34.0479, 100.6197), "North America": (54.5260, -105.2551),
    "South America": (-8.7832, -55.4915), "Mozambique": (-18.6657, 35.5296),
    "Venezuela": (6.4238, -66.5897), "DRC": (-4.0383, 21.7587),
}

SUBREDDITS = ["news", "worldnews", "earthquakes", "weather", "StormComing", "Emergency", "climate"]

# Per-source cooldown tracker
_source_last_called = {}
_source_cooldown = {
    "reddit": 30,   # 30 seconds between reddit calls
    "usgs":   60,   # 60 seconds (data changes slowly)
    "gdelt":  300,  # 5 minutes — heavy rate limit
    "rss":    120,  # 2 minutes
}


def _is_on_cooldown(source: str) -> bool:
    last = _source_last_called.get(source, 0)
    return (time.time() - last) < _source_cooldown.get(source, 60)


def _mark_called(source: str):
    _source_last_called[source] = time.time()


class RealTimeStreamer:
    """
    Multi-platform real-time streamer.
    Fetches from Reddit, USGS, GDELT, and News RSS with cooldowns.
    Falls back to synthetic data when APIs are unavailable / rate-limited.
    """

    def __init__(self):
        self.post_count = 0
        self.user_agent = 'python:crisisai:2.0 (by /u/CrisisBot)'
        self.seen_ids = set()

    def _extract_location(self, text: str) -> tuple:
        text_lower = text.lower()
        found = []
        for loc_name in GLOBAL_LOCATIONS.keys():
            if re.search(r'\b' + re.escape(loc_name.lower()) + r'\b', text_lower):
                found.append(loc_name)

        if 'london' in text_lower:   found.append("UK")
        elif 'paris' in text_lower:  found.append("France")
        elif 'tokyo' in text_lower:  found.append("Japan")
        elif 'new york' in text_lower or 'california' in text_lower: found.append("United States")

        if found:
            loc = found[0]
            lat, lon = GLOBAL_LOCATIONS[loc]
        else:
            loc = "Global"
            lat = random.uniform(-40, 60)
            lon = random.uniform(-180, 180)

        lat += random.uniform(-0.5, 0.5)
        lon += random.uniform(-0.5, 0.5)
        return loc, round(lat, 4), round(lon, 4)

    def _fetch_reddit(self, size: int) -> list:
        if not Config.ENABLE_REDDIT or _is_on_cooldown("reddit"):
            return []
        _mark_called("reddit")
        url = f"https://www.reddit.com/r/{'+'.join(SUBREDDITS)}/new.json?limit={size * 2}"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': self.user_agent})
            res = urllib.request.urlopen(req, timeout=10)
            data = json.loads(res.read())
            children = data.get('data', {}).get('children', [])
            posts = []
            for c in children:
                p = c['data']
                if p.get('id') not in self.seen_ids:
                    posts.append({
                        "id": f"reddit_{p.get('id', uuid.uuid4().hex[:6])}",
                        "text": (p.get('title', '') + ' ' + p.get('selftext', '')).strip(),
                        "platform": "reddit",
                        "user": p.get('author', 'reddit_user'),
                        "engagement": int(p.get('ups', 0)),
                        "raw_id": p.get('id'),
                    })
            print(f"[Streamer] Reddit: fetched {len(posts)} posts")
            return posts
        except Exception:
            return []

    def _fetch_usgs_earthquakes(self) -> list:
        if not Config.ENABLE_USGS or _is_on_cooldown("usgs"):
            return []
        _mark_called("usgs")
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_hour.geojson"
        try:
            res = urllib.request.urlopen(url, timeout=10)
            data = json.loads(res.read())
            features = data.get('features', [])
            posts = []
            for f in features:
                props = f['properties']
                eid = f['id']
                if eid not in self.seen_ids:
                    mag = props.get('mag', 0)
                    place = props.get('place', 'Unknown')
                    posts.append({
                        "id": f"usgs_{eid}",
                        "text": f"USGS Alert: Earthquake M{mag} near {place}. Status: {props.get('status', 'reported')}",
                        "platform": "usgs",
                        "user": "USGS_Official",
                        "engagement": 200,
                        "lat": f['geometry']['coordinates'][1],
                        "lon": f['geometry']['coordinates'][0],
                        "disaster_type": "earthquake",
                        "raw_id": eid,
                    })
            print(f"[Streamer] USGS: fetched {len(posts)} earthquakes")
            return posts
        except Exception:
            return []

    def _fetch_gdelt(self, size: int) -> list:
        if not Config.ENABLE_GDELT or _is_on_cooldown("gdelt"):
            return []
        _mark_called("gdelt")
        url = ("https://api.gdeltproject.org/api/v2/doc/doc"
               "?query=disaster+emergency+crisis&mode=artlist&format=json&maxrecords=15")
        try:
            res = urllib.request.urlopen(url, timeout=12)
            data = json.loads(res.read())
            articles = data.get('articles', [])
            posts = []
            for art in articles:
                uid = art.get('url', str(uuid.uuid4()))
                if uid not in self.seen_ids:
                    posts.append({
                        "id": f"gdelt_{uuid.uuid4().hex[:6]}",
                        "text": art.get('title', ''),
                        "platform": "gdelt",
                        "user": art.get('sourcecountry', 'GlobalNews'),
                        "engagement": random.randint(50, 500),
                        "raw_id": uid,
                    })
            print(f"[Streamer] GDELT: fetched {len(posts)} articles")
            return posts
        except Exception as e:
            # Only print unexpected errors, not routine rate limits / DNS
            if '429' not in str(e) and 'getaddrinfo' not in str(e):
                print(f"[Streamer] GDELT Error: {e}")
            return []

    def _fetch_rss(self) -> list:
        if not Config.ENABLE_NEWSAPI or _is_on_cooldown("rss"):
            return []
        _mark_called("rss")
        url = ("https://news.google.com/rss/search"
               "?q=disaster+OR+crisis+OR+emergency+OR+earthquake&hl=en-US&gl=US&ceid=US:en")
        try:
            res = urllib.request.urlopen(url, timeout=10)
            root = ET.fromstring(res.read())
            posts = []
            for item in root.findall('.//item'):
                title_el = item.find('title')
                link_el = item.find('link')
                if title_el is None or link_el is None:
                    continue
                title = title_el.text or ''
                link = link_el.text or uuid.uuid4().hex
                if link not in self.seen_ids:
                    posts.append({
                        "id": f"news_{uuid.uuid4().hex[:6]}",
                        "text": title,
                        "platform": "news",
                        "user": "GlobalNewsHub",
                        "engagement": random.randint(10, 200),
                        "raw_id": link,
                    })
            print(f"[Streamer] RSS News: fetched {len(posts)} articles")
            return posts
        except Exception:
            return []

    def _fetch_gdacs(self) -> list:
        if _is_on_cooldown("gdacs"):
            return []
        _mark_called("gdacs")
        try:
            feed = feedparser.parse('https://www.gdacs.org/xml/rss.xml')
            posts = []
            for entry in feed.entries[:10]:
                if entry.link not in self.seen_ids:
                    geo = entry.get('geo_lat', None)
                    lat = float(entry.geo_lat) if hasattr(entry, 'geo_lat') else 0.0
                    lon = float(entry.geo_long) if hasattr(entry, 'geo_long') else 0.0
                    
                    posts.append({
                        "id": f"gdacs_{uuid.uuid4().hex[:6]}",
                        "text": f"GDACS Alert: {entry.title}. {entry.description}",
                        "platform": "gdacs",
                        "user": "GDACS_Official",
                        "engagement": 300,
                        "lat": lat,
                        "lon": lon,
                        "raw_id": entry.link,
                    })
            print(f"[Streamer] GDACS: fetched {len(posts)} alerts")
            return posts
        except Exception as e:
            print(f"[Streamer] GDACS Error: {e}")
            return []

    def _fetch_reliefweb(self) -> list:
        if _is_on_cooldown("reliefweb"):
            return []
        _mark_called("reliefweb")
        try:
            url = "https://api.reliefweb.int/v1/reports?appname=crisisai&limit=10&preset=latest"
            response = requests.get(url, timeout=10)
            data = response.json()
            posts = []
            for item in data.get('data', []):
                fields = item.get('fields', {})
                link = item.get('href', uuid.uuid4().hex)
                if link not in self.seen_ids:
                    posts.append({
                        "id": f"rw_{uuid.uuid4().hex[:6]}",
                        "text": f"ReliefWeb Report: {fields.get('title', 'Crisis Update')}",
                        "platform": "reliefweb",
                        "user": "ReliefWeb",
                        "engagement": 150,
                        "raw_id": link,
                    })
            print(f"[Streamer] ReliefWeb: fetched {len(posts)} reports")
            return posts
        except Exception as e:
            print(f"[Streamer] ReliefWeb Error: {e}")
            return []

    def _synthetic_post(self) -> dict:
        """Generate one realistic synthetic post for fallback / bootstrap."""
        text, d_type, loc_name = random.choice(SYNTHETIC_TEXTS)
        lat, lon = GLOBAL_LOCATIONS.get(loc_name, (0.0, 0.0))
        lat += random.uniform(-2, 2)
        lon += random.uniform(-2, 2)
        platforms = ["reddit", "news", "twitter", "facebook", "instagram"]
        platform = random.choice(platforms)
        uid = f"syn_{uuid.uuid4().hex[:8]}"
        return {
            "id": uid,
            "text": text,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": f"user_{random.randint(1000, 9999)}",
            "location": loc_name,
            "lat": round(lat, 4),
            "lon": round(lon, 4),
            "retweets": random.randint(0, 500) if platform in ['twitter', 'reddit'] else 0,
            "likes": random.randint(0, 5000),
            "replies": random.randint(0, 500),
            "disaster_type": d_type,
            "platform": platform,
        }

    def _fetch_mock_socials(self, size: int) -> list:
        """Simulate real-time feeds from platforms without public APIs."""
        posts = []
        platforms = ['twitter', 'facebook', 'instagram']
        
        # We generate 1-3 posts per call to mix into the live stream
        for _ in range(random.randint(1, 4)):
            text, d_type, loc_name = random.choice(SYNTHETIC_TEXTS)
            lat, lon = GLOBAL_LOCATIONS.get(loc_name, (0.0, 0.0))
            platform = random.choice(platforms)
            
            # Format text based on platform style
            if platform == 'twitter':
                text = f"🚨 Breaking: {text} #{d_type} #{loc_name.replace(' ', '')}"
                user = f"user_{uuid.uuid4().hex[:4]}"
            elif platform == 'instagram':
                text = f"Stay safe everyone 🙏 {text} \n\n📸: shared by local\n#{d_type} #emergency"
                user = f"photo_{uuid.uuid4().hex[:4]}"
            else: # facebook
                text = f"Emergency update for {loc_name}: {text}. Please share with family and friends."
                user = f"Community_{loc_name.replace(' ', '')}"
                
            posts.append({
                "id": f"{platform}_{uuid.uuid4().hex[:6]}",
                "text": text,
                "platform": platform,
                "user": user,
                "engagement": random.randint(100, 5000),
                "lat": lat + random.uniform(-1, 1),
                "lon": lon + random.uniform(-1, 1),
                "disaster_type": d_type,
                "raw_id": str(uuid.uuid4())
            })
            
        print(f"[Streamer] Social Mocks: generated {len(posts)} posts (Twitter/FB/IG)")
        return posts

    def _format_post(self, raw: dict) -> dict:
        self.post_count += 1
        text = raw.get('text', '')

        if 'lat' in raw and 'lon' in raw:
            lat, lon = raw['lat'], raw['lon']
            loc_name = self._extract_location(text)[0]
        else:
            loc_name, lat, lon = self._extract_location(text)

        d_type = raw.get('disaster_type', 'normal')
        if d_type == 'normal':
            tl = text.lower()
            if 'flood' in tl:                       d_type = 'flood'
            elif 'fire' in tl or 'wildfire' in tl:  d_type = 'wildfire'
            elif 'hurricane' in tl or 'storm' in tl: d_type = 'hurricane'
            elif 'quake' in tl or 'earthquake' in tl: d_type = 'earthquake'
            elif 'tornado' in tl:                   d_type = 'tornado'
            elif 'tsunami' in tl:                   d_type = 'tsunami'
            elif 'pandemic' in tl or 'virus' in tl: d_type = 'pandemic'
            elif 'explo' in tl:                     d_type = 'explosion'

        return {
            "id": raw['id'],
            "text": text[:800],
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": raw.get('user', 'anonymous'),
            "location": loc_name,
            "lat": lat,
            "lon": lon,
            "retweets": raw.get('engagement', 0),
            "likes": int(raw.get('engagement', 0) * random.uniform(1.2, 3)),
            "replies": random.randint(0, 50),
            "disaster_type": d_type,
            "platform": raw['platform'],
        }

    def generate_batch(self, size: int = 20, force_crisis: bool = False) -> list:
        """Fetch a batch from all enabled sources; pad with synthetic data if needed."""
        pool = []
        pool.extend(self._fetch_reddit(size))
        pool.extend(self._fetch_usgs_earthquakes())
        pool.extend(self._fetch_gdelt(size))
        pool.extend(self._fetch_rss())
        pool.extend(self._fetch_gdacs())
        pool.extend(self._fetch_reliefweb())
        pool.extend(self._fetch_mock_socials(size))

        processed = []
        for p in pool:
            rid = p.get('raw_id')
            if rid not in self.seen_ids:
                processed.append(self._format_post(p))
                if rid:
                    self.seen_ids.add(rid)

        # Trim seen_ids if growing too large
        if len(self.seen_ids) > 2000:
            self.seen_ids = set(list(self.seen_ids)[-1000:])

        # Pad with synthetic posts if real data is sparse
        attempts = 0
        while len(processed) < size and attempts < size:
            processed.append(self._synthetic_post())
            attempts += 1

        random.shuffle(processed)
        return processed[:size]

    def generate_dataset(self, n: int = 500) -> list:
        """
        Fast bootstrap dataset. Uses synthetic data primarily and enriches
        with one round of real API calls.  Never blocks in a loop.
        """
        print(f"[Streamer] Generating bootstrap dataset of {n} posts...")
        dataset = []

        # Try one round of real data (non-blocking)
        try:
            real = self.generate_batch(size=50)
            dataset.extend(real)
            print(f"[Streamer] Got {len(real)} real posts for bootstrap")
        except Exception as e:
            print(f"[Streamer] Real fetch failed during bootstrap: {e}")

        # Fill remainder with synthetic posts instantly
        while len(dataset) < n:
            dataset.append(self._synthetic_post())

        random.shuffle(dataset)
        print(f"[Streamer] Bootstrap dataset ready: {len(dataset[:n])} posts")
        return dataset[:n]
