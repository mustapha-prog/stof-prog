from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import pandas as pd
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # مفتاح سرّي للجلسات

# مسار ملف Excel
EXCEL_FILE = r"C:\Users\mustapha\OneDrive\Bureau\projrt1\reserv.xlsx"

# إنشاء ملف Excel إذا لم يكن موجود
if not os.path.exists(EXCEL_FILE):
    df = pd.DataFrame(columns=["الاسم الكامل", "رقم الهاتف", "اليوم", "الساعة", "الملعب", "تم التأكيد"])
    df.to_excel(EXCEL_FILE, index=False)

# بيانات المدير
ADMIN_USERNAME = 'admin'
ADMIN_PASSWORD = '1234554321'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/resv')
def resv():
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('resv.html', current_date=current_date)

@app.route('/submit_booking', methods=['POST'])
def submit_booking():
    fullname = request.form['fullname']
    phone = request.form['phone']
    day = request.form['day']
    hour = request.form['hour']
    field = request.form['field']

    df = pd.read_excel(EXCEL_FILE)

    # التأكد من عدم تكرار الحجز بنفس رقم الهاتف
    if ((df['رقم الهاتف'] == phone) & (df['اليوم'] == day)).any():
        return jsonify({'status': 'error', 'message': 'رقم الهاتف محجوز بالفعل في هذا اليوم.'})

    # التأكد من عدم تكرار نفس الحجز (نفس اليوم، الساعة، والملعب)
    if ((df['اليوم'] == day) & (df['الساعة'] == hour) & (df['الملعب'] == int(field))).any():
        return jsonify({'status': 'error', 'message': 'هذه الساعة محجوزة بالفعل لهذا الملعب.'})

    # إضافة الحجز الجديد
    new_booking = pd.DataFrame([{
        "الاسم الكامل": fullname,
        "رقم الهاتف": phone,
        "اليوم": day,
        "الساعة": hour,
        "الملعب": int(field),
        "تم التأكيد": False
    }])

    df = pd.concat([df, new_booking], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)

    return jsonify({'status': 'success', 'message': 'تم الحجز بنجاح!'})

@app.route('/dispo')
def dispo():
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('dispo.html', current_date=current_date)

@app.route('/get_bookings/<date>')
def get_bookings(date):
    if not os.path.exists(EXCEL_FILE):
        return jsonify({'field1': [], 'field2': []})

    df = pd.read_excel(EXCEL_FILE)
    df_day = df[df['اليوم'] == date]

    hours = [f"{h:02d}:00" for h in range(9, 24)] + ["00:00"]
    bookings_field1 = df_day[df_day['الملعب'] == 1]['الساعة'].tolist()
    bookings_field2 = df_day[df_day['الملعب'] == 2]['الساعة'].tolist()

    return jsonify({
        'hours': hours,
        'field1': bookings_field1,
        'field2': bookings_field2
    })

# ----------------------------------------
# مسارات لوحة تحكم المدير
# ----------------------------------------

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            error = "اسم المستخدم أو كلمة المرور غير صحيحة."
            return render_template('admin.html', error=error)
    return render_template('admin.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if not os.path.exists(EXCEL_FILE):
        bookings = []
    else:
        df = pd.read_excel(EXCEL_FILE)
        bookings = df.to_dict(orient='records')

    return render_template('admin_dashboard.html', bookings=bookings)

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/confirm/<int:booking_id>')
def confirm_booking(booking_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    df = pd.read_excel(EXCEL_FILE)

    if booking_id < len(df):
        df.at[booking_id, 'تم التأكيد'] = True
        df.to_excel(EXCEL_FILE, index=False)

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/edit/<int:booking_id>', methods=['GET', 'POST'])
def edit_booking(booking_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    df = pd.read_excel(EXCEL_FILE)

    if request.method == 'POST':
        df.at[booking_id, 'الاسم الكامل'] = request.form['fullname']
        df.at[booking_id, 'رقم الهاتف'] = request.form['phone']
        df.at[booking_id, 'اليوم'] = request.form['day']
        df.at[booking_id, 'الساعة'] = request.form['hour']
        df.at[booking_id, 'الملعب'] = int(request.form['field'])
        df.to_excel(EXCEL_FILE, index=False)
        return redirect(url_for('admin_dashboard'))

    booking = df.iloc[booking_id]
    return render_template('edit_booking.html', booking=booking, booking_id=booking_id)

@app.route('/admin/delete/<int:booking_id>')
def delete_booking(booking_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    df = pd.read_excel(EXCEL_FILE)

    if booking_id < len(df):
        df = df.drop(index=booking_id).reset_index(drop=True)
        df.to_excel(EXCEL_FILE, index=False)

    return redirect(url_for('admin_dashboard'))

# ----------------------------------------

if __name__ == '__main__':
    app.run(debug=True)
