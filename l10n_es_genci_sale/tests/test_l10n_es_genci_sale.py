# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo.exceptions import UserError
from odoo.tests.common import TransactionCase


class TestL10nEsGenciSale(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env["res.company"].create({"name": "Test Company"})

        cls.partner = cls.env["res.partner"].create(
            {
                "name": "GENCI Partner",
                "genci_subject": True,
                "company_id": cls.company.id,
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

        cls.product = cls.env["product.product"].create(
            {
                "name": "GENCI Product",
                "genci_subject": "yes",
                "genci_rule_id": cls.rule_valid.id,
                "uom_id": uom.id,
            }
        )

        cls.income_account = cls.env["account.account"].create(
            {
                "name": "GENCI Income",
                "code": "X2000",
                "account_type": "income",
                "company_id": cls.company.id,
            }
        )

        cls.genci_service = cls.env.ref(
            "l10n_es_genci_account.product_genci_service"
        ).with_company(cls.company)

        cls.genci_service.sudo().write(
            {
                "property_account_income_id": cls.income_account.id,
            }
        )

        cls.genci_service.categ_id.sudo().write(
            {
                "property_account_income_categ_id": cls.income_account.id,
            }
        )

    def test_genci_rule_date_constraint_invalid(self):

        self.product.genci_rule_id = self.rule_invalid

        with self.assertRaises(UserError):
            self.env["sale.order"].create(
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
                                "product_uom_qty": 1,
                                "price_unit": 10.0,
                            },
                        )
                    ],
                }
            )

    def test_genci_rule_date_constraint_valid(self):

        self.product.genci_rule_id = self.rule_valid
        order = self.env["sale.order"].create(
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
                            "product_uom_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        self.assertTrue(order, "The valid order was not created correctly.")

    def test_manage_genci_order_lines(self):
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        order = self.env["sale.order"].create(
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
                            "product_uom_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.with_context(avoid_recursion=True).manage_genci_order_lines()
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        genci_lines = order.order_line.filtered(lambda l: l.product_id == genci_service)
        self.assertEqual(len(genci_lines), 1, "GENCI line was not created.")
        self.assertEqual(
            genci_lines[0].price_unit,
            self.rule_valid.unit_price,
            "GENCI line price unit is incorrect.",
        )

    def test_apply_genci(self):
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        order = self.env["sale.order"].create(
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
                            "product_uom_qty": 2,
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
            "apply_genci should generate GENCI lines for draft orders with is_genci=True.",
        )
        self.assertEqual(
            genci_lines[0].price_unit,
            self.rule_valid.unit_price,
            "GENCI line created by apply_genci() has incorrect unit price.",
        )

    def test_write_remove_genci_lines_when_is_genci_disabled(self):
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        order = self.env["sale.order"].create(
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
                            "product_uom_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.apply_genci()
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        self.assertTrue(
            order.order_line.filtered(lambda l: l.product_id == genci_service)
        )
        order.write({"is_genci": False})
        self.assertFalse(
            order.order_line.filtered(lambda l: l.product_id == genci_service),
            "GENCI lines should be deleted when is_genci is set to False.",
        )

    def test_write_reapply_genci_on_order_line_change(self):
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        order = self.env["sale.order"].create(
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
                            "product_uom_qty": 1,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        order.apply_genci()
        initial_lines = order.order_line.filtered(
            lambda l: l.product_id == genci_service
        )
        self.assertEqual(len(initial_lines), 1)
        order.write(
            {
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 2,
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
            "GENCI lines should be recalculated, not duplicated.",
        )

    def test_create_applies_genci(self):
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.rule_valid
        genci_service = self.env.ref("l10n_es_genci_account.product_genci_service")
        order = self.env["sale.order"].create(
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
                                "product_uom_qty": 2,
                                "price_unit": 100.0,
                            },
                        )
                    ],
                }
            ]
        )[0]
        genci_lines = order.order_line.filtered(lambda l: l.product_id == genci_service)
        self.assertTrue(
            genci_lines,
            "It was expected that GENCI lines would be created when the order is created.",
        )
        original_line = order.order_line.filtered(
            lambda l: l.product_id.genci_subject == "yes"
        )
        expected_amount = (
            original_line.product_uom_qty
            * original_line.product_id.genci_rule_id.unit_price
        )
        self.assertEqual(
            original_line.genci_amount,
            expected_amount,
            "The genci_amount of the original line was not calculated correctly.",
        )
