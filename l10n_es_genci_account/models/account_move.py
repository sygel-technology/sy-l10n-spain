# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    is_genci = fields.Boolean(
        string="Is GENCI",
        default=True,
        help=(
            "If unchecked, the GENCI rate will not be applied even "
            "if the products require it.",
        ),
    )

    @api.constrains("invoice_date", "invoice_line_ids")
    def _check_genci_rules_dates(self):
        for move in self.filtered(lambda m: m.is_genci and m.partner_id.genci_subject):
            invoice_date = move.invoice_date or fields.Date.today()
            for line in move.invoice_line_ids.filtered(
                lambda l: l.product_id.genci_subject == "yes"
                and l.product_id.genci_rule_id
            ):
                rule = line.product_id.genci_rule_id
                if (rule.date_from and invoice_date < rule.date_from) or (
                    rule.date_to and invoice_date > rule.date_to
                ):
                    raise UserError(
                        _(
                            "No GENCI rule is valid for the product '%(product)s' "
                            "on the invoice date (%(date)s)."
                        )
                        % {
                            "product": line.product_id.display_name,
                            "date": invoice_date,
                        }
                    )

    def manage_genci_invoice_lines(self):
        """Manage GENCI lines, always adding them at the end of the invoice."""
        genci_product = self.env.ref("l10n_es_genci_account.product_genci_service")

        for move in self:
            # Remove existing GENCI lines in the invoice
            genci_invoice_lines = move.line_ids.filtered(
                lambda l: l.product_id == genci_product
            )
            if genci_invoice_lines:
                genci_invoice_lines.unlink()
            # Determine if GENCI should be applied by fiscal position and partner
            if move.fiscal_position_id:
                apply_genci = move.fiscal_position_id.genci_subject
            else:
                apply_genci = move.is_genci and move.partner_id.genci_subject
            if not apply_genci:
                continue
            # Filter invoice lines that are subject to GENCI
            genci_source_lines = move.invoice_line_ids.filtered(
                lambda l: l.product_id.genci_subject == "yes"
                and (
                    l.product_id.genci_rule_id
                    or l.product_id.product_tmpl_id.genci_rule_id
                )
            )
            if not genci_source_lines:
                continue
            # Aggregate quantities by GENCI rule and calculate line amounts
            rule_quantities = {}
            for line in genci_source_lines:
                rule = (
                    line.product_id.genci_rule_id
                    or line.product_id.product_tmpl_id.genci_rule_id
                )
                rule_quantities.setdefault(rule, 0.0)
                rule_quantities[rule] += line.quantity
                line.genci_amount = line.quantity * rule.unit_price
            # Determine last sequence number in invoice lines
            last_sequence = (
                move.line_ids and max(move.line_ids.mapped("sequence") or [0]) or 0
            )
            # Create GENCI lines at the end of the invoice
            genci_vals_list = []
            sequence = last_sequence
            for rule, total_qty in rule_quantities.items():
                genci_account = (
                    genci_product.property_account_income_id
                    or genci_product.categ_id.property_account_income_categ_id
                )
                if not genci_account:
                    raise UserError(
                        _(
                            "No accounting account is defined for the GENCI product "
                            "'%(product)s'."
                        )
                        % {"product": genci_product.display_name}
                    )
                sequence += 1
                genci_vals_list.append(
                    {
                        "move_id": move.id,
                        "product_id": genci_product.id,
                        "quantity": total_qty,
                        "price_unit": rule.unit_price,
                        "purchase_price": rule.unit_price,
                        "name": f"GENCI: {rule.name}",
                        "account_id": genci_account.id,
                        "sequence": sequence,
                    }
                )
            if genci_vals_list:
                move.env["account.move.line"].create(genci_vals_list)

    def apply_genci(self):
        draft_moves = self.filtered(lambda m: m.state == "draft" and m.is_genci)
        if draft_moves:
            draft_moves.with_context(avoid_recursion=True).manage_genci_invoice_lines()

    def write(self, vals):
        # Check if the 'is_genci' flag is being updated
        is_genci_changed = "is_genci" in vals
        res = super().write(vals)
        # Only iterate over moves where GENCI is disabled and is_genci was changed
        for move in self.filtered(lambda m: is_genci_changed and not m.is_genci):
            genci_product = self.env.ref("l10n_es_genci_account.product_genci_service")
            move.line_ids.filtered(lambda l: l.product_id == genci_product).unlink()
        # Recalculate GENCI lines if relevant fields changed or GENCI was enabled
        if (
            any(key in vals for key in ["invoice_line_ids", "move_type", "partner_id"])
            or is_genci_changed
        ):
            move_to_apply = self.filtered(lambda m: m.state == "draft" and m.is_genci)
            if move_to_apply:
                # Avoid recursion when generating GENCI invoice lines
                move_to_apply.with_context(
                    avoid_recursion=True
                ).manage_genci_invoice_lines()
        return res

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves.apply_genci()
        return moves
