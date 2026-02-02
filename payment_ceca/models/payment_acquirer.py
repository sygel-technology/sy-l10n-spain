# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import hashlib

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..controllers.main import PaymentTransacionCecaController


class PaymentAcquirer(models.Model):
    _inherit = "payment.acquirer"

    def _get_ceca_url(self, env):
        if env == "prod":
            return "https://pgw.ceca.es/tpvweb/tpv/compra.action"
        else:
            return "https://tpv.ceca.es/tpvweb/tpv/compra.action"

    provider = fields.Selection(
        selection_add=[("ceca", "Ceca")], ondelete={"ceca": "set default"}
    )
    ceca_acquirer_bin = fields.Char()
    ceca_merchant_id = fields.Char()
    ceca_terminal_id = fields.Char()
    ceca_business_name = fields.Char()
    ceca_encriptation_key = fields.Char()
    ceca_exponente = fields.Char()
    ceca_tipo_moneda = fields.Char()
    ceca_force_bizum = fields.Boolean(string="Force Bizum")
    ceca_force_card = fields.Boolean(string="Force Card")
    ceca_force_google = fields.Boolean(string="Force Google Pay")
    ceca_force_apple = fields.Boolean(string="Force Apple Pay")

    @api.constrains(
        "ceca_force_bizum", "ceca_force_card", "ceca_force_google", "ceca_force_apple"
    )
    def _check_unique_force_method(self):
        for sel in self:
            if (
                sel.provider == "ceca"
                and [
                    sel.ceca_force_bizum,
                    sel.ceca_force_card,
                    sel.ceca_force_google,
                    sel.ceca_force_apple,
                ].count(True)
                > 1
            ):
                raise ValidationError(_("Only one payment mode can be forced."))

    def ceca_values(self, values):

        base_url = self.env["ir.config_parameter"].get_param("web.base.url")

        api_url = self._get_ceca_url("prod" if self.state == "enabled" else "test")
        MerchantID = self.ceca_merchant_id
        AcquirerBIN = self.ceca_acquirer_bin
        TerminalID = self.ceca_terminal_id
        Exponente = self.ceca_exponente
        TipoMoneda = self.ceca_tipo_moneda
        URL_OK = "{}{}".format(base_url, PaymentTransacionCecaController._return_url)
        URL_NOK = "{}{}?transaction={}".format(
            base_url, PaymentTransacionCecaController._error_url, values["reference"]
        )
        Num_operacion = values["reference"]
        # REVISAR ESTO COPIADO DEL OTRO MÓDULO
        amount_split = str(values["amount"]).split(".")
        Importe = str(amount_split[0]) + str(amount_split[1])
        # Fix ad 0 final
        if len(amount_split[1]) == 1:
            Importe = str(Importe) + "0"
        Idioma = 1
        Pago_soportado = "SSL"
        Cifrado = "SHA2"
        Clave = self.ceca_encriptation_key
        Firma = "{}{}{}{}{}{}{}{}{}{}{}".format(
            Clave,
            MerchantID,
            AcquirerBIN,
            TerminalID,
            Num_operacion,
            Importe,
            TipoMoneda,
            Exponente,
            Cifrado,
            URL_OK,
            URL_NOK,
        )
        Firma = hashlib.sha256(Firma.encode()).hexdigest()
        values.update(
            {
                "api_url": api_url,
                "MerchantID": MerchantID,
                "AcquirerBIN": AcquirerBIN,
                "TerminalID": TerminalID,
                "Exponente": Exponente,
                "TipoMoneda": TipoMoneda,
                "URL_OK": URL_OK,
                "URL_NOK": URL_NOK,
                "Num_operacion": Num_operacion,
                "Importe": Importe,
                "Idioma": Idioma,
                "Pago_soportado": Pago_soportado,
                "Descripcion": values["reference"],
                "Firma": Firma,
                "Cifrado": Cifrado,
            }
        )
        if self.ceca_force_card:
            values.update({"inicioTarjeta": "1"})
        elif self.ceca_force_bizum:
            values.update({"inicioBizum": "1"})
        elif self.ceca_force_google:
            values.update({"inicioGoogle": "1"})
        elif self.ceca_force_apple:
            values.update({"inicioApple": "1"})
        return values

    def _get_default_payment_method_id(self):
        self.ensure_one()
        if self.provider != "ceca":
            return super()._get_default_payment_method_id()
        return self.env.ref("payment_ceca.payment_method_ceca").id
