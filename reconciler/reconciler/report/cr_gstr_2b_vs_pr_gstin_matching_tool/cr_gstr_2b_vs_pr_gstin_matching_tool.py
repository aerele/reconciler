# Copyright (c) 2013, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json
from frappe import _
from frappe.utils import comma_and, add_months
from six import string_types
from reconciler.reconciler.doctype.cd_gstr_2b_data_upload_tool.cd_gstr_2b_data_upload_tool import *

def execute(filters=None):
	return MatchingTool(filters).run()

class MatchingTool(object):
	def __init__(self, filters=None):
		self.filters = frappe._dict(filters or {})

	def run(self):
		self.get_columns()
		self.get_data()
		return self.columns, self.data

	def get_columns(self):
		if self.filters['view_type'] == 'Supplier View':
			self.columns = [{
					"label": "GSTIN",
					"fieldname": "gstin",
					"fieldtype": "Data",
					"width": 200
				},
				{
					"label": "Supplier",
					"fieldname": "supplier",
					"fieldtype": "Link",
					"options": "Supplier",
					"width": 200
				},
				{
					"label": "Tax Difference",
					"fieldname": "tax_difference",
					"fieldtype": "Float",
					"width": 200
				},
				{
					"label": "Total 2B",
					"fieldname": "total_2b",
					"fieldtype": "Int",
					"width": 200
				},
				{
					"label": "Total PR",
					"fieldname": "total_pr",
					"fieldtype": "Int",
					"width": 200
				},
				{
					"label": "Total Pending Documents",
					"fieldname": "total_pending_documents",
					"fieldtype": "Int",
					"width": 200
				}
				]
		else:
			self.columns = [{
					"label": "2B Invoice No",
					"fieldname": "2b_invoice_no",
					"fieldtype": "Data",
					"width": 200
				},
				{
					"label": "2B Invoice Date",
					"fieldname": "2b_invoice_date",
					"fieldtype": "Data",
					"width": 200
				},
				{
					"label": "PR Invoice No",
					"fieldname": "pr_invoice_no",
					"fieldtype": "Data",
					"width": 200
				},
				{
					"label": "PR Invoice Date",
					"fieldname": "pr_invoice_date",
					"fieldtype": "Data",
					"width": 200
				},
				{
					"label": "2B Total Value",
					"fieldname": "2b_total_value",
					"fieldtype": "Float",
					"width": 200
				},
				{
					"label": "PR Total Value",
					"fieldname": "pr_total_value",
					"fieldtype": "Float",
					"width": 200
				},
				{
					"label": "Tax Difference",
					"fieldname": "tax_difference",
					"fieldtype": "Float",
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
					"label": "Status",
					"fieldname": "status",
					"fieldtype": "Data",
					"width": 200
				},
				{
					"label": "View",
					"fieldname": "view",
					"fieldtype": "Button",
					"width": 200
				},
				{
					"label": "Link/Unlink",
					"fieldname": "link_or_unlink",
					"fieldtype": "Button",
					"width": 200
				}]

	def get_data(self):
		data = []
		if self.filters['based_on'] == 'Return Period':
			if 'return_period' in self.filters and self.filters['return_period']:
				gstr2b_conditions = [['cf_return_period','=',self.filters['return_period']]]
				month_threshold = -(frappe.db.get_single_value('CD GSTR 2B Settings', 'month_threshold'))
				return_period_year = int(self.filters['return_period'][-4::])
				return_period_month = int(self.filters['return_period'][:2])
				to_date = last_day_of_month(return_period_year, return_period_month)
				if not to_date:
					frappe.throw(_(f'To date not found for the PR filters'))

				from_date = add_months(to_date, month_threshold)

			else:
				frappe.throw(_("Please select return period"))
		else:
			if not self.filters['from_date']:
				frappe.throw(_("Please select from date"))
			if not self.filters['to_date']:
				frappe.throw(_("Please select to date"))
 			
			from_date = self.filters['from_date']
			to_date = self.filters['to_date']
			gstr2b_conditions = [['cf_document_date' ,'>=',self.filters['from_date']],
			['cf_document_date' ,'<=',self.filters['to_date']]]

			pr_conditions = [['bill_date' ,'>=',self.filters['from_date']],
			['bill_date' ,'<=',self.filters['to_date']]]
 
		if self.filters['view_type'] == 'Supplier View':
			gstr2b_conditions.extend([
			['cf_company_gstin', '=', self.filters['company_gstin']]])

			if 'transaction_type' in self.filters:
				gstr2b_conditions.append(['cf_transaction_type' ,'=', self.filters['transaction_type']])

			gstr2b_entries = frappe.db.get_all('CD GSTR 2B Entry', filters= gstr2b_conditions, fields =['cf_party_gstin','cf_party', 'cf_tax_amount', 'cf_purchase_invoice', 'cf_status'])
			
			if not self.filters['based_on'] == 'Return Period':
				pr_conditions.extend([
				['docstatus' ,'=', 1],
				['company_gstin', '=', self.filters['company_gstin']]])
				pr_entries = frappe.db.get_all('Purchase Invoice', filters=pr_conditions, fields =['supplier_gstin', 'supplier', 'name'])
			else:
				pr_entries = []
				for entry in gstr2b_entries:
					if entry['cf_purchase_invoice']:
						doc = frappe.get_doc('Purchase Invoice', entry['cf_purchase_invoice'])
						pr_entries.append({'supplier_gstin':doc.supplier_gstin,
						'supplier':doc.supplier,
						'name':doc.name})

			gstin_wise_data = {}
			
			for entry in gstr2b_entries:
				if not entry['cf_party_gstin'] in gstin_wise_data:
					gstin_wise_data[entry['cf_party_gstin']] = [entry['cf_party'], entry['cf_tax_amount'], 0]
				else:
					gstin_wise_data[entry['cf_party_gstin']][1] += entry['cf_tax_amount']
			
			if not 'transaction_type' in self.filters or \
				self.filters['transaction_type'] == 'Invoice':
				for entry in pr_entries:
					if not entry['supplier_gstin'] in gstin_wise_data:
						gstin_wise_data[entry['supplier_gstin']] = [entry['supplier'], 0, get_tax_details(entry['name'])['total_tax_amount']]
					else:
						gstin_wise_data[entry['supplier_gstin']][2] += get_tax_details(entry['name'])['total_tax_amount']

			for key in gstin_wise_data.keys():
				row = {	'supplier': gstin_wise_data[key][0],
						'gstin': key, 
						'tax_difference': round(abs(gstin_wise_data[key][1]- gstin_wise_data[key][2]), 2),
						'total_2b': len([entry for entry in gstr2b_entries if entry['cf_party_gstin'] == key]),
						'total_pr': len([entry for entry in pr_entries if entry['supplier_gstin'] == key]),
						'total_pending_documents': len([entry for entry in gstr2b_entries if entry['cf_party_gstin'] == key and entry['cf_status'] == 'Pending'])}
				data.append(row)

		else:
			suppliers = [row['name'] for row in frappe.db.get_all('Supplier') if row]
			match_status = ["Exact Match", "Partial Match", "Probable Match", "Mismatch", "Missing in PR", "Missing in 2B"]
			document_status = ['Pending', 'Accepted']
			
			if 'match_status' in self.filters:
				match_status = [self.filters['match_status']]
			
			if 'document_status' in self.filters:
				document_status = [self.filters['document_status']]

			if 'supplier' in self.filters:
				suppliers = [self.filters['supplier']]

			gstr2b_conditions.extend([
			['cf_status', 'in', document_status],
			['cf_match_status','in', match_status],
			['cf_company_gstin', '=', self.filters['company_gstin']]])

			if 'transaction_type' in self.filters:
				gstr2b_conditions.append(['cf_transaction_type' ,'=', self.filters['transaction_type']])
			if suppliers and not 'supplier_gstin' in self.filters:
				gstr2b_conditions.append(['cf_party', 'in', suppliers])

			if 'supplier_gstin' in self.filters:
				gstr2b_conditions.append(['cf_party_gstin', '=', self.filters['supplier_gstin']])

			gstr2b_entries = frappe.db.get_all('CD GSTR 2B Entry', filters= gstr2b_conditions, fields =['cf_document_number','cf_document_date', 'cf_party_gstin',
				'cf_purchase_invoice', 'cf_match_status', 'cf_reason', 'cf_status', 'cf_tax_amount','cf_total_amount', 'name'])

			for entry in gstr2b_entries:
				bill_details = frappe.db.get_value("Purchase Invoice", {'name':entry['cf_purchase_invoice']}, ['bill_no', 'bill_date', 'rounded_total'])
				button = f"""<Button class="btn btn-primary btn-xs center"  gstr2b = {entry["name"]} purchase_inv ={entry["cf_purchase_invoice"]} onClick='update_status(this.getAttribute("gstr2b"), this.getAttribute("purchase_inv"))'>View</a>"""
				link_or_unlink = f"""<Button class="btn btn-primary btn-xs center"  gstr2b = {entry["name"]} status = {entry['cf_status']} onClick='unlink_pr(this.getAttribute("gstr2b"), this.getAttribute("status"))'>Unlink</a>"""
				if 'Missing in PR' == entry['cf_match_status']:
					button = f"""<Button class="btn btn-primary btn-xs center"  gstr2b = {entry["name"]} purchase_inv ={entry["cf_purchase_invoice"]} onClick='create_purchase_inv(this.getAttribute("gstr2b"), this.getAttribute("purchase_inv"))'>View</a>"""
					link_or_unlink = f"""<Button class="btn btn-primary btn-xs center"  gstr2b = {entry["name"]}  from_date = {from_date} to_date = {to_date} onClick='get_unlinked_pr_list(this.getAttribute("gstr2b"), this.getAttribute("from_date"), this.getAttribute("to_date"))'>Link</a>"""
				tax_diff = entry['cf_tax_amount']
				if entry['cf_purchase_invoice']:
					tax_diff = round(abs(entry['cf_tax_amount']- get_tax_details(entry['cf_purchase_invoice'])['total_tax_amount']), 2)
				data.append({
				'2b_invoice_no': entry['cf_document_number'],
				'2b_invoice_date': entry['cf_document_date'],  
				'pr_invoice_no': bill_details[0] if bill_details and bill_details[0] else None,
				'pr_invoice_date': bill_details[1] if bill_details and bill_details[1] else None,
				'tax_difference': tax_diff,
				'2b_total_value': entry['cf_total_amount'],
				'pr_total_value': bill_details[2] if bill_details and bill_details[2] else None,
				'match_status': entry['cf_match_status'], 
				'reason':entry['cf_reason'],
				'status': entry['cf_status'],
				'view': button,
				'gstr_2b': entry['name'],
				'link_or_unlink': link_or_unlink})

			if len(document_status) != 1 and 'Missing in 2B' in match_status and self.filters['based_on'] == 'Date':
				if not 'transaction_type' in self.filters or \
				self.filters['transaction_type'] == 'Invoice':
					pr_conditions.extend([
					['docstatus' ,'=', 1],
					['company_gstin', '=', self.filters['company_gstin']]])

					if suppliers and not 'supplier_gstin' in self.filters:
						pr_conditions.append(['supplier' ,'in', suppliers])
					
					if 'supplier_gstin' in self.filters:
						pr_conditions.append(['supplier_gstin' ,'=', self.filters['supplier_gstin']])

					pr_entries = frappe.db.get_all('Purchase Invoice', filters=pr_conditions, fields =['name', 'bill_no', 'bill_date', 'rounded_total', 'supplier_gstin'])

					for inv in pr_entries:
						is_linked = frappe.db.get_value('CD GSTR 2B Entry', {'cf_purchase_invoice': inv['name']}, 'name')
						if not is_linked:
							tax_diff = get_tax_details(inv['name'])['total_tax_amount']
							button = f"""<Button class="btn btn-primary btn-xs center"  gstr2b = '' purchase_inv ={inv["name"]} onClick='render_summary(this.getAttribute("gstr2b"), this.getAttribute("purchase_inv"))'>View</a>"""
							data.append({
								'2b_invoice_no': None,
								'2b_invoice_date': None,  
								'pr_invoice_no': inv['bill_no'],
								'pr_invoice_date': inv['bill_date'],
								'tax_difference': tax_diff,
								'2b_total_value': None,
								'pr_total_value': inv['rounded_total'],
								'match_status': 'Missing in 2B', 
								'reason':None,
								'status': None,
								'view': button})
		self.data = data

