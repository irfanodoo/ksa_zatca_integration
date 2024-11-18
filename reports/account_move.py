from odoo import api, fields, models
from datetime import timedelta
import lxml.etree as ET
import base64

class AccountMoveReport(models.Model):
    _inherit = 'account.move'

    def _default_currency_id(self):
        currency = self.env['res.currency'].sudo().search([('name', '=', 'SAR')], limit=1)
        return currency or None

    invoice_multi_currency_id = fields.Many2one(
        'res.currency', string='Invoice Report Currency', default=_default_currency_id
    )

    def _get_zatca_report_base_filename(self):
        self.ensure_one()
        return "%s - %s - %s" % (
            self.company_id.vat,
            "{:%Y-%m-%d %H_%M_%S}".format(self.invoice_datetime + timedelta(hours=3)),
            self.id,
        )

    def get_tax_amount(self):
        data = 0.0
        for rec in self.invoice_line_ids:
            taxable_amount = rec.price_unit * rec.quantity
            tax_amount = (rec.tax_ids[0].amount if rec.tax_ids else 0.0)
            data += (tax_amount * taxable_amount) / 100
        return data

    def print_einv_standard(self):
        return self.env.ref('ksa_zatca_integration.report_sales_order').report_action(self)

    def print_einv_b2c(self):
        return self.env.ref('ksa_zatca_integration.report_e_invoicing_b2c').report_action(self)

    def get_invoice_type_code(self):
        if not self.zatca_invoice:
            return "Invoice data not available"
        try:
            invoice = base64.b64decode(self.zatca_invoice).decode()
            xml_file = ET.fromstring(invoice).getroottree()
            ksa_2 = xml_file.find("//{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode")
            return ksa_2.attrib.get('name', '') if ksa_2 is not None else "Code not found"
        except (TypeError, ValueError, ET.ParseError) as e:
            return f"Error processing invoice: {e}"

    def get_bt_131(self, id):
        if not self.zatca_invoice:
            return "Invoice data not available"
        try:
            invoice = base64.b64decode(self.zatca_invoice).decode()
            xml_file = ET.fromstring(invoice).getroottree()
            bt_131_find = f"//{{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}}ID[.='{id}']"
            bt_126 = xml_file.find(bt_131_find).getparent()
            bt_131 = bt_126.find('{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}LineExtensionAmount')
            return bt_131.text if bt_131 is not None else "0.0"
        except Exception as e:
            return f"Error: {e}"

    def get_bt_136(self, id):
        if not self.zatca_invoice:
            return "Invoice data not available"
        try:
            invoice = base64.b64decode(self.zatca_invoice).decode()
            xml_file = ET.fromstring(invoice).getroottree()
            bt_136_find = f"//{{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}}ID[.='{id}']"
            bt_126 = xml_file.find(bt_136_find).getparent()
            bg_27 = bt_126.find('{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AllowanceCharge')
            bt_136 = bg_27.find('{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Amount') if bg_27 is not None else None
            return bt_136.text if bt_136 is not None else "0.0"
        except Exception as e:
            return f"Error: {e}"

    def get_ksa_11(self, id):
        if not self.zatca_invoice:
            return "Invoice data not available"
        try:
            invoice = base64.b64decode(self.zatca_invoice).decode()
            xml_file = ET.fromstring(invoice).getroottree()
            ksa_11_find = f"//{{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}}ID[.='{id}']"
            bt_126 = xml_file.find(ksa_11_find).getparent()
            tax_total = bt_126.find('{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal')
            ksa_11 = tax_total.find('{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}TaxAmount') if tax_total is not None else None
            return ksa_11.text if ksa_11 is not None else "0.0"
        except Exception as e:
            return f"Error: {e}"

    def get_ksa_12(self, id):
        if not self.zatca_invoice:
            return "Invoice data not available"
        try:
            invoice = base64.b64decode(self.zatca_invoice).decode()
            xml_file = ET.fromstring(invoice).getroottree()
            ksa_12_find = f"//{{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}}ID[.='{id}']"
            bt_126 = xml_file.find(ksa_12_find).getparent()
            tax_total = bt_126.find('{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}TaxTotal')
            ksa_12 = tax_total.find('{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}RoundingAmount') if tax_total is not None else None
            return ksa_12.text if ksa_12 is not None else "0.0"
        except Exception as e:
            return f"Error: {e}"

    def get_bt_120(self):
        return ''  # Functionality needs to be implemented if required
