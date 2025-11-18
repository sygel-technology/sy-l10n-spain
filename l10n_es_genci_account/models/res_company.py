# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    genci_enable = fields.Boolean(
        string="Enable GENCI",
        default=False,
        help=(
            "Activates the GENCI module for this company, "
            "enabling all related configurations."
        ),
    )
    genci_show_in_reports = fields.Boolean(
        string="Show detailed GENCI amount in report lines",
        help="If active, GENCI amount is shown in reports.",
    )

    def write(self, vals):
        res = super().write(vals)
        if "genci_enable" in vals:
            group = self.env.ref("l10n_es_genci_account.group_genci_enabled")
            for company in self:
                users = company.user_ids
                if vals["genci_enable"]:
                    users.write({"groups_id": [(4, group.id)]})
                else:
                    users.write({"groups_id": [(3, group.id)]})
        return res
