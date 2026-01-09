## Prerequisites

Before using this module, make sure that the base module *l10n_es_genci_account*
is correctly configured:

#### 1. Company enabled for GENCI

- Go to *Settings → Companies → Select your company*
- In the *GENCI* tab, enable *"Company subject to GENCI"*

#### 2. GENCI rules configured

- Go to *Invoicing → Configuration → GENCI → GENCI Rules*
- Create the required rules with their corresponding rates
- Configure validity dates if needed

#### 3. Products configured

- On each product form, *Invoicing* tab:
- Enable *"Subject to GENCI"*
- Select the applicable *GENCI rule*

#### 4. Contacts configured

- By default, all contacts are *subject to GENCI*
- If a contact should NOT apply GENCI, disable "Subject to GENCI" on the contact form

## Valued delivery slip configuration

For the GENCI contribution to appear on the valued delivery slip, the delivery slip contact must have the **"Valued Delivery Slip"** option enabled in the "Sales & Purchases" tab of the contact form.

#### Steps

1. Go to *Contacts* and open the customer form
2. Open the *"Sales & Purchases"* tab
3. Enable the *"Valued Delivery Slip"* checkbox
