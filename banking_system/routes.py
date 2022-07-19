# from banking_system import app,mysql
from flask import render_template, request, json, Response, flash, redirect, session
from flask import url_for
import os
from banking_system import app, db
from banking_system.model import *
import datetime
from banking_system.functions import *


@app.route('/', methods=['GET', 'POST'])
def home():
    # Allow Login Functionality
    formData = {}
    # If user already login then redirect to customer search page
    if session.get('username'):
        return redirect(url_for('customer_status'))
    if request.method == "POST":
        username = request.form.get('username', None)
        password = request.form.get('password', None)
        formData['username'] = username
        formData['password'] = password
        if username and password:
            hashpassword = password
            if user_obj := UserRegistration.query.filter_by(username=username, password=hashpassword).first():
                session['username'] = user_obj.username
                flash("User login successfully")
                return redirect(url_for('customer_status'))
            else:
                flash("Username or password invalid")
        else:
            flash("Something wents wrong, please contact developer")
    return render_template('index.html', formData=formData)


@app.route('/customer', methods=['GET', 'POST'], defaults={'update_id': None})
@app.route('/customer/<update_id>', methods=['GET', 'POST'])
def customer(update_id):  # sourcery skip: low-code-quality
    # If user not login then redirect to login page
    if not session.get('username'):
        return redirect(url_for('home'))
    # Form list state
    # Set Default Country 1 - India
    states = State.query.filter_by(country_id=1).all()
    formData = {'states': states, 'update_id': update_id}
    # Form Persistence
    if update_id:
        customer_obj = Customer.query.get(update_id)
        postData = {'customer_name': customer_obj.name, 'customer_ssn_id': customer_obj.ssn_id, 'age': customer_obj.age,
                    'address': customer_obj.address, 'state_id': customer_obj.state, 'city_id': customer_obj.city}

        cities = City.query.filter_by(state_id=postData['state_id']).all()
        formData['cities'] = cities
        formData['postForm'] = postData
        del postData
    # Post Request Handle
    if request.method == "POST":
        postData = request.form
        if update_id:
            customerName = postData['customer_name']
            age = postData['age']
            address = postData['address']
            customer_obj = Customer.query.get(update_id)
            customer_obj.age = age
            customer_obj.address = address
            customer_obj.name = customerName
            # Adds new Customer record to database
            db.session.add(customer_obj)
            db.session.commit()  # Commits all changes
            flash("Customer updates successfully")
            # Saved in Customer Status Model
            if update_id:
                customer_status_obj = CustomerStatus(
                    update_id, customer_obj.ssn_id, "Customer update complete")
                # Adds new Customer record to database
                db.session.add(customer_status_obj)
                db.session.commit()  # Commits all changes
                return redirect(url_for('customer_status'))

        else:
            customerSsnId = postData['customer_ssn_id']
            customer_exists = Customer.query.filter_by(
                ssn_id=customerSsnId).count()
            customerSsnId = postData['customer_ssn_id']
            if not customer_exists:
                customerName = postData['customer_name']
                age = postData['age']
                address = postData['address']
                stateId = postData['state_id']
                cityId = postData['city_id']
                formatted_date = get_formatted_date()
                customer_obj = Customer(
                    customerSsnId, customerName, age, address, stateId, cityId, formatted_date)
                # Adds new Customer record to database
                db.session.add(customer_obj)
                db.session.commit()  # Commits all changes
                # Saved in Customer Status Model
                if customer_obj.id:
                    customer_status_obj = CustomerStatus(
                        customer_obj.id, customerSsnId, "Customer created successfully")
                    # Adds new Customer record to database
                    db.session.add(customer_status_obj)
                    db.session.commit()  # Commits all changes
                flash("Customer creation initiated successfully")
                return redirect(url_for('customer_status'))
            else:
                formData['postForm'] = postData
                if postData['state_id']:
                    cities = City.query.filter_by(
                        state_id=postData['state_id']).all()
                    formData['cities'] = cities
                flash("Customer SSN Id already exists")

    return render_template('customer_register.html', formData=formData)


