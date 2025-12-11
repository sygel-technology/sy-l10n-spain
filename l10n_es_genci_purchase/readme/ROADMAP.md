Pending Features:

- **Product GENCI flag type**
  The `genci_subject` field on products is currently a selection (`yes` / `no`), inherited from `l10n_es_genci_account`.
  Once this field is migrated to a Boolean in the parent module, this module should be updated accordingly to use a Boolean flag.

- **GENCI logic reuse**
  Purchase and Sale modules currently share very similar GENCI logic.
  As a future improvement or during a migration, this logic should be extracted
  into a shared mixin to reduce duplication and improve maintainability.

- **Units of Measure handling for GENCI calculations**
  GENCI amounts are currently computed per purchased unit (product_qty), without applying any Unit of Measure (UoM) conversion. This is an intentional design decision, as GENCI rules are defined per product unit. If future requirements introduce UoM-dependent GENCI rules (e.g. weight or volume based), this logic should be reviewed and adapted accordingly.
