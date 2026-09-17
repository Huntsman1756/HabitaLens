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


def _validate_completeness(data: dict, size: int, limit: int | None = None) -> None:
    for key in ("error", "errors", "exception", "exceptions"):
        if key in data:
            raise ValueError("source returned an error response")
    for key in ("exceededTransferLimit", "hasMore", "truncated"):
        if key in data and data[key] not in (False, "false", "0"):
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


def json_features(content: bytes, *, limit: int | None = None) -> list[dict]:
    data = json.loads(content.decode("utf-8"))
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        raise ValueError("expected a feature collection")
    features = data.get("features")
    if not isinstance(features, list):
        raise ValueError("missing or invalid feature list")
    _validate_completeness(data, len(features), limit)
    if "properties" in data:
        if not isinstance(data["properties"], dict):
            raise ValueError("invalid collection metadata")
        _validate_completeness(data["properties"], len(features))
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


def xml_features(content: bytes, names: set[str], *, limit: int) -> list[ET.Element]:
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
        {localname(key): value for key, value in root.attrib.items()}, len(features), limit
    )
    return features


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
        # La clave incluye un hash de la peticion (url+params): cambiar bbox,
        # radio o capa nunca reutiliza una respuesta cacheada obsoleta.
        import hashlib

        digest = hashlib.sha256(
            f"{request.url}?{request.query_string()}".encode()
        ).hexdigest()[:10]
        return self.source.fetch(
            self.source_id,
            f"{kind}:{key}:{digest}",
            request,
            refresh=self.refresh,
            ext=ext,
            meta={"source": self.source_id, "kind": kind, "key": key},
        )

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
