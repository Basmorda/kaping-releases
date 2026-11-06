"""Rassemble les fiches *.meta.json en un index.json lu par l'appli (liste des régions téléchargeables)."""
import glob
import json
import sys
import time

d = sys.argv[1]
regions = []
for f in sorted(glob.glob(f"{d}/*.meta.json")):
    m = json.load(open(f, encoding="utf-8"))
    if m.get("count", 0) > 0 and m.get("bbox"):
        regions.append(m)
print(json.dumps({"version": 1, "date": int(time.time() * 1000),
                  "attribution": "© contributeurs OpenStreetMap (ODbL)", "regions": regions}, ensure_ascii=False))
