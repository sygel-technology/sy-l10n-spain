# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo.addons.account_invoice_custom_rounding.tests.test_account_invoice_custom_rounding import (  # noqa: E501
    TestAccountInvoiceCustomRounding,
)


class TestFacturaeCustomRounding(TestAccountInvoiceCustomRounding):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write(
            {
                "vat": "ES73524583T",
                "city": "Valencia",
                "street": "street",
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_v").id,
                "zip": "46001",
            }
        )
        cls.partner.write(
            {
                "vat": "ESC2259530J",
                "street": "street",
                "city": "Valencia",
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_v").id,
                "zip": "46001",
            }
        )
        cls.fe = "http://www.facturae.es/Facturae/2009/v3.2/Facturae"

    def _create_facturae(self, move_id):
        wizard = (
            self.env["create.facturae"]
            .with_context(
                active_ids=move_id.ids,
                active_model="account.move",
            )
            .create({})
        )
        wizard.write({"firmar_facturae": False})
        wizard.create_facturae_file()
        return etree.fromstring(base64.b64decode(wizard.facturae))

    def test_facturae_custom_rounding_company_round_per_line(self):
        self.company.write({"tax_calculation_rounding_method": "round_per_line"})

        # Invoice has no custom rounding method
        invoice = self.create_invoice()
        invoice.action_post()
        facturae = self._create_facturae(invoice)
        taxes_outputs_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/TaxesOutputs/Tax/TaxAmount/TotalAmount",
            namespaces={"fe": self.fe},
        )[0].text
        invoice_totals_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/InvoiceTotals/TotalTaxOutputs",
            namespaces={"fe": self.fe},
        )[0].text
        self.assertFalse(invoice.tax_calculation_rounding_method)
        self.assertEqual(taxes_outputs_amount, invoice_totals_amount)

        # Invoice's custom rounding method is equal to company's rounding method
        invoice = self.create_invoice()
        invoice.write({"tax_calculation_rounding_method": "round_per_line"})
        invoice._check_balanced()
        invoice.action_post()
        facturae = self._create_facturae(invoice)
        taxes_outputs_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/TaxesOutputs/Tax/TaxAmount/TotalAmount",
            namespaces={"fe": self.fe},
        )[0].text
        invoice_totals_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/InvoiceTotals/TotalTaxOutputs",
            namespaces={"fe": self.fe},
        )[0].text
        self.assertEqual(
            invoice.tax_calculation_rounding_method,
            self.company.tax_calculation_rounding_method,
        )
        self.assertEqual(taxes_outputs_amount, invoice_totals_amount)

        # Invoice's custom rounding method is different to company's rounding method
        invoice = self.create_invoice()
        invoice.write({"tax_calculation_rounding_method": "round_globally"})
        invoice._check_balanced()
        invoice.action_post()
        facturae = self._create_facturae(invoice)
        taxes_outputs_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/TaxesOutputs/Tax/TaxAmount/TotalAmount",
            namespaces={"fe": self.fe},
        )[0].text
        invoice_totals_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/InvoiceTotals/TotalTaxOutputs",
            namespaces={"fe": self.fe},
        )[0].text
        self.assertTrue(invoice.tax_calculation_rounding_method)
        self.assertNotEqual(
            invoice.tax_calculation_rounding_method,
            self.company.tax_calculation_rounding_method,
        )
        self.assertEqual(taxes_outputs_amount, invoice_totals_amount)

    def test_facturae_custom_rounding_company_round_globally(self):
        self.company.write({"tax_calculation_rounding_method": "round_globally"})

        # Invoice has no custom rounding method
        invoice = self.create_invoice()
        invoice.action_post()
        facturae = self._create_facturae(invoice)
        taxes_outputs_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/TaxesOutputs/Tax/TaxAmount/TotalAmount",
            namespaces={"fe": self.fe},
        )[0].text
        invoice_totals_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/InvoiceTotals/TotalTaxOutputs",
            namespaces={"fe": self.fe},
        )[0].text
        self.assertFalse(invoice.tax_calculation_rounding_method)
        self.assertEqual(taxes_outputs_amount, invoice_totals_amount)

        # Invoice's custom rounding method is equal to company's rounding method
        invoice = self.create_invoice()
        invoice.write({"tax_calculation_rounding_method": "round_globally"})
        invoice._check_balanced()
        invoice.action_post()
        facturae = self._create_facturae(invoice)
        taxes_outputs_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/TaxesOutputs/Tax/TaxAmount/TotalAmount",
            namespaces={"fe": self.fe},
        )[0].text
        invoice_totals_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/InvoiceTotals/TotalTaxOutputs",
            namespaces={"fe": self.fe},
        )[0].text
        self.assertEqual(
            invoice.tax_calculation_rounding_method,
            self.company.tax_calculation_rounding_method,
        )
        self.assertEqual(taxes_outputs_amount, invoice_totals_amount)

        # Invoice's custom rounding method is different to company's rounding method
        invoice = self.create_invoice()
        invoice.write({"tax_calculation_rounding_method": "round_per_line"})
        invoice._check_balanced()
        invoice.action_post()
        facturae = self._create_facturae(invoice)
        taxes_outputs_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/TaxesOutputs/Tax/TaxAmount/TotalAmount",
            namespaces={"fe": self.fe},
        )[0].text
        invoice_totals_amount = facturae.xpath(
            "/fe:Facturae/Invoices/Invoice/InvoiceTotals/TotalTaxOutputs",
            namespaces={"fe": self.fe},
        )[0].text
        self.assertTrue(invoice.tax_calculation_rounding_method)
        self.assertNotEqual(
            invoice.tax_calculation_rounding_method,
            self.company.tax_calculation_rounding_method,
        )
        self.assertEqual(taxes_outputs_amount, invoice_totals_amount)
