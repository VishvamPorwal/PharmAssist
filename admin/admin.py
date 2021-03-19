from flask import Blueprint, render_template
import database.database_structure 

admin = Blueprint("admin", __name__, static_folder = "static", template_folder = "templates")



@admin.route("/")
@admin.route("/records", methods = ['POST', 'GET'])
def records():
	pharmacist_list = Pharmacists.query.filter_by().all()
	if request.method == 'POST':
		email = request.form.get("email")
		pharmacist = Pharmacists.query.filter_by(email = email).first()
		inventory_list = Inventory.query.filter_by(owner = pharmacist).all()
		return render_template("pharmacist_inventory.html", inventory_list = inventory_list)
	else:
		return render_template("admin_records.html", pharmacist_list = pharmacist_list)