@app.route('/customer-status', methods=['GET', 'POST'])
def customer_status():
    # If user not login then redirect to login page
    if not session.get('username'):
        return redirect(url_for('home'))

    customer_status = Customer.query.outerjoin(CustomerStatus).add_columns(Customer.id, Customer.name, Customer.ssn_id, CustomerStatus.message,
                                                                           CustomerStatus.status, CustomerStatus.updated_at).order_by(Customer.id.asc(), CustomerStatus.updated_at.asc()).all()
    formData = {'customer_status': customer_status}
    return render_template('customer_status.html', formData=formData)


@app.route('/viewprofile', methods=['GET', 'POST'], defaults={'id': None})
@app.route('/viewprofile/<id>', methods=['GET', 'POST'])
def view_profile(id):
    formData = {}
    # If user not login then redirect to login page
    if not session.get('username'):
        return redirect(url_for('home'))
    if customer_obj := Customer.query.get(id):
        formData['customer'] = customer_obj
        formData['update_id'] = id
    else:
        flash("Customer is either delete or customer id not valid")
        return redirect(url_for('customer_status'))
    return render_template('customer_view_profile.html', formData=formData)


@app.route('/create-account', methods=['GET', 'POST'])
def create_account():
    formData = {}
    if request.method == "POST":
        username = request.form.get('username', None)
        password = request.form.get('password', None)
        formData['username'] = username
        formData['password'] = password
        print(username,password)
        if username and password:
            # if user_exists := UserRegistration.query.filter_by(username=username).count():
            #     flash("Username is already present please choose another")
            # else:
            encrypt_password = password
            user_obj = UserRegistration( username, encrypt_password, get_formatted_date())
            db.session.add(user_obj)
            db.session.commit()
            flash("User created successfully")
            return redirect(url_for('home'))
        else:
            flash("Something wents wrong, please contact developer")
    return render_template('registration.html', formData=formData)

# Delete Customer details


@app.route('/ajax/delete_customer', methods=['POST'])
def ajax_delete_customer():
    if not session.get('username'):
        data = {'url': url_for('home'), 'status': True}
        return data
    if request.method == "POST":
        if customer_id := request.form.get('customer_id', 0):
            customer_obj = Customer.query.get(customer_id)
            db.session.delete(customer_obj)
            db.session.commit()
            flash("Customer Details successfully deleted")
        else:
            flash("Something wents wrong, Please try again")
    data = {'status': True, 'url': url_for('customer_status')}
    return data


@app.route('/ajax/change_state', methods=['POST'])
def ajax_change_state():
    # Handle Post Request
    html = ''
    if request.method == "POST":
        state_id = request.form.get('state_id', 0)
        html = '<option value="">Select city..</option>'
        if state_id:
            cities = City.query.filter_by(state_id=state_id).all()
            for city in cities:
                html += f'<option value="{city.id}">{city.name}</option>'
    return {'status': False} if html == '' else {'status': True, 'data': html}


# Acount Profile
@app.route('/cash-deposit', methods=['GET', 'POST'], defaults={'id': None})
@app.route('/cash-deposit/<id>', methods=['GET', 'POST'])
def cash_deposit_account(id):
    formData = {}
    if not session.get('username'):
        return redirect(url_for('home'))
    if id:
        account_obj = Account.query.get(id)
    if account_obj:
        formData['account_obj'] = account_obj
        formData['account_id'] = id
        account_type_lists = account_type_list()
        formData['account_type_list'] = account_type_lists
    else:
        flash("Account is either delete or account not created yet")
        return redirect(url_for('account_search'))
    return render_template('case_deposit.html', formData=formData)


@app.route('/account-status', methods=['GET', 'POST'])
def account_status():
    # If user not login then redirect to login page
    if not session.get('username'):
        return redirect(url_for('home'))
    account_status = Customer.query.outerjoin(AccountStatus).add_columns(AccountStatus.account_id,
                                                                         Customer.id, AccountStatus.account_type, AccountStatus.message,
                                                                         AccountStatus.status, AccountStatus.updated_at).order_by(Customer.id.asc(), AccountStatus.updated_at.asc()).all()
    formData = {'account_status': account_status}
    return render_template('account_status.html', formData=formData)


