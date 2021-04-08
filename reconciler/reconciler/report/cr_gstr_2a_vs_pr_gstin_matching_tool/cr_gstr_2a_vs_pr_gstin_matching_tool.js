// Copyright (c) 2016, Aerele Technologies Private Limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CR GSTR 2A vs PR GSTIN Matching Tool"] = {
	"filters": [
		{
			fieldname: "cf_company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "cf_gst_state",
			label: __("GST State"),
			fieldtype: "Select",
			options: [
				'Andaman and Nicobar Islands',
				'Andhra Pradesh',
				'Arunachal Pradesh',
				'Assam',
				'Bihar',
				'Chandigarh',
				'Chhattisgarh',
				'Dadra and Nagar Haveli and Daman and Diu',
				'Delhi',
				'Goa',
				'Gujarat',
				'Haryana',
				'Himachal Pradesh',
				'Jammu and Kashmir',
				'Jharkhand',
				'Karnataka',
				'Kerala',
				'Ladakh',
				'Lakshadweep Islands',
				'Madhya Pradesh',
				'Maharashtra',
				'Manipur',
				'Meghalaya',
				'Mizoram',
				'Nagaland',
				'Odisha',
				'Other Territory',
				'Pondicherry',
				'Punjab',
				'Rajasthan',
				'Sikkim',
				'Tamil Nadu',
				'Telangana',
				'Tripura',
				'Uttar Pradesh',
				'Uttarakhand',
				'West Bengal'],
			reqd: 1,
			on_change: () => {
				frappe.call({
					method:"reconciler.reconciler.doctype.cd_gstr_2a_data_upload_tool.cd_gstr_2a_data_upload_tool.get_gstin_for_company",
					args:{company: frappe.query_report.get_filter_value('cf_company'), gst_state: frappe.query_report.get_filter_value('cf_gst_state')},
					callback: function(r){
						if (r.message){
							frappe.query_report.set_filter_value("cf_company_gstin",r.message);
						}
						else {
							frappe.query_report.set_filter_value("cf_company_gstin","");
						}
					}
				})
			},
		},	
		{
			fieldname: "cf_company_gstin",
			label: __("Company GSTIN"),
			fieldtype: "Data",
			reqd: 1,
			read_only: 1
		},	
		{
			fieldname: "cf_from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			reqd: 1
		},
		{
			fieldname:"cf_to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			reqd: 1
		},
		{
			fieldname: "cf_transaction_type",
			label: __("Transaction Type"),
			fieldtype: "Select",
			options: ['','Invoice', 'CDN']
		},
		{
			fieldname: "cf_view_type",
			label: __("View Type"),
			fieldtype: "Select",
			options: ['Supplier View', 'Document View'],
			default: 'Supplier View',
			reqd: 1
		},
		{
			fieldname: "cf_supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: 'Supplier',
			depends_on:  "eval:doc.cf_view_type == 'Document View'"
		},
		{
			fieldname: "cf_match_status",
			label: __("Match Status"),
			fieldtype: "Select",
			options: ["Exact Match", "Suggested", "Mismatch", "Missing in PR", "Missing in 2A"],
			depends_on:  "eval:doc.cf_view_type == 'Document View'"
		}
	],
	after_datatable_render: function(datatable_obj) {
		$(datatable_obj.wrapper).find(".dt-row-0").find('input[type=checkbox]');
	},
	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true
		});
	},
	onload: function(query_report) {
	query_report.page.clear_menu();
	query_report.page.add_action_item(__("✔️ Accept system values"), () => {
		var selected_rows = [];
		let is_selected = false;
			$('.dt-scrollable').find(":input[type=checkbox]").each((idx, row) => {
				if(row.checked){
					is_selected = true;
					selected_rows.push({'gstr_2a':frappe.query_report.data[idx]['gstr_2a']});
				}
			});
			if(is_selected == false)
			{
				frappe.throw(__("Please select rows to update status"));
				return
			}
			else{
			frappe.call('reconciler.reconciler.report.cr_gstr_2a_vs_pr_gstin_matching_tool.cr_gstr_2a_vs_pr_gstin_matching_tool.update_status', {
				data: selected_rows,
				status: 'Accept system values',
				freeze: true
			}).then(r => {
				frappe.msgprint(__("Status Updated"));
			});
		}
	})
	query_report.page.add_action_item(__("✔️ Accept gstr2a values"), () => {
		var selected_rows = [];
		let is_selected = false;
			$('.dt-scrollable').find(":input[type=checkbox]").each((idx, row) => {
				if(row.checked){
					is_selected = true;
					selected_rows.push({'gstr_2a':frappe.query_report.data[idx]['gstr_2a']});
				}
			});
			if(is_selected == false)
			{
				frappe.throw(__("Please select rows to update status"));
				return
			}
			else{
			frappe.call('reconciler.reconciler.report.cr_gstr_2a_vs_pr_gstin_matching_tool.cr_gstr_2a_vs_pr_gstin_matching_tool.update_status', {
				data: selected_rows,
				status: 'Accept gstr2a values',
				freeze: true
			}).then(r => {
				frappe.msgprint(__("Status Updated"));
			});
		}
	})
	query_report.page.add_action_item(__("⌛Pending"), () => {
		var selected_rows = [];
		let is_selected = false;
			$('.dt-scrollable').find(":input[type=checkbox]").each((idx, row) => {
				if(row.checked){
					is_selected = true;
					selected_rows.push({'gstr_2a':frappe.query_report.data[idx]['gstr_2a']});
				}
			});
			if(is_selected == false)
			{
				frappe.throw(__("Please select rows to update status"));
				return
			}
			else{
			frappe.call('reconciler.reconciler.report.cr_gstr_2a_vs_pr_gstin_matching_tool.cr_gstr_2a_vs_pr_gstin_matching_tool.update_status', {
				data: selected_rows,
				status: 'Pending',
				freeze: true
			}).then(r => {
				frappe.msgprint(__("Status Updated"));
			});
		}
	})
}
}
var render = function(tax_details, other_details, dialog) {
	let tax_details_summary = () => {
		let summary = ``
		$.each(tax_details, function(i, d) {
			summary+=`
				<tr>
					<td>${i}</td>`
			for (let key in d) {
				summary+=`
					<td>${d[key]}</td>`
			}
			summary+=`</tr>`
		});
		return `
			<div>
				<table class="table table-bordered">
					<tr>
						<th width="20%">${__('Data Source')}</th>
						<th width="10%">${__('Taxable Value')}</th>
						<th width="10%">${__('Tax Value')}</th>
						<th width="10%">${__('IGST')}</th>
						<th width="10%">${__('CGST')}</th>
						<th width="10%">${__('SGST')}</th>
						<th width="10%">${__('CESS')}</th>
					</tr>
					${summary}
				</table>
			</div>
		`;
	}

	let other_details_summary = () => {
		let summary = ``
		$.each(other_details, function(i, d) {
			summary+=`
				<tr>
					<td>${i}</td>`
			for (let key in d) {
				summary+=`
					<td>${d[key]}</td>`
			}
			summary+=`</tr>`
		});
		return `
			<div>
				<table class="table table-bordered">
					<tr>
						<th width="20%">${__('Data Source')}</th>
						<th width="10%">${__('Doc No')}</th>
						<th width="10%">${__('Date')}</th>
						<th width="10%">${__('POS')}</th>
						<th width="10%">${__('Reverse Charge')}</th>
					</tr>
					${summary}
				</table>
			</div>
		`;
	}
	let html = `
		${tax_details_summary()}
		${other_details_summary()}
	`;

	dialog.get_field('preview_html').html(html);
}

