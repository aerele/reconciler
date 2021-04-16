// Copyright (c) 2021, Aerele Technologies Private Limited and contributors
// For license information, please see license.txt

frappe.ui.form.on('CD GSTR 2B Entry', {
	refresh: function(frm) {
		if(!frm.doc.__islocal){ 
			frm.add_custom_button(__("Link Supplier"), function() {
			 frm.trigger('link_supplier');
			});
			if(frm.doc.cf_purchase_invoice){ 
				frm.add_custom_button(__("Unlink PR"), function() {
				 frm.trigger('unlink_pr');
			 });}
			frm.add_custom_button(__("Rematch result"), function() {
			 frm.trigger('rematch_result');
		 });}
	},
	link_supplier: function(frm){
		frappe.call({
			method: "reconciler.reconciler.doctype.cd_gstr_2b_entry.cd_gstr_2b_entry.link_supplier",
			freeze: true,
			freeze_message: __("Processing..."),
			args: {doc_name:frm.doc.name}
		})
	},
	rematch_result: function(frm){
		frappe.call({
			method: "reconciler.reconciler.doctype.cd_gstr_2b_entry.cd_gstr_2b_entry.rematch_result",
			freeze: true,
			freeze_message: __("Processing..."),
			args: {doc_name:frm.doc.name}
		})
	},
	unlink_pr: function(frm){
		if (frm.doc.cf_match_status){
		if (frm.doc.cf_status == 'Accepted'){
		frappe.confirm(__('This action will overwrite the status. Are you sure you want to unlink this accepted document?'),
		function() {
			frappe.call({
				method: "reconciler.reconciler.doctype.cd_gstr_2b_entry.cd_gstr_2b_entry.unlink_pr",
				freeze: true,
				freeze_message: __("Processing..."),
				args: {doc_name:frm.doc.name},
				callback: function(r) {
					frm.reload_doc();
					frappe.msgprint(__("PR Unlinked successfully"))
				}
			})
		}
	);
		}
	else{
		frappe.call({
			method: "reconciler.reconciler.doctype.cd_gstr_2b_entry.cd_gstr_2b_entry.unlink_pr",
			freeze: true,
			freeze_message: __("Processing..."),
			args: {doc_name:frm.doc.name},
			callback: function(r) {
				frm.reload_doc();
				frappe.msgprint(__("PR Unlinked successfully"))
			}
		})
	}
	}
}
});
