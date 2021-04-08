# -*- coding: utf-8 -*-
# Copyright (c) 2021, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import  _
from frappe.model.document import Document
from frappe.core.page.background_jobs.background_jobs import get_info
from frappe.utils.background_jobs import enqueue
from datetime import datetime
from erpnext.accounts.utils import get_fiscal_year

class CDGSTR2ADataUploadTool(Document):
	def validate(self):
		json_data = frappe.get_file_json(frappe.local.site_path + self.cf_upload_gstr_2a_data)
		if not json_data['gstin'] == self.cf_company_gstin:
			frappe.throw(_(f'Invalid JSON. Company GSTIN mismatched with uploaded 2A data.'))

	def after_insert(self):
		enqueued_jobs = [d.get("job_name") for d in get_info()]
		json_data = frappe.get_file_json(frappe.local.site_path + self.cf_upload_gstr_2a_data)
		if self.name in enqueued_jobs:
			frappe.msgprint(
				_("Create GSTR 2A entries already in progress. Please wait for sometime.")
			)
		else:
			enqueue(
				create_gstr2a_entries,
				queue = "default",
				timeout = 6000,
				event = 'create_gstr2a_entries',
				json_data = json_data,
				doc = self,
				job_name = self.name
			)
			frappe.msgprint(
				_("Create GSTR 2A entries job added to the queue. Please check after sometime.")
			)

def create_gstr2a_entries(json_data, doc):
	total_entries_created = 0
	data = {'doctype' :'CD GSTR 2A Entry',
		'cf_company': doc.cf_company,
		'cf_gst_state': doc.cf_gst_state}

	try:
		doc.cf_no_of_entries_in_json = 0
		data['cf_company_gstin']  = json_data['gstin']
		del json_data['gstin']
		data['cf_financial_period']  = json_data['fp']
		del json_data['fp']
		if 'b2b' in json_data:
			transaction_based_mappings = {
				'inum': 'cf_document_number',
				'idt': 'cf_document_date'
			}
			amendment_type = {
				'R': 'Receiver GSTIN Amended',
				'N': 'Invoice Number Amended',
				'D': 'Details Amended'
			}
			data['cf_transaction_type'] = 'Invoice'
			doc, total_entries_created = update_transaction_details('inv', json_data['b2b'], transaction_based_mappings,\
				 data, doc, total_entries_created, amendment_type)
		if 'cdn' in json_data:
			amendment_type = {
				'R': 'Receiver GSTIN Amended',
				'N': 'Note Number Amended',
				'D': 'Details Amended'
			}
			transaction_based_mappings = { 
				'inum': 'cf_against_invoice_number',
				'idt': 'cf_against_invoice_date',
				'ntty': 'cf_note_type',
				"nt_num": 'cf_document_number',
				"nt_dt": 'cf_document_date'
				}
			data['cf_transaction_type'] = 'CDN'
			doc, total_entries_created = update_transaction_details('nt', json_data['cdn'], transaction_based_mappings,\
				data, doc, total_entries_created, amendment_type)

		doc.cf_no_of_updated_entries = len(doc.cf_gstr_2a_updated_records)
		doc.save()
		frappe.db.set_value('CD GSTR 2A Data Upload Tool',doc.name,'cf_no_of_newly_created_entries', f"""<a href="#List/CD GSTR 2A Entry/List?cf_uploaded_via={doc.name}">{total_entries_created}</a>""")
		frappe.db.commit()
	except:
		traceback = frappe.get_traceback()
		frappe.log_error(title = 'GSTR 2A Json Upload Error',message=traceback)		

