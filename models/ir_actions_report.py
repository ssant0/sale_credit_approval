from odoo import SUPERUSER_ID, _, models

from .credit_gate import raise_credit_blocked


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _check_credit_gate_report(self, report_ref, res_ids):
        """Bloquea cualquier reporte de una orden a crédito sin aprobar."""
        if self.env.user.id == SUPERUSER_ID:
            return
        if not res_ids:
            return

        report = self._get_report(report_ref)
        if report.model != "sale.order":
            return

        if isinstance(res_ids, str) and "," in res_ids:
            res_ids = [int(value) for value in res_ids.split(",") if value.strip()]
        elif isinstance(res_ids, (int, str)):
            res_ids = [int(res_ids)]
        orders = self.env["sale.order"].browse(res_ids)
        for order in orders:
            if order.credit_gate_required and order.credit_gate_state != "approved":
                raise_credit_blocked(
                    self.env, order, _("imprimir ni previsualizar")
                )

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        self._check_credit_gate_report(report_ref, res_ids)
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

    def _render_qweb_html(self, report_ref, docids, data=None):
        self._check_credit_gate_report(report_ref, docids)
        return super()._render_qweb_html(report_ref, docids=docids, data=data)
