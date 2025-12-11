# Prerequisites

Before using this module, ensure that the base module **`l10n_es_genci_account`** is properly configured:

- Company GENCI is enabled
  *(Settings → Companies → GENCI tab)*
- GENCI rules are created with validity dates if necessary
- Products purchased from suppliers are configured as **"Subject to GENCI"** with linked rules
- Vendors have **"Subject to GENCI"** enabled when appropriate

For detailed configuration instructions, refer to the **`l10n_es_genci_account`** module documentation.

# 1. Create a Purchase Order

1. Go to **Purchase → Orders → Requests for Quotation → Create**
2. Select a vendor that has **"Subject to GENCI"** enabled

# 2. Apply GENCI Checkbox

- The **"Apply GENCI"** checkbox appears in the order header
  *(only when company GENCI is enabled)*
- If the vendor is GENCI-subject, this box should be checked to apply GENCI rules
- If left unchecked, **GENCI lines will not be created**, even if products require it

# 3. Add Products

- Add products that are configured as **"Subject to GENCI"**
- Products must have a valid GENCI rule assigned
- The rule’s validity dates must include the purchase order date

# 4. Automatic GENCI Line Creation

GENCI lines are automatically generated when:

- You save the purchase order
- Or you modify order lines

Behavior:

- **One GENCI line is created per distinct GENCI rule**
- **Quantity = sum of all purchased quantities using that rule**
- GENCI lines appear at the bottom of the order lines

# Application Logic

**Conditions for GENCI Application**

GENCI logic is applied only when:

- The company has GENCI enabled
- The **"Apply GENCI"** checkbox is enabled on the purchase order
- The vendor is subject to GENCI
- The fiscal position (if defined) allows GENCI
- Products have valid GENCI rules for the purchase order date

If any requirement is not met, GENCI lines will not be generated.
