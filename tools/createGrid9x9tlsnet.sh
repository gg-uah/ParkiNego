#!/bin/bash
netconvert --osm grid9x9.osm \
--output-file grid9x9tls.net.xml \
--tls.guess true \
--no-internal-links true \

netconvert --osm grid9x9.osm \
--output-file grid9x9tls.net.xml \
--tls.guess true \
--no-internal-links true \
--tls.set `./get_all_edge_id.py grid9x9tls.net.xml`
