# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def action_account_move_manual_sii_result_wizard(self):
        if not self.env[
            "account.move.manual.sii.result.wizard"
        ].filter_editable_move_ids(self):
            raise UserError(
                _(
                    "None of the selected moves can be edited "
                    "because they are not invoices subject to the SII"
                )
            )

        return {
            "name": _("Edit SII Result Values Wizard"),
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "account.move.manual.sii.result.wizard",
            "target": "new",
            "context": {
                "active_ids": self.ids,
            },
        }