@app.route('/account-profile', methods=['GET', 'POST'], defaults={'id': None})
@app.route('/account-profile/<id>', methods=['GET', 'POST'])
def account_view_profile(id):
    formData = {}
    # If user not login then redirect to login page
    if not session.get('username'):
        return redirect(url_for('home'))
    # id represent account_id- customer first check corresponding customer , account is available or not
    # if not then return back with error - account create first
    if id:
        account_obj = Account.query.get(id)
    if account_obj:
        formData['account_obj'] = account_obj
        formData['account_id'] = id
        account_type_lists = account_type_list()
        formData['account_type_list'] = account_type_lists
    else:
        flash("Account is either delete or account not created yet")
        return redirect(url_for('account_search'))
    return render_template('account_view_profile.html', formData=formData)


@app.route('/account-search', methods=['GET', 'POST'])
def account_search():
    # If user not login then redirect to login page
    if not session.get('username'):
        return redirect(url_for('home'))
    formData = {'post_url': url_for('account_search')}
    formData['account_type'] = account_type_list()
    if request.method == "POST":
        customer_id = request.form.get('customer_id')
        account_id = request.form.get('account_id')
        account_type_id = request.form.get('account_type', 1)
        if customer_id:
            if account_obj := Account.query.filter_by(customer_id=customer_id, account_type=account_type_id).first():
                return redirect(url_for('account_view_profile')+'/'+str(account_obj.id))
            else:
                flash("Account not found for corresponding customer id")
        elif account_id:
            if account_obj := Account.query.filter_by(id=account_id).first():
                return redirect(url_for('account_view_profile')+'/'+str(account_obj.id))
            else:
                flash("Account not found for corresponding account id")
        else:
            flash("Something went wrong, please contact developer")
    return render_template('account_search.html', formData=formData)

# Delete Account details


@app.route('/ajax/delete_account', methods=['POST'])
def ajax_account_delete():
    # If user not login then redirect to login page
    if not session.get('username'):
        data = {'url': url_for('home'), 'status': True}
        return data
    if request.method == "POST":
        if account_id := request.form.get('account_id', 0):
            account_obj = Account.query.get(account_id)
            db.session.delete(account_obj)
            db.session.commit()
            flash("Account Detail successfully deleted")
        else:
            flash("Something wents wrong, Please try again")
    data = {'status': True, 'url': url_for('account_search')}
    return data

# Deposit Cash


@app.route('/cash-deposit', methods=['GET', 'POST'], defaults={'id': None})
@app.route('/cash-deposit/<id>', methods=['GET', 'POST'])
def cash_deposit(id):
    formData = {}
    # If user not login then redirect to login page
    if not session.get('username'):
        return redirect(url_for('home'))
    # id represent account_id- customer first check corresponding customer , account is available or not
    # if not then return back with error - account create first
    if id:
        account_obj = Account.query.get(id)
        print(account_obj)
    if account_obj:
        formData['account_obj'] = account_obj
        formData['account_id'] = id
        account_type_lists = account_type_list()
        formData['account_type_list'] = account_type_lists
    else:
        flash("Account is either delete or account not created yet")
        return redirect(url_for('account_status'))
    return render_template('case_deposit.html', formData=formData)

# Withdraw Cash


@app.route('/cash-withdraw', methods=['GET', 'POST'], defaults={'id': None})
@app.route('/cash-withdraw/<id>', methods=['GET', 'POST'])
def cash_withdraw(id):
    formData = {}
    # If user not login then redirect to login page
    if not session.get('username'):
        return redirect(url_for('home'))
    # id represent account_id- customer first check corresponding customer , account is available or not
    # if not then return back with error - account create first
    if id:
        account_obj = Account.query.get(id)
    if account_obj:
        formData['account_obj'] = account_obj
        formData['account_id'] = id
        account_type_lists = account_type_list()
        formData['account_type_list'] = account_type_lists
    else:
        flash("Account is either delete or account not created yet")
        return redirect(url_for('account_search'))
    return render_template('cash_withdraw.html', formData=formData)