var update_status= function(gstr2a, purchase_inv) {
	var dialog = new frappe.ui.Dialog({
		title: __("Selection Summary"),
		fields: [
			{
				"label": "Preview",
				"fieldname": "preview_html",
				"fieldtype": "HTML"
			},
			{
				"label": "Action",
				"fieldname": "action",
				"fieldtype": "Select",
				"reqd": 1,
				"options": ['Accept System Value', 'Accept GSTR2A Value', 'Pending']
			}
		],
		primary_action: function() {
			frappe.call('reconciler.reconciler.report.cr_gstr_2a_vs_pr_gstin_matching_tool.cr_gstr_2a_vs_pr_gstin_matching_tool.update_status', {
				data: [{'gstr_2a': gstr2a}],
				status: dialog.fields_dict.action.value
			}).then(r => {
				frappe.msgprint(__("Status Updated"));
			});
			dialog.hide();
		},
		primary_action_label: __('Update'),
	});
	frappe.call('reconciler.reconciler.report.cr_gstr_2a_vs_pr_gstin_matching_tool.cr_gstr_2a_vs_pr_gstin_matching_tool.get_selection_details', {
		gstr2a: gstr2a,
		purchase_inv: purchase_inv,
		show_tax: 1,
		freeze: true
	}).then(r => {
		this.render(r.message[0], r.message[1], dialog);
	});
	dialog.get_field('preview_html').html('Loading...');
	dialog.show();
	dialog.$wrapper.find('.modal-dialog').css("width", "800px");
}

var create_purchase_inv= function(gstr2a, purchase_inv) {
	var dialog = new frappe.ui.Dialog({
		title: __("Selection Summary"),
		fields: [
			{
				"label": "Preview",
				"fieldname": "preview_html",
				"fieldtype": "HTML"
			}
		],
		primary_action: function() {
			frappe.show_progress('Creating Purchase Invoice..', 70, 100, 'Please wait');
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "CD GSTR 2A Entry",
					name: gstr2a,
				},
				callback(r) {
					if(r.message) {
						var gstr2a_doc = r.message;
						frappe.new_doc("Purchase Invoice",{"company": gstr2a_doc.cf_company},
						doc => {doc.bill_no = gstr2a_doc.cf_invoice_number,
						doc.supplier = frappe.query_report.get_filter_value('cf_supplier'),
						doc.bill_date = gstr2a_doc.cf_invoice_date,
						doc.reverse_charge = gstr2a_doc.cf_reverse_charge, 
						doc.gst_category = gstr2a_doc.cf_invoice_type,
						doc.place_of_supply = gstr2a_doc.cf_place_of_supply,
						doc.grand_total = gstr2a_doc.cf_invoice_amount,
						doc.taxes_and_charges_added = gstr2a_doc.cf_tax_amount,
						doc.total = gstr2a_doc.cf_taxable_amount,
						doc.supplier_gstin = gstr2a_doc.party_gstin,
						doc.company_gstin = gstr2a_doc.company_gstin});
					}
				}
			});
			dialog.hide();
		},
		primary_action_label: __('Create')
	});
	frappe.call('reconciler.reconciler.report.cr_gstr_2a_vs_pr_gstin_matching_tool.cr_gstr_2a_vs_pr_gstin_matching_tool.get_selection_details', {
		gstr2a: gstr2a,
		purchase_inv: purchase_inv,
		show_tax: 1,
		freeze: true
	}).then(r => {
		this.render(r.message[0], r.message[1], dialog);
	});
	dialog.get_field('preview_html').html('Loading...');
	dialog.show();
	dialog.$wrapper.find('.modal-dialog').css("width", "800px");
}