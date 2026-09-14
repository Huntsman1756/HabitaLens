"""Transporte HTTP con cache, timeout y backoff, y transporte de fixtures offline.

El codigo de proveedores depende de la interfaz :class:`Source`, no de httpx.
Los tests inyectan :class:`FixtureSource` y jamas realizan llamadas live.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import httpx

from habitalens.cache import CacheStore


@dataclass(frozen=True)
class HttpRequest:
    method: str
    url: str
    params: tuple[tuple[str, str], ...] = ()
    data: bytes | None = None
    headers: tuple[tuple[str, str], ...] = ()

    def query_string(self) -> str:
        if not self.params:
            return ""
        from urllib.parse import urlencode

        return urlencode(list(self.params))


@dataclass(frozen=True)
class HttpResponse:
    status_code: int
    content: bytes
    headers: dict[str, str] = field(default_factory=dict)


class Transport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse: ...


class HttpxTransport:
    """Transporte real con timeout, reintentos y backoff exponencial."""

    def __init__(self, timeout: float = 60.0, retries: int = 3, backoff: float = 1.5):
        self.timeout = timeout
        self.retries = max(1, retries)
        self.backoff = backoff

    def send(self, request: HttpRequest) -> HttpResponse:
        last_error: Exception | None = None
        for attempt in range(self.retries):
            try:
                with httpx.Client(
                    timeout=self.timeout,
                    follow_redirects=True,
                    headers=dict(request.headers),
                ) as client:
                    response = client.request(
                        request.method,
                        request.url,
                        params=list(request.params) or None,
                        content=request.data,
                    )
                if response.status_code >= 500:
                    raise httpx.HTTPStatusError(
                        f"server error {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                return HttpResponse(
                    status_code=response.status_code,
                    content=response.content,
                    headers=dict(response.headers),
                )
            except (httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt + 1 < self.retries:
                    time.sleep(self.backoff ** attempt)
        raise RuntimeError(f"fallo de transporte para {request.url}: {last_error}")


class Source(Protocol):
    offline: bool

    def fetch(
        self,
        namespace: str,
        key: str,
        request: HttpRequest,
        *,
        refresh: bool = False,
        ext: str = "xml",
        meta: dict | None = None,
    ) -> bytes: ...


class HttpSource:
    """Source live: consulta HTTP y cachea la respuesta cruda en disco."""

    offline = False

    def __init__(self, cache: CacheStore | None = None, transport: Transport | None = None):
        self.cache = (cache or CacheStore()).ensure()
        self.transport = transport or HttpxTransport()

    def fetch(
        self,
        namespace: str,
        key: str,
        request: HttpRequest,
        *,
        refresh: bool = False,
        ext: str = "xml",
        meta: dict | None = None,
    ) -> bytes:
        if not refresh:
            cached = self.cache.read_raw(namespace, key, ext)
            if cached is not None:
                return cached
        response = self.transport.send(request)
        if response.status_code >= 400:
            raise RuntimeError(
                f"HTTP {response.status_code} en {request.url} "
                f"({len(response.content)} bytes)"
            )
        self.cache.write_raw(namespace, key, response.content, ext=ext, meta=meta)
        return response.content


class FixtureSource:
    """Source offline: sirve fixtures congeladas. Nunca toca la red."""

    offline = True

    def __init__(self, fixtures: dict[str, str | Path | bytes]):
        self.fixtures = {k: v for k, v in fixtures.items()}

    def _lookup(self, namespace: str, key: str):
        for candidate in (f"{namespace}:{key}", key, namespace):
            if candidate in self.fixtures:
                return self.fixtures[candidate]
        return None

    def fetch(
        self,
        namespace: str,
        key: str,
        request: HttpRequest,
        *,
        refresh: bool = False,
        ext: str = "xml",
        meta: dict | None = None,
    ) -> bytes:
        value = self._lookup(namespace, key)
        if value is None:
            raise KeyError(
                f"fixture offline no encontrada para '{namespace}:{key}'. "
                "Los tests deben declarar todas las respuestas."
            )
        if isinstance(value, bytes):
            return value
        path = Path(value)
        if path.suffix == ".gz":
            import gzip

            return gzip.decompress(path.read_bytes())
        return path.read_bytes()
