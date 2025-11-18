# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from datetime import date, timedelta

from odoo.tests import TransactionCase


class TestL10nEsAccountGenci(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.material = cls.env["genci.material"].create({"name": "Metal"})
        cls.capacity = cls.env["genci.capacity"].create({"name": "5L"})

        uom_id = cls.env.ref("uom.product_uom_unit").id

        cls.genci_rule = cls.env["genci.rule"].create(
            {
                "name": "Rate",
                "material_id": cls.material.id,
                "capacity_id": cls.capacity.id,
                "use_type": "commercial",
                "unit_price": 10.0,
                "date_from": date.today() - timedelta(days=1),
                "date_to": date.today() + timedelta(days=1),
            }
        )

        cls.product_template_yes = cls.env["product.template"].create(
            {
                "name": "GENCI Product Yes",
                "type": "consu",
                "genci_subject": "yes",
                "genci_rule_id": cls.genci_rule.id,
                "list_price": 100.0,
                "uom_id": uom_id,
                "uom_po_id": uom_id,
            }
        )
        cls.product_template_no = cls.env["product.template"].create(
            {
                "name": "GENCI Product No",
                "type": "consu",
                "genci_subject": "no",
                "list_price": 100.0,
                "uom_id": uom_id,
                "uom_po_id": uom_id,
            }
        )

        cls.product = cls.product_template_yes.product_variant_ids[0]

        cls.company = cls.env["res.company"].create({"name": "Test Company"})
        cls.user = cls.env["res.users"].create(
            {
                "name": "Test User",
                "login": "testuser",
                "company_ids": [(6, 0, [cls.company.id])],
                "company_id": cls.company.id,
            }
        )
        cls.genci_group = cls.env.ref("l10n_es_genci_account.group_genci_enabled")

        cls.partner_subject = cls.env["res.partner"].create(
            {
                "name": "GENCI Partner",
                "genci_subject": True,
                "company_id": cls.company.id,
            }
        )
        cls.partner_not_subject = cls.env["res.partner"].create(
            {
                "name": "Non-GENCI Partner",
                "genci_subject": False,
                "company_id": cls.company.id,
            }
        )

        cls.genci_service = cls.env.ref("l10n_es_genci_account.product_genci_service")

        cls.income_account = cls.env["account.account"].create(
            {
                "name": "GENCI Sales",
                "code": "X1000",
                "account_type": "income",
                "company_id": cls.company.id,
            }
        )
        cls.receivable_account = cls.env["account.account"].create(
            {
                "name": "Receivable",
                "code": "X1100",
                "account_type": "asset_receivable",
                "company_id": cls.company.id,
            }
        )

        cls.product_template_yes.categ_id.write(
            {
                "property_account_income_categ_id": cls.income_account.id,
            }
        )

        cls.sale_journal = cls.env["account.journal"].create(
            {
                "name": "Test Sales Journal",
                "code": "TSJ",
                "type": "sale",
                "company_id": cls.company.id,
                "default_account_id": cls.income_account.id,
            }
        )

    def test_compute_auto_name(self):
        rule = self.env["genci.rule"].create(
            {
                "material_id": self.material.id,
                "capacity_id": self.capacity.id,
                "use_type": "commercial",
                "unit_price": 10.0,
            }
        )
        expected_name = "Rule | Metal - 5L - Commercial"
        self.assertEqual(
            rule.name, expected_name, "The computed name is incorrect on creation"
        )

    def test_genci_has_amount_yes(self):
        """Test that genci_has_amount is True when genci_subject is 'yes'"""
        product = self.product_template_yes.product_variant_ids[0]
        self.assertTrue(product.genci_has_amount)

    def test_genci_has_amount_no(self):
        """Test that genci_has_amount is False when genci_subject is not 'yes'"""
        product = self.product_template_no.product_variant_ids[0]
        self.assertFalse(product.genci_has_amount)

    def test_enable_genci_adds_group(self):
        """Test that enabling genci_enable adds the GENCI group to all company users"""
        self.company.write({"genci_enable": True})
        self.assertIn(
            self.genci_group,
            self.user.groups_id,
            "The GENCI group should be assigned to the user",
        )

    def test_disable_genci_removes_group(self):
        """Test that disabling genci_enable removes the GENCI group from all company users"""
        self.company.write({"genci_enable": True})
        self.company.write({"genci_enable": False})
        self.env.invalidate_all()
        self.assertNotIn(
            self.genci_group,
            self.user.groups_id,
            "The GENCI group should be removed from the user",
        )

    def test_manage_genci_invoice_lines_creates_lines(self):
        """Test that GENCI lines are correctly generated at the end of the invoice."""

        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.genci_rule
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_subject.id,
                "invoice_date": date.today(),
                "company_id": self.company.id,
                "journal_id": self.sale_journal.id,
                "is_genci": True,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 2,
                            "price_unit": 100.0,
                            "account_id": self.income_account.id,
                        },
                    )
                ],
            }
        )
        invoice.manage_genci_invoice_lines()
        genci_product = self.genci_service
        genci_lines = invoice.line_ids.filtered(lambda l: l.product_id == genci_product)
        self.assertTrue(genci_lines, "No GENCI line was created.")
        for line in genci_lines:
            self.assertEqual(
                line.price_unit,
                line.purchase_price,
                "GENCI line should have zero margin.",
            )
        original_line = invoice.invoice_line_ids.filtered(
            lambda l: l.product_id.genci_subject == "yes"
        )
        self.assertIsNotNone(
            original_line.genci_amount, "genci_amount was not set on the original line"
        )
        expected_amount = (
            original_line.quantity * original_line.product_id.genci_rule_id.unit_price
        )
        self.assertEqual(
            original_line.genci_amount,
            expected_amount,
            "genci_amount not computed correctly.",
        )

    def test_apply_genci_creates_lines(self):
        """Test that apply_genci creates GENCI lines correctly."""

        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.genci_rule

        draft_invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_subject.id,
                "invoice_date": date.today(),
                "company_id": self.company.id,
                "journal_id": self.sale_journal.id,
                "is_genci": True,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 3,
                            "price_unit": 100.0,
                            "account_id": self.income_account.id,
                        },
                    )
                ],
            }
        )
        draft_invoice.apply_genci()

        genci_product = self.genci_service
        genci_lines = draft_invoice.line_ids.filtered(
            lambda l: l.product_id == genci_product
        )
        self.assertTrue(genci_lines, "The GENCI line was not created.")

        for line in genci_lines:
            rule = self.product.genci_rule_id
            self.assertEqual(line.price_unit, rule.unit_price, "Incorrect unit price")
            self.assertEqual(
                line.purchase_price, rule.unit_price, "Incorrect purchase price"
            )

        original_line = draft_invoice.invoice_line_ids.filtered(
            lambda l: l.product_id.genci_subject == "yes"
        )
        expected_amount = (
            original_line.quantity * original_line.product_id.genci_rule_id.unit_price
        )
        self.assertEqual(
            original_line.genci_amount,
            expected_amount,
            "genci_amount was not calculated correctly",
        )

    def test_write_updates_genci_lines(self):
        genci_product = self.env.ref("l10n_es_genci_account.product_genci_service")
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.genci_rule
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner_subject.id,
                "invoice_date": date.today(),
                "company_id": self.company.id,
                "journal_id": self.sale_journal.id,
                "is_genci": True,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": 100.0,
                            "account_id": self.income_account.id,
                        },
                    )
                ],
            }
        )
        genci_lines = invoice.line_ids.filtered(lambda l: l.product_id == genci_product)
        self.assertTrue(
            genci_lines,
            (
                "It was expected that the GENCI line would be created "
                "when the invoice was created."
            ),
        )
        invoice.write({"is_genci": False})
        genci_lines_after = invoice.line_ids.filtered(
            lambda l: l.product_id == genci_product
        )
        self.assertFalse(
            genci_lines_after,
            "The GENCI lines should be removed when is_genci is deactivated.",
        )
        invoice.write(
            {
                "is_genci": True,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 2,
                            "price_unit": 200.0,
                            "account_id": self.income_account.id,
                        },
                    )
                ],
            }
        )
        genci_lines_after_update = invoice.line_ids.filtered(
            lambda l: l.product_id == genci_product
        )
        self.assertTrue(
            genci_lines_after_update,
            (
                "It was expected that the GENCI lines would be regenerated "
                "when adding lines with is_genci=True."
            ),
        )

    def test_create_applies_genci(self):
        genci_product = self.env.ref("l10n_es_genci_account.product_genci_service")
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.genci_rule
        invoice = self.env["account.move"].create(
            [
                {
                    "move_type": "out_invoice",
                    "partner_id": self.partner_subject.id,
                    "invoice_date": date.today(),
                    "company_id": self.company.id,
                    "journal_id": self.sale_journal.id,
                    "is_genci": True,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "quantity": 3,
                                "price_unit": 150.0,
                                "account_id": self.income_account.id,
                            },
                        )
                    ],
                }
            ]
        )[0]

        genci_lines = invoice.line_ids.filtered(lambda l: l.product_id == genci_product)
        self.assertTrue(
            genci_lines,
            (
                "It was expected that the GENCI line would be created "
                "automatically when the invoice is created."
            ),
        )
        original_line = invoice.invoice_line_ids.filtered(
            lambda l: l.product_id.genci_subject == "yes"
        )
        expected_amount = (
            original_line.quantity * original_line.product_id.genci_rule_id.unit_price
        )
        self.assertEqual(
            original_line.genci_amount,
            expected_amount,
            "The genci_amount was not calculated correctly.",
        )
