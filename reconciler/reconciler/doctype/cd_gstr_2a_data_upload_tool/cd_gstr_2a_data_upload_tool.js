// Copyright (c) 2021, Aerele Technologies Private Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('CD GSTR 2A Data Upload Tool', {
	cf_gst_state: function(frm){
		frappe.call({
			method:"reconciler.reconciler.doctype.cd_gstr_2a_data_upload_tool.cd_gstr_2a_data_upload_tool.get_gstin_for_company",
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
