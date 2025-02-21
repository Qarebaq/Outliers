from flask import Flask, render_template, redirect, url_for, request, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo, NumberRange
import datetime

# فرم برای وارد کردن ساعت تمرین روزانه
class PracticeForm(FlaskForm):
    hours = IntegerField('Enter hours of practice today', validators=[DataRequired(), NumberRange(min=0)])

# فرم ثبت‌نام
class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])

# تنظیمات Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # کلید امن برای نشست‌ها
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

# مدل User
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    total_hours = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

# فرم ورود
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])

@app.route("/")  # روت صفحه اصلی (ایندکس)
def index():
    return redirect(url_for('login'))  # هدایت به صفحه لاگین

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.password == form.password.data:
            session['user_id'] = user.id  # ذخیره اطلاعات کاربر در نشست
            flash('Login successful!')
            return redirect(url_for('dashboard'))  # هدایت به داشبورد بعد از ورود موفق
        else:
            flash("Invalid email or password. Please try again.")
    return render_template('login.html', form=form)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():
        # گرفتن داده‌های فرم
        username = form.username.data
        email = form.email.data
        password = form.password.data
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # ایجاد کاربر جدید
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash('Your account has been created!', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)  # ارسال فرم به قالب

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    user_id = session.get('user_id')
    if user_id:
        user = User.query.get(user_id)
        form = PracticeForm()

        # مقداردهی به time_to_goal_years
        time_to_goal_years = None  # مقدار پیش‌فرض

        if form.validate_on_submit():
            hours_today = form.hours.data
            user.total_hours += hours_today  # اضافه کردن ساعت‌های تمرین روزانه به total_hours
            db.session.commit()  # ذخیره تغییرات در دیتابیس
            flash(f'Your total hours have been updated: {user.total_hours} hours.')

            # محاسبه مدت زمان باقی‌مانده برای رسیدن به 10,000 ساعت
            hours_needed = 10000 - user.total_hours
            avg_daily_hours = 2  # فرض کنیم کاربر روزی 2 ساعت کار می‌کند
            time_to_goal_days = hours_needed / avg_daily_hours

            # اطمینان از اینکه time_to_goal_years محاسبه شده باشد
            if time_to_goal_days > 0:
                time_to_goal_years = time_to_goal_days / 365  # تبدیل به سال

        return render_template('dashboard.html', user=user, form=form, time_to_goal_years=time_to_goal_years)
    else:
        flash("You must be logged in to view this page.")
        return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
