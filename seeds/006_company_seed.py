"""
Seed: 006_company_seed.py
Seeds initial company settings record.
"""
from app.services.encryption_service import EncryptionService


def run(db):
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM company")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO company (
                ruc, razon_social, nombre_comercial, direccion_matriz, telefono, email,
                ambiente_sri, establecimiento, punto_emision, secuencial_factura,
                secuencial_cotizacion,
                contribuyente_especial, obligado_contabilidad, firma_path, firma_pass,
                sri_email, smtp_host, smtp_port, smtp_user, smtp_pass, smtp_ssl
            ) VALUES (
                '1792998877001', 'FLETING SOLUTIONS S.A.S.', 'FLETING POS & TECH',
                'Av. de los Granados N40-100 y 6 de Diciembre, Quito - Ecuador',
                '0991234567', 'facturacion@fleting.ec', 1, '001', '001', 1,
                1,
                '', 'SI', '', '', 'recepcion.sri@sri.gob.ec',
                'smtp.gmail.com', 587, 'facturacion.demo@fleting.ec', ?, 0
            )
        """, (EncryptionService.encrypt(""),))

    db.commit()