# Transfer Cash


@app.route('/cash-tranfer', methods=['GET', 'POST'], defaults={'id': None})
@app.route('/cash-tranfer/<id>', methods=['GET', 'POST'])
def cash_transfer(id):
    formData = {}
    # If user not login then redirect to login page
    if not session.get('username'):
        return redirect(url_for('home'))
    # id represent account_id- customer first check corresponding customer , account is available or not
    # if not then return back with error - account create first
    if id:
        account_obj = Account.query.get(id)
    if account_obj:
        formData['account_obj'] = account_obj
        formData['account_id'] = id
        account_type_lists = account_type_list()
        accounts = Account.query.add_columns(
            Account.id, Account.customer_id).all()
        formData['accounts'] = accounts
        formData['account_type_list'] = account_type_lists
    else:
        flash("Account is either delete or account not created yet")
        return redirect(url_for('account_search'))
    return render_template('cash_transfer.html', formData=formData)


@app.route('/ajax/transaction_control', methods=['POST'])
def transaction_control():
    # If user not login then redirect to login page
    if not session.get('username'):
        data = {'url': url_for('home'), 'status': True}
        return data
    if request.method == "POST":
        amount = request.form.get('amount', 0)
        source_account_id = request.form.get('source_account_id', 0)
        transaction_type = request.form.get('transaction_type', 0)
        transfer_account_id = request.form.get('transfer_account_id', 0)
        if amount or source_account_id or transaction_type:
            status = add_transaction(int(transaction_type), int(
                amount), int(source_account_id), int(transfer_account_id))
        else:
            flash('Somethings wents wrong')
    data = {'url': url_for('account_view_profile')+'/' +
            str(source_account_id), 'status': status}
    return data


# @app.route('/create-account', methods=['GET', 'POST'])
# def account():
#     formData = {}
#     if request.method == "POST":
#         username = request.form.get('username', None)
#         password = request.form.get('password', None)
#         formData['username'] = username
#         formData['password'] = password
#         if username and password:
#             if user_exists := UserRegistration.query.filter_by(username=username).count():
#                 flash("Username is already present please choose another")
#             else:
#                 # perform operation
#                 encrypt_password = UserRegistration.hashing(password)
#                 user_obj = UserRegistration(
#                     username, encrypt_password, get_formatted_date())
#                 # saved object into db
#                 db.session.add(user_obj)  # Adds new User record to database
#                 db.session.commit()  # Commits all changes
#                 flash("User created successfully")
#                 return redirect(url_for('home'))
#         else:
#             flash("Something wents wrong, please contact developer")
#     return render_template('registration.html', formData=formData)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if session.get('username'):
        session['username'] = None
    return redirect(url_for('home'))


@app.route('/account-statement', methods=['GET', 'POST'])
def account_statement():
    # If user not login then redirect to login page
    if not session.get('username'):
        return redirect(url_for('home'))
    accounts = Account.query.add_columns(Account.id, Account.customer_id).all()
    formData = {'accounts': accounts, 'search_by': 1}
    if request.method == "POST":
        # Search Account statement by search id
        last_transaction_number = request.form.get(
            'last_transaction_number', None)
        startdate = request.form.get('startdate', None)
        enddate = request.form.get('enddate', None)
        search_by = request.form.get('search_by', None)
        account_id = request.form.get('account_id', None)
        formData['search_by'] = search_by
        formData['account_id'] = account_id
        if search_by and int(search_by) == 1:
            formData['last_transaction_number'] = last_transaction_number
            if transaction_control := TransactionControl.query.filter_by(account_id=account_id).order_by(TransactionControl.created_at.desc()).limit(int(last_transaction_number)):
                formData['account_transactions'] = transaction_control
            else:
                flash("No transaction detail found in applied filter")
        elif search_by and int(search_by) == 2:
            formData['startdate'] = startdate
            formData['enddate'] = enddate
            # search by last transaction number
            startdate_format = datetime.strptime(
                f"{startdate} 00:00:00", '%m/%d/%Y %H:%M:%S')

            enddate_format = datetime.strptime(
                f"{enddate} 23:59:59", '%m/%d/%Y %H:%M:%S')
            print(enddate_format)
            if startdate_format <= enddate_format:
                if transaction_control := TransactionControl.query.filter_by(account_id=account_id).filter(TransactionControl.created_at.between(startdate_format, enddate_format)).order_by(TransactionControl.created_at.desc()).all():
                    formData['account_transactions'] = transaction_control
                else:
                    flash("No transaction detail found in applied filter")
            else:
                flash("Statement not found if start date greater then end date")
        else:
            flash("Something wents wrong, please contact devloper")

    return render_template('account_statement.html', formData=formData)


