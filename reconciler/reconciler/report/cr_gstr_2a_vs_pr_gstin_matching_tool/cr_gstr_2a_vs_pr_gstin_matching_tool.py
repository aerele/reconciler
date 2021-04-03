# Copyright (c) 2013, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from erpnext.regional.india.utils import get_gst_accounts

def execute(filters=None):
	return MatchingTool(filters).run()

class MatchingTool(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})

	def run(self):
		self.get_columns()
		self.get_data()
		skip_total_row = 0
		self.report_summary = self.get_report_summary()

		return self.columns, self.data, None, None, self.report_summary, skip_total_row

	def get_columns(self):
		if self.filters and self.filters['cf_document_type'] == 'Invoices':
			if self.filters['cf_view_type'] == 'Supplier View':
				self.columns = [{
						"label": "GSTIN",
						"fieldname": "gstin",
						"fieldtype": "Data",
						"width": 200
					},
					{
						"label": "Supplier Name",
						"fieldname": "supplier_name",
						"fieldtype": "Data",
						"width": 200
					},
					{
						"label": "Tax Difference",
						"fieldname": "tax_difference",
						"fieldtype": "Float",
						"width": 200
					}]
			else:
				self.columns = [{
						"label": "GSTR 2A",
						"fieldname": "gstr_2a",
						"fieldtype": "Link",
						"options": "CD GSTR 2A Entry",
						"width": 200
					},
					{
						"label": "PR",
						"fieldname": "pr",
						"fieldtype": "Link",
						"options": "Purchase Invoice",
						"width": 200
					},
					{
						"label": "Match Status",
						"fieldname": "match_status",
						"fieldtype": "Data",
						"width": 200
					},
					{
						"label": "Reason",
						"fieldname": "reason",
						"fieldtype": "Data",
						"width": 200
					},
					{
						"label": "View",
						"fieldname": "view",
						"fieldtype": "Button",
						"width": 200
					}]

	def get_data(self):
		data = []
		if self.filters and self.filters['cf_document_type'] == 'Invoices':
			if self.filters['cf_view_type'] == 'Supplier View':
				gstr2a_entries = frappe.db.get_all('CD GSTR 2A Entry', filters=[['cf_invoice_date' ,'>=',self.filters['cf_from_date']],
				['cf_invoice_date' ,'<=',self.filters['cf_to_date']],
				['cf_company_gstin', '=', self.filters['cf_company_gstin']]], fields =['cf_party_gstin','cf_tax_amount'])
				
				pi_entries = frappe.db.get_all('Purchase Invoice', filters=[['bill_date' ,'>=',self.filters['cf_from_date']],
				['bill_date' ,'<=',self.filters['cf_to_date']],
				['company_gstin', '=', self.filters['cf_company_gstin']]], fields =['supplier_gstin','taxes_and_charges_added'])

				supplier_data_by_2a = {}
				for entry in gstr2a_entries:
					if not entry['cf_party_gstin'] in supplier_data_by_2a:
						supplier_data_by_2a[entry['cf_party_gstin']] = [get_supplier_by_gstin(entry['cf_party_gstin']), entry['cf_tax_amount'], 0]
					else:
						supplier_data_by_2a[entry['cf_party_gstin']][1] += entry['cf_tax_amount']
				
				for entry in pi_entries:
					if not entry['supplier_gstin'] in supplier_data_by_2a:
						supplier_data_by_2a[entry['supplier_gstin']] = [get_supplier_by_gstin(entry['supplier_gstin']), 0, entry['taxes_and_charges_added']]
					else:
						supplier_data_by_2a[entry['supplier_gstin']][2] += entry['taxes_and_charges_added']

				for key in supplier_data_by_2a.keys():
					data.append({'supplier_name': supplier_data_by_2a[key][0], 'gstin': key, 'tax_difference': abs(supplier_data_by_2a[key][1]- supplier_data_by_2a[key][2])})

			else:
				if not 'cf_supplier' in self.filters:
					frappe.throw('Please select supplier')

				linked_inv = set()
				match_status = ["Exact Match", "Suggested", "Mismatch", "Missing in PR", "Missing in 2A"]
				if 'cf_match_status' in self.filters:
					match_status = [self.filters['cf_match_status']]
				
				gstr2a_entries = frappe.db.get_all('CD GSTR 2A Entry', filters=[['cf_invoice_date' ,'>=',self.filters['cf_from_date']],
				['cf_invoice_date' ,'<=',self.filters['cf_to_date']],
				['cf_match_status','in', match_status],
				['cf_company_gstin', '=', self.filters['cf_company_gstin']]], fields =['cf_invoice_number','cf_party_gstin', 'cf_purchase_invoice', 'cf_match_status', 'cf_reason', 'name'])

				for entry in gstr2a_entries:
					linked_inv.add(entry['cf_purchase_invoice'])
					if get_supplier_by_gstin(entry['cf_party_gstin']) == self.filters['cf_supplier']:
						button = f"""<Button class="btn btn-primary btn-xs center"  gstr2a = {entry["name"]} pi ={entry["cf_purchase_invoice"]} onClick='set_listeners(this.getAttribute("gstr2a"), this.getAttribute("pi"))'>View</a>"""
						bill_no = frappe.db.get_value("Purchase Invoice", entry['cf_purchase_invoice'], 'bill_no')
						data.append({'gstr_2a': entry['cf_invoice_number'], 
						'pr': bill_no, 
						'match_status': entry['cf_match_status'], 
						'reason':entry['cf_reason'],
						'view': button})

				if 'Missing in 2A' in match_status:
					pi_entries = frappe.db.get_all('Purchase Invoice', filters=[['bill_date' ,'>=',self.filters['cf_from_date']],
					['bill_date' ,'<=',self.filters['cf_to_date']],
					['company_gstin', '=', self.filters['cf_company_gstin']]], fields =['name', 'supplier_gstin', 'bill_no'])

					for inv in pi_entries:
						if not inv['name'] in linked_inv and \
							get_supplier_by_gstin(inv['supplier_gstin']) == self.filters['cf_supplier']:
								button = f"""<Button class="btn btn-primary btn-xs center"  gstr2a = '' pi ={inv["name"]} onClick='set_listeners(this.getAttribute("gstr2a"), this.getAttribute("pi"))'>View</a>"""
								data.append({'gstr_2a': None, 
								'pr': inv['bill_no'], 
								'match_status': 'Missing in 2A', 
								'reason': None,
								'view': button})
		self.data = data
	
	def get_report_summary(self):
		summary = []
		match_status = {'Mismatch':'Red', 'Exact Match':'Green', 'Suggested':'Blue', 'Missing in 2A':'Red', 'Missing in PR':'Red'}
		entries = frappe.db.get_all('CD GSTR 2A Entry', filters=[['cf_invoice_date' ,'>=',self.filters['cf_from_date']],
			['cf_invoice_date' ,'<=',self.filters['cf_to_date']],
			['cf_company_gstin', '=', self.filters['cf_company_gstin']]], fields =['cf_match_status'])
		for status in match_status:
			summary.append(
				{
				"value": len([entry for entry in entries if entry['cf_match_status'] == status]),
				"indicator": match_status[status],
				"label": status,
				"datatype": "Float",
			},
			)
		return summary

