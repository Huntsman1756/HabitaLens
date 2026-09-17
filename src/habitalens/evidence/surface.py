"""Superficie anunciada vs oficial, con semantica de comparabilidad.

Catastro distingue superficie construida privativa, elementos comunes y anejos;
el mercado anuncia util, construida o construida con comunes. Por eso:

- Si el concepto del anuncio es comparable con el oficial -> ``AREA_MISMATCH``
  (diferencia factual, con tolerancia).
- Si solo hay un m2 sin concepto -> ``POTENTIAL_AREA_MISMATCH`` (no se afirma
  discrepancia; se pide verificar el concepto).

Sin geometria y sin score. No requiere fuentes nuevas: superficie anunciada es un
input manual.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from habitalens.evidence.models import EvidenceFinding, FindingStatus

DEFAULT_TOLERANCE = 0.05
KIND_MISMATCH = "area.mismatch"
KIND_POTENTIAL = "area.potential_mismatch"
# Compatibilidad con la version previa.
KIND = "surface.discrepancy_m2"


class SurfaceConcept(StrEnum):
    UNKNOWN = "unknown"
    CONSTRUIDA = "construida"
    UTIL = "util"
    CONSTRUIDA_CON_COMUNES = "construida_con_comunes"


class ComparabilityStatus(StrEnum):
    DIRECT = "directa"
    PARTIAL = "parcial"
    NOT_COMPARABLE = "no_comparable"
    INSUFFICIENT = "insuficiente"


@dataclass(frozen=True)
class SurfaceComponents:
    built_m2: float | None = None
    common_m2: float | None = None
    annex_m2: float | None = None


@dataclass(frozen=True)
class AreaComparison:
    advertised_m2: float
    advertised_concept: SurfaceConcept
    official: SurfaceComponents
    reference_m2: float | None
    difference_m2: float | None
    relative_difference: float | None
    comparability: ComparabilityStatus
    tolerance: float
    exceeds_tolerance: bool | None
    kind: str
    refcat: str | None = None


# ---------------------------------------------------------------------------
# Version simple (comparacion 1:1), mantenida por compatibilidad.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SurfaceComparison:
    advertised_m2: float
    official_m2: float
    difference_m2: float
    relative_difference: float
    tolerance: float
    exceeds_tolerance: bool
    refcat: str | None = None


def compare_surface(
    advertised_m2: float,
    official_m2: float,
    *,
    refcat: str | None = None,
    tolerance: float = DEFAULT_TOLERANCE,
) -> SurfaceComparison:
    advertised = float(advertised_m2)
    official = float(official_m2)
    if advertised <= 0 or official <= 0:
        raise ValueError("las superficies deben ser positivas")
    if tolerance < 0:
        raise ValueError("tolerance no puede ser negativa")
    difference = advertised - official
    relative = difference / official
    return SurfaceComparison(
        advertised_m2=advertised,
        official_m2=official,
        difference_m2=difference,
        relative_difference=relative,
        tolerance=tolerance,
        exceeds_tolerance=abs(relative) > tolerance,
        refcat=refcat,
    )


def surface_finding(
    property_id: str,
    comparison: SurfaceComparison,
    *,
    source: str = "surface",
    source_version: str,
    provenance_id: str | None = None,
) -> EvidenceFinding:
    note = (
        f"anunciada={comparison.advertised_m2} m2; oficial={comparison.official_m2} m2; "
        f"relativa={comparison.relative_difference:+.1%}; tolerancia={comparison.tolerance:.0%}; "
        f"excede={'si' if comparison.exceeds_tolerance else 'no'}"
    )
    return EvidenceFinding(
        property_id=property_id,
        source=source,
        source_version=source_version,
        kind=KIND,
        status=FindingStatus.DERIVED,
        value=comparison.difference_m2,
        unit="m2",
        method="advertised-vs-official-surface",
        inputs=("advertised_m2", "official_m2"),
        provenance_id=provenance_id,
        note=note,
    )


# ---------------------------------------------------------------------------
# Comparabilidad (P1.A)
# ---------------------------------------------------------------------------


def _reference_for(
    concept: SurfaceConcept, official: SurfaceComponents
) -> tuple[float | None, ComparabilityStatus]:
    built = official.built_m2
    common = official.common_m2
    built_plus_common = None
    if built is not None and common is not None:
        built_plus_common = built + common
    if concept == SurfaceConcept.CONSTRUIDA:
        return built, ComparabilityStatus.DIRECT if built is not None else ComparabilityStatus.INSUFFICIENT
    if concept == SurfaceConcept.CONSTRUIDA_CON_COMUNES:
        return (
            built_plus_common,
            ComparabilityStatus.DIRECT if built_plus_common is not None else ComparabilityStatus.INSUFFICIENT,
        )
    if concept == SurfaceConcept.UTIL:
        # util no equivale exactamente a construida -> solo parcial
        return built, ComparabilityStatus.PARTIAL if built is not None else ComparabilityStatus.INSUFFICIENT
    # unknown
    fallback = built_plus_common if built_plus_common is not None else built
    return fallback, ComparabilityStatus.INSUFFICIENT if fallback is None else ComparabilityStatus.NOT_COMPARABLE


def compare_area(
    advertised_m2: float,
    official: SurfaceComponents,
    *,
    advertised_concept: SurfaceConcept = SurfaceConcept.UNKNOWN,
    refcat: str | None = None,
    tolerance: float = DEFAULT_TOLERANCE,
) -> AreaComparison:
    advertised = float(advertised_m2)
    if advertised <= 0:
        raise ValueError("la superficie anunciada debe ser positiva")
    if tolerance < 0:
        raise ValueError("tolerance no puede ser negativa")

    reference, comparability = _reference_for(advertised_concept, official)
    factual = comparability == ComparabilityStatus.DIRECT
    kind = KIND_MISMATCH if factual else KIND_POTENTIAL

    if reference is None:
        return AreaComparison(
            advertised_m2=advertised,
            advertised_concept=advertised_concept,
            official=official,
            reference_m2=None,
            difference_m2=None,
            relative_difference=None,
            comparability=comparability,
            tolerance=tolerance,
            exceeds_tolerance=None,
            kind=kind,
            refcat=refcat,
        )

    difference = advertised - reference
    relative = difference / reference
    return AreaComparison(
        advertised_m2=advertised,
        advertised_concept=advertised_concept,
        official=official,
        reference_m2=reference,
        difference_m2=difference,
        relative_difference=relative,
        comparability=comparability,
        tolerance=tolerance,
        exceeds_tolerance=abs(relative) > tolerance,
        kind=kind,
        refcat=refcat,
    )


def area_finding(
    property_id: str,
    comparison: AreaComparison,
    *,
    source: str = "surface",
    source_version: str,
    provenance_id: str | None = None,
) -> EvidenceFinding:
    official = comparison.official
    parts = [f"anunciada={comparison.advertised_m2} m2 ({comparison.advertised_concept.value})"]
    if official.built_m2 is not None:
        parts.append(f"construida={official.built_m2} m2")
    if official.common_m2 is not None:
        parts.append(f"comunes={official.common_m2} m2")
    if official.annex_m2 is not None:
        parts.append(f"anejos={official.annex_m2} m2")
    parts.append(f"referencia={comparison.reference_m2}")
    parts.append(f"comparabilidad={comparison.comparability.value}")
    if comparison.relative_difference is not None:
        parts.append(f"relativa={comparison.relative_difference:+.1%}")
        parts.append(f"excede={'si' if comparison.exceeds_tolerance else 'no'}")
    if comparison.comparability == ComparabilityStatus.PARTIAL:
        parts.append("util y construida son conceptos distintos; la diferencia no acredita discrepancia")
    if comparison.comparability == ComparabilityStatus.NOT_COMPARABLE:
        parts.append("verificar que concepto de superficie usa el anuncio")

    value = comparison.difference_m2 if comparison.difference_m2 is not None else comparison.advertised_m2
    return EvidenceFinding(
        property_id=property_id,
        source=source,
        source_version=source_version,
        kind=comparison.kind,
        status=FindingStatus.DERIVED,
        value=value,
        unit="m2",
        method="advertised-vs-official-comparability",
        inputs=("advertised_m2", "advertised_concept", "official_components"),
        provenance_id=provenance_id,
        note="; ".join(parts),
    )
