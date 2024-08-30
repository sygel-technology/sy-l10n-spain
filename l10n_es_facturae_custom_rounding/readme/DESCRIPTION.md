When the FacturaE is generated, it does not consider the taxes values
calculated in the invoice to populate the information in the
TaxesOutputs section, but it calculates it on the fly when creating the
file. It causes trouble when the account_invoice_custom_rounding module
is installed, as FacturaE does not consider the custom rounding method
that might be applied to the invoice. The goal of this module is making
l10n_es_facturae and account_invoice_custom_rounding modules compatible.
