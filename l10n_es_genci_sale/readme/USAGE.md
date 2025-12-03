# Prerequisites

Before using this module, ensure that the base module **`l10n_es_genci_account`** is properly configured:

- Company GENCI is enabled
  *(Settings → Companies → GENCI tab)*
- GENCI rules are created with validity dates if necessary
- Products are configured as **"Subject to GENCI"** with linked rules
- Partners have **"Subject to GENCI"** checked (default)

**Important:**

For GENCI fee lines to compute and update their invoiced quantities correctly, ensure that the “Tasa GENCI” product is configured with the invoicing policy “Based on ordered quantities.”
GENCI lines are not driven by delivered quantities; they must always follow the product’s ordered quantity invoicing logic.

For detailed configuration instructions, refer to the **`l10n_es_genci_account`** module documentation.

# 1. Create a Sale Order

1. Go to **Sales → Orders → Quotations → Create**
2. Select a partner that has **"Subject to GENCI"** enabled

# 2. Apply GENCI Checkbox

- The **"Apply GENCI"** checkbox appears in the order header
  *(only when company GENCI is enabled)*
- If the partner is GENCI-subject, check this box to apply GENCI rates
- If it remains unchecked, **GENCI lines will not be created**, even if products require it

# 3. Add Products

- Add products that are configured as **"Subject to GENCI"**
- Products must have a valid GENCI rule assigned
- The rule’s validity dates must include the order date

# 4. Automatic GENCI Line Creation

GENCI lines are automatically generated when:

- You save the order
- Or you modify order lines

Behavior:

- **One GENCI line is created per distinct GENCI rule**
- **Quantity = sum of all product quantities using that rule**

# Application Logic

**Conditions for GENCI Application**
- Company has GENCI enabled
- "Apply GENCI" checkbox is checked on the order
- Partner is subject to GENCI
- Fiscal position (if set) allows GENCI
- Products have valid GENCI rules for the order date
