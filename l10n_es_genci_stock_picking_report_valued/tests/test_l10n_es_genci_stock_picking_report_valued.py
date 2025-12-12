# Copyright 2025 Ángel Rivas <angel.rivas@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase


class TestL10nEsGenciStockPickingReportValued(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.partner = cls.env["res.partner"].create(
            {"name": "Partner GENCI", "genci_subject": True}
        )
        cls.uom = cls.env.ref("uom.product_uom_unit")
        cls.tax_a = cls.env["account.tax"].create(
            {
                "name": "TAX A 21%",
                "amount": 21.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": cls.company.id,
            }
        )
        cls.tax_b = cls.env["account.tax"].create(
            {
                "name": "TAX B 0%",
                "amount": 0.0,
                "amount_type": "percent",
                "type_tax_use": "sale",
                "company_id": cls.company.id,
            }
        )
        # GENCI service product (the one passed to _get_genci_product_taxes)
        cls.genci_product = cls.env.ref(
            "l10n_es_genci_account.product_genci_service"
        ).with_company(cls.company)
        cls.genci_product.write({"taxes_id": [(6, 0, [cls.tax_a.id])]})
        # Fiscal position mapping TAX A -> TAX B
        cls.fpos = cls.env["account.fiscal.position"].create(
            {
                "name": "FPos GENCI Test",
                "company_id": cls.company.id,
            }
        )
        cls.env["account.fiscal.position.tax"].create(
            {
                "position_id": cls.fpos.id,
                "tax_src_id": cls.tax_a.id,
                "tax_dest_id": cls.tax_b.id,
            }
        )
        # A product + sale order line to generate a sale_line on the move line
        cls.product = cls.env["product.product"].create(
            {
                "name": "Product X",
                "type": "product",
                "uom_id": cls.uom.id,
                "uom_po_id": cls.uom.id,
            }
        )
        # GENCI rule data
        cls.material = cls.env["genci.material"].create({"name": "Metal"})
        cls.capacity = cls.env["genci.capacity"].create({"name": "1L"})

        cls.genci_rule = cls.env["genci.rule"].create(
            {
                "material_id": cls.material.id,
                "capacity_id": cls.capacity.id,
                "use_type": "commercial",
                "unit_price": 10.0,
            }
        )
        # Use the same product but configured as GENCI-subject for move line compute
        cls.product_genci = cls.product
        cls.product_genci.write(
            {
                "genci_rule_id": cls.genci_rule.id,
                "genci_has_amount": True,
            }
        )

    def _create_move_line(self, fiscal_position=None):
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "is_genci": True,
                "fiscal_position_id": fiscal_position.id if fiscal_position else False,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product_genci.id,
                            "product_uom_qty": 1.0,
                            "price_unit": 10.0,
                        },
                    )
                ],
            }
        )
        sol = order.order_line[0]
        picking = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.env.ref("stock.picking_type_out").id,
                "location_id": self.env.ref("stock.stock_location_stock").id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "origin": order.name,
            }
        )
        move = self.env["stock.move"].create(
            {
                "name": self.product_genci.display_name,
                "product_id": self.product_genci.id,
                "product_uom": self.uom.id,
                "product_uom_qty": 1.0,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
                "picking_id": picking.id,
                "sale_line_id": sol.id,
            }
        )
        move_line = self.env["stock.move.line"].create(
            {
                "move_id": move.id,
                "picking_id": picking.id,
                "product_id": self.product_genci.id,
                "product_uom_id": self.uom.id,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
                "qty_done": 1.0,
            }
        )
        return move_line

    def test_get_genci_product_taxes(self):
        # No taxes => False
        self.genci_product.write({"taxes_id": [(5, 0, 0)]})
        ml = self._create_move_line(fiscal_position=self.fpos)
        self.assertFalse(ml._get_genci_product_taxes(self.genci_product))
        # Restore taxes for next checks
        self.genci_product.write({"taxes_id": [(6, 0, [self.tax_a.id])]})
        # No fiscal position => original taxes
        ml = self._create_move_line(fiscal_position=None)
        taxes = ml._get_genci_product_taxes(self.genci_product)
        self.assertEqual(taxes.ids, [self.tax_a.id])
        # With fiscal position mapping => mapped taxes
        ml = self._create_move_line(fiscal_position=self.fpos)
        taxes = ml._get_genci_product_taxes(self.genci_product)
        self.assertEqual(taxes.ids, [self.tax_b.id])

    def test_compute_genci_amount(self):
        # Move line linked to a sale_line with GENCI enabled,
        # without fiscal position mapping to 0%
        ml = self._create_move_line(fiscal_position=None)
        # Ensure the sale order is GENCI (helper must set it)
        ml.sale_line.order_id.is_genci = True
        ml._compute_genci_amount()
        self.assertEqual(ml.genci_rule_id, self.genci_rule)
        self.assertEqual(ml.genci_amount_subtotal, self.genci_rule.unit_price)
        self.assertGreater(
            ml.genci_amount_tax, 0.0, "GENCI tax amount should be computed"
        )
        self.assertAlmostEqual(
            ml.genci_amount_total,
            ml.genci_amount_subtotal + ml.genci_amount_tax,
            places=2,
        )

    def test_get_report_valued_total_amount_with_genci(self):
        ml = self._create_move_line(fiscal_position=None)
        picking = ml.picking_id
        picking.sale_id.is_genci = True
        ml._compute_genci_amount()
        picking._compute_genci_amounts()
        total = picking._get_report_valued_total_amount()
        base_total = picking.amount_total or 0.0
        expected_total = base_total + picking.genci_amount_total
        self.assertAlmostEqual(
            total,
            expected_total,
            places=2,
        )

    def test_get_report_valued_total_amount_without_genci(self):
        ml = self._create_move_line(fiscal_position=None)
        picking = ml.picking_id
        picking.sale_id.is_genci = False
        ml._compute_genci_amount()
        picking._compute_genci_amounts()
        total = picking._get_report_valued_total_amount()
        base_total = picking.amount_total or 0.0
        self.assertAlmostEqual(
            total,
            base_total,
            places=2,
        )