@app.route('/excel-write-statement', methods=['GET', 'POST'])
def write_statement_into_excel():  # sourcery skip: avoid-builtin-shadow
    import numpy as np
    import pandas as pd
    from io import BytesIO
    from flask import send_file
    if not session.get('username'):
        return redirect(url_for('home'))
    if request.method != "POST":
        return redirect(url_for('account_statement'))
    # Search Account statement by search id
    last_transaction_number = request.form.get(
        'last_transaction_number', None)
    startdate = request.form.get('startdate', None)
    enddate = request.form.get('enddate', None)
    search_by = request.form.get('search_by', None)
    account_id = request.form.get('account_id', None)
    formData = {'search_by': search_by, 'account_id': account_id}
    if search_by and int(search_by) == 1:
        formData['last_transaction_number'] = last_transaction_number
        # search by last transaction number
        transaction_controls = TransactionControl.query.filter_by(account_id=account_id).order_by(
            TransactionControl.created_at.desc()).limit(int(last_transaction_number))
        if transaction_controls:
            formData['account_transactions'] = transaction_controls
        else:
            flash("No transaction detail found in applied filter")
    elif search_by and int(search_by) == 2:
        formData['startdate'] = startdate
        formData['enddate'] = enddate
        # search by last transaction number
        startdate_format = datetime.strptime(
            f"{startdate} 00:00:00", '%m/%d/%Y %H:%M:%S')

        enddate_format = datetime.strptime(
            f"{enddate} 23:59:59", '%m/%d/%Y %H:%M:%S')
        if startdate_format <= enddate_format:
            transaction_controls = TransactionControl.query.filter_by(account_id=account_id).filter(
                TransactionControl.created_at.between(startdate_format, enddate_format)).order_by(TransactionControl.created_at.desc()).all()
            if transaction_controls:
                formData['account_transactions'] = transaction_controls
            else:
                flash("No transaction detail found in applied filter")
                return redirect(url_for('account_statement'))
        else:
            flash("Statement not found if start date greater then end date")
            return redirect(url_for('account_statement'))
    else:
        flash("Something wents wrong, please contact devloper")
        return redirect(url_for('account_statement'))
    # create a random Pandas dataframe
    dataframe = pd.DataFrame()
    for iterate, transaction_control in enumerate(transaction_controls):
        dataframe.at[iterate,
                     "Transaction Id"] = transaction_control.transaction_id
        dataframe.at[iterate, "Description"] = transaction_control.description
        dataframe.at[iterate,
                     "Date(YYYY-MM-DD)"] = transaction_control.created_at
        dataframe.at[iterate, "Amount"] = transaction_control.amount
    # create an output stream
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')

    # taken from the original question
    dataframe.to_excel(writer, startrow=0, merge_cells=False,
                       sheet_name="AccountSheet")
    workbook = writer.book
    worksheet = writer.sheets["AccountSheet"]
    format = workbook.add_format(
        {'border': 1, 'align': 'left', 'font_size': 10})
    format.set_bg_color('#eeeeee')
    # the writer has done its job
    writer.close()

    # go back to the beginning of the stream
    output.seek(0)

    # finally return the file
    return send_file(output, attachment_filename="account_statement.xlsx", as_attachment=True)
