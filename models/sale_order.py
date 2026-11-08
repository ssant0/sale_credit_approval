from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .credit_gate import (
    check_credit_approval,
    get_approver,
    is_approver,
    is_credit_required,
    notify_approver_by_email,
    raise_credit_blocked,
)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    credit_gate_required = fields.Boolean(
        string="Requiere aprobación de crédito",
        compute="_compute_credit_gate_required",
    )
    credit_gate_state = fields.Selection(
        [
            ("none", "Sin aprobación"),
            ("pending", "Pendiente"),
            ("approved", "Aprobado"),
            ("rejected", "Rechazado"),
        ],
        string="Estado del crédito",
        default="none",
        readonly=True,
        copy=False,
        tracking=True,
    )
    credit_gate_approved_by = fields.Many2one(
        "res.users", string="Aprobado por", readonly=True, copy=False
    )
    credit_gate_approved_date = fields.Datetime(
        string="Fecha de aprobación", readonly=True, copy=False
    )
    credit_gate_is_approver = fields.Boolean(
        string="Es aprobador", compute="_compute_credit_gate_is_approver"
    )
    credit_gate_message = fields.Char(
        string="Mensaje de crédito", compute="_compute_credit_gate_message"
    )

    @api.depends("payment_term_id")
    def _compute_credit_gate_required(self):
        for order in self:
            order.credit_gate_required = is_credit_required(order.env, order)

    @api.depends_context("uid")
    def _compute_credit_gate_is_approver(self):
        value = is_approver(self.env)
        for order in self:
            order.credit_gate_is_approver = value

    @api.depends(
        "credit_gate_required",
        "credit_gate_state",
        "credit_gate_approved_by",
        "credit_gate_approved_date",
    )
    def _compute_credit_gate_message(self):
        for order in self:
            if not order.credit_gate_required:
                order.credit_gate_message = ""
            elif order.credit_gate_state == "approved":
                order.credit_gate_message = _(
                    "Crédito aprobado por %(user)s el %(date)s."
                ) % {
                    "user": order.credit_gate_approved_by.name or "",
                    "date": order.credit_gate_approved_date
                    and order.credit_gate_approved_date.strftime("%d/%m/%Y %H:%M")
                    or "",
                }
            elif order.credit_gate_state == "pending":
                order.credit_gate_message = _(
                    "Crédito pendiente de aprobación. No se puede confirmar, "
                    "enviar, imprimir ni previsualizar."
                )
            elif order.credit_gate_state == "rejected":
                order.credit_gate_message = _(
                    "Crédito rechazado. Revisa las condiciones o solicita de "
                    "nuevo."
                )
            else:
                order.credit_gate_message = _(
                    "Venta a crédito: requiere aprobación antes de confirmar, "
                    "enviar, imprimir o previsualizar."
                )

    def action_request_credit_approval(self):
        """Envía la solicitud al aprobador y abre el diálogo de notificación."""
        self.ensure_one()
        if not self.credit_gate_required:
            raise UserError(_("Esta orden no es una venta a crédito."))
        if self.credit_gate_state == "approved":
            return

        approver = get_approver(self.env)
        if not approver:
            raise UserError(_(
                "No hay un aprobador de crédito configurado. Ve a "
                "Contabilidad → Ajustes → Aprobación de crédito en ventas."
            ))

        self.write({
            "credit_gate_state": "pending",
            "credit_gate_approved_by": False,
            "credit_gate_approved_date": False,
        })
        email_sent = notify_approver_by_email(self.env, self, approver)
        notify = self.env["sale.credit.approval.notify"].create({
            "order_id": self.id,
            "approver_id": approver.id,
            "email_sent": email_sent,
        })
        return {
            "type": "ir.actions.act_window",
            "name": "Solicitud de aprobación de crédito",
            "res_model": "sale.credit.approval.notify",
            "res_id": notify.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_approve_credit(self):
        self.ensure_one()
        if not is_approver(self.env):
            raise UserError(_(
                "Solo el aprobador configurado puede aprobar el crédito."
            ))
        if self.credit_gate_state != "pending":
            raise UserError(_("La orden no está pendiente de aprobación."))
        self.write({
            "credit_gate_state": "approved",
            "credit_gate_approved_by": self.env.user.id,
            "credit_gate_approved_date": fields.Datetime.now(),
        })
        self.message_post(body=_("Crédito aprobado por %s.") % self.env.user.name)
        return True

    def action_reject_credit(self):
        self.ensure_one()
        if not is_approver(self.env):
            raise UserError(_(
                "Solo el aprobador configurado puede rechazar el crédito."
            ))
        if self.credit_gate_state != "pending":
            raise UserError(_("La orden no está pendiente de aprobación."))
        self.write({
            "credit_gate_state": "rejected",
            "credit_gate_approved_by": False,
            "credit_gate_approved_date": False,
        })
        self.message_post(body=_("Crédito rechazado por %s.") % self.env.user.name)
        return True

    def action_quotation_send(self):
        self._check_credit_gate_actions()
        return super().action_quotation_send()

    @api.readonly
    def action_preview_sale_order(self):
        self._check_credit_gate_actions()
        return super().action_preview_sale_order()

    def _check_credit_gate_actions(self):
        if self.env.su:
            return
        for order in self:
            if order.credit_gate_required and order.credit_gate_state != "approved":
                raise_credit_blocked(
                    self.env, order, _("enviar, imprimir ni previsualizar")
                )

    def action_confirm(self):
        for order in self:
            check_credit_approval(self.env, order)
        return super().action_confirm()

    def write(self, vals):
        res = super().write(vals)
        if {"payment_term_id", "partner_id"} & vals.keys():
            self._reset_credit_gate()
        return res

    def _reset_credit_gate(self):
        """Reinicia la aprobación cuando cambian condiciones relevantes."""
        for order in self:
            if order.credit_gate_state != "none" or order.credit_gate_approved_by:
                order.write({
                    "credit_gate_state": "none",
                    "credit_gate_approved_by": False,
                    "credit_gate_approved_date": False,
                })
