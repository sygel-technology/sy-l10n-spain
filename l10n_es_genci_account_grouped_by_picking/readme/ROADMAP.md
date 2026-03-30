**Known issues**

It has been identified that when a delivery is returned and a customer invoice is generated (standard invoice, not a refund), the GENCI line associated with the returned product is displayed with a positive amount, whereas it should be negative.

This issue does not occur in credit notes (out_refund), where the behavior is correct.

The root cause is that the module `account_invoice_report_grouped_by_picking` applies a sign correction when grouping invoice lines by picking. This logic is implemented in the method lines_grouped_by_picking, where quantities are adjusted using an internal sign computation together with `_get_signed_quantity_done()`.

Reference:
*https://github.com/OCA/account-invoice-reporting/blob/9a1c954f9b220fc90b507e2d8c52f83618c2797d/account_invoice_report_grouped_by_picking/models/account_move.py#L65*

**Possible solution**

A possible solution would be to introduce a small helper method in this module to replicate the sign logic used in the original implementation, and apply it when computing GENCI quantities (e.g. in `_get_genci_qty_by_picking_rule`).
