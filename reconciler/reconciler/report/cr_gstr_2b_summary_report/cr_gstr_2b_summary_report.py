# Copyright (c) 2013, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns += [
	{'label': 'Based on', 'fieldname': 'based_on', 'fieldtype': 'Data', 'width': 120},
	{'label': 'No. of Entries', 'fieldname': 'no_of_entries', 'fieldtype': 'Int', 'width': 30},
	{'label': 'Taxable Amount', 'fieldname': 'taxable_amount', 'fieldtype': 'Currency', 'options': 'currency', 'width': 120},
	{'label': 'IGST Amount', 'fieldname': 'igst_amount', 'fieldtype': 'Currency', 'options': 'currency', 'width': 120},
	{'label': 'CGST Amount', 'fieldname': 'cgst_amount', 'fieldtype': 'Currency', 'options': 'currency', 'width': 120},
	{'label': 'SGST Amount', 'fieldname': 'sgst_amount', 'fieldtype': 'Currency', 'options': 'currency', 'width': 120},
	{'label': 'CESS Amount', 'fieldname': 'cess_amount', 'fieldtype': 'Currency', 'options': 'currency', 'width': 120}]
	data = get_data(data, filters)
	return columns, data

def get_data(data, filters):
	based_on_details = [
		'Accepted 2B Entries',
		'Pending 2B Entries',
		'Eligible Tax',
		'Ineligible Tax',
		'Import Of Capital Goods Tax',
		'Import Of Service Tax',
		'Input Service Distributor Tax',
		'Reverse Charge']
	for row in based_on_details:
		conditions = {'cf_return_period': filters['return_period'],
				'cf_company': filters['company'],
				'cf_company_gstin': filters['company_gstin'],
				'cf_transaction_type': 'Invoice'}

		if row in ['Accepted 2B Entries', 'Eligible Tax', 'Ineligible Tax', 'Import Of Capital Goods Tax', 'Import Of Service Tax', 'Input Service Distributor Tax', 'Reverse Charge']:
			conditions['cf_status'] = 'Accepted'

		if row == 'Pending 2B Entries':
			conditions['cf_status'] = 'Pending'

		if row == 'Reverse Charge':
			conditions['cf_reverse_charge'] = 'Y'

		entries = frappe.db.get_list('CD GSTR 2B Entry', conditions, 
			['cf_igst_amount','cf_cgst_amount', 'cf_sgst_amount','cf_cess_amount', 'cf_taxable_amount', 'cf_purchase_invoice'])

		if row in ['Eligible Tax', 'Ineligible Tax', 'Import Of Capital Goods Tax', 'Import Of Service Tax', 'Input Service Distributor Tax']:
			for entry in entries[:]:
				if entry['cf_purchase_invoice']:
					itc_eligibility = frappe.db.get_value('Purchase Invoice', entry['cf_purchase_invoice'],'eligibility_for_itc')
					if row == 'Eligible Tax' and itc_eligibility != 'All Other ITC':
						entries.remove(entry)
					if row == 'Ineligible Tax' and itc_eligibility != 'Ineligible':
						entries.remove(entry)
					if row == 'Import Of Capital Goods Tax' and itc_eligibility != 'Import Of Capital Goods':
						entries.remove(entry)
					if row == 'Import Of Service Tax' and itc_eligibility != 'Import Of Service':
						entries.remove(entry)
					if row == 'Input Service Distributor Tax' and itc_eligibility != 'Input Service Distributor':
						entries.remove(entry)

		data.append({
			'based_on': row,
			'no_of_entries': len(entries),
			'taxable_amount': sum([entry['cf_taxable_amount'] for entry in entries]) if entries else 0,
			'igst_amount': sum([entry['cf_igst_amount'] for entry in entries]) if entries else 0,
			'cgst_amount': sum([entry['cf_cgst_amount'] for entry in entries])if entries else 0,
			'sgst_amount': sum([entry['cf_sgst_amount'] for entry in entries])if entries else 0,
			'cess_amount': sum([entry['cf_cess_amount'] for entry in entries])if entries else 0})

	return data