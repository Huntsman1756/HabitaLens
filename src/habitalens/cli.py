"""CLI de HabitaLens (gate G0-A).

Comando: ``habitalens resolve <refcat|direccion>``.

La salida NUNCA incluye geometria catastral: solo refcat, superficie, uso (si la
fuente lo expone), territorio, version de fuente y CRS fuente.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from habitalens import DISCLAIMER, __version__
from habitalens.resolver import PropertyResolver, ResolverError

HELP_TEXT = (
    "HabitaLens - analisis reproducible de inmuebles desde fuentes publicas.\n\n"
    "Comandos:\n"
    "  resolve   Resuelve una referencia catastral o una direccion.\n"
    "  report    Genera informe HTML/PDF + manifest de procedencia.\n\n"
    f"{DISCLAIMER}"
)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help=HELP_TEXT,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"habitalens {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Muestra la version y sale.",
    ),
) -> None:
    """HabitaLens (G0-A)."""


@app.command(help=f"Resuelve <refcat|direccion> a parcela + edificios.\n\n{DISCLAIMER}")
def resolve(
    reference: str = typer.Argument(..., help="Referencia catastral o direccion."),
    refresh: bool = typer.Option(
        False, "--refresh", help="Fuerza el refetch ignorando la cache local."
    ),
    as_json: bool = typer.Option(False, "--json", help="Salida JSON (sin geometria)."),
) -> None:
    try:
        property_ = PropertyResolver(refresh=refresh).resolve(reference)
    except ResolverError as exc:
        typer.echo(f"INCONCLUSIVE: {exc}", err=True)
        raise typer.Exit(code=2) from exc
    except Exception as exc:
        typer.echo(f"FAIL: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    if as_json:
        typer.echo(property_.model_dump_json(indent=2))
        return

    parcel = property_.parcel
    typer.echo(f"refcat        : {parcel.refcat}")
    typer.echo(f"superficie_m2 : {parcel.area_m2}")
    typer.echo(f"uso           : {parcel.land_use or 'no expuesto por la fuente'}")
    typer.echo(f"territorio    : {parcel.territory.value}")
    typer.echo(f"proveedor     : {parcel.provider}")
    typer.echo(f"version_fuente: {parcel.source_version}")
    typer.echo(f"crs_fuente    : {parcel.crs}")
    typer.echo(f"edificios     : {len(property_.buildings)}")
    if property_.address is not None:
        typer.echo(f"direccion     : {property_.address.label}")
    typer.echo("")
    typer.echo(DISCLAIMER)


@app.command(help=f"Genera informe HTML/PDF + manifest desde un manifest JSON.\n\n{DISCLAIMER}")
def report(
    manifest: Path = typer.Argument(..., help="Ruta al provenance_manifest.json o manifest base."),
    out: Path = typer.Option(Path("report"), "--out", help="Directorio de salida."),
) -> None:
    from habitalens.report import generate_report

    data = json.loads(Path(manifest).read_text(encoding="utf-8"))
    artifacts = generate_report(data, Path(out))
    typer.echo(f"html     : {artifacts.html_path}")
    typer.echo(f"pdf      : {artifacts.pdf_path} ({artifacts.pdf_pages} paginas)")
    typer.echo(f"manifest : {artifacts.manifest_path}")
    typer.echo("")
    typer.echo(DISCLAIMER)


@app.command(help=f"Contrasta la superficie anunciada con la oficial (comparabilidad).\n\n{DISCLAIMER}")
def surface(
    refcat: str = typer.Argument(..., help="Referencia catastral."),
    advertised: float = typer.Option(..., "--advertised", help="Superficie anunciada en m2."),
    concept: str = typer.Option(
        "unknown",
        "--concept",
        help="Concepto del anuncio: unknown | construida | util | construida_con_comunes.",
    ),
    official_built: float = typer.Option(None, "--official-built", help="Superficie construida oficial (m2), si se conoce."),
    official_common: float = typer.Option(None, "--official-common", help="Elementos comunes oficiales (m2), si se conocen."),
    tolerance: float = typer.Option(0.05, "--tolerance", help="Tolerancia relativa (por defecto 0.05)."),
) -> None:
    from habitalens.evidence.surface import (
        ComparabilityStatus,
        SurfaceComponents,
        SurfaceConcept,
        compare_area,
    )

    try:
        surface_concept = SurfaceConcept(concept)
    except ValueError as exc:
        typer.echo(f"FAIL: concepto no valido ({concept})", err=True)
        raise typer.Exit(code=1) from exc

    try:
        property_ = PropertyResolver().resolve_refcat(refcat)
    except ResolverError as exc:
        typer.echo(f"INCONCLUSIVE: {exc}", err=True)
        raise typer.Exit(code=2) from exc

    built = official_built
    if built is None and property_.parcel.provider == "dgc":
        try:
            from habitalens.cadastre_providers import get_provider

            data = get_provider("dgc").corroborate_reference(refcat)
            built = data.area_m2
        except Exception:
            built = None

    components = SurfaceComponents(built_m2=built, common_m2=official_common)
    result = compare_area(
        advertised, components, advertised_concept=surface_concept, refcat=refcat, tolerance=tolerance
    )

    typer.echo(f"refcat            : {result.refcat}")
    typer.echo(f"superficie_anuncio: {result.advertised_m2} m2 ({result.advertised_concept.value})")
    typer.echo(f"construida_oficial: {result.official.built_m2}")
    typer.echo(f"comunes_oficial   : {result.official.common_m2}")
    typer.echo(f"referencia        : {result.reference_m2}")
    typer.echo(f"comparabilidad    : {result.comparability.value}")
    if result.comparability == ComparabilityStatus.INSUFFICIENT:
        typer.echo("INCONCLUSIVE: sin superficie oficial comparable; aportar --official-built")
    else:
        typer.echo(f"diferencia        : {result.difference_m2:+.2f} m2")
        typer.echo(f"diferencia_rel    : {result.relative_difference:+.1%}")
        typer.echo(
            f"excede_tolerancia : {'si' if result.exceeds_tolerance else 'no'} (tol {result.tolerance:.0%})"
        )
        typer.echo(f"hallazgo          : {result.kind}")
    typer.echo("")
    typer.echo(DISCLAIMER)


if __name__ == "__main__":  # pragma: no cover
    app()