@frappe.whitelist()
def return_period_query():
	return_period_list = []
	rp_list = frappe.db.get_list('CD GSTR 2B Data Upload Tool',['cf_return_period'])
	for data in rp_list:
		return_period_list.append(data['cf_return_period'])
	return sorted(set(return_period_list))

@frappe.whitelist()
def get_selection_details(gstr2b, purchase_inv):
	tax_details = {}
	other_details = {}
	gstr2b_doc = None
	pi_doc = None
	if gstr2b:
		gstr2b_doc = frappe.get_doc('CD GSTR 2B Entry', gstr2b)
	if not purchase_inv == 'None':
		pi_doc = frappe.get_doc('Purchase Invoice', purchase_inv)
		tax_wise_details = get_tax_details(purchase_inv)
		is_linked = frappe.db.get_value('CD GSTR 2B Entry', {'cf_purchase_invoice': purchase_inv}, 'name')
	
	if gstr2b_doc:
		tax_details['GSTR-2B'] = [gstr2b_doc.cf_taxable_amount,
							gstr2b_doc.cf_tax_amount,
							gstr2b_doc.cf_igst_amount,
							gstr2b_doc.cf_cgst_amount,
							gstr2b_doc.cf_sgst_amount,
							gstr2b_doc.cf_cess_amount]
		
		other_details['GSTR-2B'] = [
							comma_and("""<a href="#Form/CD GSTR 2B Entry/{0}">{1}</a>""".format(gstr2b_doc.name, gstr2b_doc.name)),
							gstr2b_doc.cf_document_number,
							gstr2b_doc.cf_document_date,
							gstr2b_doc.cf_place_of_supply,
							gstr2b_doc.cf_reverse_charge,
							gstr2b_doc.cf_return_period,
							gstr2b_doc.cf_match_status,
							gstr2b_doc.cf_reason if gstr2b_doc.cf_reason else '-',
							gstr2b_doc.cf_status]

	if pi_doc:
		pi_details = [pi_doc.total,
						tax_wise_details['total_tax_amount']]
		for tax_amt_type in tax_wise_details:
			if not tax_amt_type == 'total_tax_amount':
				pi_details.append(tax_wise_details[tax_amt_type])

		tax_details['PR'] = pi_details

		other_details['PR'] = [
							comma_and("""<a href="#Form/Purchase Invoice/{0}">{1}</a>""".format(pi_doc.name, pi_doc.name)),
							pi_doc.bill_no,
							pi_doc.bill_date,
							pi_doc.place_of_supply,
							pi_doc.reverse_charge,
							f'{pi_doc.posting_date.month}/{pi_doc.posting_date.year}',
							'-',
							'-' if is_linked else 'Missing in 2B',
							'-'
							]
	return [tax_details, other_details]