def update_transaction_details(txn_key, txn_details, mappings, data, uploaded_doc, total_entries_created, amendment_type):

	# Define mapping for json and gstr2a entry fields
	party_based_field_mappings = {
		'ctin': 'cf_party_gstin',
		'cfs': 'cf_gstr15_filing_status',
		'cfs3b': 'cf_gstr3b_filing_status',
		'dtcancel': 'cf_cancellation_date',
		'fldtr1': 'cf_gstr15_filing_date',
		'flprdr1': 'cf_gstr15_filing_period'}

	common_field_mappings = {
		'val': 'cf_total_amount', 
		'pos': 'cf_place_of_supply',
		'rchrg': 'cf_reverse_charge',
		'inv_typ':'cf_invoice_type',
		'aspd': 'cf_amended_return_period',
		'atyp': 'cf_amendment_type'
	}

	invoice_item_field_mappings = { "rt": 'cf_tax_rate',
		"txval": 'cf_taxable_amount',
		"iamt": 'cf_igst_amount',
		"camt": 'cf_cgst_amount',
		"samt": 'cf_sgst_amount',
		"csamt": 'cf_cess_amount'
	}

	common_field_mappings.update(mappings)

	# Define Expansions
	note_type = {
		"C":"Credit",
		"D":"Debit"
	}

	inv_type = {'R': 'Registered Regular',
		'DE': 'Deemed Export',
		'SEWP': 'SEZ Exports with payment',
		'SEWOP': 'SEZ exports without payment'}

	state_numbers = {
		"35": "Andaman and Nicobar Islands",
		"37": "Andhra Pradesh",
		"12": "Arunachal Pradesh",
		"18": "Assam",
		"10": "Bihar",
		"04": "Chandigarh",
		"22": "Chhattisgarh",
		"26": "Dadra and Nagar Haveli and Daman and Diu",
		"07": "Delhi",
		"30": "Goa",
		"24": "Gujarat",
		"06": "Haryana",
		"02": "Himachal Pradesh",
		"01": "Jammu and Kashmir",
		"20": "Jharkhand",
		"29": "Karnataka",
		"32": "Kerala",
		"38": "Ladakh",
		"31": "Lakshadweep Islands",
		"23": "Madhya Pradesh",
		"27": "Maharashtra",
		"14": "Manipur",
		"17": "Meghalaya",
		"15": "Mizoram",
		"13": "Nagaland",
		"21": "Odisha",
		"98": "Other Territory",
		"34": "Pondicherry",
		"03": "Punjab",
		"08": "Rajasthan",
		"11": "Sikkim",
		"33": "Tamil Nadu",
		"36": "Telangana",
		"16": "Tripura",
		"09": "Uttar Pradesh",
		"05": "Uttarakhand",
		"19": "West Bengal"
		}

	for row in txn_details:
		for key in list(row.keys()):
			if key in party_based_field_mappings:
				data[party_based_field_mappings[key]] = row[key]
				if key == 'ctin':
					data['cf_party'] = get_supplier_by_gstin(row[key])
				del row[key]
			if key == txn_key:
				uploaded_doc.cf_no_of_entries_in_json += len(row[txn_key])
				for inv in row[txn_key]:
					new_doc = frappe.get_doc(data)
					inv_tax_amt = 0
					for key1 in list(inv.keys()):
						if key1 in common_field_mappings:
							setattr(new_doc, common_field_mappings[key1], inv[key1])
							if key1 in ['idt', 'nt_dt']:
								setattr(new_doc, common_field_mappings[key1], datetime.strptime(inv[key1] , "%d-%m-%Y").date())
							if key1 == 'inv_typ':
								setattr(new_doc, common_field_mappings[key1], inv_type[inv[key1]])
							if key1 == 'ntty':
								setattr(new_doc, common_field_mappings[key1], note_type[inv[key1]])
							if key1 == 'atyp':
								setattr(new_doc, common_field_mappings[key1], amendment_type[inv[key1]])
							if key1 == 'pos':
								setattr(new_doc, common_field_mappings[key1], inv[key1]+'-'+state_numbers[inv[key1]])
							del inv[key1]
						if key1 == 'itms':
							new_doc, tax_details = update_inv_items(inv, new_doc, invoice_item_field_mappings)
							for tax_key in invoice_item_field_mappings:
								if not tax_key in ['rt', 'txval']:
									inv_tax_amt += tax_details[tax_key]
								setattr(new_doc, invoice_item_field_mappings[tax_key], tax_details[tax_key])
					setattr(new_doc, 'cf_uploaded_via', uploaded_doc.name)
					setattr(new_doc, 'cf_other_fields', str(row))
					setattr(new_doc, 'cf_tax_amount', inv_tax_amt)
					fiscal_year = get_fiscal_year(new_doc.cf_document_date)[0]
					setattr(new_doc, 'cf_fiscal_year', fiscal_year)
					compare_fields = {
							'cf_transaction_type': new_doc.cf_transaction_type,
							'cf_company_gstin': new_doc.cf_company_gstin,
							'cf_party_gstin': new_doc.cf_party_gstin,
							'cf_fiscal_year': new_doc.cf_fiscal_year,
							'cf_document_number': new_doc.cf_document_number
						}
					if new_doc.cf_note_type and not new_doc.cf_transaction_type == 'Invoice':
						compare_fields['cf_note_type'] =  new_doc.cf_note_type
					if new_doc.cf_party:
						compare_fields['cf_party'] =  new_doc.cf_party
	
					existing_doc_name = frappe.db.get_value('CD GSTR 2A Entry', compare_fields, 'name')
					if not existing_doc_name:
						total_entries_created += 1
						new_doc.save()
					else:
						is_changed = False
						existing_doc = frappe.get_doc('CD GSTR 2A Entry', existing_doc_name)
						meta = frappe.get_meta('CD GSTR 2A Entry').fields
						for field in meta:
							if field.fieldtype in ['Data', 'Date', 'Link', 'Currency'] and not field.fieldname == 'cf_uploaded_via':
								if not getattr(existing_doc, field.fieldname) == getattr(new_doc, field.fieldname):
									setattr(existing_doc, field.fieldname, getattr(new_doc, field.fieldname))
									is_changed = True
						if is_changed:
							uploaded_doc.append('cf_gstr_2a_updated_records',{
								"gstr_2a_entry" : existing_doc_name
							})
							existing_doc.save()
	return uploaded_doc, total_entries_created

