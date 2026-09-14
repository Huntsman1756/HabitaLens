"""Construccion de peticiones WFS 2.0 (KVP) usadas por los adaptadores."""

from __future__ import annotations

from habitalens.net import HttpRequest

FES_NS = "http://www.opengis.net/fes/2.0"
WFS_NS = "http://www.opengis.net/wfs/2.0"


def equals_filter(property_ref: str, literal: str, prefixes: dict[str, str] | None = None) -> str:
    prefixes = prefixes or {}
    declarations = "".join(
        f' xmlns:{prefix}="{uri}"' for prefix, uri in prefixes.items()
    )
    return (
        f'<fes:Filter xmlns:fes="{FES_NS}"{declarations}>'
        "<fes:PropertyIsEqualTo>"
        f"<fes:ValueReference>{property_ref}</fes:ValueReference>"
        f"<fes:Literal>{literal}</fes:Literal>"
        "</fes:PropertyIsEqualTo>"
        "</fes:Filter>"
    )


def get_feature_request(
    url: str,
    type_name: str,
    *,
    filter_xml: str | None = None,
    bbox: str | None = None,
    count: int | None = None,
    srs_name: str | None = None,
    version: str = "2.0.0",
) -> HttpRequest:
    params: list[tuple[str, str]] = [
        ("service", "WFS"),
        ("version", version),
        ("request", "GetFeature"),
        ("typeNames", type_name),
    ]
    if filter_xml:
        params.append(("filter", filter_xml))
    if bbox:
        params.append(("bbox", bbox))
    if count is not None:
        params.append(("count", str(count)))
    if srs_name:
        params.append(("srsName", srs_name))
    return HttpRequest(method="GET", url=url, params=tuple(params))


def capabilities_request(url: str, version: str = "2.0.0") -> HttpRequest:
    return HttpRequest(
        method="GET",
        url=url,
        params=(
            ("service", "WFS"),
            ("version", version),
            ("request", "GetCapabilities"),
        ),
    )


def bbox_value(minx: float, miny: float, maxx: float, maxy: float, crs: str) -> str:
    return f"{minx},{miny},{maxx},{maxy},{crs}"
