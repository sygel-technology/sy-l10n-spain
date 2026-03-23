# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    genci_amount = fields.Monetary(
        string="GENCI Contribution",
        currency_field="currency_id",
        readonly=True,
        help="GENCI contribution corresponding to this product line.",
    )
    genci_rule_id = fields.Many2one(
        comodel_name="genci.rule",
        string="GENCI Rule",
        readonly=True,
        help="GENCI rule used to generate this invoice line.",
    )
