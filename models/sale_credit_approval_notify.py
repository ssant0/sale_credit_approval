from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import html_escape

from .credit_gate import build_whatsapp_url, record_url


class SaleCreditApprovalNotify(models.TransientModel):
    _name = "sale.credit.approval.notify"
    _description = "Notificación de aprobación de crédito"

    order_id = fields.Many2one("sale.order", string="Orden", readonly=True)
    approver_id = fields.Many2one("res.users", string="Aprobador", readonly=True)
    email_sent = fields.Boolean(string="Correo enviado", readonly=True)
    message = fields.Html(
        string="Mensaje", compute="_compute_message", sanitize=False
    )
    whatsapp_url = fields.Char(string="WhatsApp", compute="_compute_whatsapp")
    has_phone = fields.Boolean(compute="_compute_whatsapp")

    @api.depends("order_id", "approver_id", "email_sent", "has_phone")
    def _compute_message(self):
        for rec in self:
            order = rec.order_id
            link = record_url(order) if order else ""
            if rec.email_sent:
                email_note = _("Se envió un correo al aprobador.")
            else:
                email_note = _(
                    "No se pudo enviar el correo (revisa el servidor SMTP). "
                    "Puedes notificarle por WhatsApp."
                )
            if not rec.has_phone:
                email_note += _(" El aprobador no tiene WhatsApp configurado.")
            rec.message = (
                "<p>La cotización <b>%s</b> de <b>%s</b> por <b>%.2f %s</b> "
                "es a crédito y requiere la aprobación de <b>%s</b>.</p>"
                "<p>%s</p><p><a href=\"%s\">Abrir la cotización</a></p>"
            ) % (
                html_escape(order.name or ""),
                html_escape(order.partner_id.name or ""),
                order.amount_total,
                html_escape(order.currency_id.name or ""),
                html_escape(rec.approver_id.name or ""),
                email_note,
                html_escape(link),
            )

    @api.depends("order_id", "approver_id")
    def _compute_whatsapp(self):
        for rec in self:
            url = False
            if rec.order_id and rec.approver_id:
                url = build_whatsapp_url(rec.env, rec.order_id, rec.approver_id)
            rec.whatsapp_url = url or False
            rec.has_phone = bool(url)

    def action_open_whatsapp(self):
        self.ensure_one()
        if not self.whatsapp_url:
            raise UserError(_(
                "El aprobador no tiene un número de WhatsApp configurado. "
                "Agrégalo en Contabilidad → Ajustes → Aprobación de crédito "
                "en ventas."
            ))
        return {
            "type": "ir.actions.act_url",
            "url": self.whatsapp_url,
            "target": "new",
        }
