# -*- coding: utf-8 -*-
# Copyright (c) 2021, Aerele Technologies Private Limited and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import  _
from frappe.model.document import Document
from frappe.core.page.background_jobs.background_jobs import get_info
from frappe.utils.background_jobs import enqueue

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
	total_taxable_amt = 0
	total_tax_amt = 0
	total_entries = 0
	#Define mapping for json and gstr2a entry fields
	company_field_mappings = {'gstin': 'cf_company_gstin', 'fp': 'cf_financial_period'}
	
	party_based_field_mappings = {
		'ctin': 'cf_party_gstin',
		'cfs': 'cf_gstr15_filing_status',
		'cfs3b': 'cf_gstr3b_filing_status',
		'dtcancel': 'cf_cancellation_date',
		'fldtr1': 'cf_gstr15_filing_date',
		'flprdr1': 'cf_gstr15_filing_period'}

	invoice_field_mappings = { 'inum': 'cf_invoice_number',
		'idt': 'cf_invoice_date',
		'val': 'cf_invoice_amount', 
		'pos': 'cf_place_of_supply',
		'rchrg': 'cf_reverse_charge',
		'inv_typ':'cf_invoice_type'
		}

	invoice_item_field_mappings = { "rt": 'cf_tax_rate',
		"txval": 'cf_taxable_amount',
		"iamt": 'cf_igst_amount',
		"camt": 'cf_cgst_amount',
		"samt": 'cf_sgst_amount',
		"csamt": 'cf_cess_amount'
	}

	inv_typ = {'R': 'Registered Regular',
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

	data = {'doctype':'CD GSTR 2A Entry',
		'cf_company': doc.cf_company,
		'cf_gst_state': doc.cf_gst_state}

	check_existing = {'inum': 'cf_invoice_number', 'idt': 'cf_invoice_date'}

	for key in company_field_mappings:
		data[company_field_mappings[key]] = json_data[key]
		del json_data[key]

	for row in json_data['b2b']:
		for key in list(row.keys()):
			if key in party_based_field_mappings:
				data[party_based_field_mappings[key]] = row[key]
				del row[key]
			if key == 'inv':
				for inv in row['inv']:
					new_doc = frappe.get_doc(data)
					del data['doctype']
					inv_tax_amt = 0
					for key1 in list(inv.keys()):
						if key1 in invoice_field_mappings:
							setattr(new_doc, invoice_field_mappings[key1], inv[key1])
							if key1 == 'inv_typ':
								setattr(new_doc, invoice_field_mappings[key1], inv_typ[inv[key1]])
							if key1 == 'pos':
								setattr(new_doc, invoice_field_mappings[key1], inv[key1]+'-'+state_numbers[inv[key1]])
							if key1 in check_existing:
								data[check_existing[key1]] = inv[key1]
							del inv[key1]
						if key1 == 'itms':
							new_doc, tax_details = update_inv_items(inv, new_doc, invoice_item_field_mappings)
							for tax_key in invoice_item_field_mappings:
								if not tax_key in ['rt', 'txval']:
									inv_tax_amt += tax_details[tax_key]
								setattr(new_doc, invoice_item_field_mappings[tax_key], tax_details[tax_key])
					setattr(new_doc, 'cf_uploaded_via', doc.name)
					setattr(new_doc, 'cf_other_fields', str(row))
					setattr(new_doc, 'cf_tax_amount', inv_tax_amt)
					if not frappe.db.exists("CD GSTR 2A Entry", data):
						total_entries += 1
						total_tax_amt += inv_tax_amt
						total_taxable_amt += new_doc.cf_taxable_amount
						new_doc.save()
						new_doc.submit()
					data['doctype'] = 'CD GSTR 2A Entry'
					del data['cf_invoice_number']
					del data['cf_invoice_date']
	frappe.db.set_value('CD GSTR 2A Data Upload Tool', doc.name, 'cf_total_gstr_2a_entries', total_entries)
	frappe.db.set_value('CD GSTR 2A Data Upload Tool', doc.name, 'cf_taxable_amount', round(total_taxable_amt,2))
	frappe.db.set_value('CD GSTR 2A Data Upload Tool', doc.name, 'cf_tax_amount', round(total_tax_amt,2))
	frappe.db.commit()			

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
		new_doc.append('cf_gstr_2a_invoice_item_details', item_details)
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