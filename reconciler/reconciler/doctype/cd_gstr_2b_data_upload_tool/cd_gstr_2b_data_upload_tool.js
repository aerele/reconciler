// Copyright (c) 2021, Aerele Technologies Private Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('CD GSTR 2B Data Upload Tool', {
	refresh: function(frm){
		frm.trigger("show_summary");
		if(frm.doc.cf_is_matching_completed){ 
		frm.add_custom_button(("Rematch Results"), function() {
			frm.trigger('rematch_results');
		});
	}
	},
  rematch_results: function(frm){
    frappe.call({
      method: "reconciler.reconciler.doctype.cd_gstr_2b_data_upload_tool.cd_gstr_2b_data_upload_tool.rematch_results",
      freeze: true,
      args: {uploaded_doc_name:frm.doc.name}
    })
	},
	show_summary: function(frm) {
		let total_taxable_amount = frm.doc.__onload.total_taxable_amount;
		let total_tax_amount = frm.doc.__onload.total_tax_amount;
		let match_summary = frm.doc.__onload.match_summary;
		if(frm.doc.cf_no_of_newly_created_entries) {
			let section = frm.dashboard.add_section(
				frappe.render_template('cd_gstr2b_match_summary', {
					data: match_summary,
					total_tax_amount: total_tax_amount,
					total_taxable_amount : total_taxable_amount
				})
			);
			frm.dashboard.show();
		}
	},
	cf_gst_state: function(frm){
		frappe.call({
			method:"reconciler.reconciler.doctype.cd_gstr_2b_data_upload_tool.cd_gstr_2b_data_upload_tool.get_gstin_for_company",
			args:{company: frm.doc.cf_company, gst_state: frm.doc.cf_gst_state},
			callback: function(r){
				if (r.message){
					frm.set_value("cf_company_gstin",r.message)
				}
				else {
					frm.set_value("cf_company_gstin","")
				}
			}
		})
	}
});
