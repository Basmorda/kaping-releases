"""Liste des régions à extraire (matrice GitHub Actions), d'après l'index de Geofabrik.

Pour chaque pays du continent : le pays entier s'il n'a pas de subdivisions,
sinon ses subdivisions de premier niveau (régions françaises, Länder allemands…),
pour garder des fichiers petits à télécharger sur le téléphone.

Usage : python3 pois_liste.py "europe"            (continents ou pays, séparés par des virgules)
Sortie : matrix=[{...}, ...] à ajouter à $GITHUB_OUTPUT
"""
import json
import sys
import urllib.request

zones = [z.strip() for z in (sys.argv[1] if len(sys.argv) > 1 else "").split(",") if z.strip()] or ["europe"]
req = urllib.request.Request("https://download.geofabrik.de/index-v1-nogeom.json",
                             headers={"User-Agent": "LoupRide-pois/1.0 (+https://github.com/Basmorda/kaping-releases)"})
feats = json.load(urllib.request.urlopen(req, timeout=60))["features"]
by_id = {f["properties"]["id"]: f["properties"] for f in feats}
children = {}
for p in by_id.values():
    if p.get("parent"):
        children.setdefault(p["parent"], []).append(p)


def item(p, country):
    return {"id": p["id"], "name": p["name"], "country": country["id"], "countryName": country["name"],
            "url": p["urls"]["pbf"]}


out = []
for z in zones:
    if z not in by_id:
        print(f"zone inconnue : {z}", file=sys.stderr)
        continue
    # une zone qui a des pays comme enfants (continent) ou bien un pays directement
    countries = children.get(z, []) if by_id[z].get("parent") is None else [by_id[z]]
    for c in sorted(countries, key=lambda p: p["id"]):
        subs = children.get(c["id"], [])
        if subs:
            out += [item(s, c) for s in sorted(subs, key=lambda p: p["id"])]
        else:
            out.append(item(c, c))

if len(out) > 256:
    print(f"{len(out)} régions : trop pour une seule matrice (256 max)", file=sys.stderr)
    out = out[:256]
print("matrix=" + json.dumps(out, ensure_ascii=False))
print(f"{len(out)} régions", file=sys.stderr)
