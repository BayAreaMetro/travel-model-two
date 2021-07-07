# Intro
This is a description for SF county link database sf_link_with_tomtom_lanes_for_Dave.geojson.  The primary purpose is to observe TomTom conflation and Lane info.

The links are developed based on Shared Streets geometries, so there are links consisting of multiple OSM edges, and the corresponding OSM attributes are engineered as list of values.

TomTom data was conflated using SHST match.  For SF county, the combination of TomTom's ['ID', 'F_JNCTID', 'T_JNCTID'] is sufficient to serve as unique TomTom handle.  For the entire Bay Area, user will need to create new unique TomTom handle.


## 'shstReferenceId', 'shstGeometryId', 'fromIntersectionId', 'toIntersectionId'

Shared Streets IDs


## 'wayId'

OSM way id for edges.


## 'u', 'v', 'highway', "lanes", "name"

OSM sample attributes.


## "tomtom_id", "tomtom_f_jnctid", "tomtom_t_jnctid"

TomTom IDs, the combination can be used as unique handle for SF county.


## "LANES"

TomTom # lanes.
