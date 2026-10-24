"""
Seed: 006_company_seed.py
Crea la configuración inicial vacía de la empresa.

Los datos reales (RUC, razón social, certificado, etc.) se registran desde
la pantalla "Mi Empresa".
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
                '', 'MI EMPRESA', 'MI NEGOCIO',
                '', '', '', 1, '001', '001', 1,
                1,
                '', 'NO', '', '', 'recepcion.sri@sri.gob.ec',
                'smtp.gmail.com', 587, '', ?, 0
            )
        """, (EncryptionService.encrypt(""),))

    db.commit()
