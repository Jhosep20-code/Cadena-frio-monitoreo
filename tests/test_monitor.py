import pytest

from src.monitor import (
    LecturaInvalida,
    clasificar,
    hay_excursion,
    promedio,
    resumen,
)


class TestClasificar:
    def test_temperatura_dentro_del_rango(self):
        assert clasificar(4.5) == "OK"

    def test_limite_inferior_es_valido(self):
        assert clasificar(2.0) == "OK"

    def test_limite_superior_es_valido(self):
        assert clasificar(8.0) == "OK"

    def test_temperatura_baja_genera_alerta(self):
        assert clasificar(1.9) == "ALERTA_BAJA"

    def test_temperatura_alta_genera_alerta(self):
        assert clasificar(8.1) == "ALERTA_ALTA"

    def test_lectura_no_numerica_lanza_error(self):
        with pytest.raises(LecturaInvalida):
            clasificar("sensor desconectado")

    def test_lectura_nula_lanza_error(self):
        with pytest.raises(LecturaInvalida):
            clasificar(None)


class TestExcursiones:
    def test_jornada_sin_excursiones(self):
        assert hay_excursion([3.0, 4.0, 5.0]) is False

    def test_jornada_con_una_excursion(self):
        assert hay_excursion([3.0, 9.5, 5.0]) is True


class TestPromedio:
    def test_promedio_correcto(self):
        assert promedio([4.0, 6.0]) == 5.0

    def test_promedio_sin_lecturas_lanza_error(self):
        with pytest.raises(LecturaInvalida):
            promedio([])


class TestResumen:
    def test_resumen_conforme(self):
        r = resumen([4.0, 4.5, 5.0])
        assert r["estado"] == "CONFORME"
        assert r["excursiones"] == 0
        assert r["total"] == 3

    def test_resumen_no_conforme(self):
        r = resumen([4.0, 12.0, 5.0])
        assert r["estado"] == "NO CONFORME"
        assert r["excursiones"] == 1
        assert r["maxima"] == 12.0

    def test_resumen_calcula_promedio_redondeado(self):
        assert resumen([4.0, 5.0, 6.0])["promedio"] == 5.0
