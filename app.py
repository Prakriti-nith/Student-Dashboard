from flask import Flask, request, render_template, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps
import time
import datetime

#forecasting 
import numpy as np
from statsmodels.tsa.arima_model import ARIMA

app = Flask(__name__)
# Config MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'gupta@123'
#Change Password Accordingly
app.config['MYSQL_DB'] = 'results'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
mysql = MySQL(app)

# Index
@app.route('/')
def index():
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(roll_no) FROM students ")
    data = cur.fetchall()
    temp = data[0]
    #number of entries in Students Tables
    countall = float(temp['COUNT(roll_no)'])
    to_pass = []
    
    cur.execute("SELECT COUNT(roll_no) FROM students where cgpi <= 4")
    data = cur.fetchall()
    temp = data[0]
    count = float(temp['COUNT(roll_no)'])
    to_pass.append(float("{0:.2f}".format((count/countall)*100)))

    cur.execute("SELECT COUNT(roll_no) FROM students where cgpi > 4 AND cgpi <=6 ")
    data = cur.fetchall()
    temp = data[0]
    count = float(temp['COUNT(roll_no)'])
    to_pass.append(float("{0:.2f}".format((count/countall)*100)))

    cur.execute("SELECT COUNT(roll_no) FROM students where cgpi > 6 AND cgpi <= 7 ")
    data = cur.fetchall()
    temp = data[0]
    count = float(temp['COUNT(roll_no)'])
    to_pass.append(float("{0:.2f}".format((count/countall)*100)))

    cur.execute("SELECT COUNT(roll_no) FROM students where cgpi > 7 AND cgpi <= 8 ")
    data = cur.fetchall()
    temp = data[0]
    count = float(temp['COUNT(roll_no)'])
    to_pass.append(float("{0:.2f}".format((count/countall)*100)))

    cur.execute("SELECT COUNT(roll_no) FROM students where cgpi > 8 AND cgpi <= 9 ")
    data = cur.fetchall()
    temp = data[0]
    count = float(temp['COUNT(roll_no)'])
    to_pass.append(float("{0:.2f}".format((count/countall)*100)))

    cur.execute("SELECT COUNT(roll_no) FROM students where cgpi > 9 AND cgpi <= 10 ")
    data = cur.fetchall()
    temp = data[0]
    count = float(temp['COUNT(roll_no)'])
    to_pass.append(float("{0:.2f}".format((count/countall)*100)))
    # print(to_pass)
    return render_template('home.html' , data = to_pass)

# Register form class
class RegisterForm(Form):
    name = StringField('Name', [validators.Length(min=1, max=50)])
    email = StringField('Email', [validators.Length(min=6, max=50)])
    roll_number = StringField('Roll Number', [validators.Length(min=5, max=15)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')

# USer Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        roll_number = form.roll_number.data
        password = sha256_crypt.encrypt(str(form.password.data))

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute query
        cur.execute("INSERT INTO user(name, email, roll_number, password) VALUES(%s, %s, %s, %s)", (name, email, roll_number, password))

        # Commit to DB
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('index'))

    return render_template('register.html', form=form)

# User login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get Form Fields
        roll_number = request.form['roll_number']

        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by roll_number
        result = cur.execute("SELECT * FROM user WHERE roll_number = %s", [roll_number])

        if result > 0:
            # Get stored hash
            data = cur.fetchone()
            password = data['password'] 

            # Compare Passwords
            if sha256_crypt.verify(password_candidate, password):
                # passed
                app.logger.info('PASSWORD MATCHED')
                session['logged_in'] = True
                session['roll_number'] = roll_number

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))
            else:
                error = 'Invalid Login'
                return render_template('login.html', error=error)
            cur.close
        else:
            error = 'Username not found'
            return render_template('login.html', error=error)

    return render_template('login.html')

# Decorator: Checks if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

