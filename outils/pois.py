"""Transforme un extrait OpenStreetMap (GeoJSON séquentiel produit par « osmium export »)
en fichier de points d'intérêt LoupRide : [[lat, lon, type, nom], ...] compressé en gzip.

Les règles de tri sont les mêmes que dans l'appli (Pois.classify).
Usage : python3 pois.py f.geojsonseq <id> <nom> <pays> <nom du pays> <dossier de sortie>
"""
import gzip
import json
import os
import sys
import time

src, rid, name, country, country_name, outdir = sys.argv[1:7]


def classify(t):
    a = t.get("amenity", "")
    s = t.get("shop", "")
    if s == "bakery":
        return "bakery"
    if s in ("supermarket", "convenience"):
        return "shop"
    if t.get("landuse") == "cemetery" or a == "grave_yard":
        return "cemetery"
    if a == "toilets":
        return "toilets"
    if s == "bicycle" or a == "bicycle_repair_station":
        return "repair"
    if a in ("cafe", "bar", "pub"):
        return "cafe"
    if a == "shelter":
        return None if t.get("shelter_type") == "public_transport" else "shelter"
    if t.get("tourism") == "camp_site":
        return "camping"
    if a in ("drinking_water", "water_point") or t.get("man_made") == "water_tap":
        return None if t.get("drinking_water") == "no" else "water"
    return None


def center(g):
    """Point représentatif : le point lui-même, ou la moyenne des sommets du contour extérieur."""
    tp, c = g["type"], g["coordinates"]
    if tp == "Point":
        return c
    if tp == "LineString":
        ring = c
    elif tp == "Polygon":
        ring = c[0]
    elif tp == "MultiPolygon":
        ring = max((p[0] for p in c), key=len)
    else:
        return None
    if not ring:
        return None
    return [sum(p[0] for p in ring) / len(ring), sum(p[1] for p in ring) / len(ring)]


pts, seen = [], set()
with open(src, encoding="utf-8") as f:
    for line in f:
        line = line.strip().lstrip("\x1e")
        if not line:
            continue
        try:
            feat = json.loads(line)
        except ValueError:
            continue
        tags = feat.get("properties") or {}
        kind = classify(tags)
        if not kind:
            continue
        c = center(feat.get("geometry") or {})
        if not c:
            continue
        lon, lat = round(c[0], 5), round(c[1], 5)
        key = (lat, lon, kind)
        if key in seen:
            continue
        seen.add(key)
        pts.append([lat, lon, kind, (tags.get("name") or "")[:60]])

os.makedirs(outdir, exist_ok=True)
data = json.dumps(pts, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
fname = f"{rid}.json.gz"
with gzip.open(os.path.join(outdir, fname), "wb", compresslevel=9) as g:
    g.write(data)
meta = {
    "id": rid, "name": name, "country": country, "countryName": country_name, "file": fname,
    "count": len(pts), "bytes": os.path.getsize(os.path.join(outdir, fname)), "date": int(time.time() * 1000),
    "bbox": [min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts)] if pts else None,
}
with open(os.path.join(outdir, f"{rid}.meta.json"), "w", encoding="utf-8") as m:
    json.dump(meta, m, ensure_ascii=False)
print(f"{rid} : {len(pts)} points, {meta['bytes'] // 1024} Ko")
