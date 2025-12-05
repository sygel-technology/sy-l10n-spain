# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class GenciMaterial(models.Model):
    _name = "genci.material"
    _description = "Material for GENCI"
    _rec_name = "name"

    name = fields.Char(
        string="Material Type",
        required=True,
        help="Type of material (metal, plastic, glass, etc.)",
    )
