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
from frappe.utils import comma_and

class CDGSTR2BDataUploadTool(Document):
	def validate(self):
		json_data = frappe.get_file_json(frappe.local.site_path + self.cf_upload_gstr_2b_data)
		return_period = json_data['data']['rtnprd']
		existing_doc = frappe.db.get_value('CD GSTR 2B Data Upload Tool', {'cf_return_period': return_period}, 'name')
		if existing_doc:
			frappe.throw(_(f'Unable to proceed. Already another document {comma_and("""<a href="#Form/CD GSTR 2B Data Upload Tool/{0}">{1}</a>""".format(existing_doc, existing_doc))} uploaded for the return period {frappe.bold(return_period)}.'))
		if not json_data['data']['gstin'] == self.cf_company_gstin:
			frappe.throw(_(f'Invalid JSON. Company GSTIN mismatched with uploaded 2B data.'))

	def before_save(self):
		json_data = frappe.get_file_json(frappe.local.site_path + self.cf_upload_gstr_2b_data)
		self.cf_return_period = json_data['data']['rtnprd']

	def after_insert(self):
		enqueued_jobs = [d.get("job_name") for d in get_info()]
		json_data = frappe.get_file_json(frappe.local.site_path + self.cf_upload_gstr_2b_data)
		if self.name in enqueued_jobs:
			frappe.msgprint(
				_("Create GSTR 2B entries already in progress. Please wait for sometime.")
			)
		else:
			enqueue(
				create_gstr2b_entries,
				queue = "default",
				timeout = 6000,
				event = 'create_gstr2b_entries',
				json_data = json_data,
				doc = self,
				job_name = self.name
			)
			frappe.msgprint(
				_("Create GSTR 2B entries job added to the queue. Please check after sometime.")
			)

def create_gstr2b_entries(json_data, doc):
	total_entries_created = 0
	data = {'doctype' :'CD GSTR 2B Entry',
		'cf_company': doc.cf_company,
		'cf_gst_state': doc.cf_gst_state}

	try:
		doc.cf_no_of_entries_in_json = 0
		data['cf_company_gstin']  = json_data['data']['gstin']
		del json_data['data']['gstin']
		data['cf_generation_date']  = datetime.strptime(json_data['data']['gendt'] , "%d-%m-%Y").date()
		del json_data['data']['gendt']
		data['cf_return_period']  = json_data['data']['rtnprd']
		del json_data['data']['rtnprd']
		if 'b2b' in json_data['data']['docdata']:
			transaction_based_mappings = {
				'inum': 'cf_document_number'
			}
			data['cf_transaction_type'] = 'Invoice'
			doc, total_entries_created = update_transaction_details('inv', json_data['data']['docdata']['b2b'], transaction_based_mappings,\
				 data, doc, total_entries_created)
		if 'cdnr' in json_data['data']['docdata']:
			transaction_based_mappings = {
				'typ': 'cf_note_type',
				"nt_num": 'cf_document_number',
				'suptyp': 'cf_note_supply_type'
				}
			data['cf_transaction_type'] = 'CDN'
			doc, total_entries_created = update_transaction_details('nt', json_data['data']['docdata']['cdnr'], transaction_based_mappings,\
				data, doc, total_entries_created)

		doc.save(ignore_permissions=True)
		doc.reload()
		frappe.db.set_value('CD GSTR 2B Data Upload Tool',doc.name,'cf_no_of_newly_created_entries', f"""<a href="#List/CD GSTR 2B Entry/List?cf_uploaded_via={doc.name}">{total_entries_created}</a>""")
		frappe.db.commit()
	except:
		traceback = frappe.get_traceback()
		frappe.log_error(title = 'GSTR 2B Json Upload Error',message=traceback)		

def update_transaction_details(txn_key, txn_details, mappings, data, uploaded_doc, total_entries_created):

	# Define mapping for json and gstr2b entry fields
	party_based_field_mappings = {
		'trdnm': 'cf_trade_name',
		'ctin': 'cf_party_gstin',
		'supfildt': 'cf_gstr15_filing_date',
		'supprd': 'cf_gstr15_filing_period'}

	common_field_mappings = {
		'dt': 'cf_document_date',
		'val': 'cf_total_amount', 
		'pos': 'cf_place_of_supply',
		'rev': 'cf_reverse_charge',
		'itcavl': 'cf_itc_availability',
		'typ':'cf_invoice_type',
		'rsn': 'cf_reason_for_itc_unavailability'
	}

	invoice_item_field_mappings = { "rt": 'cf_tax_rate',
		"txval": 'cf_taxable_amount',
		"igst": 'cf_igst_amount',
		"cgst": 'cf_cgst_amount',
		"sgst": 'cf_sgst_amount',
		"cess": 'cf_cess_amount'
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
	
	note_supply_type = {'R': 'Registered Regular',
		'DE': 'Deemed Export',
		'SEWP': 'SEZ Exports with payment',
		'SEWOP': 'SEZ exports without payment',
		'CBW': 'Customs Bonded Warehouse'}

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
		uploaded_doc.cf_no_of_entries_in_json += len(row[txn_key])
		for inv in row[txn_key]:
			new_doc = frappe.get_doc(data)
			inv_tax_amt = 0
			for key1 in list(inv.keys()):
				if key1 in common_field_mappings:
					setattr(new_doc, common_field_mappings[key1], inv[key1])
					if key1 == 'dt':
						setattr(new_doc, common_field_mappings[key1], datetime.strptime(inv[key1] , "%d-%m-%Y").date())
					if key1 == 'suptyp':
						setattr(new_doc, common_field_mappings[key1], note_supply_type[inv[key1]])
					if key1 == 'typ' and txn_key == 'inv':
						setattr(new_doc, common_field_mappings[key1], inv_type[inv[key1]])
					if key1 == 'typ' and txn_key == 'nt':
						setattr(new_doc, common_field_mappings[key1], note_type[inv[key1]])
					if key1 == 'pos':
						setattr(new_doc, common_field_mappings[key1], inv[key1]+'-'+state_numbers[inv[key1]])
					del inv[key1]
				if key1 == 'items':
					new_doc, tax_details = update_inv_items(inv, new_doc, invoice_item_field_mappings)
					for tax_key in invoice_item_field_mappings:
						if not tax_key in ['rt', 'txval']:
							inv_tax_amt += tax_details[tax_key]
						setattr(new_doc, invoice_item_field_mappings[tax_key], tax_details[tax_key])
			setattr(new_doc, 'cf_uploaded_via', uploaded_doc.name)
			setattr(new_doc, 'cf_other_fields', str(inv))
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

			existing_doc_name = frappe.db.get_value('CD GSTR 2B Entry', compare_fields, 'name')
			if not existing_doc_name:
				total_entries_created += 1
				new_doc.save(ignore_permissions=True)
				new_doc.reload()
	return uploaded_doc, total_entries_created

def update_inv_items(inv, new_doc, invoice_item_field_mappings):
	tax_details = {'igst': 0, 'cgst': 0, 'sgst': 0, 'cess':0, 'rt': 0, 'txval': 0}
	item_list = []
	for row in inv['items']:
		item_details = {}
		for item_det in list(row):
			if item_det in invoice_item_field_mappings:
				item_details[invoice_item_field_mappings[item_det]] = row[item_det]
				tax_details[item_det] += row[item_det]
				del row[item_det]
		if len(row) == 1 and 'num' in row:
			inv['items'].remove(row)
		new_doc.append('cf_gstr_2b_invoice_item_details', item_details)
	if not inv['items']:
		del inv['items']
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