def get_supplier_by_gstin(gstin):
	supplier = None
	link_name = frappe.db.sql("""select
		`tabDynamic Link`.link_name
	from
		`tabAddress`, `tabDynamic Link`
	where 
		`tabAddress`.gstin = %(gstin)s and 
		`tabDynamic Link`.parent = `tabAddress`.name and
		`tabDynamic Link`.parenttype = 'Address' and
		`tabDynamic Link`.link_doctype = 'Supplier'""", {"gstin": gstin})
	
	if link_name and link_name[0][0]:
		supplier = link_name[0][0]
	return supplier

@frappe.whitelist()
def get_selection_details(gstr2a, pi, show_tax):
	show_tax = int(show_tax)
	details = {}
	gstr2a_doc = None
	account_head_fields = {
			'igst_account',
			'cgst_account',
			'sgst_account',
			'cess_account'
		}
	if gstr2a:
		gstr2a_doc = frappe.get_doc('CD GSTR 2A Entry', gstr2a)
	pi_doc = frappe.get_doc('Purchase Invoice', pi)
	gst_accounts = get_gst_accounts(pi_doc.company)
	for row in pi_doc.taxes:
		for accounts in gst_accounts.values():
			if row.account_head in accounts:
				if not type(accounts[-1]) == int:
					accounts.append(0)
				accounts[-1]+=row.tax_amount
	
	if show_tax:
		if gstr2a_doc:
			details['GSTR-2A'] = [gstr2a_doc.cf_taxable_amount,
								gstr2a_doc.cf_tax_amount,
								gstr2a_doc.cf_igst_amount,
								gstr2a_doc.cf_cgst_amount,
								gstr2a_doc.cf_sgst_amount,
								gstr2a_doc.cf_cess_amount]

		pi_details = [pi_doc.total,
						pi_doc.taxes_and_charges_added]
		for acc in account_head_fields:
			tax_amt = 0
			if len(gst_accounts[acc])==3:
				tax_amt = gst_accounts[acc][-1]
			pi_details.append(tax_amt)
		details['PR'] = pi_details

	else:
		if gstr2a_doc:
			details['GSTR-2A'] = [gstr2a_doc.cf_invoice_number,
								gstr2a_doc.cf_invoice_date,
								gstr2a_doc.cf_place_of_supply,
								gstr2a_doc.cf_reverse_charge]

		details['PR'] = [pi_doc.bill_no,
							pi_doc.bill_date,
							pi_doc.place_of_supply,
							pi_doc.reverse_charge]
	return details

@frappe.whitelist()
def update_status(gstr2a, status):
	frappe.db.set_value('CD GSTR 2A Entry', gstr2a, 'status', status)
	frappe.db.commit()
