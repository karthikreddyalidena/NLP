"""
Disaster-related keywords organized by category and severity.
Used for crisis scoring and data generation.
"""

DISASTER_CATEGORIES = {
    "earthquake": {
        "primary": ["earthquake", "quake", "tremor", "seismic", "aftershock", "magnitude", "richter"],
        "secondary": ["building collapse", "trapped", "rubble", "debris", "evacuation", "shelter"],
        "severity_weight": 0.9
    },
    "flood": {
        "primary": ["flood", "flooding", "inundation", "flash flood", "storm surge", "deluge"],
        "secondary": ["stranded", "rescue", "boats", "rising water", "evacuation", "dam break"],
        "severity_weight": 0.80
    },
    "hurricane": {
        "primary": ["hurricane", "typhoon", "cyclone", "tropical storm", "category 4", "category 5"],
        "secondary": ["landfall", "storm surge", "mandatory evacuation", "wind speed", "eye wall"],
        "severity_weight": 0.85
    },
    "wildfire": {
        "primary": ["wildfire", "forest fire", "bushfire", "inferno", "blaze", "fire spread"],
        "secondary": ["evacuate", "air quality", "smoke", "containment", "firefighters", "acres burned"],
        "severity_weight": 0.80
    },
    "tornado": {
        "primary": ["tornado", "twister", "funnel cloud", "EF5", "EF4", "EF3", "vortex"],
        "secondary": ["shelter in place", "debris", "path of destruction", "mobile home", "warning"],
        "severity_weight": 0.88
    },
    "tsunami": {
        "primary": ["tsunami", "tidal wave", "wave surge", "inundation", "seawave"],
        "secondary": ["coastal evacuation", "warning siren", "high ground", "ocean receding"],
        "severity_weight": 0.92
    },
    "explosion": {
        "primary": ["explosion", "blast", "detonation", "bomb", "gas explosion", "chemical plant"],
        "secondary": ["casualties", "injuries", "evacuate", "hazmat", "emergency response"],
        "severity_weight": 0.87
    },
    "pandemic": {
        "primary": ["outbreak", "pandemic", "epidemic", "virus", "pathogen", "contagion"],
        "secondary": ["quarantine", "lockdown", "deaths", "hospitalizations", "spread"],
        "severity_weight": 0.83
    }
}

URGENCY_KEYWORDS = [
    "emergency", "urgent", "help", "SOS", "trapped", "dying", "critical", "immediate",
    "now", "please help", "rescue", "mayday", "distress", "need assistance", "life threatening"
]

GEOGRAPHIC_INDICATORS = [
    "downtown", "north", "south", "east", "west", "district", "county", "city",
    "zone", "region", "area", "neighborhood", "suburb", "village", "town"
]

NEGATIVE_SENTIMENT_AMPLIFIERS = [
    "devastating", "catastrophic", "deadly", "fatal", "massive", "severe", "extreme",
    "crisis", "disaster", "tragedy", "chaos", "panic", "fear", "terror", "horrible",
    "worst", "destroyed", "obliterated", "unprecedented", "alarming"
]

POSITIVE_RECOVERY_KEYWORDS = [
    "safe", "rescued", "recovered", "stable", "improving", "contained", "relief",
    "aid", "support", "volunteer", "donate", "help arriving", "under control"
]

ALL_DISASTER_KEYWORDS = []
for cat, data in DISASTER_CATEGORIES.items():
    ALL_DISASTER_KEYWORDS.extend(data["primary"])
    ALL_DISASTER_KEYWORDS.extend(data["secondary"])

ALL_KEYWORDS = list(set(ALL_DISASTER_KEYWORDS + URGENCY_KEYWORDS + NEGATIVE_SENTIMENT_AMPLIFIERS))
