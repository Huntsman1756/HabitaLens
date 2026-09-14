"""Motor de evidencia: misma entrada + mismas versiones = mismos hallazgos.

Orquesta las fuentes sobre la geometria de una propiedad del corpus
preregistrado. Las fuentes no activadas o con error se registran como
INCONCLUSIVE; nunca se degradan a UNAVAILABLE ni se inventan datos.
"""

from __future__ import annotations

from habitalens.evidence.corpus import CorpusProperty
from habitalens.evidence.crs import choose_operational_crs
from habitalens.evidence.geometry import parse_wkt, to_wgs84
from habitalens.evidence.models import (
    EvidenceFinding,
    FindingStatus,
    PropertyEvidence,
)
from habitalens.sources import EvidenceSource, all_sources


def _inconclusive(
    source: EvidenceSource,
    property_id: str,
    operational_crs: str,
    reason: str,
) -> EvidenceFinding:
    return EvidenceFinding(
        property_id=property_id,
        source=source.source_id,
        source_version=source.source_version(),
        kind=f"{source.source_id}.status",
        status=FindingStatus.INCONCLUSIVE,
        source_crs=source.config.get("default_crs"),
        operational_crs=operational_crs,
        method="source-not-usable",
        note=reason,
    )


class EvidenceEngine:
    def __init__(
        self,
        sources: dict[str, EvidenceSource] | None = None,
        *,
        cache=None,
        provenance=None,
        refresh: bool = False,
    ):
        self.sources = sources or all_sources(
            cache=cache, provenance=provenance, refresh=refresh
        )

    def evaluate(
        self,
        corpus_property: CorpusProperty,
        geometry_wkt: str,
        source_crs: str,
    ) -> PropertyEvidence:
        geometry = parse_wkt(geometry_wkt)
        centroid = to_wgs84(geometry, source_crs).centroid
        operational_crs = choose_operational_crs(centroid.x)

        findings: list[EvidenceFinding] = []
        for source in self.sources.values():
            if not source.usable:
                findings.append(
                    _inconclusive(
                        source,
                        corpus_property.id,
                        operational_crs,
                        source.unusable_reason or "fuente no activada",
                    )
                )
                continue
            try:
                findings.extend(
                    source.evaluate(
                        geometry, source_crs, operational_crs, corpus_property.id
                    )
                )
            except Exception as exc:
                findings.append(
                    _inconclusive(
                        source,
                        corpus_property.id,
                        operational_crs,
                        f"{type(exc).__name__}: {exc}",
                    )
                )
        return PropertyEvidence(
            property_id=corpus_property.id,
            source_crs=source_crs,
            operational_crs=operational_crs,
            findings=tuple(findings),
        )
