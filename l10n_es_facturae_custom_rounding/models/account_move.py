# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models, tools


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_facturae_tax_info(self):
        output_taxes, withheld_taxes = super()._get_facturae_tax_info()
        rounding_method = self.tax_calculation_rounding_method
        if (
            rounding_method
            and rounding_method != self.company_id.tax_calculation_rounding_method
        ):
            for tax in output_taxes:
                output_taxes[tax]["amount"] = 0.0
                withheld_taxes[tax]["amount"] = 0.0
            sign = -1 if self.move_type[:3] == "out" else 1
            for line in self.line_ids:
                base = line.balance * sign
                for tax in line.tax_ids:
                    tax_amount = base * tax.amount / 100
                    if rounding_method == "round_per_line":
                        tax_amount = tools.float_round(
                            tax_amount, precision_rounding=self.currency_id.rounding
                        )
                    if tools.float_compare(tax.amount, 0, precision_digits=2) >= 0:
                        output_taxes[tax]["amount"] += tax_amount
                    else:
                        withheld_taxes[tax]["amount"] += tax_amount
        return output_taxes, withheld_taxes
