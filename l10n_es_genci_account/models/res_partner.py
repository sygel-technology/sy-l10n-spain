# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    genci_subject = fields.Boolean(
        string="Subject to GENCI",
        default=True,
        help="Determine if this customer/supplier is subject to the Genci rate.",
    )
