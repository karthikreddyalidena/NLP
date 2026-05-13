import requests, json, statistics

base = 'http://127.0.0.1:5000'

print("=== SYSTEM STATUS ===")
s = requests.get(f'{base}/api/status').json()
print(json.dumps(s, indent=2))

print("\n=== CRISIS STATS ===")
cs = requests.get(f'{base}/api/crisis_stats').json()
print(json.dumps(cs, indent=2))

print("\n=== ALERTS ===")
al = requests.get(f'{base}/api/alerts').json()
print(f"Total alerts: {len(al)}")
if al:
    by_sev = {}
    for a in al:
        lvl = a.get('severity_level','?')
        by_sev[lvl] = by_sev.get(lvl,0)+1
    print("By severity:", json.dumps(by_sev, indent=2))
    print("Sample alert:")
    print(json.dumps(al[0], indent=2))

print("\n=== GEO / DISTRESS STATS ===")
geo = requests.get(f'{base}/api/geo').json()
print(f"Total geo points: {len(geo)}")
if geo:
    distress_vals = [g['distress'] for g in geo]
    print(f"Mean distress:  {statistics.mean(distress_vals):.4f}")
    print(f"Max distress:   {max(distress_vals):.4f}")
    print(f"Min distress:   {min(distress_vals):.4f}")
    if len(distress_vals) > 1:
        print(f"Stdev distress: {statistics.stdev(distress_vals):.4f}")
    high_distress = [d for d in distress_vals if d > 0.65]
    print(f"High distress posts (>0.65): {len(high_distress)} ({100*len(high_distress)/len(distress_vals):.1f}%)")
    types = {}
    for g in geo:
        t = g.get('type','unknown')
        types[t] = types.get(t,0)+1
    print("Disaster type distribution:")
    for k,v in sorted(types.items(), key=lambda x:-x[1]):
        print(f"  {k:15s}: {v:3d}  ({100*v/len(geo):.1f}%)")

print("\n=== TOPIC LABELS ===")
topics = requests.get(f'{base}/api/topics').json()
for t in topics:
    print(f"  [{t['topic_id']}] {t['label']}")

print("\n=== CLUSTER PROFILES ===")
try:
    cp = requests.get(f'{base}/api/cluster_profiles').json()
    if isinstance(cp, dict) and cp:
        print(json.dumps(cp, indent=2))
    else:
        print("No cluster profiles yet.")
except Exception as e:
    print(f"Error: {e}")
