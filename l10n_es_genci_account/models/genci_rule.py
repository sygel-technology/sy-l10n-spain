# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class GenciRule(models.Model):
    _name = "genci.rule"
    _description = "Genci Rule"

    name = fields.Char(
        compute="_compute_auto_name",
        store=True,
        help="Descriptive name of the GENCI rule",
    )
    material_id = fields.Many2one(
        comodel_name="genci.material",
        string="Material Type",
        required=True,
        help="Material type of the container to which this GENCI rate applies",
    )
    capacity_id = fields.Many2one(
        comodel_name="genci.capacity",
        string="Container Capacity",
        required=True,
        help="Capacity or volume of the container to which this GENCI rate applies",
    )
    use_type = fields.Selection(
        [("commercial", "Commercial"), ("industrial", "Industrial")],
        string="Use",
        required=True,
    )
    unit_price = fields.Float(required=True, digits=(16, 4))
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id.id,
    )
    date_from = fields.Date(
        string="From", help="Start date of the validity period of this rate"
    )
    date_to = fields.Date(
        string="To", help="End date of the validity period of this rate"
    )

    def copy(self, default=None):
        default = dict(default or {})
        default["name"] = _("%s (copy)") % self.name
        return super().copy(default)

    @api.depends("material_id", "capacity_id", "use_type", "name")
    def _compute_auto_name(self):
        for rec in self:
            material = rec.material_id.name if rec.material_id else ""
            capacity = rec.capacity_id.name if rec.capacity_id else ""
            use_type = (
                dict(self._fields["use_type"].selection).get(rec.use_type)
                if rec.use_type
                else ""
            )
            auto_parts = [p for p in [material, capacity, use_type] if p]
            auto_name = " - ".join(auto_parts)
            if rec.name and " | " in rec.name:
                user_part, _ = rec.name.split(" | ", 1)
            else:
                user_part = rec.name or "Rule"
            rec.name = f"{user_part} | {auto_name}" if auto_name else user_part
