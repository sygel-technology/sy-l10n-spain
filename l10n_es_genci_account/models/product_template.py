# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    genci_subject = fields.Selection(
        [("yes", "Yes"), ("no", "No")],
        default="no",
        string="Subject To GENCI",
        required=True,
    )
    genci_rule_id = fields.Many2one(
        "genci.rule",
        string="GENCI Rule",
        compute="_compute_genci_rule_id",
        inverse="_inverse_genci_rule_id",
        store=True,
    )

    @api.onchange("genci_subject")
    def _onchange_genci_subject(self):
        if self.genci_subject == "no":
            self.genci_rule_id = False

    @api.depends("product_variant_ids", "product_variant_ids.genci_rule_id")
    def _compute_genci_rule_id(self):
        for template in self:
            rules = template.product_variant_ids.mapped("genci_rule_id")
            template.genci_rule_id = rules[0] if len(rules) == 1 else False

    def _inverse_genci_rule_id(self):
        for template in self:
            template.product_variant_ids.write(
                {"genci_rule_id": template.genci_rule_id.id}
            )
