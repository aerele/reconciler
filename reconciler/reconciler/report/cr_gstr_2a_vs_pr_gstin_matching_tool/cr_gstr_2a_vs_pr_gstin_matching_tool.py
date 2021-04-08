# Copyright (c) 2013, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from erpnext.regional.india.utils import get_gst_accounts
from six import string_types

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
					"label": "GSTR 2A - Invoice Number",
					"fieldname": "gstr_2a_inv",
					"fieldtype": "Data",
					"width": 200
				},
				{
					"label": "PR - Invoice Number",
					"fieldname": "pr_inv",
					"fieldtype": "Data",
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
		status = [None, 'Pending']
		if self.filters['cf_view_type'] == 'Supplier View':
			gstr2a_conditions = [
			['cf_status' ,'in', status],
			['cf_document_date' ,'>=',self.filters['cf_from_date']],
			['cf_document_date' ,'<=',self.filters['cf_to_date']],
			['cf_company_gstin', '=', self.filters['cf_company_gstin']]]
			if 'cf_transaction_type' in self.filters:
				gstr2a_conditions.append(['cf_transaction_type' ,'=', self.filters['cf_transaction_type']])

			gstr2a_entries = frappe.db.get_all('CD GSTR 2A Entry', filters= gstr2a_conditions, fields =['cf_party_gstin','cf_tax_amount', 'cf_party'])
			pi_entries = frappe.db.get_all('Purchase Invoice', filters=[['bill_date' ,'>=',self.filters['cf_from_date']],
			['bill_date' ,'<=',self.filters['cf_to_date']],
			['docstatus' ,'=', 1],
			['company_gstin', '=', self.filters['cf_company_gstin']]], fields =['supplier_gstin','taxes_and_charges_added', 'supplier'])
			supplier_data_by_2a = {}
			for entry in gstr2a_entries:
				if not entry['cf_party_gstin'] in supplier_data_by_2a:
					supplier_data_by_2a[entry['cf_party_gstin']] = [entry['cf_party'], entry['cf_tax_amount'], 0]
				else:
					supplier_data_by_2a[entry['cf_party_gstin']][1] += entry['cf_tax_amount']
			
			if not 'cf_transaction_type' in self.filters or \
				self.filters['cf_transaction_type'] == 'Invoice':
				for entry in pi_entries:
					if not entry['supplier_gstin'] in supplier_data_by_2a:
						supplier_data_by_2a[entry['supplier_gstin']] = [entry['supplier'], 0, entry['taxes_and_charges_added']]
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

			gstr2a_conditions = [['cf_document_date' ,'>=',self.filters['cf_from_date']],
			['cf_status' ,'in', status],
			['cf_party', '=', self.filters['cf_supplier']],
			['cf_document_date' ,'<=',self.filters['cf_to_date']],
			['cf_match_status','in', match_status],
			['cf_company_gstin', '=', self.filters['cf_company_gstin']]]

			if 'cf_transaction_type' in self.filters:
				gstr2a_conditions.append(['cf_transaction_type' ,'=', self.filters['cf_transaction_type']])
			
			gstr2a_entries = frappe.db.get_all('CD GSTR 2A Entry', filters= gstr2a_conditions, fields =['cf_document_number','cf_party_gstin', 'cf_purchase_invoice', 'cf_match_status', 'cf_reason', 'name'])

			for entry in gstr2a_entries:
				linked_inv.add(entry['cf_purchase_invoice'])
				button = f"""<Button class="btn btn-primary btn-xs center"  gstr2a = {entry["name"]} purchase_inv ={entry["cf_purchase_invoice"]} onClick='update_status(this.getAttribute("gstr2a"), this.getAttribute("purchase_inv"))'>View</a>"""
				if 'Missing in PR' == entry['cf_match_status']:
					button = f"""<Button class="btn btn-primary btn-xs center"  gstr2a = {entry["name"]} purchase_inv ={entry["cf_purchase_invoice"]} onClick='create_purchase_inv(this.getAttribute("gstr2a"), this.getAttribute("purchase_inv"))'>View</a>"""
				bill_no = frappe.db.get_value("Purchase Invoice", entry['cf_purchase_invoice'], 'bill_no')
				data.append({
				'gstr_2a': entry['name'],
				'pr': entry['cf_purchase_invoice'],
				'gstr_2a_inv': entry['cf_document_number'], 
				'pr_inv': bill_no, 
				'match_status': entry['cf_match_status'], 
				'reason':entry['cf_reason'],
				'view': button})

			if 'Missing in 2A' in match_status:
				if not 'cf_transaction_type' in self.filters or \
				self.filters['cf_transaction_type'] == 'Invoice':
					pi_entries = frappe.db.get_all('Purchase Invoice', filters=[['bill_date' ,'>=',self.filters['cf_from_date']],
					['bill_date' ,'<=',self.filters['cf_to_date']],
					['docstatus' ,'=', 1],
					['supplier' ,'=',self.filters['cf_supplier']],
					['company_gstin', '=', self.filters['cf_company_gstin']]], fields =['name', 'supplier_gstin', 'bill_no'])

					for inv in pi_entries:
						if not inv['name'] in linked_inv:
							button = f"""<Button class="btn btn-primary btn-xs center"  gstr2a = '' purchase_inv ={inv["name"]} onClick='update_status(this.getAttribute("gstr2a"), this.getAttribute("purchase_inv"))'>View</a>"""
							data.append({
							'gstra_2a': None,
							'pr': inv['name'],
							'gstr_2a_inv': None, 
							'pr_inv': inv['bill_no'], 
							'match_status': 'Missing in 2A', 
							'reason': None,
							'view': button})
		self.data = data
	
	def get_report_summary(self):
		summary = []
		pr_entries = []
		pr_tax_amt = 0
		gstr2a_conditions = [['cf_document_date' ,'>=',self.filters['cf_from_date']],
			['cf_document_date' ,'<=',self.filters['cf_to_date']],
			['cf_company_gstin', '=', self.filters['cf_company_gstin']]]
		pr_conditions = [['bill_date' ,'>=',self.filters['cf_from_date']],
			['bill_date' ,'<=',self.filters['cf_to_date']],
			['docstatus' ,'=', 1],
			['company_gstin', '=', self.filters['cf_company_gstin']]]
		if 'cf_supplier' in self.filters:
			pr_conditions.append(['supplier' ,'=',self.filters['cf_supplier']])
			gstr2a_conditions.append(['cf_party' ,'=',self.filters['cf_supplier']])
		if 'cf_transaction_type' in self.filters:
				gstr2a_conditions.append(['cf_transaction_type' ,'=', self.filters['cf_transaction_type']])

		match_status = {'Mismatch':'Red', 'Exact Match':'Green', 'Suggested':'Blue', 'Missing in 2A':'Red', 'Missing in PR':'Red'}
		entries = frappe.db.get_all('CD GSTR 2A Entry', filters= gstr2a_conditions, fields =['cf_match_status', 'cf_tax_amount', 'cf_purchase_invoice'])
		gstr2a_tax_amt = sum([entry['cf_tax_amount'] for entry in entries if entry['cf_tax_amount']])
		if not 'cf_transaction_type' in self.filters or \
				self.filters['cf_transaction_type'] == 'Invoice':
			pr_entries = frappe.db.get_all('Purchase Invoice', filters= pr_conditions , fields =['taxes_and_charges_added', 'name'])
			pr_tax_amt = sum([entry['taxes_and_charges_added'] for entry in pr_entries if entry['taxes_and_charges_added']])
		pr_by_2a = [entry['cf_purchase_invoice'] for entry in entries]
		pr = [entry['name'] for entry in pr_entries]
		for status in match_status:
			if status == 'Missing in 2A':
				diff = len(set(pr)-set(pr_by_2a))
				summary.append(
				{
				"value": diff,
				"indicator": match_status[status],
				"label": status,
				"datatype": "Float",
				},
				)

			else:
				summary.append(
					{
					"value": len([entry for entry in entries if entry['cf_match_status'] == status]),
					"indicator": match_status[status],
					"label": status,
					"datatype": "Float",
				},
				)
		summary.append(
				{
				"value": f'{len(entries)}(2A) & {len(pr_entries)}(PR)',
				"indicator": 'Green',
				"label": 'Total Docs',
				"datatype": "Data",
			},
			)
		summary.append(
				{
				"value": gstr2a_tax_amt,
				"indicator": 'Blue',
				"label": 'GSTR 2A Tax Amount',
				"datatype": "Float",
			},
			)
		summary.append(
				{
				"value": pr_tax_amt,
				"indicator": 'Blue',
				"label": 'PR Tax Amount',
				"datatype": "Float",
			},
			)
		summary.append(
				{
				"value": abs(gstr2a_tax_amt - pr_tax_amt),
				"indicator": 'Red',
				"label": 'Tax Difference',
				"datatype": "Float",
			},
			)
		return summary

@frappe.whitelist()
def get_selection_details(gstr2a, purchase_inv):
	tax_details = {}
	other_details = {}
	gstr2a_doc = None
	pi_doc = None
	account_head_fields = {
			'igst_account',
			'cgst_account',
			'sgst_account',
			'cess_account'
		}
	if gstr2a:
		gstr2a_doc = frappe.get_doc('CD GSTR 2A Entry', gstr2a)
	if not purchase_inv == 'None':
		pi_doc = frappe.get_doc('Purchase Invoice', purchase_inv)
		gst_accounts = get_gst_accounts(pi_doc.company)
		for row in pi_doc.taxes:
			for accounts in gst_accounts.values():
				if row.account_head in accounts:
					if not type(accounts[-1]) == int:
						accounts.append(0)
					accounts[-1]+=row.tax_amount
	
	if gstr2a_doc:
		tax_details['GSTR-2A'] = [gstr2a_doc.cf_taxable_amount,
							gstr2a_doc.cf_tax_amount,
							gstr2a_doc.cf_igst_amount,
							gstr2a_doc.cf_cgst_amount,
							gstr2a_doc.cf_sgst_amount,
							gstr2a_doc.cf_cess_amount]
		
		other_details['GSTR-2A'] = [gstr2a_doc.cf_document_number,
							gstr2a_doc.cf_document_date,
							gstr2a_doc.cf_place_of_supply,
							gstr2a_doc.cf_reverse_charge]

	if pi_doc:
		pi_details = [pi_doc.total,
						pi_doc.taxes_and_charges_added]
		for acc in account_head_fields:
			tax_amt = 0
			if len(gst_accounts[acc])==3:
				tax_amt = gst_accounts[acc][-1]
			pi_details.append(tax_amt)
		tax_details['PR'] = pi_details

		other_details['PR'] = [pi_doc.bill_no,
							pi_doc.bill_date,
							pi_doc.place_of_supply,
							pi_doc.reverse_charge]
	return [tax_details, other_details]

@frappe.whitelist()
def update_status(data, status):
	if isinstance(data, string_types):
		data = json.loads(data)
	for row in data:
		if row:
			frappe.db.set_value('CD GSTR 2A Entry', row['gstr_2a'], 'cf_status', status)
	frappe.db.commit()
