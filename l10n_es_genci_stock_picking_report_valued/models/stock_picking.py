# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    genci_amount_subtotal = fields.Monetary(
        compute="_compute_genci_amounts",
        compute_sudo=True,
        currency_field="currency_id",
    )
    genci_amount_tax = fields.Monetary(
        compute="_compute_genci_amounts",
        compute_sudo=True,
        currency_field="currency_id",
    )
    genci_amount_total = fields.Monetary(
        compute="_compute_genci_amounts",
        compute_sudo=True,
        currency_field="currency_id",
    )
    picking_total_with_genci = fields.Monetary(
        compute="_compute_genci_amounts",
        compute_sudo=True,
        currency_field="currency_id",
    )
    genci_rule_summary = fields.Json(
        compute="_compute_genci_amounts",
        compute_sudo=True,
        help=(
            "Summary of GENCI amounts per applied GENCI rule in the picking. "
            "Each entry contains the rule name and its untaxed amount, taxes, "
            "and total amount."
        ),
    )

    @api.depends(
        "move_line_ids",
        "move_line_ids.genci_amount_subtotal",
        "move_line_ids.genci_amount_tax",
        "move_line_ids.genci_amount_total",
        "sale_id",
        "sale_id.is_genci",
    )
    def _compute_genci_amounts(self):
        for picking in self:
            # Always initialize values to avoid cache misses
            summary = {}
            subtotal = 0.0
            tax = 0.0
            total = 0.0
            # Compute GENCI amounts only for GENCI sale pickings
            if picking.sale_id and picking.sale_id.is_genci and picking.move_line_ids:
                for line in picking.move_line_ids:
                    rule = line.product_id.genci_rule_id
                    if not rule:
                        continue
                    # Initialize the summary entry for this GENCI rule
                    rule_id = rule.id
                    if rule_id not in summary:
                        summary[rule_id] = {
                            "name": rule.name,
                            "untaxed": 0.0,
                            "tax": 0.0,
                            "total": 0.0,
                        }
                    # Accumulate amounts per GENCI rule
                    summary[rule_id]["untaxed"] += line.genci_amount_subtotal
                    summary[rule_id]["tax"] += line.genci_amount_tax
                    summary[rule_id]["total"] += line.genci_amount_total
                    # Accumulate global GENCI totals for the picking
                    subtotal += line.genci_amount_subtotal
                    tax += line.genci_amount_tax
                    total += line.genci_amount_total
            # Assign computed GENCI totals to the picking
            picking.genci_rule_summary = summary
            picking.genci_amount_subtotal = subtotal
            picking.genci_amount_tax = tax
            picking.genci_amount_total = total
            picking.picking_total_with_genci = picking.amount_total + total

    def _get_report_valued_total_amount(self):
        total = super()._get_report_valued_total_amount()
        if self.sale_id and self.sale_id.is_genci:
            total += self.genci_amount_total or 0.0
        return total
