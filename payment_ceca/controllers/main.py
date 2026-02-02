# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaymentTransacionCecaController(http.Controller):

    _return_url = "/payment/ceca/feedback"
    _error_url = "/payment/ceca/error"
    _transaction_answer_url = "/payment/ceca/notify"

    @http.route(_return_url, type="http", auth="public", methods=["GET"], website=True)
    def ceca_form_feedback(self, **post):
        return request.redirect("/payment/status")

    @http.route(_error_url, type="http", auth="public", methods=["GET"], website=True)
    def ceca_form_error(self, **post):
        if post.get("transaction"):
            _logger.info(
                "Cancelling CECA Transaction {}.".format(post.get("transaction"))
            )
            transaction = (
                request.env["payment.transaction"]
                .sudo()
                .search(
                    [
                        ("provider", "=", "ceca"),
                        ("reference", "=", post.get("transaction")),
                        ("state", "=", "draft"),
                    ],
                    limit=1,
                )
            )
            if transaction:
                transaction._set_canceled()
        return request.redirect("/payment/status")

    @http.route(
        _transaction_answer_url,
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def ceca_notify(self, **post):
        _logger.info("CECA Online Notification: {}".format(post))
        request.env["payment.transaction"]._handle_feedback_data("ceca", post)
        return "success"
