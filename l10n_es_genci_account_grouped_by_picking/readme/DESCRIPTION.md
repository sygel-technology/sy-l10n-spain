This module acts as a bridge between l10n_es_genci_account and account_invoice_report_grouped_by_picking.

In the base GENCI module, contribution lines are generated at invoice level, without considering stock pickings. As a result, when using reports grouped by picking, GENCI lines are not properly distributed and may appear without a picking reference.

This module enhances that behavior by:

Assigning the corresponding genci_rule_id to generated GENCI invoice lines.
Distributing GENCI lines across pickings based on the quantities delivered per picking.
Ensuring compatibility with the grouped invoice report provided by account_invoice_report_grouped_by_picking.

The implementation is intentionally kept in a separate module to avoid adding a direct dependency in the core GENCI module and to keep responsibilities well separated.
