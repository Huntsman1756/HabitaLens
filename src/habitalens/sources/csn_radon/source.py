"""CSN radon: fuente registrada pero NO activada.

Verificado (G0-B recon): no existe WFS/WMS ni FeatureServer para el potencial de
radon; solo un File Geodatabase descargable y JSON embebido en un webmap de
ArcGIS. No hay licencia abierta declarada. Conforme a la regla "licencia y
acceso antes que parsing", la fuente se evalua como INCONCLUSIVE y no produce
hallazgos OBSERVED/DERIVED hasta que se declare licencia y acceso reproducible.
"""

from __future__ import annotations

from habitalens.evidence.models import EvidenceFinding, FindingStatus
from habitalens.sources.base import EvidenceSource


class CsnRadonSource(EvidenceSource):
    source_id = "csn_radon"

    def evaluate(self, geometry, source_crs, operational_crs, property_id) -> list[EvidenceFinding]:
        return [
            EvidenceFinding(
                property_id=property_id,
                source=self.source_id,
                source_version=self.source_version(),
                kind="csn_radon.potential",
                status=FindingStatus.INCONCLUSIVE,
                source_crs=self.config.get("default_crs"),
                operational_crs=operational_crs,
                method="not-activated",
                inputs=(),
                note=self.unusable_reason,
            )
        ]
