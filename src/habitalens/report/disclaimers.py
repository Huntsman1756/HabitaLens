"""Disclaimers obligatorios y atribuciones por fuente (G0-D)."""

from __future__ import annotations

from habitalens import DISCLAIMER

#: Atribucion/licencia obligatoria por fuente.
ATTRIBUTIONS: dict[str, str] = {
    "snczi": (
        "Zonas inundables: Sistema Nacional de Cartografia de Zonas Inundables "
        "(SNCZI), MITECO. CC BY 4.0. Nombrar la fuente: MITECO."
    ),
    "eprtr": (
        "Instalaciones industriales: European Environment Agency, European "
        "Pollutant Release and Transfer Register (E-PRTR). CC BY 4.0."
    ),
    "csn_radon": (
        "Potencial de radon (CSN): fuente NO activada; resultado INCONCLUSIVE. "
        "Sin licencia abierta declarada."
    ),
    "siu": (
        "Clasificacion urbanistica: Sistema de Informacion Urbana (SIU), MIVAU. "
        "Reutilizacion (Ley 37/2007 / RD 1495/2011) con cita de la fuente."
    ),
    "ncse02": (
        "Peligrosidad sismica NCSE-02: Instituto Geografico Nacional (IGN). "
        "CC-BY 4.0 ign.es."
    ),
    "btn": (
        "Redes de transporte (BTN): Instituto Geografico Nacional / CNIG. "
        "CC-BY 4.0 ign.es."
    ),
}

_GENERIC_ATTRIBUTION = "Fuente publica con atribucion segun su licencia declarada."


class DisclaimerError(RuntimeError):
    """Falta un disclaimer o atribucion obligatoria."""


def _normalize_ws(text: str) -> str:
    return " ".join(str(text).split())


def required_disclaimers(source_ids) -> list[str]:
    texts = [DISCLAIMER]
    for source_id in sorted(set(source_ids)):
        texts.append(ATTRIBUTIONS.get(source_id, _GENERIC_ATTRIBUTION))
    return texts


def missing_disclaimers(text: str, source_ids) -> list[str]:
    haystack = _normalize_ws(text)
    return [item for item in required_disclaimers(source_ids) if _normalize_ws(item) not in haystack]


def assert_disclaimers(text: str, source_ids) -> None:
    missing = missing_disclaimers(text, source_ids)
    if missing:
        raise DisclaimerError(f"faltan disclaimers obligatorios: {len(missing)}")


def assert_snapshot_disclaimers(text: str, disclaimers: tuple[str, ...]) -> None:
    haystack = _normalize_ws(text)
    missing = [item for item in disclaimers if _normalize_ws(item) not in haystack]
    if missing:
        raise DisclaimerError(f"faltan disclaimers del manifest: {len(missing)}")
