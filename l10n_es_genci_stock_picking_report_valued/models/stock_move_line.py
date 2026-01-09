# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    genci_amount_subtotal = fields.Monetary(
        compute="_compute_genci_amount",
        compute_sudo=True,
        currency_field="currency_id",
    )
    genci_amount_tax = fields.Monetary(
        compute="_compute_genci_amount",
        compute_sudo=True,
        currency_field="currency_id",
    )
    genci_amount_total = fields.Monetary(
        compute="_compute_genci_amount",
        compute_sudo=True,
        currency_field="currency_id",
    )
    genci_rule_id = fields.Many2one(
        "genci.rule",
        compute="_compute_genci_amount",
        readonly=True,
    )

    def _get_genci_product_taxes(self, genci_product):
        """Map GENCI product taxes through fiscal position (similar to SIGAUS)."""
        taxes = genci_product.taxes_id
        mapped_taxes = False
        if taxes:
            sale = self.sale_line.order_id if self.sale_line else False
            fiscal_position = sale.fiscal_position_id if sale else False
            mapped_taxes = fiscal_position.map_tax(taxes) if fiscal_position else taxes
        return mapped_taxes

    def _get_genci_tax_base_line_dict(self, genci_product, price, qty):
        """Prepare tax base line dict for account.tax._compute_taxes()."""
        return self.env["account.tax"]._convert_to_tax_base_line_dict(
            self,
            partner=self.sale_line.order_partner_id,
            currency=self.currency_id,
            product=genci_product,
            taxes=self._get_genci_product_taxes(genci_product),
            price_unit=price,
            quantity=qty,
        )

    @api.depends(
        "product_id",
        "qty_done",
        "reserved_qty",
        "sale_line",
        "sale_line.order_id.is_genci",
        "sale_line.order_id.date_order",
        "product_id.genci_has_amount",
        "product_id.genci_rule_id",
    )
    def _compute_genci_amount(self):
        Tax = self.env["account.tax"]
        for line in self:
            # Reset GENCI amounts for the move line
            line.genci_amount_subtotal = 0.0
            line.genci_amount_tax = 0.0
            line.genci_amount_total = 0.0
            line.genci_rule_id = False
            # Check if GENCI must be applied to this move line
            if (
                not line.product_id
                or not line.sale_line
                or not line.sale_line.order_id.is_genci
                or not line.product_id.genci_has_amount
                or not line.product_id.genci_rule_id
            ):
                continue
            # Get the GENCI rule linked to the product
            rule = line.product_id.genci_rule_id
            line.genci_rule_id = rule
            # Determine the quantity to be valued in the picking
            qty = line._get_report_valued_quantity() or line.qty_done or 0.0
            if not qty:
                continue
            price_unit = rule.unit_price
            # GENCI service product used for tax and accounting configuration
            genci_product = self.env.ref("l10n_es_genci_account.product_genci_service")
            # Build the tax base line and compute taxes
            tax_base_line = line._get_genci_tax_base_line_dict(
                genci_product=genci_product,
                price=price_unit,
                qty=qty,
            )
            tax_res = Tax._compute_taxes([tax_base_line])
            totals = list(tax_res["totals"].values())[0]
            # Assign computed GENCI amounts
            line.genci_amount_subtotal = totals.get("amount_untaxed", 0.0)
            line.genci_amount_tax = totals.get("amount_tax", 0.0)
            line.genci_amount_total = line.genci_amount_subtotal + line.genci_amount_tax