def update_inv_items(inv, new_doc, invoice_item_field_mappings):
	tax_details = {'iamt': 0, 'camt': 0, 'samt': 0, 'csamt':0, 'rt': 0, 'txval': 0}
	item_list = []
	for item_det in inv['itms']:
		item_details = {}	
		for det_key in list(item_det['itm_det']):
			if det_key in invoice_item_field_mappings:
				item_details[invoice_item_field_mappings[det_key]] = item_det['itm_det'][det_key]
				tax_details[det_key] += item_det['itm_det'][det_key]
				del item_det['itm_det'][det_key]
		if not item_det['itm_det']:
			del item_det['itm_det']
		if len(item_det) == 1 and 'num' in item_det:
			inv['itms'].remove(item_det)
		new_doc.append('cf_gstr_2a_invoice_item_details', item_details)
	if not inv['itms']:
		del inv['itms']
	return new_doc, tax_details

@frappe.whitelist()
def get_gstin_for_company(company, gst_state):
	company_gstin = frappe.db.sql("""select
		`tabAddress`.gstin
	from
		`tabAddress`, `tabDynamic Link`
	where
		`tabAddress`.gst_state = %(gst_state)s and 
		`tabDynamic Link`.parent = `tabAddress`.name and
		`tabDynamic Link`.parenttype = 'Address' and
		`tabDynamic Link`.link_doctype = 'Company' and
		`tabDynamic Link`.link_name = %(company)s""", {"company": company, "gst_state": gst_state})
	
	if company_gstin and company_gstin[0][0]:
		return company_gstin[0][0]
	else:
		frappe.throw(_(f'Company GSTIN not found for the selected state.'))

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