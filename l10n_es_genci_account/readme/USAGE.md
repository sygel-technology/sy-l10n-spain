Usage Flow

1. Create invoice.
2. Add products with GENCI rules.
3. If all conditions met (partner, fiscal pos, rule, date, etc.) → GENCI line(s) auto-added.

Application Logic

- One GENCI line per distinct rule.
- Uses generated product: "Tasa GENCI (R.D. 1055/2022)".
- Line description comes from rule name.
- Amount = Unit Rate × Total Quantity across matching products.

Error Handling

- If "Is GENCI" is checked and no rule applies → Warning is shown.
