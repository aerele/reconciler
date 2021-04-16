# -*- coding: utf-8 -*-
# Copyright (c) 2021, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import  _
from frappe.model.document import Document
from frappe.utils import add_months, comma_and
from erpnext.regional.india.utils import get_gst_accounts
from reconciler.reconciler.doctype.cd_gstr_2b_data_upload_tool.cd_gstr_2b_data_upload_tool import *
from frappe.utils.user import get_users_with_role

class CDGSTR2BEntry(Document):
	pass

@frappe.whitelist()
def link_supplier(doc_name):
	doc = frappe.get_doc('CD GSTR 2B Entry', doc_name)
	supplier = get_supplier_by_gstin(doc.cf_party_gstin)
	if supplier:
		doc.cf_party = supplier
		doc.save(ignore_permissions=True)
		doc.reload()
		frappe.msgprint(_("Supplier Linked successfully"))

@frappe.whitelist()
def unlink_pr(doc_name):
	doc = frappe.get_doc('CD GSTR 2B Entry', doc_name)
	if doc.cf_status == 'Accepted':
		user = frappe.session.user
		if not user in get_users_with_role("Accounts Admin") and user != 'Administrator':
			frappe.throw(_("You do not have enough permission to do this action."))
			return
	doc.cf_match_status = None
	doc.cf_reason = None
	doc.cf_status = 'Pending'
	doc.cf_purchase_invoice = None
	doc.save(ignore_permissions=True)
	doc.reload()


@frappe.whitelist()
def rematch_result(doc_name):
	match_status_priority_list = ['Exact Match','Partial Match','Probable Match',
								'Mismatch','Missing in PR']
	doc = frappe.get_doc('CD GSTR 2B Entry', doc_name)
	month_threshold = -(frappe.db.get_single_value('CD GSTR 2B Settings', 'month_threshold'))
	doc_val = frappe.db.get_values('CD GSTR 2B Data Upload Tool', filters={'name': doc.cf_uploaded_via}, 
			fieldname=["cf_company_gstin", "cf_return_period"])

	return_period_year = int(doc_val[0][1][-4::])
	return_period_month = int(doc_val[0][1][:2])
	to_date = last_day_of_month(return_period_year, return_period_month)
	if not to_date:
		frappe.throw(_(f'To date not found for the PR filters'))

	from_date = add_months(to_date, month_threshold)
	pr_list = get_pr_list(doc_val[0][0], from_date, to_date)
	gstr2b_doc_params = {
		'name': doc.name,
		'gstin': doc.cf_party_gstin,
		'document_type': doc.cf_transaction_type,
		'document_date': doc.cf_document_date,
		'document_number': doc.cf_document_number,
		'total_taxable_amount': doc.cf_taxable_amount,
		'total_tax_amount': doc.cf_tax_amount,
		'igst_amount': doc.cf_igst_amount,
		'cgst_amount': doc.cf_cgst_amount,
		'sgst_amount': doc.cf_sgst_amount,
		'cess_amount': doc.cf_cess_amount
	}
	res = get_match_status(gstr2b_doc_params, pr_list)
	if res:
		if doc.cf_match_status:
			if not doc.cf_match_status == res[1]:
				if match_status_priority_list.index(doc.cf_match_status) < \
					match_status_priority_list.index(res[1]):
					frappe.msgprint(_("Existing PR is the best match for this record"))
				else:
					update_match_status(gstr2b_doc_params, res)
					frappe.msgprint(_("Match status updated"))
		else:
			update_match_status(gstr2b_doc_params, res)
			frappe.msgprint(_("Match status updated"))
	else:
		if doc.cf_match_status == 'Missing in PR':
			frappe.throw(_("No PR matched for the given 2B record"))
		if doc.cf_match_status == None:
			doc.cf_match_status = 'Missing in PR'
			doc.cf_reason = None
			doc.cf_purchase_invoice = None
			doc.save(ignore_permissions=True)
			doc.reload()
		else:
			frappe.msgprint(_("Existing PR is the best match for this record"))

def get_linked_2b(doc, action):
	is_linked_and_pending = frappe.db.get_value('CD GSTR 2B Entry', {'cf_purchase_invoice': doc.name, 'cf_status': 'Pending'}, 'name')
	is_linked_and_accepted = frappe.db.get_value('CD GSTR 2B Entry', {'cf_purchase_invoice': doc.name, 'cf_status': 'Accepted'}, 'name')
	if is_linked_and_accepted:
		frappe.throw(_(f'This document is linked to {comma_and("""<a href="#Form/CD GSTR 2B Entry/{0}">{1}</a>""".format(is_linked_and_accepted, is_linked_and_accepted))}. Kindly unlink the document and proceed.'))
	if is_linked_and_pending:
		doc = frappe.get_doc('CD GSTR 2B Entry', is_linked_and_pending)
		doc.cf_match_status = None
		doc.cf_reason = None
		doc.cf_purchase_invoice = None
		doc.save(ignore_permissions=True)
		doc.reload()