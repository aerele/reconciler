// Copyright (c) 2021, Aerele Technologies Private Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('CD GSTR 2A Entry', {
	refresh: function(frm) {
		if(!frm.doc.__islocal){ 
			frm.add_custom_button(__("Update Entry"), function() {
			 frm.trigger('update_entry');
		 });}
	},
	update_entry: function(frm){
		frappe.call({
			method: "reconciler.reconciler.doctype.cd_gstr_2a_entry.cd_gstr_2a_entry.update_entry",
			freeze: true,
            args: {doc_name:frm.doc.name},
			callback: function(r) {
				frm.reload_doc();
				frappe.msgprint(__("Updated successfully"))
			}
		})
	}
});
