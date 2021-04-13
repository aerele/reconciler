# Copyright (c) 2013, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe, json

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
					"label": "Total 2A",
					"fieldname": "total_2a",
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
					"label": "Total Pending",
					"fieldname": "total_pending",
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
					"label": "Tax Difference",
					"fieldname": "tax_difference",
					"fieldtype": "Float",
					"width": 200
				},
				{
					"label": "Total Value",
					"fieldname": "total_value",
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
					"label": "Link",
					"fieldname": "link",
					"fieldtype": "Button",
					"width": 200
				},
				{
					"label": "Unlink",
					"fieldname": "unlink",
					"fieldtype": "Button",
					"width": 200
				}]

	def get_data(self):
		self.data = []

@frappe.whitelist()
def return_period_query():
	return_period_list = []
	rp_list = frappe.db.get_list('CD GSTR 2B Data Upload Tool',['cf_return_period'])
	for data in rp_list:
		return_period_list.append(data['cf_return_period'])
	return sorted(set(return_period_list))