@frappe.whitelist()
def update_status(data, status):
	if isinstance(data, string_types):
		data = json.loads(data)
	for row in data:
		if row and row['gstr_2b']:
			frappe.db.set_value('CD GSTR 2B Entry', row['gstr_2b'], 'cf_status', status)
	frappe.db.commit()

@frappe.whitelist()
def get_unlinked_pr_list(doctype, txt, searchfield, start, page_len, filters):
	doc = frappe.get_doc('CD GSTR 2B Entry', filters['gstr2b'])	
	pr_list = get_pr_list(doc.cf_company_gstin, filters['from_date'], filters['to_date'], supplier_gstin = doc.cf_party_gstin)
	pr_list = [[entry['name']] for entry in pr_list if entry]
	return pr_list

@frappe.whitelist()
def link_pr(gstr2b, pr):
	gstr2b_doc = frappe.get_doc('CD GSTR 2B Entry', gstr2b)
	pr_doc = frappe.get_doc('Purchase Invoice', pr)
	gstr2b_doc_params = {
		'name': gstr2b_doc.name,
		'gstin': gstr2b_doc.cf_party_gstin,
		'document_type': gstr2b_doc.cf_transaction_type,
		'document_date': gstr2b_doc.cf_document_date,
		'document_number': gstr2b_doc.cf_document_number,
		'total_taxable_amount': gstr2b_doc.cf_taxable_amount,
		'total_tax_amount': gstr2b_doc.cf_tax_amount,
		'igst_amount': gstr2b_doc.cf_igst_amount,
		'cgst_amount': gstr2b_doc.cf_cgst_amount,
		'sgst_amount': gstr2b_doc.cf_sgst_amount,
		'cess_amount': gstr2b_doc.cf_cess_amount
	}

	pr_doc_params = {'name': pr_doc.name,
					'gstin': pr_doc.supplier_gstin,
					'document_date': pr_doc.bill_date,
					'document_type': 'Invoice',
					'document_number': pr_doc.bill_no,
					'total_taxable_amount': pr_doc.total}
	
	pr_doc_params.update(get_tax_details(pr))
	res = get_match_status(gstr2b_doc_params, [pr_doc_params])
	if res:
		update_match_status(gstr2b_doc_params, res)
	else:
		frappe.throw(_("2B record data is not matched with the selected PR"))