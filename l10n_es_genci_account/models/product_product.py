# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    genci_has_amount = fields.Boolean(compute="_compute_genci_has_amount", store=True)
    genci_rule_id = fields.Many2one("genci.rule", string="GENCI rule")

    @api.depends("genci_subject")
    def _compute_genci_has_amount(self):
        for rec in self:
            rec.genci_has_amount = rec.genci_subject == "yes"
