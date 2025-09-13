frappe.ui.form.on('Task', {
    onload: function (frm) {
        console.log(frappe.user_roles.length, 'roles:', frappe.user_roles);
        if (frappe.user_roles.includes('Checklist User') && !frappe.user_roles.includes('Checklist Admin')) {
            frm.disable_form();
            frm.page.sidebar.toggle(false);
            const toggleIcon = document.querySelector('svg.sidebar-toggle-placeholder');
            if (toggleIcon) {
                toggleIcon.remove();
            }
        }
    }
});
