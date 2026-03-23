Pending Features:

- **Multi-company:** Confirm whether GENCI rules should support multi-company logic, and ensure each rule is linked to its respective company with coherent application logic.

- **Currency:** Validate whether GENCI rules can be configured in different currencies or only in euros.

- **Supplier association:** Determine if each GENCI rule should be linked to a specific supplier, and consider if multiple rules could exist for the same product depending on the supplier.

- **Product GENCI flag type:** Consider changing the genci_subject field on product.template from a selection (yes/no) to a Boolean is_genci field for simplicity and consistency in the code.

- **GENCI lines grouping by picking:**
  Currently, GENCI lines are not distributed per picking in multi-delivery scenarios.
  Instead, they are linked to the first available picking via `sale_line_ids`,
  which avoids showing them under "No reference" in reports.

  A proper distribution per picking would require leveraging the method
  `lines_grouped_by_picking`, which is provided by the module
  `account_invoice_report_grouped_by_picking`.

  To avoid introducing an additional dependency in this module,
  the current implementation keeps a simpler approach.

  If a more accurate distribution per picking is required in the future,
  it is recommended to implement it in a separate integration module
  that depends on `account_invoice_report_grouped_by_picking`.
