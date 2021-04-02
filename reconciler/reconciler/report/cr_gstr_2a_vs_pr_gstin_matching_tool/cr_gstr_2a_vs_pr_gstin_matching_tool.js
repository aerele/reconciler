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
			fieldname: "cf_document_type",
			label: __("Document Type"),
			fieldtype: "Select",
			options: ['Invoices', 'CDN'],
			default: 'Invoices',
			reqd: 1
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
	query_report.page.add_action_item(__("✔️ Accept system values"), () => {
	})
	query_report.page.add_action_item(__("✔️ Accept gstr2a values"), () => {
	})
	query_report.page.add_action_item(__("⌛Pending"), () => {
	})
	query_report.page.add_inner_button(__("Start Matching"), () => {
	})
}
}
var render = function(statuswise_count, dialog) {
}

var set_listeners= function() {
}