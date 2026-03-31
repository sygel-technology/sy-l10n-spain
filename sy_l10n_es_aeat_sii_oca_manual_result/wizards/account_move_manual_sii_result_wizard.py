# Copyright 2026 Alberto Martínez <alberto.martinez@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models

from odoo.addons.l10n_es_aeat.models.aeat_mixin import AEAT_STATES
from odoo.addons.l10n_es_aeat_sii_oca.models.sii_mixin import SII_STATES


class AccountMoveManualSiiResultWizard(models.TransientModel):
    _name = "account.move.manual.sii.result.wizard"
    _description = "Wizard to edit Sii state in moves"

    editable_move_ids = fields.Many2many(
        comodel_name="account.move",
    )
    has_warn = fields.Boolean(readonly=True)
    warn = fields.Text(readonly=True)
    aeat_state = fields.Selection(
        selection=AEAT_STATES + SII_STATES,
        string="AEAT send state",
        help="Indicates the state of this document in relation with the "
        "presentation at the AEAT",
    )
    aeat_send_failed = fields.Boolean(
        string="SII send failed",
        help="Indicates that the last attempt to communicate this document to "
        "the SII has failed. See SII return for details",
    )
    sii_csv = fields.Char(string="SII CSV")
    aeat_send_error = fields.Text(
        string="AEAT Send Error",
    )
    set_aeat_state = fields.Selection(
        selection=[("set", "Set"), ("ignore", "Ignore")],
        default="ignore",
        required=True,
    )
    set_aeat_send_failed = fields.Selection(
        selection=[("set", "Set"), ("ignore", "Ignore")],
        default="ignore",
        required=True,
    )
    set_sii_csv = fields.Selection(
        selection=[("set", "Set"), ("ignore", "Ignore")],
        default="ignore",
        required=True,
    )
    set_aeat_send_error = fields.Selection(
        selection=[("set", "Set"), ("ignore", "Ignore")],
        default="ignore",
        required=True,
    )

    @api.model
    def filter_editable_move_ids(self, moves):
        """Returns the moves in moves that can be edited by this wizard.
        The restriction is that this move must be subject to the SII.
        """
        return moves.filtered(lambda m: (m.sii_enabled and m.move_type != "entry"))

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        original_move_ids = self.env["account.move"].browse(
            self.env.context.get("active_ids")
        )
        editable_move_ids = self.filter_editable_move_ids(original_move_ids)
        invalid_move_ids = original_move_ids - editable_move_ids
        has_warn = bool(invalid_move_ids)
        warn = ""
        if has_warn:
            warn = _(
                "The following moves cannot be edited "
                "because they are not invoices subject to the SII: %(moves)s",
                moves=", ".join(invalid_move_ids.mapped("name")),
            )
        res.update(
            {"editable_move_ids": editable_move_ids, "has_warn": has_warn, "warn": warn}
        )
        return res

    def action_accept(self):
        self.ensure_one()
        vals = {}
        fields = ["aeat_state", "aeat_send_failed", "aeat_send_error", "sii_csv"]
        for field in fields:
            if self[f"set_{field}"] == "set":
                vals.update({field: self[field]})
        self.editable_move_ids.write(vals)
