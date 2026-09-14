"""CLI de HabitaLens (gate G0-A).

Comando: ``habitalens resolve <refcat|direccion>``.

La salida NUNCA incluye geometria catastral: solo refcat, superficie, uso (si la
fuente lo expone), territorio, version de fuente y CRS fuente.
"""

from __future__ import annotations

import typer

from habitalens import DISCLAIMER, __version__
from habitalens.resolver import PropertyResolver, ResolverError

HELP_TEXT = (
    "HabitaLens - analisis reproducible de inmuebles desde fuentes publicas (G0-A).\n\n"
    "Comandos:\n"
    "  resolve   Resuelve una referencia catastral o una direccion.\n\n"
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
        property_ = PropertyResolver().resolve(reference)
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


if __name__ == "__main__":  # pragma: no cover
    app()
