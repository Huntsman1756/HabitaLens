"""Contrato EvidenceSource + guarda de licencia para fuentes G0-B.

Regla: licencia y acceso antes que parsing. Una fuente sin ``LICENSE.yaml``
valido no puede inicializarse. Una fuente con licencia no declarada o sin
servicio verificable se marca ``usable=False`` y el motor solo emite
INCONCLUSIVE para ella.
"""

from __future__ import annotations

import inspect
import json
import math
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path

from habitalens.cache import CacheStore
from habitalens.config import load_endpoints
from habitalens.evidence.models import EvidenceFinding
from habitalens.licensing import LicenseDeclaration, load_license
from habitalens.net import HttpRequest, HttpSource, Source
from habitalens.provenance import ProvenanceRecorder


def _response_count(value) -> int:
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError("invalid response count")
    if isinstance(value, str) and (not value or not value.isascii() or not value.isdecimal()):
        raise ValueError("invalid response count")
    count = int(value)
    if count < 0:
        raise ValueError("invalid response count")
    return count


def _validate_completeness(data: dict, size: int, limit: int | None = None, *, page: bool = False) -> None:
    for key in ("error", "errors", "exception", "exceptions"):
        if key in data:
            raise ValueError("source returned an error response")
    # hasMore/truncated no son senales seguibles: invalidan la pagina incluso
    # en modo paginado. next/exceededTransferLimit/links los gestiona el
    # paginador y solo se toleran con page=True.
    for key in ("hasMore", "truncated"):
        if key in data and data[key] not in (False, "false", "0"):
            raise ValueError("incomplete source response")
    if not page:
        if "exceededTransferLimit" in data and data["exceededTransferLimit"] not in (False, "false", "0"):
            raise ValueError("incomplete source response")
        for key in ("next", "nextPage", "nextRecord"):
            if data.get(key):
                raise ValueError("paginated source response")
        links = data.get("links", [])
        if not isinstance(links, list) or any(not isinstance(link, dict) for link in links):
            raise ValueError("invalid response links")
        if any(link.get("rel") == "next" for link in links):
            raise ValueError("paginated source response")
    total_known = False
    for key in ("numberReturned", "numberMatched", "totalFeatures", "numberOfFeatures", "count"):
        if key not in data:
            continue
        if data[key] == "unknown" and key in {"numberMatched", "totalFeatures"}:
            continue
        if _response_count(data[key]) != size:
            raise ValueError("incomplete or inconsistent response count")
        if key in {"numberMatched", "totalFeatures", "count"}:
            total_known = True
    if limit is not None and size >= limit and not total_known:
        raise ValueError("response reached request limit without a complete total")


def json_features(content: bytes, *, limit: int | None = None, page: bool = False) -> list[dict]:
    data = json.loads(content.decode("utf-8"))
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise ValueError("expected a feature collection")
    features = data.get("features")
    if not isinstance(features, list):
        raise ValueError("missing or invalid feature list")
    _validate_completeness(data, len(features), limit, page=page)
    if "properties" in data:
        if not isinstance(data["properties"], dict):
            raise ValueError("invalid collection metadata")
        _validate_completeness(data["properties"], len(features), page=page)
    for feature in features:
        if not isinstance(feature, dict) or feature.get("type") != "Feature":
            raise ValueError("invalid feature")
        if "properties" not in feature or not isinstance(feature["properties"], (dict, type(None))):
            raise ValueError("invalid feature properties")
    return features


def feature_geometry(feature: dict, allowed_types: set[str]):
    from shapely import get_coordinates, make_valid, union_all
    from shapely.geometry import shape

    data = feature.get("geometry")
    if not isinstance(data, dict) or data.get("type") not in allowed_types:
        raise ValueError("missing or unsupported feature geometry")
    geometry = shape(data)

    # Las fuentes publicas entregan geometrias reales con autointersecciones y
    # miembros degenerados; se reparan y se descartan remanentes sin area.
    # Un componente que pierde area real o una feature sin nada interpretable
    # invalidan la respuesta: no se cuentan resultados parciales.
    parts = list(getattr(geometry, "geoms", None) or [geometry])
    kept = []
    for part in parts:
        if part.is_empty:
            continue
        if not all(
            math.isfinite(value) for row in get_coordinates(part) for value in row
        ):
            raise ValueError("invalid feature geometry")
        try:
            area = part.area
        except Exception:
            area = float("nan")
        candidate = part if part.is_valid else make_valid(part)
        components = list(getattr(candidate, "geoms", None) or [candidate])
        usable = [c for c in components if c.geom_type in allowed_types and not c.is_empty]
        if not usable:
            if not math.isfinite(area) or area > 0:
                raise ValueError("invalid feature geometry")
            continue
        if any(c.geom_type not in allowed_types and not c.is_empty and c.area > 0
               for c in components):
            raise ValueError("invalid feature geometry")
        kept.extend(usable)
    if not kept:
        raise ValueError("invalid feature geometry")
    geometry = union_all(kept)
    if (
        geometry.is_empty
        or not geometry.is_valid
        or not all(math.isfinite(value) for row in get_coordinates(geometry) for value in row)
    ):
        raise ValueError("invalid feature geometry")
    return geometry


