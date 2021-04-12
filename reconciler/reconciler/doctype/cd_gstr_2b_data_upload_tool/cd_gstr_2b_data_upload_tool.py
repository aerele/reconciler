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
from frappe.utils import comma_and, add_months
from erpnext.regional.india.utils import get_gst_accounts
import re
from operator import itemgetter

class CDGSTR2BDataUploadTool(Document):
	def onload(self):
		total_taxable_amount = 0
		total_tax_amount = 0
		amount_list = frappe.db.get_values('CD GSTR 2B Entry', {'cf_uploaded_via': self.name},['cf_taxable_amount','cf_tax_amount'])
		if amount_list:
			for row in amount_list:
				if row:
					total_taxable_amount += row[0]
					total_tax_amount += row[1]
		self.set_onload('total_taxable_amount', round(total_taxable_amount, 2))
		self.set_onload('total_tax_amount', round(total_tax_amount, 2))
		self.set_onload('match_summary', self.get_match_summary())

	def get_match_summary(self):
		match_summary = [{'match_type':'Exact Match','total_docs':0},
						{'match_type':'Partial Match','total_docs':0},
						{'match_type':'Probable Match','total_docs':0},
						{'match_type':'Mismatch','total_docs':0},
						{'match_type':'Missing in PR','total_docs':0}]
		for row in match_summary:
			row['total_docs'] = frappe.db.count('CD GSTR 2B Entry', {'cf_uploaded_via': self.name, 'cf_match_status': row['match_type']})

		return match_summary

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
				"ntnum": 'cf_document_number',
				'suptyp': 'cf_note_supply_type'
				}
			data['cf_transaction_type'] = 'CDN'
			doc, total_entries_created = update_transaction_details('nt', json_data['data']['docdata']['cdnr'], transaction_based_mappings,\
				data, doc, total_entries_created)

		doc.save(ignore_permissions=True)
		doc.reload()
		frappe.db.set_value('CD GSTR 2B Data Upload Tool',doc.name,'cf_no_of_newly_created_entries', f"""<a href="#List/CD GSTR 2B Entry/List?cf_uploaded_via={doc.name}">{total_entries_created}</a>""")
		frappe.db.commit()
		link_documents(doc.name)
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
			setattr(new_doc, 'cf_status', 'Pending')
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
	for row in inv['items'][:]:
		item_details = {}
		for item_det in list(row.keys()):
			if item_det in invoice_item_field_mappings:
				item_details[invoice_item_field_mappings[item_det]] = row[item_det]
				tax_details[item_det] += row[item_det]
				del row[item_det]
		new_doc.append('cf_gstr_2b_invoice_item_details', item_details)
		if len(row) == 1 and 'num' in row:
			inv['items'].remove(row)
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

def link_documents(uploaded_doc_name):
	# 12 months back PR record from the previous month of return preiod will be fetched
	month_threshold = -12
	doc_val = frappe.db.get_values('CD GSTR 2B Data Upload Tool', filters={'name': uploaded_doc_name}, 
			fieldname=["cf_company_gstin", "cf_return_period"])

	return_period_year = int(doc_val[0][1][-4::])
	return_period_month = int(doc_val[0][1][:2])
	to_date = last_day_of_month(return_period_year, return_period_month)
	if not to_date:
		frappe.throw(_(f'To date not found for the PR filters'))

	from_date = add_months(to_date, month_threshold)
	gstr2b_list = frappe.get_list('CD GSTR 2B Entry', 
						filters={'cf_uploaded_via': uploaded_doc_name,
						'cf_status': 'Pending'},
						fields=[
						'name',
						'cf_party_gstin as gstin',
						'cf_transaction_type as document_type',
						'cf_document_date as document_date',
						'cf_document_number as document_number',
						'cf_taxable_amount as total_taxable_amount',
						'cf_tax_amount as total_tax_amount',
						'cf_igst_amount as igst_amount',
						'cf_cgst_amount as cgst_amount',
						'cf_sgst_amount as sgst_amount',
						'cf_cess_amount as cess_amount'
						])
	pr_list = get_pr_list(doc_val[0][0], from_date, to_date)
	for doc in gstr2b_list:
		is_exactly_matched = frappe.db.get_value('CD GSTR 2B Entry', {'name': doc['name'],'cf_match_status': 'Exact Match'})
		if not is_exactly_matched:
			pr = get_match_status(doc, pr_list)
			pr_list[:] = [doc for doc in pr_list if doc != pr]
			if not pr:
				frappe.db.set_value('CD GSTR 2B Entry', doc['name'], 'cf_match_status', 'Missing in PR')
				frappe.db.set_value('CD GSTR 2B Entry', doc['name'], 'cf_reason', None)
				frappe.db.set_value('CD GSTR 2B Entry', doc['name'], 'cf_purchase_invoice', None)
				frappe.db.commit()
	frappe.db.set_value('CD GSTR 2B Data Upload Tool', uploaded_doc_name, 'cf_is_matching_completed', 1)
	frappe.db.commit()

	
