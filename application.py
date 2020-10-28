from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
import requests


headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Token 3f662fe401bcac995bf2111f66976470e1bdecdd'
}

app = Flask(__name__)

app.secret_key = 'secret_key'

app.config['MYSQL_HOST'] = 'us-cdbr-east-02.cleardb.com'
app.config['MYSQL_USER'] = 'b6fe21968c7aaf'
app.config['MYSQL_PASSWORD'] = '6f6f2e8d' 
app.config['MYSQL_DB'] = 'heroku_0400bde6520f92f'

mysql = MySQL(app)

@app.route('/')
def index():
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	msg = ""
	if request.method == 'POST' and 'name' in request.form and 'password' in request.form:
		name = request.form['name']
		password = request.form['password']
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		sql = ("SELECT * FROM accounts WHERE name = %s AND password = %s")
		values = (name, password)
		cursor.execute(sql, values)
		account = cursor.fetchone()
		if account:
			session['loggedin'] = True
			session['id'] = account['id']
			session['username'] = account['name']
			return redirect(url_for("home"))
		else:	
			msg = 'Incorrect username/password'

	return render_template('index.html', msg=msg)

@app.route('/home')
def home():
	if 'loggedin' in session:
		cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
		cursor.execute("SELECT * FROM accounts INNER JOIN holdings ON accounts.id = holdings.account_id WHERE account_id = %s", (session['id'],))
		data = cursor.fetchall()
		cursor.execute("SELECT COUNT(*) FROM holdings WHERE account_id=%s", (session['id'],))
		amount = cursor.fetchall()
		amount = amount[0]['COUNT(*)'] 
		print(amount)
		return render_template('home.html', name = session['username'], value=data, amount=amount)
	return redirect(url_for('login'))

@app.route('/search', methods=['GET', 'POST'])
def search():
	if request.method == 'POST' and 'search' in request.form:
		search = request.form['search']
		res = requests.get(f"https://api.tiingo.com/iex/{search}", headers=headers)
		data = res.json()
		session['search'] = search
		session['last'] = data[0]['last']
		session['open'] = data[0]['open']
		session['high'] = data[0]['high']
		session['timestamp'] = data[0]['quoteTimestamp']
		return redirect(url_for('view'))
		   
	return render_template('search.html')

@app.route('/logout')
def logout():
	session.pop('loggedin', None)
	session.pop('id', None)
	session.pop('username', None)
	return redirect(url_for('login'))


@app.route('/view', methods=['GET', 'POST'])
def view():
	last1 = session.get('last',None)
	open1 = session.get('open',None)
	high1 = session.get('high',None)
	time1 = session.get('timestamp',None)
	stock = str(session.get('search',None)).upper()

	return render_template('view.html', last=last1,open=open1,high=high1,time=time1,stock=stock)

@app.route('/buy', methods=['GET', 'POST'])
def buy():
	if request.method == 'POST' and 'buy' in request.form:
		buy1 = request.form['buy']
		session['buy'] = buy1
		return redirect(url_for('execute'))
	return render_template('buy.html')

@app.route('/execute', methods=['GET', 'POST'])
def execute():
	db = MySQLdb.connect("us-cdbr-east-02.cleardb.com", "b6fe21968c7aaf", "6f6f2e8d", "heroku_0400bde6520f92f")
	cur = db.cursor()
	buy = session.get('buy',None)
	last1 = session.get('last',None)
	open1 = session.get('open',None)
	high1 = session.get('high',None)
	time1 = session.get('timestamp',None)
	stock = str(session.get('search',None)).upper()
	total1 = float(buy)*float(last1)
	total = "$" + str(total1)
	session['total'] =total1


	return render_template('summary.html', buy=buy, last=last1, open=open1, high=high1, time=time1, stock=stock, total=total)

@app.route('/return_home', methods=['GET', 'POST'])
def return_home():
	cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
	db = MySQLdb.connect("us-cdbr-east-02.cleardb.com", "b6fe21968c7aaf", "6f6f2e8d", "heroku_0400bde6520f92f")
	cur = db.cursor()
	cursor.execute("SELECT cash FROM accounts WHERE id=%s", (session['id'],))
	total1 = session.get('total', None)
	initial = cursor.fetchall()
	initial = int(initial[0]['cash'])
	print(initial)
	newCash = initial - total1
	cur.execute("UPDATE accounts SET cash=%s", (newCash))
	db.commit()
	return redirect(url_for('home'))
