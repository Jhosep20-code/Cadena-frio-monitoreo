"""Configuracion comun de las pruebas.

La cache de respuestas es util en la demostracion, pero en las pruebas
falsearia los resultados: se desactiva salvo que una prueba la pida.
"""

import pytest


@pytest.fixture(autouse=True)
def sin_cache(monkeypatch, tmp_path):
    import asistente.agente as agente

    monkeypatch.setattr(agente, "CACHE_ACTIVA", False)
    monkeypatch.setattr(agente, "RUTA_CACHE", str(tmp_path / "cache.json"))
