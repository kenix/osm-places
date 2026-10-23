# OSM places

Places a hiker looks for, from OpenStreetMap, packed so an app can find them
on the device: huts, bivouacs, shelters, drinking water, campsites and
viewpoints. Trail Trove reads them; nothing in here is specific to it.

Published as GitHub Release assets, one release per build. **The data is not
in this repository**: a release asset can be replaced, while binaries in the
history are in every clone for ever. What is here is the build script, the
manifest and the licence notice.

| File | What it is |
|---|---|
| `build.py` | Builds the cells from a Geofabrik extract (`osmium-tool`, Python standard library) |
| `manifest.json` | The current release and every cell in it, with sizes and counts |
| `ATTRIBUTION.md` | Source and licence |

## Using it

`manifest.json` is served from GitHub Pages:

```
https://kenix.github.io/osm-places/manifest.json
```

A cell covers 5° × 5° and is named by its south-west corner, `floor(lat / 5) * 5`
and `floor(lon / 5) * 5`, so Zurich (47.4, 8.5) lies in `45_5`. Its file is

```
<base><lat>_<lon>.json.deflate
```

with `base` from the manifest. A cell missing from the manifest holds no data
(sea, or outside the extract). A cell is raw DEFLATE (no zlib or gzip header;
Apple's `NSData.decompressed(using: .zlib)` reads it) of

```json
{"build": "2026-10-23b", "licence": "…", "places": [["hut", 4610942, 788880, "Mischabelhütte", 3340, "n240063383"], ["water", 4737000, 854000, null, null, "n1234"]]}
```

Each place is `[kind, lat·1e5, lon·1e5, name, ele, osm]`. `ele` (metres) is
kept for huts and bivouacs only. `osm` is the OpenStreetMap element, `n`, `w`
or `r` and its id, so `w123` is `https://www.openstreetmap.org/way/123`.

The manifest's `format` is 2 since `osm` was added (`places-2026-10-23b`); a
manifest without it is format 1, whose rows end after `ele` with trailing nulls
dropped. A reader skips fields it does not know, so a new field goes at the end.
`build` is the release name without `places-`.

| Kind | OpenStreetMap tags |
|---|---|
| `hut` | `tourism=alpine_hut` |
| `bivouac` | `tourism=wilderness_hut`, `amenity=shelter` + `shelter_type=basic_hut` |
| `shelter` | `amenity=shelter`, not a bus, picnic, field, sun or parking shelter |
| `water` | `amenity=drinking_water`; a spring, tap, fountain or well with `drinking_water=yes` |
| `campsite` | `tourism=camp_site` |
| `viewpoint` | `tourism=viewpoint` |

Never `access=private|no`, never `drinking_water=no`. Ways and areas sit at the
mean of their outer ring.

## Building a release

```sh
brew install osmium-tool
python3 -c "import urllib.request as u; u.urlretrieve('https://download.geofabrik.de/europe-latest.osm.pbf', 'work/europe-latest.osm.pbf')"
python3 -I build.py work/europe-latest.osm.pbf places-<yyyy-mm-dd>
gh release create places-<yyyy-mm-dd> out/*.json.deflate --notes-file ATTRIBUTION.md
git commit -am "release: places-<yyyy-mm-dd>" && git push   # the manifest goes live with Pages
```

Upload the release before pushing the manifest: an app reads the manifest
first. About once a quarter; Europe only for now.
