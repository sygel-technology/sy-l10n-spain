This module extends `l10n_es_genci_account` to integrate GENCI functionality into the Purchase workflow.

It automatically creates GENCI rate lines in purchase orders when products subject to GENCI are added, and ensures correct linkage of GENCI amounts with vendor bills.

## Key Features

- **"Apply GENCI" checkbox** on purchase orders to control GENCI application
- **Automatic creation of GENCI lines** based on product rules and purchased quantities
- **Consolidation of multiple products sharing the same GENCI rule** into a single GENCI line
- **Display of GENCI amounts on purchase order reports** (when enabled in company settings)
