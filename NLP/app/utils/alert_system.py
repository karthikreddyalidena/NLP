"""
Alert system: manages alert deduplication, routing, and escalation.
"""

from datetime import datetime
from collections import deque


class AlertManager:
    def __init__(self, max_alerts=500):
        self.alerts = deque(maxlen=max_alerts)
        self.active_incidents = {}

    def add_alert(self, alert: dict):
        if alert:
            alert['display_time'] = datetime.utcnow().strftime('%H:%M:%S')
            self.alerts.appendleft(alert)
            # Track active incidents
            key = f"{alert.get('location')}_{alert.get('disaster_type')}"
            self.active_incidents[key] = alert

    def get_recent(self, n=20):
        return list(self.alerts)[:n]

    def get_active_incidents(self):
        return list(self.active_incidents.values())

    def get_counts_by_severity(self):
        counts = {'CRITICAL': 0, 'HIGH': 0, 'MODERATE': 0, 'LOW': 0}
        for a in self.alerts:
            lvl = a.get('severity_level', 'LOW')
            if lvl in counts:
                counts[lvl] += 1
        return counts

    def clear_old(self):
        self.active_incidents = {}
