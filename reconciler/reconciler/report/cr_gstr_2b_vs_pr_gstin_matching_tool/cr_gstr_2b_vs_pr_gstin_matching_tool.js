// Copyright (c) 2016, Aerele Technologies Private Limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["CR GSTR 2B vs PR GSTIN Matching Tool"] = {
	"filters": [
		{
			fieldname: "company",
			label: __("Company"),
			fieldtype: "Link",
			options: "Company",
			default: frappe.defaults.get_user_default("Company"),
			reqd: 1
		},
		{
			fieldname: "gst_state",
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
					method:"reconciler.reconciler.doctype.cd_gstr_2b_data_upload_tool.cd_gstr_2b_data_upload_tool.get_gstin_for_company",
					args:{company: frappe.query_report.get_filter_value('company'), gst_state: frappe.query_report.get_filter_value('gst_state')},
					callback: function(r){
						if (r.message){
							frappe.query_report.set_filter_value("company_gstin",r.message);
						}
						else {
							frappe.query_report.set_filter_value("company_gstin","");
						}
					}
				})
			},
		},	
		{
			fieldname: "company_gstin",
			label: __("Company GSTIN"),
			fieldtype: "Data",
			reqd: 1,
			read_only: 1
		},	
		{
			fieldname: 'based_on',
			label: __('Based On'),
			fieldtype: 'Select',
			options: ['Date', 'Return Period'],
			default: 'Date',
			reqd: 1,
			on_change: () => {
				var based_on = frappe.query_report.get_filter_value('based_on');
				if (based_on == 'Return Period'){
				frappe.call({
					method : 'reconciler.reconciler.report.cr_gstr_2b_vs_pr_gstin_matching_tool.cr_gstr_2b_vs_pr_gstin_matching_tool.return_period_query',
					freeze : true,
					callback: function(r) {
						if(r.message) {
							let return_periods = r.message
							let options = []
							for(let option of return_periods){
								options.push({
									"value":option,
									"description":""
								})
							}
							var return_period = frappe.query_report.get_filter('return_period');
							return_period.df.options = options;
							return_period.refresh();
						}
					}
				});

				}
		}
		},
		{
			fieldname: "from_date",
			label: __("From Date"),
			fieldtype: "Date",
			default: frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			depends_on:  "eval:doc.based_on == 'Date'"
		},
		{
			fieldname:"to_date",
			label: __("To Date"),
			fieldtype: "Date",
			default: frappe.datetime.get_today(),
			depends_on:  "eval:doc.based_on == 'Date'"
		},
		{
			fieldname: "return_period",
			label: __("Return Period"),
			fieldtype: "Select",
			depends_on:  "eval:doc.based_on == 'Return Period'"
		},
		{
			fieldname: "transaction_type",
			label: __("Transaction Type"),
			fieldtype: "Select",
			options: ['','Invoice', 'CDN']
		},
		{
			fieldname: "view_type",
			label: __("View Type"),
			fieldtype: "Select",
			options: ['Supplier View', 'Document View'],
			default: 'Supplier View',
			reqd: 1
		},
		{
			fieldname: "supplier",
			label: __("Supplier"),
			fieldtype: "Link",
			options: 'Supplier',
			depends_on:  "eval:doc.view_type == 'Document View'"
		},
		{
			fieldname: "gstin",
			label: __("GSTIN"),
			fieldtype: "Data",
			depends_on:  "eval:doc.view_type == 'Document View'"
		},
		{
			fieldname: "match_status",
			label: __("Match Status"),
			fieldtype: "Select",
			options: ["","Exact Match", "Suggested", "Mismatch", "Missing in PR", "Missing in 2B"],
			depends_on:  "eval:doc.view_type == 'Document View'"
		},
		{
			fieldname: "action",
			label: __("Action"),
			fieldtype: "Select",
			options: ["","Pending", "Accepted"],
			depends_on:  "eval:doc.view_type == 'Document View'"
		}
	],
	get_datatable_options(options) {
		return Object.assign(options, {
			checkboxColumn: true
		});
	}
}
