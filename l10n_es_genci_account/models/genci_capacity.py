# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class GenciCapacity(models.Model):
    _name = "genci.capacity"
    _description = "Container Capacity for GENCI"
    _rec_name = "name"

    name = fields.Char(
        string="Capacity",
        required=True,
        help="Capacity or volume of the container (e.g., 1L, 5L)",
    )
