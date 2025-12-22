# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    is_genci = fields.Boolean(
        string="Apply GENCI",
        default=False,
        help="Indicates whether GENCI should be applied to this purchase order.",
    )
    genci_company = fields.Boolean(
        string="Company GENCI Enabled",
        compute="_compute_genci_company",
    )

    @api.depends("company_id.genci_enable")
    def _compute_genci_company(self):
        for order in self:
            order.genci_company = bool(order.company_id.genci_enable)

    @api.onchange("partner_id")
    def _onchange_partner_genci(self):
        for order in self:
            order.is_genci = (
                order.partner_id.genci_subject if order.partner_id else False
            )

    @api.constrains("order_line", "is_genci")
    def _check_genci_rules_dates(self):
        for order in self.filtered(lambda o: o.is_genci and o.partner_id.genci_subject):
            date_to_check = fields.Date.to_date(
                order.date_order or fields.Datetime.now()
            )
            genci_lines = order.order_line.filtered(
                lambda l: l.product_id.genci_subject == "yes"
                and l.product_id.genci_rule_id
            )
            for line in genci_lines:
                rule = line.product_id.genci_rule_id
                rule_from = (
                    fields.Date.to_date(rule.date_from) if rule.date_from else None
                )
                rule_to = fields.Date.to_date(rule.date_to) if rule.date_to else None
                if (rule_from and date_to_check < rule_from) or (
                    rule_to and date_to_check > rule_to
                ):
                    raise UserError(
                        _(
                            "No GENCI rule is valid for the product '%(product)s' "
                            "on the order date (%(date)s)."
                        )
                        % {
                            "product": line.product_id.display_name,
                            "date": date_to_check,
                        }
                    )

    def manage_genci_order_lines(self):
        genci_product = self.env.ref("l10n_es_genci_account.product_genci_service")
        for order in self:
            order._remove_genci_lines()
            # Decide whether GENCI applies
            apply_genci = False
            if order.fiscal_position_id:
                apply_genci = order.fiscal_position_id.genci_subject
            else:
                if order.is_genci and not order.partner_id.genci_subject:
                    raise UserError(
                        _(
                            "GENCI cannot be applied because "
                            "the vendor is not subject to GENCI."
                        )
                    )
                apply_genci = order.is_genci
            if not apply_genci:
                continue
            # Collect source lines
            source_lines = order.order_line.filtered(
                lambda l: l.product_id.genci_subject == "yes"
                and l.product_id.genci_rule_id
            )
            if not source_lines:
                continue
            # Compute quantities per rule
            rule_quantities = {}
            for line in source_lines:
                rule = line.product_id.genci_rule_id
                rule_quantities.setdefault(rule, 0.0)
                rule_quantities[rule] += line.product_qty
                line.genci_amount = line.product_qty * rule.unit_price
            last_seq = max(order.order_line.mapped("sequence") or [0])
            seq = last_seq
            vals_list = []
            genci_account = (
                genci_product.property_account_expense_id
                or genci_product.categ_id.property_account_expense_categ_id
            )
            if not genci_account:
                raise UserError(
                    _("No accounting account defined for GENCI product %s")
                    % genci_product.display_name
                )
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
            if vals_list:
                pol_model = self.env["purchase.order.line"]
                for vals in vals_list:
                    try:
                        pol_model.create(vals)
                    except Exception:
                        product = self.env["product.product"].browse(
                            vals.get("product_id")
                        )
                        raise UserError(
                            _(
                                "GENCI line could not be created.\n\n"
                                "Purchase Order: %(order)s\n"
                                "Product: %(product)s\n"
                                "GENCI Rule: %(rule)s\n\n"
                                "Please check the configuration of the GENCI "
                                "product and its accounting accounts."
                            )
                            % {
                                "order": order.name or order.id,
                                "product": product.display_name,
                                "rule": vals.get("name"),
                            }
                        ) from None

    def _prepare_genci_line_vals(self, genci_product, rule, qty, sequence):
        self.ensure_one()
        return {
            "order_id": self.id,
            "product_id": genci_product.id,
            "product_qty": qty,
            "price_unit": rule.unit_price,
            "name": f"GENCI: {rule.name}",
            "sequence": sequence,
            "genci_amount": qty * rule.unit_price,
        }

    def _remove_genci_lines(self):
        genci_product = self.env.ref(
            "l10n_es_genci_account.product_genci_service",
        )
        self.order_line.filtered(lambda l: l.product_id == genci_product).unlink()

    def apply_genci(self):
        target = self.filtered(lambda o: o.state in ["draft", "sent"] and o.is_genci)
        if target:
            target.with_context(avoid_recursion=True).manage_genci_order_lines()

    @api.model_create_multi
    def create(self, vals_list):
        partner_model = self.env["res.partner"]
        for vals in filter(lambda v: v.get("partner_id"), vals_list):
            partner = partner_model.browse(vals["partner_id"]).exists()
            if partner and partner.genci_subject and "is_genci" not in vals:
                vals["is_genci"] = True
        orders = super().create(vals_list)
        orders.apply_genci()
        return orders

    def write(self, vals):
        partner_changed = "partner_id" in vals
        is_genci_changed = "is_genci" in vals
        res = super().write(vals)
        for order in self:
            if (
                partner_changed
                and order.partner_id.genci_subject
                and not is_genci_changed
            ):
                order.is_genci = True
            if is_genci_changed and not order.is_genci:
                order._remove_genci_lines()
        if partner_changed or is_genci_changed or "order_line" in vals:
            target = self.filtered(
                lambda o: o.state in ["draft", "sent"] and o.is_genci
            )
            if target:
                target.with_context(avoid_recursion=True).manage_genci_order_lines()
        return res
