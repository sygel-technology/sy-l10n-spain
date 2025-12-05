To configure this module, you need to:

1. Enable GENCI for the company:
    - Go to Settings → Users & Companies → Companies.
    - Select the desired company.
    - In the GENCI tab, check Enable GENCI.
    - Save the changes.

This enables the GENCI functionality for all invoices of that company and makes GENCI-specific configurations available elsewhere in the system.

2. Create GENCI Rules:
    - Material type (metal, plastic, etc.).
    - Usage type (commercial or industrial).
    - Container capacity (1L, 5L, etc.).
    - Rate amount (price per unit, excluding taxes).
    - Validity period (start/end date).
    - Rule name will be used as invoice line description.

3. Configure Products:
    - "Subject to GENCI" = Yes.
    - Link GENCI rule on Genci Tab.

4. Configure Partners:
    - GENCI Subject checked by default.
    - Uncheck if not applicable.

5. Fiscal Positions:
    - GENCI Subject checkbox controls inclusion.

6. Invoice Header Field: "Is GENCI":
    - Default depends on partner config.
    - If unchecked, GENCI lines removed even if products apply.
