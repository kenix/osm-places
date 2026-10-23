# OSM places — source and licence

These files are data, not program code. They are published separately from
any application binary and are downloaded by the app when needed.

Contains information from **OpenStreetMap**, © OpenStreetMap contributors,
made available under the **Open Database License (ODbL) 1.0**.

- Source: https://www.openstreetmap.org, via the Geofabrik extracts at
  https://download.geofabrik.de
- Licence: https://opendatacommons.org/licenses/odbl/1-0/
- Copyright and attribution: https://www.openstreetmap.org/copyright
- Modifications: reduced to six kinds of place (see `README.md`), each with
  its position rounded to 1e-5°, its name and, for huts, its height; lines
  and areas replaced by a single point.

**Share-alike:** these cells are a derived database and are themselves
licensed under the ODbL 1.0. `build.py` in this repository reproduces them
from the public extract. The notice also travels inside every cell, in its
`licence` field.

An app that shows these places credits "© OpenStreetMap contributors" where
they appear.