def xml_features(content: bytes, names: set[str], *, limit: int, page: bool = False) -> list[ET.Element]:
    from habitalens.cadastre_providers.inspire import localname

    root = ET.fromstring(content)
    if localname(root.tag) != "FeatureCollection":
        raise ValueError("expected a feature collection")
    if any(
        localname(element.tag) in {"ExceptionReport", "Exception", "ServiceExceptionReport", "ServiceException"}
        for element in root.iter()
    ):
        raise ValueError("source returned an XML exception")
    features = []
    for child in root:
        name = localname(child.tag)
        if name == "boundedBy":
            continue
        if name not in {"member", "featureMember", "featureMembers"}:
            raise ValueError("unexpected feature collection member")
        members = list(child)
        if not members or (name != "featureMembers" and len(members) != 1):
            raise ValueError("missing or invalid feature member")
        if any(localname(member.tag) not in names for member in members):
            raise ValueError("unexpected feature type")
        features.extend(members)
    _validate_completeness(
        {localname(key): value for key, value in root.attrib.items()},
        len(features),
        limit,
        page=page,
    )
    return features


def wfs_next_request(request: HttpRequest, content: bytes) -> HttpRequest | None:
    """Siguiente pagina WFS: atributo ``next`` de la FeatureCollection raiz."""
    from habitalens.cadastre_providers.inspire import localname

    root = ET.fromstring(content)
    if localname(root.tag) != "FeatureCollection":
        raise ValueError("expected a feature collection")
    href = root.get("next")
    if not href:
        return None
    return HttpRequest(method="GET", url=href)


