# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_genci_invoice_line_vals(
        self, move, genci_product, rule, total_qty, genci_account, sequence
    ):
        """Extend GENCI line values with the applied rule."""
        vals = super()._prepare_genci_invoice_line_vals(
            move=move,
            genci_product=genci_product,
            rule=rule,
            total_qty=total_qty,
            genci_account=genci_account,
            sequence=sequence,
        )
        vals["genci_rule_id"] = rule.id
        return vals

    def lines_grouped_by_picking(self):
        """Extend grouping to distribute GENCI lines by picking."""
        result = super().lines_grouped_by_picking()
        return self._distribute_genci_lines_by_picking(result)

    def _get_genci_product(self):
        """Return the GENCI service product."""
        return self.env.ref("l10n_es_genci_account.product_genci_service")

    def _get_genci_source_lines(self):
        """Return invoice lines subject to GENCI with a valid rule."""
        self.ensure_one()
        return self.invoice_line_ids.filtered_domain(
            [
                ("product_id.genci_subject", "=", "yes"),
                "|",
                ("product_id.genci_rule_id", "!=", False),
                ("product_id.product_tmpl_id.genci_rule_id", "!=", False),
            ]
        )

    @api.model
    def _get_genci_rule_from_line(self, line):
        """Return the applicable GENCI rule for an invoice line."""
        return (
            line.product_id.genci_rule_id
            or line.product_id.product_tmpl_id.genci_rule_id
        )

    def _distribute_genci_lines_by_picking(self, result):
        """Distribute GENCI lines across pickings based on delivered quantities."""
        self.ensure_one()
        clean_result = result
        genci_product = self._get_genci_product()
        genci_lines = self.invoice_line_ids.filtered(
            lambda l: l.product_id == genci_product and l.genci_rule_id
        )
        if genci_lines:
            qty_by_picking_rule = self._get_genci_qty_by_picking_rule()
            clean_result = [
                item for item in result if item.get("line") not in genci_lines
            ]
            empty_picking = self.env["stock.picking"]
            for line in genci_lines:
                found = False
                for (picking, rule), qty in qty_by_picking_rule.items():
                    if rule == line.genci_rule_id:
                        clean_result.append(
                            {
                                "picking": picking,
                                "line": line,
                                "quantity": qty,
                            }
                        )
                        found = True
                if not found:
                    clean_result.append(
                        {
                            "picking": empty_picking,
                            "line": line,
                            "quantity": line.quantity,
                        }
                    )
            no_picking = []
            with_picking = []
            for item in clean_result:
                if item["picking"]:
                    with_picking.append(item)
                else:
                    no_picking.append(item)
            clean_result = no_picking + self._sort_grouped_lines(with_picking)
        return clean_result

    def _get_genci_qty_by_picking_rule(self):
        """Compute quantities per (picking, GENCI rule)."""
        self.ensure_one()
        qty_by_picking_rule = {}
        for line in self._get_genci_source_lines():
            rule = self._get_genci_rule_from_line(line)
            for move_line in line.move_line_ids.filtered(
                lambda ml: ml.picking_id and ml.picking_id.state == "done"
            ):
                key = (move_line.picking_id, rule)
                qty_by_picking_rule[key] = (
                    qty_by_picking_rule.get(key, 0.0) + move_line.quantity_done
                )
        return qty_by_picking_rule
