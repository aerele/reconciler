# -*- coding: utf-8 -*-
# Copyright (c) 2021, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from erpnext.regional.india.utils import get_gst_accounts
from reconciler.reconciler.doctype.cd_gstr_2b_data_upload_tool.cd_gstr_2b_data_upload_tool import get_supplier_by_gstin

class CDGSTR2BEntry(Document):
	pass

@frappe.whitelist()
def update_entry(doc_name):
	doc = frappe.get_doc('CD GSTR 2B Entry', doc_name)
	doc.cf_party = get_supplier_by_gstin(doc.cf_party_gstin)
	doc.save(ignore_permissions=True)
	doc.reload()
