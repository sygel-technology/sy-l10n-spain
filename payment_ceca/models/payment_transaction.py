# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, models

from odoo.addons.payment.models.payment_acquirer import ValidationError


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def _get_tx_from_feedback_data(self, provider, data):
        """Override of payment to find the transaction based on Ceca data.

        :param str provider: The provider of the acquirer that handled the transaction
        :param dict data: The feedback data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if inconsistent data were received
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_feedback_data(provider, data)
        if provider != "ceca":
            return tx
        reference = data.get("Num_operacion")
        if not reference:
            raise ValidationError(_("Ceca: Received data with missing Num_operacion"))
        tx = self.sudo().search(
            [
                ("provider", "=", "ceca"),
                ("reference", "=", reference),
                ("state", "=", "draft"),
            ],
            limit=1,
        )
        if not tx:
            raise ValidationError(
                _("Ceca: No transaction found matching reference %(ref)s.")
                % {"ref": reference}
            )
        return tx

    def _process_feedback_data(self, data):
        """Override of payment to process the transaction based on Ceca data.

        Note: self.ensure_one()

        :param dict data: The feedback data build from information passed to the return route.
        :return: None
        :raise: ValidationError if inconsistent data were received
        """
        super()._process_feedback_data(data)
        if self.provider != "ceca":
            return

        try:
            self.sudo()._set_done()
            self.sudo().write({"acquirer_reference": data.get("Referencia")})
        except Exception as e:
            raise ValidationError(
                _("Ceca: Transaction %(ref)s could not be validated.")
                % {"ref": data.reference}
            ) from e

    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return ceca-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing values
            of the transaction
        :return: The dict of acquirer-specific processing values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider != "ceca":
            return res
        res.update(self.acquirer_id.ceca_values(processing_values))
        return res

    def _get_sent_message(self):
        """Override of payment to return a different message.

        :return: The 'transaction sent' message
        :rtype: str
        """
        message = super()._get_sent_message()
        if self.provider == "ceca":
            message = _("The customer has selected %(p_name)s to make the payment.") % {
                "p_name": self.acquirer_id.name
            }
        return message
