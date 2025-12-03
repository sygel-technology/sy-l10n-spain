# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    genci_amount = fields.Monetary(
        string="GENCI Amount",
        currency_field="currency_id",
        readonly=True,
    )

    def _compute_qty_invoiced(self):
        res = super()._compute_qty_invoiced()
        genci_product = self.env.ref(
            "l10n_es_genci_account.product_genci_service",
            raise_if_not_found=False,
        )
        if genci_product:
            for line in self.filtered(lambda l: l.product_id == genci_product):
                rule_name = line.name.replace("GENCI:", "").strip()
                source_lines = line.order_id.order_line.filtered(
                    lambda l: l.product_id.genci_subject == "yes"
                    and l.product_id.genci_rule_id
                    and l.product_id.genci_rule_id.name == rule_name
                )
                if not source_lines:
                    line.qty_invoiced = 0
                    continue
                invoice_product_lines = self.env["account.move.line"].search(
                    [
                        ("sale_line_ids", "in", source_lines.ids),
                        ("move_id.state", "!=", "cancel"),
                    ]
                )
                billed_qty = sum(invoice_product_lines.mapped("quantity"))
                line.qty_invoiced = min(billed_qty, line.product_uom_qty)
        return res
