# Copyright 2026 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from datetime import date, timedelta

from odoo.tests import TransactionCase


class TestL10nEsGenciAccountGroupedbyPicking(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.material = cls.env["genci.material"].create({"name": "Metal"})
        cls.capacity = cls.env["genci.capacity"].create({"name": "5L"})
        uom_unit = cls.env.ref("uom.product_uom_unit")
        cls.uom_unit = uom_unit
        cls.genci_rule = cls.env["genci.rule"].create(
            {
                "name": "Rule",
                "material_id": cls.material.id,
                "capacity_id": cls.capacity.id,
                "use_type": "commercial",
                "unit_price": 10.0,
                "date_from": date.today() - timedelta(days=1),
                "date_to": date.today() + timedelta(days=1),
            }
        )
        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Customer GENCI",
                "genci_subject": True,
                "company_id": cls.company.id,
            }
        )
        cls.income_account = cls.env["account.account"].create(
            {
                "name": "GENCI Sales",
                "code": "X2000",
                "account_type": "income",
                "company_id": cls.company.id,
            }
        )
        cls.receivable_account = cls.env["account.account"].create(
            {
                "name": "Receivable",
                "code": "X2100",
                "account_type": "asset_receivable",
                "company_id": cls.company.id,
            }
        )
        cls.sale_journal = cls.env["account.journal"].create(
            {
                "name": "Test Sales Journal",
                "code": "TGJ",
                "type": "sale",
                "company_id": cls.company.id,
                "default_account_id": cls.income_account.id,
            }
        )
        cls.product_template = cls.env["product.template"].create(
            {
                "name": "GENCI Product",
                "type": "consu",
                "genci_subject": "yes",
                "genci_rule_id": cls.genci_rule.id,
                "list_price": 100.0,
                "uom_id": uom_unit.id,
                "uom_po_id": uom_unit.id,
            }
        )
        cls.product_template.categ_id.write(
            {"property_account_income_categ_id": cls.income_account.id}
        )
        cls.product = cls.product_template.product_variant_ids[0]

        cls.genci_service = cls.env.ref("l10n_es_genci_account.product_genci_service")

    def test_manage_genci_assigns_rule(self):
        """GENCI lines should have genci_rule_id assigned."""
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.genci_rule
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": date.today(),
                "journal_id": self.sale_journal.id,
                "company_id": self.company.id,
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
        genci_lines = invoice.line_ids.filtered(
            lambda l: l.product_id == self.genci_service
        )
        self.assertTrue(genci_lines, "GENCI line should be created")
        for line in genci_lines:
            self.assertEqual(
                line.genci_rule_id,
                self.genci_rule,
                "GENCI line must store its rule",
            )

    def test_get_genci_qty_by_picking_rule(self):
        """GENCI quantities should be grouped by picking and rule."""
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.genci_rule
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": date.today(),
                "journal_id": self.sale_journal.id,
                "company_id": self.company.id,
                "is_genci": True,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 4,
                            "price_unit": 100.0,
                            "account_id": self.income_account.id,
                        },
                    )
                ],
            }
        )
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product)
        self.assertTrue(line, "Source invoice line should exist")
        customer_loc = self.env.ref("stock.stock_location_customers")
        internal_loc = self.env.ref("stock.stock_location_stock")
        picking_type = self.env["stock.picking.type"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        picking_1 = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": picking_type.id,
                "location_id": internal_loc.id,
                "location_dest_id": customer_loc.id,
            }
        )
        picking_2 = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": picking_type.id,
                "location_id": internal_loc.id,
                "location_dest_id": customer_loc.id,
            }
        )
        move_1 = self.env["stock.move"].create(
            {
                "name": self.product.display_name,
                "product_id": self.product.id,
                "product_uom_qty": 2.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking_1.id,
                "location_id": internal_loc.id,
                "location_dest_id": customer_loc.id,
            }
        )
        move_2 = self.env["stock.move"].create(
            {
                "name": self.product.display_name,
                "product_id": self.product.id,
                "product_uom_qty": 2.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking_2.id,
                "location_id": internal_loc.id,
                "location_dest_id": customer_loc.id,
            }
        )
        (move_1 | move_2)._action_confirm()
        (move_1 | move_2)._action_assign()
        move_1.quantity_done = 2.0
        move_2.quantity_done = 2.0
        (move_1 | move_2)._action_done()
        line.move_line_ids = [(6, 0, [move_1.id, move_2.id])]
        self.assertEqual(picking_1.state, "done")
        self.assertEqual(picking_2.state, "done")
        self.assertEqual(move_1.quantity_done, 2.0)
        self.assertEqual(move_2.quantity_done, 2.0)
        self.assertIn(move_1, line.move_line_ids)
        self.assertIn(move_2, line.move_line_ids)
        qty_by_picking_rule = invoice._get_genci_qty_by_picking_rule()
        self.assertEqual(
            qty_by_picking_rule.get((picking_1, self.genci_rule)),
            2.0,
            "Picking 1 should contain 2 GENCI units",
        )
        self.assertEqual(
            qty_by_picking_rule.get((picking_2, self.genci_rule)),
            2.0,
            "Picking 2 should contain 2 GENCI units",
        )

    def test_lines_grouped_by_picking_distributes_genci_lines(self):
        """GENCI lines should be distributed by picking in grouped report data."""
        self.product.genci_subject = "yes"
        self.product.genci_rule_id = self.genci_rule
        invoice = self.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": self.partner.id,
                "invoice_date": date.today(),
                "journal_id": self.sale_journal.id,
                "company_id": self.company.id,
                "is_genci": True,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "quantity": 4,
                            "price_unit": 100.0,
                            "account_id": self.income_account.id,
                        },
                    )
                ],
            }
        )
        line = invoice.invoice_line_ids.filtered(lambda l: l.product_id == self.product)
        self.assertTrue(line, "Source invoice line should exist")
        customer_loc = self.env.ref("stock.stock_location_customers")
        internal_loc = self.env.ref("stock.stock_location_stock")
        picking_type = self.env["stock.picking.type"].search(
            [("company_id", "=", self.company.id)], limit=1
        )
        picking_1 = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": picking_type.id,
                "location_id": internal_loc.id,
                "location_dest_id": customer_loc.id,
            }
        )
        picking_2 = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": picking_type.id,
                "location_id": internal_loc.id,
                "location_dest_id": customer_loc.id,
            }
        )
        move_1 = self.env["stock.move"].create(
            {
                "name": self.product.display_name,
                "product_id": self.product.id,
                "product_uom_qty": 2.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking_1.id,
                "location_id": internal_loc.id,
                "location_dest_id": customer_loc.id,
            }
        )
        move_2 = self.env["stock.move"].create(
            {
                "name": self.product.display_name,
                "product_id": self.product.id,
                "product_uom_qty": 2.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking_2.id,
                "location_id": internal_loc.id,
                "location_dest_id": customer_loc.id,
            }
        )
        (move_1 | move_2)._action_confirm()
        (move_1 | move_2)._action_assign()
        move_1.quantity_done = 2.0
        move_2.quantity_done = 2.0
        (move_1 | move_2)._action_done()
        line.move_line_ids = [(6, 0, [move_1.id, move_2.id])]
        self.assertEqual(picking_1.state, "done")
        self.assertEqual(picking_2.state, "done")
        invoice.manage_genci_invoice_lines()
        grouped_lines = invoice.lines_grouped_by_picking()
        genci_grouped_lines = [
            item
            for item in grouped_lines
            if item["line"].product_id == self.genci_service
        ]
        self.assertEqual(
            len(genci_grouped_lines),
            2,
            "GENCI lines should be distributed into two grouped entries",
        )
        picking_qty = {
            item["picking"]: item["quantity"] for item in genci_grouped_lines
        }
        self.assertEqual(
            picking_qty.get(picking_1),
            2.0,
            "Picking 1 should contain 2 GENCI units",
        )
        self.assertEqual(
            picking_qty.get(picking_2),
            2.0,
            "Picking 2 should contain 2 GENCI units",
        )
        no_reference_lines = [
            item for item in genci_grouped_lines if not item["picking"]
        ]
        self.assertFalse(
            no_reference_lines,
            "GENCI lines should not remain without picking reference",
        )
