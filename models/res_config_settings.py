from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    credit_gate_enabled = fields.Boolean(
        string="Requerir aprobación para ventas a crédito",
        config_parameter="sale_credit_approval.enabled",
        help="Si se activa, las cotizaciones con un plazo distinto al de "
             "contado requieren la aprobación del usuario seleccionado.",
    )
    credit_gate_cash_term_id = fields.Many2one(
        "account.payment.term",
        string="Plazo de contado",
        config_parameter="sale_credit_approval.cash_term_id",
        default=lambda self: self.env.ref(
            "account.account_payment_term_immediate", raise_if_not_found=False
        ).id or False,
        help="Plazo que se considera pago de contado. Cualquier otro plazo "
             "se trata como venta a crédito.",
    )
    credit_gate_user_id = fields.Many2one(
        "res.users",
        string="Aprobador de crédito",
        config_parameter="sale_credit_approval.user_id",
        domain=[("share", "=", False)],
        help="Solo este usuario puede aprobar o rechazar el crédito. Debe "
             "tener acceso a Ventas para abrir la orden.",
    )
    credit_gate_whatsapp = fields.Char(
        string="WhatsApp del aprobador",
        config_parameter="sale_credit_approval.whatsapp",
        help="Número con código de país, sin + ni espacios "
             "(ej. 526681234567). Si se deja vacío, se usa el teléfono "
             "del aprobador.",
    )