def arcgis_next_request(request: HttpRequest, content: bytes) -> HttpRequest | None:
    """Siguiente pagina JSON: ``exceededTransferLimit``/``resultOffset`` o ``next``.

    Soporta la paginacion ArcGIS REST (``exceededTransferLimit`` +
    ``resultOffset``, reescrito dentro del cuerpo POST si la peticion lo es) y
    enlaces ``next``/``links[rel=next]`` estilo OGC API. Una pagina que declara
    mas datos pero devuelve 0 features, o una senal de paginacion que no puede
    seguirse, se rechaza en vez de aceptar el resultado parcial.
    """
    from urllib.parse import parse_qsl, urlencode

    data = json.loads(content.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("invalid paged response")

    href = data.get("next") or data.get("nextPage") or data.get("nextRecord")
    if href is None:
        links = data.get("links")
        if isinstance(links, list):
            href = next(
                (link.get("href") for link in links
                 if isinstance(link, dict) and link.get("rel") == "next"),
                None,
            )
    if href is not None:
        if not isinstance(href, str) or not href.startswith("http"):
            raise ValueError("invalid pagination link")
        return HttpRequest(method="GET", url=href)

    exceeded = data.get("exceededTransferLimit")
    properties = data.get("properties")
    if isinstance(properties, dict):
        exceeded = exceeded or properties.get("exceededTransferLimit")
    if not exceeded:
        return None
    features = data.get("features")
    returned = len(features) if isinstance(features, list) else 0
    if not returned:
        raise ValueError("paginated response without features")
    if request.data is not None:
        fields = parse_qsl(request.data.decode("utf-8"), keep_blank_values=True)
        previous = next(
            (int(v) for k, v in fields if k == "resultOffset" and v.isdigit()), 0
        )
        body = urlencode(
            [(k, v) for k, v in fields if k != "resultOffset"]
            + [("resultOffset", str(previous + returned))]
        ).encode()
        return HttpRequest(
            method=request.method, url=request.url, params=request.params,
            data=body, headers=request.headers,
        )
    params = [(k, v) for k, v in request.params if k != "resultOffset"]
    previous = next((int(v) for k, v in request.params if k == "resultOffset" and v.isdigit()), 0)
    return HttpRequest(
        method=request.method,
        url=request.url,
        params=(*params, ("resultOffset", str(previous + returned))),
        data=request.data,
        headers=request.headers,
    )


def arcgis_polygon(geometry) -> dict:
    """Geometria de parcela WGS84 como poligono JSON Esri para ArcGIS REST."""
    parts = [geometry] if geometry.geom_type == "Polygon" else [
        part for part in getattr(geometry, "geoms", []) if part.geom_type == "Polygon"
    ]
    if not parts:
        raise ValueError("property geometry has no polygonal part")
    rings = []
    for polygon in parts:
        rings.append([list(coord) for coord in polygon.exterior.coords])
        rings.extend([list(coord) for coord in ring.coords] for ring in polygon.interiors)
    return {"rings": rings, "spatialReference": {"wkid": 4326}}


def xml_positions(element: ET.Element) -> list[list[tuple[float, float]]]:
    from habitalens.cadastre_providers.inspire import localname

    positions = []
    for child in element.iter():
        if child.get("srsDimension", "2") != "2":
            raise ValueError("unsupported response dimension")
        if localname(child.tag) != "posList":
            continue
        numbers = [float(part) for part in (child.text or "").split()]
        if len(numbers) < 4 or len(numbers) % 2 or not all(map(math.isfinite, numbers)):
            raise ValueError("invalid response positions")
        coords = [(numbers[i + 1], numbers[i]) for i in range(0, len(numbers), 2)]
        if "count" in child.attrib and _response_count(child.attrib["count"]) != len(coords):
            raise ValueError("inconsistent position count")
        positions.append(coords)
    if not positions:
        raise ValueError("missing response positions")
    return positions


class SourceUnavailableError(RuntimeError):
    """La fuente no puede aportar dato aplicable (no es INCONCLUSIVE)."""


class EvidenceSource(ABC):
    source_id: str = ""

    def __init__(
        self,
        source: Source | None = None,
        cache: CacheStore | None = None,
        provenance: ProvenanceRecorder | None = None,
        refresh: bool = False,
    ):
        if not self.source_id:
            raise ValueError(f"{type(self).__name__} no define source_id")
        self.package_dir = Path(inspect.getfile(type(self))).parent
        self.license: LicenseDeclaration = load_license(self.package_dir)
        self._cache = cache or getattr(source, "cache", None) or CacheStore()
        self.source: Source = source or HttpSource(cache=self._cache)
        self.provenance = provenance or ProvenanceRecorder(self._cache.root)
        self.refresh = refresh
        self.config = load_endpoints()["evidence_sources"][self.source_id]
        self.usable: bool = bool(self.config.get("usable", True))
        self.unusable_reason: str | None = self.config.get("unusable_reason")

    def source_version(self) -> str:
        return str(self.config["source_version"])

    @abstractmethod
    def evaluate(
        self,
        geometry,
        source_crs: str,
        operational_crs: str,
        property_id: str,
    ) -> list[EvidenceFinding]:
        ...

    def _fetch(
        self,
        kind: str,
        key: str,
        request: HttpRequest,
        *,
        ext: str = "json",
    ) -> bytes:
        # La clave incluye un hash de la peticion (url+params+cuerpo): cambiar
        # bbox, radio o capa nunca reutiliza una respuesta cacheada obsoleta.
        import hashlib

        material = f"{request.url}?{request.query_string()}".encode() + (request.data or b"")
        digest = hashlib.sha256(material).hexdigest()[:10]
        return self.source.fetch(
            self.source_id,
            f"{kind}:{key}:{digest}",
            request,
            refresh=self.refresh,
            ext=ext,
            meta={"source": self.source_id, "kind": kind, "key": key},
        )

    def _fetch_pages(
        self,
        kind: str,
        property_id: str,
        request: HttpRequest,
        next_request,
        *,
        max_pages: int = 8,
        ext: str = "json",
    ) -> list[tuple[bytes, str]]:
        """Fetch paginado: sigue ``next_request`` hasta agotar paginas.

        Cada pagina queda cacheada y registrada en procedencia con su propia
        peticion. Si el servicio no termina de paginar, se rechaza la respuesta
        (max_pages) en vez de aceptar un resultado incompleto.
        """
        pages = []
        current = request
        for index in range(max_pages):
            content = self._fetch(kind, f"{property_id}:{kind}#p{index}", current, ext=ext)
            provenance_id = self._record(kind, property_id, current, content)
            pages.append((content, provenance_id))
            current = next_request(current, content)
            if current is None:
                return pages
        raise ValueError(f"pagination limit reached after {max_pages} pages")

    def _record(self, kind: str, property_id: str, request: HttpRequest, content: bytes) -> str:
        record = self.provenance.record(
            provider=self.source_id,
            territory="multi",
            kind=kind,
            source_version=self.source_version(),
            crs=str(self.config.get("default_crs", "EPSG:4326")),
            refcat=property_id,
            url=request.url,
            request_params=request.params,
            offline=self.source.offline,
            content=content,
        )
        return record.provenance_id
