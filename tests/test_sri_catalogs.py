import unittest

from tests.base import ensure_faker

ensure_faker()

from app.services.sri_catalogs import (
    calcular_totales_linea,
    codigo_forma_pago,
    etiqueta_forma_pago,
    normalizar_forma_pago,
    validar_ice,
)


class FormasPagoTest(unittest.TestCase):
    def test_codigos_sri_de_formas_de_pago(self):
        self.assertEqual(codigo_forma_pago("EFECTIVO"), "01")
        self.assertEqual(codigo_forma_pago("TARJETA_CREDITO"), "19")
        self.assertEqual(codigo_forma_pago("TARJETA_DEBITO"), "16")
        self.assertEqual(codigo_forma_pago("TRANSFERENCIA"), "20")
        # Compatibilidad con el valor genérico antiguo.
        self.assertEqual(codigo_forma_pago("TARJETA"), "20")
        self.assertEqual(codigo_forma_pago("otra-cosa"), "20")

    def test_normaliza_alias_y_etiquetas(self):
        self.assertEqual(normalizar_forma_pago("Tarjeta de crédito"), "TARJETA_CREDITO")
        self.assertEqual(normalizar_forma_pago("tarjeta-debito"), "TARJETA_DEBITO")
        self.assertEqual(etiqueta_forma_pago("TARJETA_CREDITO"), "Tarjeta de crédito")
        self.assertEqual(etiqueta_forma_pago("TARJETA_DEBITO"), "Tarjeta de débito")


class ICETest(unittest.TestCase):
    def test_valida_codigo_y_tarifa(self):
        ok, value = validar_ice("3031", 10)
        self.assertTrue(ok)
        self.assertEqual(value, ("3031", 10.0))

        ok, value = validar_ice("", 0)
        self.assertTrue(ok)
        self.assertEqual(value, ("", 0.0))

        ok, _ = validar_ice("", 10)
        self.assertFalse(ok)

        ok, _ = validar_ice("30", 10)
        self.assertFalse(ok)

        ok, _ = validar_ice("3031", -1)
        self.assertFalse(ok)

    def test_calcula_ice_y_base_de_iva(self):
        line = calcular_totales_linea(
            cantidad=1,
            precio_unitario=100,
            descuento=0,
            iva_porcentaje=15,
            ice_codigo="3031",
            ice_porcentaje=10,
        )
        self.assertAlmostEqual(line["subtotal"], 100.0)
        self.assertAlmostEqual(line["valor_ice"], 10.0)
        # La base del IVA incluye el ICE.
        self.assertAlmostEqual(line["valor_iva"], 16.5)
        self.assertAlmostEqual(line["total"], 126.5)

    def test_calcula_descuento_y_sin_ice(self):
        line = calcular_totales_linea(2, 50, 10, 15, "", 0)
        self.assertAlmostEqual(line["subtotal"], 90.0)
        self.assertAlmostEqual(line["valor_ice"], 0.0)
        self.assertAlmostEqual(line["valor_iva"], 13.5)
        self.assertAlmostEqual(line["total"], 103.5)

    def test_codigo_ice_invalido_lanza_error(self):
        with self.assertRaises(ValueError):
            calcular_totales_linea(1, 10, 0, 15, "12", 10)


if __name__ == "__main__":
    unittest.main()
