"""Discrepancia entre superficie anunciada y superficie oficial (G0 extra).

Capacidad de valor inmediato: contrasta la superficie que anuncia un anuncio con
la superficie oficial ya disponible en el catastro. No requiere fuentes nuevas:
solo un campo de entrada (superficie anunciada). Sin geometria y sin score.
"""

from __future__ import annotations

from dataclasses import dataclass

from habitalens.evidence.models import EvidenceFinding, FindingStatus

DEFAULT_TOLERANCE = 0.05
KIND = "surface.discrepancy_m2"


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
    """Compara superficie anunciada vs oficial.

    ``relative_difference`` es (anunciada - oficial) / oficial. Positivo = el
    anuncio dice mas superficie que el catastro.
    """

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
