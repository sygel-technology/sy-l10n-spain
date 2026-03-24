# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    genci_rule_id = fields.Many2one(
        comodel_name="genci.rule",
        string="GENCI Rule",
        readonly=True,
        help="GENCI rule used to generate this invoice line.",
    )
