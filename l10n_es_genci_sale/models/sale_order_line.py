# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


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

    def _get_genci_vals(self, order, genci_product):
        vals_list = []
        source_lines = order.order_line.filtered(
            lambda l: l.product_id != genci_product
            and l.product_id.genci_subject == "yes"
            and l.product_id.genci_rule_id
        )
        if source_lines:
            rule_quantities = {}
            for line in source_lines:
                rule = line.product_id.genci_rule_id
                rule_quantities.setdefault(rule, 0.0)
                rule_quantities[rule] += line.product_uom_qty
                line.genci_amount = line.product_uom_qty * rule.unit_price

            last_seq = max(order.order_line.mapped("sequence") or [0])
            seq = last_seq

            for rule, qty in rule_quantities.items():
                seq += 1
                vals_list.append(
                    order._prepare_genci_line_vals(
                        genci_product=genci_product,
                        rule=rule,
                        qty=qty,
                        sequence=seq,
                    )
                )
        return vals_list

    def _sync_genci_lines(self, orders, genci_product):
        for order in orders:
            expected_vals = self._get_genci_vals(order, genci_product)
            existing_lines = order.order_line.filtered(
                lambda l: l.product_id == genci_product
            )
            duplicated_lines = self.env["sale.order.line"]
            seen_names = set()
            for line in existing_lines:
                if line.name in seen_names:
                    duplicated_lines |= line
                else:
                    seen_names.add(line.name)
            if duplicated_lines:
                duplicated_lines.with_context(avoid_line_recursion=True).unlink()
                existing_lines -= duplicated_lines
            existing_by_name = {line.name: line for line in existing_lines}
            expected_by_name = {vals["name"]: vals for vals in expected_vals}
            for name, vals in expected_by_name.items():
                if name in existing_by_name:
                    existing_by_name[name].with_context(
                        avoid_line_recursion=True
                    ).write(
                        {
                            "product_uom_qty": vals["product_uom_qty"],
                            "price_unit": vals["price_unit"],
                            "sequence": vals["sequence"],
                            "genci_amount": vals["genci_amount"],
                        }
                    )
                else:
                    self.with_context(avoid_line_recursion=True).create(vals)
            for name, line in existing_by_name.items():
                if name not in expected_by_name:
                    line.with_context(avoid_line_recursion=True).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        if not self.env.context.get("avoid_line_recursion"):
            genci_product = self.env.ref(
                "l10n_es_genci_account.product_genci_service",
                raise_if_not_found=False,
            )
            orders = (
                lines.filtered(lambda l: l.product_id != genci_product)
                .mapped("order_id")
                .filtered(lambda o: o.state in ["draft", "sent"] and o.is_genci)
            )
            self._sync_genci_lines(orders, genci_product)
        return lines

    def write(self, vals):
        orders_before = self.mapped("order_id")
        res = super().write(vals)
        if not self.env.context.get("avoid_line_recursion") and any(
            f in vals for f in ["product_id", "product_uom_qty", "order_id"]
        ):
            genci_product = self.env.ref(
                "l10n_es_genci_account.product_genci_service",
                raise_if_not_found=False,
            )
            orders = (
                orders_before
                | self.filtered(lambda l: l.product_id != genci_product).mapped(
                    "order_id"
                )
            ).filtered(lambda o: o.state in ["draft", "sent"] and o.is_genci)
            self._sync_genci_lines(orders, genci_product)
        return res

    def unlink(self):
        orders = self.filtered(
            lambda l: l.product_id
            and l.product_id.genci_subject == "yes"
            and l.product_id.genci_rule_id
        ).mapped("order_id")
        res = super().unlink()
        if not self.env.context.get("avoid_line_recursion"):
            genci_product = self.env.ref(
                "l10n_es_genci_account.product_genci_service",
                raise_if_not_found=False,
            )
            orders = orders.filtered(
                lambda o: o.state in ["draft", "sent"] and o.is_genci
            )
            self._sync_genci_lines(orders, genci_product)
        return res