def get_pr_list(company_gstin, from_date, to_date):
	pr_list = []
	pi_doc_list = frappe.get_list('Purchase Invoice', 
						filters=[['company_gstin' ,'=',company_gstin],
						['posting_date' ,'>=',from_date],
						['docstatus', '=', 1],
						['posting_date' ,'<=',to_date]],
						fields=['name','supplier_gstin as gstin',
						'bill_date as document_date',
						'bill_no as document_number',
						'total as total_taxable_amount'])
	for row in pi_doc_list:
		is_linked = frappe.db.get_value('CD GSTR 2B Entry', {'cf_purchase_invoice': row['name'], 'cf_match_status': 'Exact Match'},'name')
		if not is_linked:
			row['document_type'] = 'Invoice'
			pr_list.append(row.update(get_tax_details(row['name'])))
	return pr_list

def get_tax_details(doc_name):
	tax_amount = []
	tax_details = {
	'igst_amount':0,
	'cgst_amount':0,
	'sgst_amount':0,
	'cess_amount':0,
	'total_tax_amount': 0}

	account_head_fields = ['igst_account','cgst_account','sgst_account','cess_account']
	doc = frappe.get_doc('Purchase Invoice', doc_name)
	gst_accounts = get_gst_accounts(doc.company)
	for row in doc.taxes:
		for accounts in gst_accounts.values():
			if row.account_head in accounts:
				if not type(accounts[-1]) == int:
					accounts.append(0)
				accounts[-1]+=row.tax_amount
	for idx in range(len(account_head_fields)):
		tax_amt = 0
		if gst_accounts[account_head_fields[idx]][-1]  and not type(gst_accounts[account_head_fields[idx]][-1]) == str:
			tax_amt = gst_accounts[account_head_fields[idx]][-1]
		tax_details[list(tax_details.keys())[idx]] = tax_amt
		tax_amount.append(tax_amt)
	tax_details['total_tax_amount'] = sum(tax_amount)
	return tax_details

def last_day_of_month(year, month):
	last_days = [31, 30, 29, 28]
	for day in last_days:
		try:
			end = datetime(year, month, day)
		except ValueError:
			continue
		else:
			return end.date()
	return None

def get_match_status(gstr2b_doc, pr_list, amount_threshold = 1):
	amount_params = {
	'total_taxable_amount',
	'total_tax_amount',
	'igst_amount',
	'cgst_amount',
	'sgst_amount',
	'cess_amount'}
	gstin_matched_pr_list = []
	gstin_doctype_matched_list = []
	remaining_list = []
	partial_match_list = []
	probable_match_list = []
	mismatch_list = []
	for pr in pr_list:
		if pr['gstin'] == gstr2b_doc['gstin']:
			if not pr['document_type'] == gstr2b_doc['document_type']:
				gstin_matched_pr_list.append(pr)
			else:
				gstin_doctype_matched_list.append(pr)
		else:
			remaining_list.append(pr)

	for pr in gstin_doctype_matched_list:
		reason = []
		count = 0
		if pr['document_date'] == gstr2b_doc['document_date']:
			count += 1
		else:
			reason.append('Document Date')
		if pr['document_number'] == gstr2b_doc['document_number']:
			count += 1
		else:
			reason.append('Document Number')
		for param in amount_params:
			if (abs(pr[param] - gstr2b_doc[param])<amount_threshold):
				count+=1
			else:
				reason.append(param.replace('_',' ').title())
		if count == 8:
			update_match_status(gstr2b_doc, [pr, 'Exact Match', reason])
			return pr
		elif count == 7:
			partial_match_list.append([pr, count, reason])
		else:
			mismatch_list.append([pr, count, reason])

	if partial_match_list:
		best_partial_match = []
		for row in partial_match_list[:]:
			if 'Document Date' not in row[2] and 'Document Number' not in row[2] \
			and 'Total Taxable Amount' not in row[2]:
				best_partial_match.append(row)
			else:
				continue
		if best_partial_match:
			update_match_status(gstr2b_doc, [best_partial_match[0][0], 'Partial Match', best_partial_match[0][2]])
			return best_partial_match[0][0]
		else:
			update_match_status(gstr2b_doc, [partial_match_list[0][0], 'Partial Match', partial_match_list[0][2]])
			return partial_match_list[0][0]

	if gstin_matched_pr_list:
		res = get_probable_match(gstin_matched_pr_list, gstr2b_doc, amount_params,'Document Type')
		if len(res)==3:
			update_match_status(gstr2b_doc, res)
			return res[0]
	
	if remaining_list:
		probable_pr_list = []
		for doc in remaining_list:
			if pr['document_type'] == gstr2b_doc['document_type']:
				probable_pr_list.append(doc)
		if probable_pr_list:
			res = get_probable_match(probable_pr_list, gstr2b_doc, amount_params, 'Supplier GSTIN')
			if len(res)==3:
				update_match_status(gstr2b_doc, res)
				return res[0]

	if mismatch_list:
		for row in mismatch_list[:]:
			if not row[0]['document_date'] == gstr2b_doc['document_date']:
				mismatch_list.remove(row)
			elif not row[0]['document_number'] == gstr2b_doc['document_number']:
				if not apply_approximation(gstr2b_doc['document_number'], row[0]['document_number']):
					mismatch_list.remove(row)
			else:
				continue
	if mismatch_list:
		mismatch_list = sorted(mismatch_list, key=itemgetter(1))
		update_match_status(gstr2b_doc, [mismatch_list[0][0], 'Mismatch', mismatch_list[0][2]])
		return mismatch_list[0][0]['name']
	return None



