from odoo import models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def create(self, vals_list):
        lines = super().create(vals_list)
        orders = lines.order_id.filtered(lambda order: isinstance(order.id, int))
        orders._reset_credit_gate()
        return lines

    def write(self, vals):
        res = super().write(vals)
        if {"product_id", "product_uom_qty", "price_unit", "discount", "tax_id"} & vals.keys():
            self.order_id._reset_credit_gate()
        return res

    def unlink(self):
        orders = self.order_id
        res = super().unlink()
        orders._reset_credit_gate()
        return res
