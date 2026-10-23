#!/usr/bin/env python3
"""Build the place cells from a Geofabrik extract.

    python3 -I build.py work/europe-latest.osm.pbf <release-tag>

Filters the extract with osmium, sorts every place into its 5° x 5° cell and writes
out/<lat>_<lon>.json.deflate (raw DEFLATE, which Apple's NSData .zlib reads) plus
manifest.json (tracked, served by GitHub Pages). Needs osmium-tool on the PATH; standard library otherwise.
"""
import json
import math
import subprocess
import sys
import zlib
from datetime import date
from pathlib import Path

CELL = 5
NOTICE = ("Contains information from OpenStreetMap, © OpenStreetMap contributors, made available under the "
          "Open Database License (ODbL) 1.0: https://opendatacommons.org/licenses/odbl/1-0/")
FILTER = [
    "nwr/tourism=alpine_hut,wilderness_hut,camp_site,viewpoint",
    "nwr/amenity=drinking_water,shelter",
    "nwr/drinking_water=yes",
]
# Shelters a hiker cannot sit out a storm in.
NOT_SHELTER = {"public_transport", "picnic_shelter", "field_shelter", "sun_shelter", "pavilion", "gazebo",
               "changing_rooms", "parking"}
WATER_SOURCES = (("natural", "spring"), ("man_made", "water_tap"), ("amenity", "fountain"),
                 ("man_made", "water_well"))


def kind(t):
    """The app's kind for an element's tags, or None. First match wins: a hut with a tap is a hut."""
    if t.get("access") in ("private", "no"):
        return None
    tourism, amenity = t.get("tourism"), t.get("amenity")
    if tourism == "alpine_hut":
        return "hut"
    if tourism == "wilderness_hut" or (amenity == "shelter" and t.get("shelter_type") == "basic_hut"):
        return "bivouac"
    if tourism == "camp_site":
        return "campsite"
    if amenity == "shelter":
        bus = "public_transport" in t or t.get("bus") == "yes" or t.get("highway") == "bus_stop"
        return None if bus or t.get("shelter_type") in NOT_SHELTER else "shelter"
    if t.get("drinking_water") == "no":
        return None
    if amenity == "drinking_water" or (t.get("drinking_water") == "yes" and any(t.get(k) == v for k, v in WATER_SOURCES)):
        return "water"
    if tourism == "viewpoint":
        return "viewpoint"
    return None


def centre(geometry):
    """A point as itself, a line or area at the mean of its vertices (outer rings only)."""
    kind, c = geometry["type"], geometry["coordinates"]
    pts = {"Point": lambda: [c], "LineString": lambda: c, "Polygon": lambda: c[0],
           "MultiPolygon": lambda: [p for poly in c for p in poly[0]]}[kind]()
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def ele(t):
    try:
        return round(float(t["ele"].replace(",", ".").removesuffix("m").strip()))
    except (KeyError, ValueError):
        return None


def place(feature):
    """[kind, lat·1e5, lon·1e5, name?, ele?], trailing nulls dropped; None for what the app skips."""
    t = feature["properties"]
    k = kind(t)
    if not k:
        return None
    lon, lat = centre(feature["geometry"])
    row = [k, round(lat * 1e5), round(lon * 1e5), t.get("name"), ele(t) if k in ("hut", "bivouac") else None]
    while row[-1] is None:
        row.pop()
    return row


def main(pbf, release):
    out = Path("out")
    out.mkdir(exist_ok=True)
    filtered = Path("work/filtered.osm.pbf")
    subprocess.run(["osmium", "tags-filter", "--overwrite", "-o", filtered, pbf, *FILTER], check=True)
    # Areas need their nodes' positions; the export keeps every tag and writes one GeoJSON feature per line.
    export = subprocess.Popen(["osmium", "export", "-f", "geojsonseq", "-x", "print_record_separator=false",
                               "-a", "type,id", filtered], stdout=subprocess.PIPE, text=True)
    cells, seen = {}, set()
    for line in export.stdout:
        feature = json.loads(line)
        # A closed way exports as an area and, unless tagged area=no, not again as a line; a multipolygon
        # relation and its outer way can both carry the tags, so keep one place per name and spot.
        row = place(feature)
        if not row:
            continue
        key = (row[0], row[3] if len(row) > 3 else None, row[1] // 20, row[2] // 20)
        if key in seen:
            continue
        seen.add(key)
        cell = f"{math.floor(row[1] / 1e5 / CELL) * CELL}_{math.floor(row[2] / 1e5 / CELL) * CELL}"
        cells.setdefault(cell, []).append(row)
    if export.wait():
        sys.exit("osmium export failed")

    manifest = {"build": date.today().isoformat(), "release": release,
                "base": f"https://github.com/kenix/osm-places/releases/download/{release}/",
                "licence": "ODbL-1.0", "attribution": "© OpenStreetMap contributors",
                "cellDegrees": CELL, "cells": {}}
    for cell, rows in sorted(cells.items()):
        body = json.dumps({"build": manifest["build"], "licence": NOTICE, "places": rows}, ensure_ascii=False,
                          separators=(",", ":")).encode()
        packer = zlib.compressobj(9, zlib.DEFLATED, -15)  # raw DEFLATE: no zlib or gzip header
        data = packer.compress(body) + packer.flush()
        (out / f"{cell}.json.deflate").write_bytes(data)
        manifest["cells"][cell] = {"bytes": len(data), "places": len(rows)}
    Path("manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    kinds = {}
    for rows in cells.values():
        for r in rows:
            kinds[r[0]] = kinds.get(r[0], 0) + 1
    total = sum(c["bytes"] for c in manifest["cells"].values())
    print(f"{len(cells)} cells, {sum(kinds.values())} places, {total / 1e6:.1f} MB, largest "
          f"{max(c['bytes'] for c in manifest['cells'].values()) / 1e6:.2f} MB", kinds)


if __name__ == "__main__":
    main(*sys.argv[1:3])