def get_probable_match(pr_list, gstr2b_doc, amount_params, probable_reason, amount_threshold =1):
	probable_list = []
	for pr in pr_list[:]:
		reason = [probable_reason]
		count = 0
		if pr['document_date'] == gstr2b_doc['document_date']:
			count += 1
		else:
			reason.append('Document Date')
		if pr['document_number'] == gstr2b_doc['document_number']:
			count += 1
		else:
			reason.append('Document Number')
		for param in amount_params:
			if (abs(pr[param] - gstr2b_doc[param])<amount_threshold):
				count+=1
			else:
				reason.append(param.replace('_',' ').title())
		if count != 8:
			pr_list.remove(pr)
		else:
			probable_list.append([pr, reason])
	if probable_list:
		return [probable_list[0][0], 'Probable Match', probable_list[0][1]]
	return []


def update_match_status(gstr2b_doc, match_result):
	doc = frappe.get_doc('CD GSTR 2B Entry', gstr2b_doc['name'])
	if match_result[0]['document_type'] == 'Invoice':
		setattr(doc, 'cf_purchase_invoice', match_result[0]['name'])
	doc.cf_match_status = match_result[1]
	doc.cf_reason = ','.join(match_result[2])
	doc.save(ignore_permissions = True)
	doc.reload()

def apply_approximation(gstr2b_invoice_no, pr_invoice_no):
	if '-' in gstr2b_invoice_no and not '-' in pr_invoice_no:
		if gstr2b_invoice_no.strip('-') == pr_invoice_no:
			return True
	if '/' in gstr2b_invoice_no and not '/' in pr_invoice_no:
		if gstr2b_invoice_no.strip('/') == pr_invoice_no:
			return True
	if gstr2b_invoice_no.strip('0') == pr_invoice_no:
		return True
	if pr_invoice_no.isnumeric() and gstr2b_invoice_no.isalnum():
		current_gstr2b_invoice_no = re.sub('\D', '', gstr2b_invoice_no)
		if pr_invoice_no.replace(' ','') == current_gstr2b_invoice_no:
			return True
		if current_gstr2b_invoice_no.strip('0') == pr_invoice_no.replace(' ',''):
			return True
	if pr_invoice_no in gstr2b_invoice_no:
		return True
	return False

@frappe.whitelist()
def rematch_results(uploaded_doc_name):
	job_name = uploaded_doc_name + 'Rematch Results'
	enqueued_jobs = [d.get("job_name") for d in get_info()]
	if job_name in enqueued_jobs:
		frappe.msgprint(
			_("Rematching already in progress. Please wait for sometime.")
		)
	else:
		enqueue(
			link_documents,
			queue = "default",
			timeout = 6000,
			event = 'link_documents',
			uploaded_doc_name = uploaded_doc_name,
			job_name = job_name
		)
		frappe.msgprint(
			_("Rematching job added to the queue. Please check after sometime.")
		)