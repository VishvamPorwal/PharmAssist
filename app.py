#imports
from flask import Flask, render_template, redirect, request, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user




# from admin.admin import admin
# from admin_credentials import admin_email, admin_password


app = Flask(__name__)
# app.register_blueprint(admin, url_prefix = "/admin")


app.secret_key = "tirpaal"


#db configuration
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///db.sqlite3'


db = SQLAlchemy(app)



#flask mail config
app.config["MAIL_DEFAULT_SENDER"] = ""
app.config["MAIL_PASSWORD"] = ""
app.config["MAIL_PORT"] = 587
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = ""
mail = Mail(app)


#flask login config
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'You need to log in'



#Database Structure

##pharmacists name table
class Pharmacists(UserMixin, db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	email = db.Column(db.String(100))
	pwd = db.Column(db.String(100))
	address = db.Column(db.String(200))
	phone_number = db.Column(db.String(12))
	inventory = db.relationship('Inventory', backref='owner')
	sales = db.relationship('Sales', backref='salesman')
	pharmacist_b_s = db.relationship('Pharmacist_B_S', backref='salesman')

@login_manager.user_loader
def load_user(user_id):
    return Pharmacists.query.get(int(user_id))


##medicines inventory table
class Inventory(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	med_name = db.Column(db.String(100))
	entry_date = db.Column(db.DateTime)
	expiry_date = db.Column(db.DateTime)
	stock = db.Column(db.Integer)
	symptoms = db.Column(db.String(300))
	rate_per_tab_bought = db.Column(db.Float)
	rate_per_tab_sell = db.Column(db.Float)
	sold = db.Column(db.Float)
	owner_id = db.Column(db.Integer, db.ForeignKey('pharmacists.id'))



#sales record table
class Sales(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	med_name = db.Column(db.String(100))
	no_of_tabs = db.Column(db.Integer)
	sale_price = db.Column(db.Float)
	selling_date = db.Column(db.DateTime)
	profit = db.Column(db.Float)
	buyer_id = db.Column(db.Integer, db.ForeignKey('customer.id'))
	salesman_id = db.Column(db.Integer, db.ForeignKey('pharmacists.id'))

#customer
class Customer(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	order = db.relationship('Sales', backref='buyer')


#total bought and sold
class Pharmacist_B_S(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	salesman_id = db.Column(db.Integer, db.ForeignKey('pharmacists.id'))
	total_bought = db.Column(db.Float)
	total_sold = db.Column(db.Float)
	

#adding data in tables
##pharmacists
def add_pharmacist(name, email, pwd, address, phone_number):
	"""
	function to add pharmacist
	usage:
		add_pharmacist("alex","alex@alex.com","xela","columbia","1234567891")
	"""	
	pharma = Pharmacists.query.filter_by(email = email).first() #if already exist
	if pharma is not None:
		return 0
	else: #new user
		session.permanent = True
		pharmacist = Pharmacists(name = name, email = email, pwd = pwd, address = address, phone_number = phone_number)
		db.session.add(pharmacist)
		db.session.commit()
		pharmacist_bs = Pharmacist_B_S(salesman_id = pharmacist.id, total_sold = 0.0, total_bought = 0.0)
		db.session.add(pharmacist_bs)
		db.session.commit()
		session["id"] = pharmacist.id
		# message = Message("You are registered in PharmaAssist!!", sender = 'edukid2021@gmail.com', recipients = [email])
		# message.body = f"Hello,{name}. We from PharmaAssist welcome you to our family. : )"
		# mail.send(message)
		return 1

##inventory
def add_med(med_name, expiry_date, stock, symptoms, rate_per_tab_bought, rate_per_tab_sell):
	"""
	function to add rows in inventory
	Usage:
		add_med("example@example.com", "Crocin", "100", "30/02/2025", "500", "Headache, fever")
	"""
	today = datetime.datetime.now()
	med_name = med_name.capitalize()
	# pharmacist = Pharmacists.query.filter_by(id = session['id']).first()
	# ph_id = session["ph_id"]
	inventory = Inventory(owner_id = session['id'], med_name = med_name, entry_date = today.date(), expiry_date = expiry_date, stock = stock, symptoms = symptoms, rate_per_tab_bought = rate_per_tab_bought, rate_per_tab_sell = rate_per_tab_sell, sold = None)
	db.session.add(inventory)
	db.session.commit()
	pharmacist_bs = Pharmacist_B_S.query.filter_by(salesman_id = session['id']).first()
	pharmacist_bs.total_bought += (inventory.rate_per_tab_bought * inventory.stock) 
	db.session.commit()


##customer
def add_customer(name):
	name = name.capitalize()
	customer = Customer(name = name)
	db.session.add(customer)
	db.session.commit()



##sales record
def add_sale_record(med_name, no_of_tabs, sale_price, profit, some_customer, some_pharamacist):
	today = datetime.datetime.now()
	
	sale = Sales(med_name = med_name, no_of_tabs = no_of_tabs, sale_price = sale_price, selling_date = today, profit = profit, buyer = some_customer, salesman = some_pharamacist)
	db.session.add(sale)
	db.session.commit()



#functions
##to calculate total bill
def calc_bill(med_list):
	grand_total = 0
	for med, info in med_list.items():
		grand_total += info[1]   
	return grand_total


##to add sales records of a customer
def customer_entry(med_list, customer_name):
	# add_customer(customer_name)
	customer_name = customer_name.capitalize()
	customer = Customer(name = customer_name)
	db.session.add(customer)
	db.session.commit()
	some_pharamacist = Pharmacists.query.filter_by(email = session['email']).first()
	for med, info in med_list.items():
		add_sale_record(med, info[0], info[1], info[2], customer, some_pharamacist)


##to modify the stock after bill ##to check
#med list = [sell_tabs, ]
def modify_stock(inventory, med_list):
	for med, info in med_list.items():
		for inven in inventory:
			if inven.med_name == med:
				inven.stock -= info[0]
				if(inven.sold == None):
					inven.sold = 0
				inven.sold += info[1]
				pharmacist_bs = Pharmacist_B_S.query.filter_by(salesman_id = session['id']).first()
				pharmacist_bs.total_sold += info[1]
				db.session.commit()
				break
	return inventory

#unique inventory
def unique_meds(inventory_list):
    s = set()
    for i in inventory_list:
        s.add(i.med_name)
    return s

##
def calc_start(y, m):
	return datetime.datetime(y, m, 1)


def calc_end(y, m):
	if m==2:
		if (y % 4) == 0:
			if (y % 100) == 0:
				if (y % 400) == 0:
				   return datetime.datetime(y,m,29)
				else:
				   return datetime.datetime(y,m,28)
			else:
				return datetime.datetime(y,m,29)
		else:
			return datetime.datetime(y,m,28)
	else:
		if m<=7:
			if m%2==0:
				return datetime.datetime(y,m,30)
			else:
				return datetime.datetime(y,m,31)
		else:
			if m%2==0:
				return datetime.datetime(y,m,31)
			else:
				return datetime.datetime(y,m,30)






##total profit between begin and end
def total_profit_bw_b_e(begin = "2021-03-01", end = "2021-03-31"):
	return db.session.query(db.func.sum(Sales.profit)).filter(Sales.selling_date > begin, Sales.selling_date < end, Sales.salesman_id == session['id']).scalar()


def total_sales_bw_b_e(begin = "2021-03-01", end = "2021-03-31"):
	return db.session.query(db.func.sum(Sales.sale_price)).filter(Sales.selling_date > begin, Sales.selling_date < end, Sales.salesman_id == session['id']).scalar()



def calc_profit(y):
	profit_yearly = list()
	for i in range(1, 13):
		beg = calc_start(y, i)
		e = calc_end(y, i)
		temp = total_profit_bw_b_e(beg, e)
		if temp is None:
			temp = 0
		profit_yearly.append(temp)
	return profit_yearly


def calc_sales(y):
	sales_yearly = list()
	for i in range(1, 13):
		beg = calc_start(y, i)
		e = calc_end(y, i)
		temp = total_sales_bw_b_e(beg, e)
		if temp is None:
			temp = 0
		sales_yearly.append(temp)
	return sales_yearly



def get_b():
	pharmacist_bs = Pharmacist_B_S.query.filter_by(salesman_id = session['id']).first()
	return pharmacist_bs.total_bought


def get_s():
	pharmacist_bs = Pharmacist_B_S.query.filter_by(salesman_id = session['id']).first()
	return pharmacist_bs.total_sold


#routes

##index
@app.route("/")
@login_required
def index():
	return redirect(url_for("home"))



##home
@app.route("/home")
@login_required
def home():
	return render_template("login.html")



##signup
@app.route("/signup", methods = ['GET', 'POST'])
def signup():
	if request.method == "POST":
		name = request.form.get("name")
		email = request.form.get("email")
		pwd = request.form.get("pwd")
		pwd_rep = request.form.get("pwd_rep")
		address = request.form.get("address")
		phone_number = request.form.get("phone_number")
		if pwd != pwd_rep:                      #if passwords dont match
		    flash("Passwords dont match")
		    return redirect("signup")
		pwd = generate_password_hash(pwd, method='sha256')
		if not (add_pharmacist(name, email, pwd, address, phone_number)):
			flash("Email already taken")
			return redirect(url_for("signup"))
		flash("Signup successful!")
		return redirect(url_for("login"))
	else:
		return render_template("login.html")



##login
@app.route('/login', methods=['POST', 'GET'])
def login():
	if request.method == "POST":
		email = request.form.get("email")
		psw = request.form.get("psw")
		# if email == admin_email:
		# 	if psw == admin_password:
		# 		return redirect(url_for("admin.records"))
		try:
			pharmacist = Pharmacists.query.filter_by(email = email).first()

			if (not (check_password_hash(pharmacist.pwd, psw))):
				flash("Wrong Password!!")
				return redirect(url_for('login'))
			else:
				flash("Logged in successfully!")
				login_user(pharmacist)
				session['email'] = email
				session['id'] = pharmacist.id
				if 'next' in session:
					next = session['next']
					return redirect(next)


				return redirect(url_for('add_medicine'))
		except:
			flash("You have not registered yet!")
			return redirect(url_for('login'))
	else:
		return render_template("login.html")



#add med

@app.route("/add_medicine", methods = ['GET', 'POST'])
@login_required
def add_medicine():
	if request.method == "POST":
		#med_name, expiry_date, stock, symptoms, rate_per_tab_bought, rate_per_tab_sell
		med_name = request.form.get("med_name")
		expiry_date = request.form.get("expiry_date")
		expiry_date = datetime.datetime.strptime(expiry_date, '%Y-%m-%d')
		stock = request.form.get("stock")
		symptoms = request.form.get("symptoms")
		rate_per_tab_bought = request.form.get("rate_per_tab_bought")
		rate_per_tab_sell = request.form.get("rate_per_tab_sell")
		add_med(med_name, expiry_date.date(), stock, symptoms, rate_per_tab_bought, rate_per_tab_sell)
		flash("Medicine added successfully!")
		return redirect(url_for("add_medicine"))
	else:
		return render_template("add_medicine.html")


#billing # to test modify
med_list = dict()

@app.route("/billing", methods = ['GET', 'POST'])
@login_required
def billing():
	# inventory_list = Inventory.query.filter(Inventory.ph_id==session["ph_id"]).all()
	# print(inventory_list[1].med_name)
	inventory_list = Inventory.query.filter_by(owner_id = session['id']).all()
	if request.method == 'POST':
		if "customer_name" not in session:
			customer_name = request.form.get("name")
			session["customer_name"] = customer_name
			return redirect("billing")
		else:
			if request.form["action"] == "add":
				med_name = request.form.get("med_name")
				no_tabs = request.form.get("no_tabs")
				no_tabs = int(no_tabs)
				try:
					# pharmacist = Pharmacists.query.filter_by(email = session['email']).first()
					Stock = Inventory.query.filter_by(med_name = med_name, owner_id = session['id']).first()
					if(Stock.stock < no_tabs):
						flash(f"you have only {Stock.stock} of {Stock.med_name}")
						return redirect(url_for("billing"))
					elif(Stock.expiry_date < datetime.datetime.now()):
						flash(f"{Stock.med_name} expired. It is now no more in your inventory.")
						db.session.delete(Stock)
						db.session.commit()
						return redirect(url_for("billing"))
					else:
						flash("added in bill")
						tot_price = Stock.rate_per_tab_sell * no_tabs
						profit = (Stock.rate_per_tab_sell - Stock.rate_per_tab_bought) * no_tabs
						values = []
						values.append(no_tabs)
						values.append(tot_price)
						values.append(profit)
						med_list[med_name] = values
						return redirect(url_for("billing"))
						# return render_template("billing.html", is_named_in = True, med_list = med_list, customer_name = session["customer_name"], inventory_list = inventory_list)
				except:
					flash("Medicine not found")
					return redirect(url_for("billing"))
					# return render_template("billing.html", is_named_in = True, med_list = med_list, customer_name = session["customer_name"], inventory_list = inventory_list)
				
			elif request.form["action"] == "clear":
				med_list.clear()
				return redirect(url_for("billing"))
				# return render_template("billing.html", is_named_in = True, med_list = med_list, customer_name = session["customer_name"], inventory_list = inventory_list)
			else:
				customer_name = session["customer_name"]
				total_bill = calc_bill(med_list)
				# inventory_for_pr = Inventory.query.filter_by(owner_id = session['id'])
				customer_entry(med_list, customer_name)
				inventory = Inventory.query.filter_by(owner_id = session['id'])
				inventory = modify_stock(inventory, med_list)
				db.session.commit()
				session.pop("customer_name", None)
				return render_template("bill.html", total_bill = total_bill, med_list = med_list, customer_name = customer_name)
	else:
		if "customer_name" not in session:
			med_list.clear()
			return render_template("billing.html", is_named_in = False)
		else:
			return render_template("billing.html", is_named_in = True, med_list = med_list, customer_name = session["customer_name"], inventory_list = unique_meds(inventory_list))



##inventory
@app.route("/inventory", methods=['POST', 'GET'])
@login_required
def inventory():
	# pharmacist = Pharmacists.query.filter_by(email = session['email']).first()
	inventory_list = Inventory.query.filter_by(owner_id = session['id']).all()
	if request.method == 'POST':
		try : 
			med_name = request.form.get("med_name")
			query_for_med = Inventory.query.filter_by(med_name = med_name, owner_id = session['id']).all()
			return render_template("display_query.html", query_for_med = query_for_med)
		except:
			flash("Medicine not found!!")
			return redirect(url_for("inventory"))
	else:
		return render_template("inventory.html", inventory_list = inventory_list)


##delete/jump to edit - inventory
@app.route("/edit", methods = ['POST'])
@login_required
def edit():
	inventory_list = Inventory.query.filter_by(owner_id = session['id']).all()
	in_id = list(request.form.to_dict().keys())
	in_id = in_id[0]
	in_id = int(in_id)
	
	for item in inventory_list:
		if item.id == in_id:
			if request.form[str(in_id)] == "delete":
				return render_template("confirm_del.html", in_id = str(in_id))
				# flash(f"{request.form.to_dict().keys()}")
				# return redirect(url_for("inventory"))

			else:
				return render_template("edit.html", query_for_med = item)
	

#are you sure to delete
@app.route("/are_you_sure", methods = ['POST'])
def are_you_sure():
	inventory_list = Inventory.query.filter_by(owner_id = session['id']).all()
	in_id = list(request.form.to_dict().keys())
	in_id = in_id[0]
	in_id = int(in_id)
	for item in inventory_list:
		if item.id == in_id:
			if request.form[str(in_id)] == "delete":
				db.session.delete(item)
				db.session.commit()
				# flash(f"{request.form.to_dict().keys()}")
				return redirect(url_for("inventory"))
			else:
				return redirect(url_for("inventory"))





##edit
@app.route("/edited", methods = ['POST'])
@login_required
def edited():
	in_id = list(request.form.to_dict().keys())
	in_id = in_id[-2]
	in_id = int(in_id)
	med_to_modify = Inventory.query.filter_by(id = in_id).first()
	if (request.form.get("med_name")) != "":
		med_to_modify.med_name = (request.form.get("med_name"))
	if request.form.get("expiry_date") != "":
		expiry_date = request.form.get("expiry_date")
		expiry_date = datetime.datetime.strptime(expiry_date, '%Y-%m-%d')
		med_to_modify.expiry_date = expiry_date
	if request.form.get("stock") != "":
		med_to_modify.stock = request.form.get("stock")
	if request.form.get("symptoms") != "":
		med_to_modify.symptoms = request.form.get("symptoms")
	if request.form.get("rate_per_tab_sell") != "":
		med_to_modify.rate_per_tab_sell = request.form.get("rate_per_tab_sell")
	db.session.commit()
	return redirect(url_for("inventory"))




@app.route("/dashboard", methods = ['GET', 'POST'])
@login_required
def dashboard():
	option_years = []
	total_bought = get_b()
	total_sold = get_s()
	year = datetime.datetime.now().year
	for tmp in range(2021, year+1):
		option_years.append(tmp)
	if request.method == "POST":
		year = request.form.get("year")
		year = int(year)
		prof_p_m = calc_profit(year)
		sales_p_m = calc_sales(year)
		# print(sales_p_m)
		return render_template("dashboard.html", year = year, prof_p_m = prof_p_m, sales_p_m = sales_p_m, total_sold = total_sold, total_bought = total_bought, option_years = option_years)
		
	
	prof_p_m = calc_profit(year)
	sales_p_m = calc_sales(year)

	# sales_p_m = [3,4,5,6,7,8,9,5,3,1,5,3]
	# print(sales_p_m)
	return render_template("dashboard.html", year = year, prof_p_m = prof_p_m, sales_p_m = sales_p_m, total_sold = total_sold, total_bought = total_bought, option_years = option_years)




##logout
@app.route('/logout')
@login_required
def logout():
	logout_user()
	session.pop("email", None)
	session.pop("id", None)
	return redirect(url_for('signup'))


#driver code
if __name__== "__main__":
	# print(calc_sales(2021))
	db.create_all()
	app.run(debug=True)
