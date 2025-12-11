# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestL10nEsGenciPurchase(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env["res.company"].create({"name": "Test Company"})

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "GENCI Supplier",
                "genci_subject": True,
                "company_id": cls.company.id,
                "supplier_rank": 1,
            }
        )

        cls.material = cls.env["genci.material"].create({"name": "Metal"})
        cls.capacity = cls.env["genci.capacity"].create({"name": "5L"})

        cls.rule_valid = cls.env["genci.rule"].create(
            {
                "name": "Valid Rule",
                "material_id": cls.material.id,
                "capacity_id": cls.capacity.id,
                "use_type": "commercial",
                "unit_price": 10.0,
                "date_from": date.today() - timedelta(days=5),
                "date_to": date.today() + timedelta(days=5),
            }
        )

        cls.rule_invalid = cls.env["genci.rule"].create(
            {
                "name": "Invalid Rule",
                "material_id": cls.material.id,
                "capacity_id": cls.capacity.id,
                "use_type": "commercial",
                "unit_price": 10.0,
                "date_from": date.today() + timedelta(days=10),
                "date_to": date.today() + timedelta(days=20),
            }
        )
        uom = cls.env.ref("uom.product_uom_unit")

        Account = cls.env["account.account"]

        cls.expense_account = Account.create(
            {
                "name": "GENCI Expense",
                "code": "X4000",
                "account_type": "expense",
                "company_id": cls.company.id,
            }
        )

        cls.income_account = Account.create(
            {
                "name": "GENCI Income",
                "code": "X5000",
                "account_type": "income",
                "company_id": cls.company.id,
            }
        )

        cls.payable_account = Account.create(
            {
                "name": "GENCI Payable",
                "code": "X3000",
                "account_type": "liability_payable",
                "company_id": cls.company.id,
            }
        )

        cls.partner.property_account_payable_id = cls.payable_account.id

        cls.product = cls.env["product.product"].create(
            {
                "name": "GENCI Product PO",
                "genci_subject": "yes",
                "genci_rule_id": cls.rule_valid.id,
                "uom_id": uom.id,
                "company_id": cls.company.id,
                "property_account_expense_id": cls.expense_account.id,
            }
        )

        cls.product.categ_id.write(
            {
                "property_account_expense_categ_id": cls.expense_account.id,
                "property_account_income_categ_id": cls.income_account.id,
            }
        )

        cls.genci_service = cls.env.ref(
            "l10n_es_genci_account.product_genci_service"
        ).with_company(cls.company)

        cls.genci_service.sudo().write(
            {
                "property_account_expense_id": cls.expense_account.id,
                "property_account_income_id": cls.income_account.id,
                "company_id": cls.company.id,
            }
        )
        cls.genci_service.categ_id.sudo().write(
            {
                "property_account_expense_categ_id": cls.expense_account.id,
                "property_account_income_categ_id": cls.income_account.id,
            }
        )

    def test_genci_rule_date_constraint_invalid(self):
        """A purchase order using an invalid GENCI rule must raise UserError."""
        self.product.genci_rule_id = self.rule_invalid
        with self.assertRaises(UserError):
            self.env["purchase.order"].create(
                {
                    "partner_id": self.partner.id,
                    "company_id": self.company.id,
                    "date_order": date.today(),
                    "is_genci": True,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "product_qty": 1,
                                "price_unit": 10.0,
                            },
                        )
                    ],
                }
            )

    def test_genci_rule_date_constraint_valid(self):
        """A purchase order using a valid GENCI rule must be created successfully."""
        self.product.genci_rule_id = self.rule_valid
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "date_order": date.today(),
                "is_genci": True,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        self.assertTrue(
            order,
            "The purchase order with a valid GENCI rule was not created correctly.",
        )

    def test_manage_genci_order_lines(self):
        """GENCI lines must be generated correctly when calling manage_genci_order_lines()."""
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "date_order": date.today(),
                "is_genci": True,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.with_context(avoid_recursion=True).manage_genci_order_lines()
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        genci_lines = order.order_line.filtered(lambda l: l.product_id == genci_service)
        self.assertEqual(
            len(genci_lines), 1, "GENCI line was not created in purchase order."
        )
        self.assertEqual(
            genci_lines[0].price_unit,
            self.rule_valid.unit_price,
            "GENCI line price_unit in PO is incorrect.",
        )
        self.assertEqual(
            genci_lines[0].product_qty,
            1,
            "GENCI line quantity in PO is incorrect.",
        )

    def test_apply_genci(self):
        """apply_genci should generate GENCI lines for draft purchase orders
        when is_genci=True."""
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "date_order": date.today(),
                "is_genci": True,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 2,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.apply_genci()
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        genci_lines = order.order_line.filtered(lambda l: l.product_id == genci_service)
        self.assertTrue(
            genci_lines,
            "apply_genci should generate GENCI lines for draft purchase orders "
            "with is_genci=True.",
        )
        self.assertEqual(
            genci_lines[0].price_unit,
            self.rule_valid.unit_price,
            "GENCI line created by apply_genci() has incorrect unit price in purchases.",
        )
        self.assertEqual(
            genci_lines[0].product_qty,
            2,
            "GENCI line created by apply_genci() should match aggregated product quantity.",
        )

    def test_write_remove_genci_lines_when_is_genci_disabled(self):
        """GENCI lines must be removed when is_genci is set to False in purchase orders."""
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "date_order": date.today(),
                "is_genci": True,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.apply_genci()
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        self.assertTrue(
            order.order_line.filtered(lambda l: l.product_id == genci_service),
            "GENCI lines should exist before disabling is_genci.",
        )
        order.write({"is_genci": False})
        self.assertFalse(
            order.order_line.filtered(lambda l: l.product_id == genci_service),
            "GENCI lines should be deleted when is_genci is set to False.",
        )

    def test_create_applies_genci(self):
        """GENCI lines must be created automatically when a purchase order is created."""
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        order = self.env["purchase.order"].create(
            [
                {
                    "partner_id": self.partner.id,
                    "company_id": self.company.id,
                    "date_order": date.today(),
                    "is_genci": True,
                    "order_line": [
                        (
                            0,
                            0,
                            {
                                "product_id": self.product.id,
                                "product_qty": 2,
                                "price_unit": 50.0,
                            },
                        )
                    ],
                }
            ]
        )[0]
        genci_lines = order.order_line.filtered(lambda l: l.product_id == genci_service)
        self.assertTrue(
            genci_lines,
            "GENCI lines should be created automatically on purchase order creation.",
        )
        expected_price = self.rule_valid.unit_price
        self.assertEqual(
            genci_lines[0].price_unit,
            expected_price,
            "The GENCI line price_unit is incorrect after automatic generation.",
        )
        original_line = order.order_line.filtered(
            lambda l: l.product_id == self.product
        )
        expected_amount = (
            original_line.product_qty
            * original_line.product_id.genci_rule_id.unit_price
        )
        self.assertEqual(
            original_line.genci_amount,
            expected_amount,
            "The genci_amount of the original purchase line was not calculated correctly.",
        )

    def test_write_auto_enable_genci_when_partner_changes(self):
        """Changing supplier to one with GENCI enabled should auto-enable is_genci,
        unless explicitly set in the same write()."""
        supplier2 = self.env["res.partner"].create(
            {
                "name": "Supplier GENCI",
                "genci_subject": True,
                "company_id": self.company.id,
            }
        )
        supplier1 = self.env["res.partner"].create(
            {
                "name": "No GENCI Supplier",
                "genci_subject": False,
                "company_id": self.company.id,
            }
        )
        order = self.env["purchase.order"].create(
            {
                "partner_id": supplier1.id,
                "company_id": self.company.id,
                "is_genci": False,
            }
        )
        order.write({"partner_id": supplier2.id})
        self.assertTrue(
            order.is_genci,
            "is_genci should auto-enable when changing to a GENCI supplier.",
        )

    def test_write_reapply_genci_on_order_line_change(self):
        """GENCI lines must be recomputed when purchase order lines change,
        but must not be duplicated."""
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "is_genci": True,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.apply_genci()
        initial_genci_lines = order.order_line.filtered(
            lambda l: l.product_id == genci_service
        )
        self.assertEqual(len(initial_genci_lines), 1)
        order.write(
            {
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 2,
                            "price_unit": 10.0,
                        },
                    )
                ]
            }
        )
        genci_lines = order.order_line.filtered(lambda l: l.product_id == genci_service)
        self.assertEqual(
            len(genci_lines),
            1,
            "GENCI lines should be recalculated but never duplicated.",
        )

    def test_compute_qty_invoiced_no_invoices(self):
        """GENCI qty_invoiced must remain 0 when no related invoices exist."""
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "is_genci": True,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 3,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.apply_genci()
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        genci_line = order.order_line.filtered(lambda l: l.product_id == genci_service)
        self.assertTrue(genci_line, "GENCI line must be created.")
        self.assertEqual(
            genci_line.qty_invoiced,
            0,
            "GENCI qty_invoiced should be 0 without invoices.",
        )

    def test_compute_qty_invoiced_partial_invoice(self):
        """GENCI qty_invoiced must equal the qty of invoiced source product lines."""
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        order = self.env["purchase.order"].create(
            {
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "is_genci": True,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_qty": 3,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.apply_genci()
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        genci_line = order.order_line.filtered(lambda l: l.product_id == genci_service)
        source_line = order.order_line.filtered(lambda l: l.product_id == self.product)
        self.assertTrue(genci_line, "GENCI line must be created.")
        self.assertTrue(source_line, "Source purchase line must exist.")
        purchase_journal = self.env["account.journal"].search(
            [
                ("type", "=", "purchase"),
                ("company_id", "=", self.company.id),
            ],
            limit=1,
        ) or self.env["account.journal"].create(
            {
                "name": "Test Purchase Journal",
                "code": "TPJ",
                "type": "purchase",
                "company_id": self.company.id,
            }
        )
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner.id,
                "company_id": self.company.id,
                "journal_id": purchase_journal.id,
                "invoice_date": fields.Date.today(),
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 1,
                            "price_unit": 10.0,
                            "purchase_line_id": source_line.id,
                        },
                    )
                ],
            }
        )
        move.action_post()
        genci_line.invalidate_recordset(["qty_invoiced"])
        self.assertEqual(
            genci_line.qty_invoiced,
            1,
            "GENCI qty_invoiced should match partially invoiced quantity.",
        )
