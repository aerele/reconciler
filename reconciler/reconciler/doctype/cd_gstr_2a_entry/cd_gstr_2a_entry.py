# -*- coding: utf-8 -*-
# Copyright (c) 2021, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.regional.india.utils import get_gst_accounts

class CDGSTR2AEntry(Document):
	def after_insert(self):
		matched_inv = self.check_for_exact_match()
		if matched_inv:
			self.cf_purchase_invoice = matched_inv
			self.cf_match_status = 'Exact Match'
		else:
			suggested_inv, status, reason = self.suggest_invoice()
			if suggested_inv:
				self.cf_purchase_invoice = suggested_inv
				self.cf_match_status = status
				self.cf_reason = ','.join(reason)
			else:
				self.cf_match_status = 'Missing in PR'

	def check_for_exact_match(self):
		is_tax_amt_same = True
		account_head_fields = {
			'cgst_account': 'cf_cgst_amount',
			'sgst_account': 'cf_sgst_amount',
			'igst_account': 'cf_igst_amount',
			'cess_account': 'cf_cess_amount'
		}
		data = {'supplier_gstin': self.cf_party_gstin,
			'company_gstin': self.cf_company_gstin,
			'bill_date': self.cf_invoice_date,
			'bill_no': self.cf_invoice_number,
			'total': self.cf_taxable_amount, 
			'taxes_and_charges_added': self.cf_tax_amount, 
			'grand_total': self.cf_invoice_amount,
			'place_of_supply': self.cf_place_of_supply,
			'gst_category': self.cf_invoice_type,
			'reverse_charge': self.cf_reverse_charge,
			'docstatus': 1}
		inv = frappe.db.get_value('Purchase Invoice', data, 'name')
		if inv:
			doc = frappe.get_doc('Purchase Invoice', inv)
			gst_accounts = get_gst_accounts(doc.company)
			for row in doc.taxes:
				for accounts in gst_accounts.values():
					if row.account_head in accounts:
						if not type(accounts[-1]) == int:
							accounts.append(0)
						accounts[-1]+=row.tax_amount

			for acc in gst_accounts:
				if len(gst_accounts[acc])==3:
					tax_amt = gst_accounts[acc][-1]
					if tax_amt:
						if not getattr(self, account_head_fields[acc]) == tax_amt:
							is_tax_amt_same = False
			if not is_tax_amt_same:
				inv = None
		return inv
	
	def suggest_invoice(self):
		status = 'Suggested'
		suggested_inv = None
		reason = []
		account_head_fields = {
			'cgst_account': 'cf_cgst_amount',
			'sgst_account': 'cf_sgst_amount',
			'igst_account': 'cf_igst_amount',
			'cess_account': 'cf_cess_amount'
		}
		amount_fields = {
			'total': 'cf_taxable_amount' , 
			'taxes_and_charges_added':  'cf_tax_amount', 
			'grand_total':  'cf_invoice_amount'
		}
		data = {'supplier_gstin': self.cf_party_gstin,
			'company_gstin': self.cf_company_gstin,
			'bill_date': self.cf_invoice_date,
			'docstatus': 1,
			'place_of_supply': self.cf_place_of_supply,
			'reverse_charge': self.cf_reverse_charge,
			'gst_category': self.cf_invoice_type}
		inv_list = frappe.db.get_list('Purchase Invoice', data, 'name')
		if not inv_list:
			return None, None, None
		for inv in inv_list:
			suggested_inv = inv['name']
			doc = frappe.get_doc('Purchase Invoice', inv['name'])
			if not doc.bill_no == self.cf_invoice_number:
				reason.append('Invoice Number')
			for field in amount_fields:
				if abs(getattr(self, amount_fields[field]) - getattr(doc, field)) > 1:
					reason.append(amount_fields[field][2:].title().replace('_', ' '))
			gst_accounts = get_gst_accounts(doc.company)
			for row in doc.taxes:
				for accounts in gst_accounts.values():
					if row.account_head in accounts:
						if not type(accounts[-1]) == int:
							accounts.append(0)
						accounts[-1]+=row.tax_amount
			for acc in gst_accounts:
				if len(gst_accounts[acc])==3:
					tax_amt = gst_accounts[acc][-1]
					if tax_amt:
						if abs(getattr(self, account_head_fields[acc]) - tax_amt) > 1:
							reason.append(account_head_fields[acc][2:].title().replace('_', ' '))

			if len(reason) > 3:
				status = 'Mismatch'

			if reason:
				break
		return suggested_inv, status, reason