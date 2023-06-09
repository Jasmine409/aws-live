from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *
from datetime import datetime

app = Flask(__name__)

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'

@app.route("/", methods=['GET', 'POST'])
def home():
    return render_template('index.html')

@app.route("/addhome", methods=['GET', 'POST'])
def addpage():
    return render_template('AddEmp.html')


@app.route("/addemp", methods=['GET', 'POST'])
def AddEmp():
    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    salary = request.form['salary']
    othours = request.form['othours']
    emp_image_file = request.files['emp_image_file']

    insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s, %s)"
    select_sql = "SELECT * FROM employee WHERE emp_id = (%s)"
    cursor = db_conn.cursor()
    cursor.execute(select_sql,(emp_id))
    if emp_image_file.filename == "":
        return "Please select a file"
    if cursor.fetchone() is not None:
        return "Employee ID already exist"
    try:   
        cursor.execute(insert_sql, (emp_id, first_name, last_name, pri_skill, location, salary, othours))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        # Uplaod image file in S3 #
        emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
        s3 = boto3.resource('s3')

        try:
            print("Data inserted in MySQL RDS... uploading image to S3...")
            s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
            bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
            s3_location = (bucket_location['LocationConstraint'])

            if s3_location is None:
                s3_location = ''
            else:
                s3_location = '-' + s3_location

            object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                s3_location,
                custombucket,
                emp_image_file_name_in_s3)
            
            print(object_url)

        except Exception as e:
            return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('AddEmpOutput.html', name=emp_name)

@app.route("/getemp", methods=['GET', 'POST'])
def getpage():
    return render_template('GetEmp.html')

@app.route("/fetchdata", methods=['GET', 'POST'])
def GetEmp():
    emp_id = request.form['emp_id']
    sysdate = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    select_sql = "SELECT * FROM employee WHERE emp_id = (%s)"
    cursor = db_conn.cursor()
    img_url = ""
    try:
        cursor.execute(select_sql,(emp_id))
        print("Fetching single row")        
        # Fetch one record from SQL query output
        record = cursor.fetchone()
        print("Fetched: ",record)
        if record is None:
            print("No data found.")
            
        else:
            emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"

            img_url = "https://fongsukdien-employee.s3.amazonaws.com/{0}".format(
                emp_image_file_name_in_s3)
            
            calc_payroll = record[5] + (record[5] * 0.05 * record[6])
    except Exception as e:
        return str(e)

    finally:
        cursor.close()

    print("fetch data done...")
    if record is None:
        return render_template('GetEmpOutput.html', 
                           out_id="ID Not Exist", 
                           out_fname="NULL", 
                           out_lname="NULL",
                           out_interest="NULL",
                           out_location="NULL",
                           out_salary="NULL",
                           out_othours="NULL",
                           out_payroll="NULL",
                           out_date="NULL",                               
                           image_url=img_url
                          )
    else :
        return render_template('GetEmpOutput.html', 
                           out_id=record[0], 
                           out_fname=record[1], 
                           out_lname=record[2],
                           out_interest=record[3],
                           out_location=record[4],
                           out_salary=record[5],
                           out_othours=record[6],
                           out_payroll=str(calc_payroll),
                           out_date=sysdate,
                           image_url=img_url
                          )

@app.route("/updateemp", methods=['GET', 'POST'])
def uppage():
    return render_template('UpdateEmp.html')

@app.route("/fetchup", methods=['POST'])
def UpdateEmp():
    emp_id = request.form['emp_id']
    select_sql = "SELECT * FROM employee WHERE emp_id = %s"
    cursor = db_conn.cursor()
    img_url = ""
    try:
        cursor.execute(select_sql,(emp_id))
        print("Fetching single row")        
        # Fetch one record from SQL query output
        record = cursor.fetchone()
        print("Fetched: ",record)
        if record is None:
            return "Employee Not Found. To add new record, please proceed to Home Page."
            
    except Exception as e:
        return str(e)

    finally:
        cursor.close()

    print("fetch data done...")
    return render_template('UpdateEmpContent.html', 
                           out_id=record[0], 
                           out_fname=record[1], 
                           out_lname=record[2],
                           out_skill=record[3],
                           out_location=record[4],
                           out_salary=record[5],
                           out_othours=record[6]
                          )

@app.route("/upemp", methods=['GET', 'POST'])
def UpEmp():

    emp_id = request.form['emp_id']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    pri_skill = request.form['pri_skill']
    location = request.form['location']
    salary = request.form['salary']
    othours = request.form['othours']
    emp_image_file = request.files['emp_image_file']

    update_sql = "UPDATE employee SET first_name=%s, last_name=%s, pri_skill=%s, location=%s, salary=%s, othours=%s WHERE emp_id = %s"
    cursor = db_conn.cursor()

    try:   
        cursor.execute(update_sql, (first_name, last_name, pri_skill, location, salary, othours, emp_id))
        db_conn.commit()
        emp_name = "" + first_name + " " + last_name
        if emp_image_file.filename != "":
            emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"

            s3 = boto3.resource('s3')
            obj = s3.Object(custombucket, emp_image_file_name_in_s3)
            obj.delete()
            try:
                print("Data inserted in MySQL RDS... uploading image to S3...")
                s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_image_file)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    custombucket,
                    emp_image_file_name_in_s3)

            except Exception as e:
                return str(e)

    finally:
        cursor.close()

    print("all modification done...")
    return render_template('UpdateEmpOutput.html', name=emp_name)

@app.route('/delete', methods=['GET', 'POST'])
def delete():
    emp_id = request.form['emp_id']
    delete_sql = "DELETE FROM employee WHERE emp_id = (%s)"

    cursor = db_conn.cursor()
    cursor.execute(delete_sql, (emp_id))
    db_conn.commit()
    object_name = "emp-id-" + str(emp_id) + "_image_file"
    s3 = boto3.resource('s3')
    s3.Object(custombucket, object_name).delete()
    record = cursor.fetchone()
    obj = s3.Object(custombucket, object_name)
    return render_template('DeleteEmpOutput.html', deleted_id=emp_id)

@app.route('/summary', methods=['POST','GET'])
def summary():
    select_sql = "SELECT * FROM employee"

    cursor = db_conn.cursor()

    cursor.execute(select_sql)
    rows = cursor.fetchall()
    total = 0
    code = ""
    for record in rows:
        full_name = record[1]+record[2]
        pay= record[5] + (record[5] * 0.05 * record[6])
        total = total + pay
        code = code + ("""
                  <li class='table-row'>
                    <div class="col col-1" >{employee_id}</div>
                    <div class="col col-2" >{name}</div>
                    <div class="col col-3" >{pri_skill}</div>
                    <div class="col col-4" >{location}</div>
                    <div class="col col-5" >{salary:.2f}</div>
                    <div class="col col-6" >{othours}</div>
                    <div class="col col-7" >{payroll:.2f}</div>
                  </li>
                """).format(employee_id=record[0],name=full_name,pri_skill=record[3],
                           location=record[4],salary=record[5],othours=record[6],payroll=pay)

    return render_template('ShowEmp.html',table_code=code, count=cursor.rowcount,total_pay=total)

@app.route("/fsd")
def fsdpage():
    return render_template('fongsukdien.html')
@app.route("/fmw")
def fmwpage():
    return render_template('mengwen.html')
@app.route("/ethan")
def ethanpage():
    return render_template('ethanlim.html')
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