def run_sql_file(filename):
    '''
    The function takes a filename and a connection as input
    and will run the SQL query on the given connection  
    '''
    cur = mysql.connection.cursor()
    start = time.time()
    
    file = open(filename, 'r')
    sql = s = " ".join(file.readlines())
    print("Start executing: " + filename + " at " + str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M")) + "\n" + sql) 
    cur.execute(sql) 
    # mysql.connection.commit() 
    end = time.time()
    print("Time elapsed to run the query:")
    print(str((end - start)*1000) + ' ms')

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get user by roll_number
    # run_sql_file('data')
    student_sem_data = []
    cur.execute("SELECT * FROM semesters WHERE roll_no  = '{}'" .format(session['roll_number']))
    data = cur.fetchall()
    #print(data)
    student_sem_cgpi = []
    student_sem_sgpi = []
    for dict_sem in data:
        student_sem_cgpi.append(dict_sem['cgpi'])
        student_sem_sgpi.append(dict_sem['sgpi'])
    #print(student_sem_cgpi)
    #print(student_sem_sgpi)

    # student_sem_data[0] = CGPI
    # student_sem_data[1] = SGPI
    student_sem_data.append(student_sem_cgpi)
    student_sem_data.append(student_sem_sgpi)

    cur.execute("SELECT * FROM students WHERE roll_no  = '{}'" .format(session['roll_number']))
    student_data = cur.fetchall()
    student_data_list = []
    student_data_list.append(student_data[0]['roll_no'])
    student_data_list.append(student_data[0]['name'])
    student_data_list.append(student_data[0]['cgpi'])
    student_data_list.append(student_data[0]['year_rank'])
    student_data_list.append(student_data[0]['college_rank'])
    #print(student_data)

    # student_sem_data[2] = student details
    student_sem_data.append(student_data_list)
    cur.execute("SELECT * FROM subjects WHERE roll_no  = '{}'" .format(session['roll_number']))
    student_subjects = cur.fetchall()
    student_subjects_list = []
    for i in student_subjects:
        stu_sub_list = []
        stu_sub_list.append(i['subject_name'])
        stu_sub_list.append(i['ObtainCR'])
        stu_sub_list.append(i['TotalCR'])
        stu_sub_list.append(int(i['semester_no'][-1]) % 10)
        student_subjects_list.append(stu_sub_list)
        # print(i)
    #print(student_subjects_list)

    # student_sem_data[3] = subject wise details of student
    student_sem_data.append(student_subjects_list)

    return render_template('dashboard.html' , data=student_sem_data)


# Dashboard
@app.route('/forecast')
@is_logged_in
def forecast():
    # Create cursor
    cur = mysql.connection.cursor()
    # Get user by roll_number
    # run_sql_file('data')
    student_sem_data = []
    cur.execute("SELECT * FROM semesters WHERE roll_no  = '{}'" .format(session['roll_number']))
    data = cur.fetchall()
    #print(data)
    student_sem_cgpi = []
    student_sem_sgpi = []
    for dict_sem in data:
        student_sem_cgpi.append(dict_sem['cgpi'])
        student_sem_sgpi.append(dict_sem['sgpi'])
    # print(student_sem_cgpi)
    # print(student_sem_sgpi)

    if len(session['roll_number'])==10 or len(session['roll_number'])==5:
        if len(student_sem_sgpi)<8:
            lst = student_sem_sgpi
            count = len(student_sem_sgpi)
            # print(session['roll_number'])
            #print(lst)
            lnRes = np.log(lst)
            #result_matrix=lnRes.asmatrix()
            model = ARIMA(lnRes, order=(0,0,1))
            model_fit = model.fit(disp=0)
            rows,coloums=count,1
            predictions=model_fit.predict(rows, rows+1)
            predictionsadjusted=np.exp(predictions)
            print(predictionsadjusted)
            student_sem_sgpi.append(float("{0:.2f}".format(predictionsadjusted[0])))
        else:
            pass
    else:
        if len(student_sem_sgpi)<10:
            lst = student_sem_sgpi
            count = len(student_sem_sgpi)
            # print(session['roll_number'])
            #print(lst)
            lnRes = np.log(lst)
            #result_matrix=lnRes.asmatrix()
            model = ARIMA(lnRes, order=(0,0,1))
            model_fit = model.fit(disp=0)
            rows,coloums=count,1
            predictions=model_fit.predict(rows, rows+1)
            predictionsadjusted=np.exp(predictions)
            print(predictionsadjusted)
            student_sem_sgpi.append(float("{0:.2f}".format(predictionsadjusted[0])))
        else:
            pass
    # student_sem_data[0] = CGPI
    # student_sem_data[1] = SGPI

    student_sem_data.append(student_sem_cgpi)
    student_sem_data.append(student_sem_sgpi)

    cur.execute("SELECT * FROM students WHERE roll_no  = '{}'" .format(session['roll_number']))
    student_data = cur.fetchall()
    student_data_list = []
    student_data_list.append(student_data[0]['roll_no'])
    student_data_list.append(student_data[0]['name'])
    student_data_list.append(student_data[0]['cgpi'])
    student_data_list.append(student_data[0]['year_rank'])
    student_data_list.append(student_data[0]['college_rank'])
    #print(student_data)

    # student_sem_data[2] = student details
    student_sem_data.append(student_data_list)

    cur.execute("SELECT * FROM subjects WHERE roll_no  = '{}'" .format(session['roll_number']))
    student_subjects = cur.fetchall()
    student_subjects_list = []
    for i in student_subjects:
        stu_sub_list = []
        stu_sub_list.append(i['subject_name'])
        stu_sub_list.append(i['ObtainCR'])
        stu_sub_list.append(i['TotalCR'])
        stu_sub_list.append(int(i['semester_no'][-1]) % 10)
        student_subjects_list.append(stu_sub_list)
        # print(i)
    #print(student_subjects_list)

    # student_sem_data[3] = subject wise details of student
    #student_sem_data.append(student_subjects_list)

    return render_template('forecast.html' , data=student_sem_data)


@app.route('/summarized')
@is_logged_in
def summarized():
    cur = mysql.connection.cursor()
    cur.execute("select semester_no, subject_name, ObtainCR , TotalCR from subjects where roll_no = '{}' order by semester_no" .format(session['roll_number']))
    data = cur.fetchall()
    # print(data)
    cur.execute("select count(distinct semester_no) as cnt from subjects where roll_no = '{}'" .format(session['roll_number']))
    semester_cnt = cur.fetchall()
    # print(semester_cnt)
    # print(type(data[0]))
    sem_cnt = semester_cnt[0]['cnt']
    # print(sem_cnt)
    # to_pass = []
    to_pass = [[] for x in range(0,sem_cnt)]
    subjects = [[] for x in range(0,sem_cnt)]
    grades = [[] for x in range(0,sem_cnt)]

    print(to_pass)
    for i in data:
        # dic['subject_name'] = i['subject_name']
        # dic['Grades'] = (int(i['ObtainCR'])*10)/int(i['TotalCR'])
        # dic['semester_no'] = int(i['semester_no'][-1])
        semester_no = int(i['semester_no'][-1]) - 1
        subjects[semester_no].append(i['subject_name'])
        grades[semester_no].append((int(i['ObtainCR'])*10)/int(i['TotalCR']))
    
    for i in range(0,sem_cnt):
        to_pass[i].append(subjects[i])
        to_pass[i].append(grades[i])
        to_pass[i].append(i)

    print(to_pass)
    # print(countall)
    
    # if len(session['roll_number']) == 10:
    #     #IIIT una
    #     year = "20" + str(session['roll_number'])[5:7]
    # else:
    #     #Dual Degree or B.Tech
    #     year = "20" + str(session['roll_number'])[0:2]
    #print(year)
    return render_template('summarized.html', data=to_pass)


if __name__ == '__main__':
    app.secret_key='secret123'
app.run(debug=True)
