"""Spike aislado osmnx: distancia a vias principales/fecrorcarril.

Una sola pregunta de producto. No toca el core. Punto de prueba: parcela DGC
G0-A (Paseo de la Castellana 255, Madrid).
"""

from __future__ import annotations

from shapely.geometry import Point

LAT, LON = 40.474018, -3.687913
EPSG = 25830


def main() -> None:
    import osmnx as ox

    print("osmnx", ox.__version__)
    point = Point(LON, LAT)
    tags = {"highway": ["motorway", "trunk", "primary", "secondary"], "railway": ["rail", "light_rail", "subway"]}
    try:
        gdf = ox.features_from_point((LAT, LON), tags=tags, dist=800)
    except Exception as exc:
        print("OSM_INCONCLUSIVE:", type(exc).__name__, str(exc)[:200])
        return
    if gdf is None or gdf.empty:
        print("OSM: sin features en 800 m")
        return

    print("features:", len(gdf), "| tipos:", sorted(set(gdf.geometry.geom_type)))
    metric = gdf.to_crs(EPSG)
    point_m = (
        __import__("geopandas").GeoSeries([point], crs="EPSG:4326").to_crs(EPSG).iloc[0]
    )
    distances = metric.distance(point_m)
    nearest = distances.idxmin()
    cols = [c for c in ("highway", "railway", "name") if c in metric.columns]
    print("nearest distance m:", round(float(distances.min()), 1))
    print("nearest attrs:", {c: metric.loc[nearest, c] for c in cols})
    for label, filt in (("major_roads", "highway"), ("rail", "railway")):
        subset = metric[metric[filt].notna()] if filt in metric.columns else metric.iloc[0:0]
        if not subset.empty:
            print(f"{label} nearest m:", round(float(subset.distance(point_m).min()), 1))


if __name__ == "__main__":
    main()
