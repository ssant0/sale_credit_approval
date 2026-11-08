{
    "name": "Aprobación de Crédito en Ventas",
    "version": "19.0.1.0.0",
    "summary": "Requiere aprobación para confirmar cotizaciones a crédito.",
    "description": """
Aprobación de Crédito en Ventas
===============================

Una cotización cuyo plazo de pago sea distinto al de contado se considera
venta a crédito. Estas órdenes no se pueden confirmar hasta que el aprobador
designado autorice el crédito.

Flujo de dos pasos:
1. El vendedor pulsa "Solicitar aprobación de crédito".
2. Se envía correo al aprobador (y opcionalmente WhatsApp) con el link.
3. El aprobador aprueba o rechaza desde la orden.
4. Con la aprobación, la orden se puede confirmar.

Si cambia el plazo, el cliente o el importe después de aprobar, la aprobación
se reinicia.
""",
    "author": "ssant0",
    "website": "https://github.com/ssant0/sale_credit_approval",
    "license": "LGPL-3",
    "category": "Sales",
    "depends": ["sale_management", "account", "mail"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/sale_order_views.xml",
        "views/sale_credit_approval_notify_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
