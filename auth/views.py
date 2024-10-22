import os
import requests
import hashlib
from flask import Blueprint, flash, redirect, request, render_template, url_for, session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from contextlib import contextmanager
from campus_eats import UserTable, Customer, Restaurant

auth_blueprints = Blueprint('auth', __name__, template_folder='templates/auth', static_folder='./static')

auth_blueprints.secret_key = os.urandom(24)  # Session 加密用

# OAuth 設定
CLIENT_ID = '20241007203637hgWIOoOg6QGH'  # 從中央大學 Portal 申請
CLIENT_SECRET = 'YUustASvU0LWPSFXygagued9EILygcfv4h3xofCYJYAuQEoMXrLatvFy'  # 從中央大學 Portal 申請
AUTHORIZATION_URL = 'https://portal.ncu.edu.tw/oauth2/authorization'
TOKEN_URL = 'https://portal.ncu.edu.tw/oauth2/token'
USER_INFO_URL = 'https://portal.ncu.edu.tw/apis/oauth/v1/info'
REDIRECT_URI = 'http://localhost:5000/customers/callback'  # 回調 URL
SCOPE = 'id identifier chinese-name email mobile-phone personal-id'

# 創建資料庫引擎
# DATABASE_URL = 'mysql+pymysql://root:mysql@localhost/campus_eats'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# 創建一個上下文管理器來自動管理 Session 的生命週期
@contextmanager
def get_session():
    session = Session()
    try:
        yield session
        session.commit()  # 若有任何變更需要提交
    except Exception as e:
        session.rollback()  # 發生錯誤時回滾事務
        raise
    finally:
        session.close()  # 結束後關閉 session

# 加密密碼
def encrypt_password(password):
    encrypted_password = hashlib.sha256(password.encode()).hexdigest()
    return encrypted_password

# portal登入
@auth_blueprints.route('/NCUlogin', methods=['GET', 'POST'])
def portal_login():
    # Redirect to the portal's OAuth login URL
    return redirect(f'{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope={SCOPE}')

# Portal授權完成後的回調處理
@auth_blueprints.route('/customers/callback')
def callback():
    code = request.args.get('code')

    if not code:
        return "Authorization code not found.", 400

    # 交換授權碼為 access token
    token_response = requests.post(TOKEN_URL, data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }, headers={'Accept': 'application/json'})

    token_json = token_response.json()
    if 'access_token' not in token_json:
        return "Failed to get access token.", 400

    access_token = token_json['access_token']

    # 使用 access token 取得使用者資訊
    user_info_response = requests.get(USER_INFO_URL, headers={
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    })

    user_info = user_info_response.json()
    username = user_info.get('identifier')
    password = encrypt_password(user_info.get('personalId')[-4:])
    role = 1  # 1 表示顧客

    name = user_info.get('chineseName')
    phone = user_info.get('mobilePhone')
    email = user_info.get('email')

    with get_session() as db_session:
        # 查詢該學號是否有在用戶資料表中
        IsUserExist = db_session.query(UserTable).filter_by(username=username).first() is not None

        # 有在用戶資料表中 -> 登入成功，顯示餐廳清單頁面
        if IsUserExist:
            session['username'] = username
            session['role'] = role
            return redirect(url_for('customers.menu'))

        # 沒有用戶資料表中 -> 自動新增資料
        else:
            new_user = UserTable(username=username, password=password, role=role)
            db_session.add(new_user)
            print(f"User '{username}' added to UserTable successfully.")

            new_customer = Customer(name=name, phone=phone, email=email, username=username)
            db_session.add(new_customer)
            db_session.commit()
            print(f"User '{username}' added to Customer successfully.")

            session['username'] = username
            session['role'] = role
            return redirect(url_for('customers.menu'))  # 新用戶自動導向顧客菜單頁面


# 通用的登入邏輯
@auth_blueprints.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        with get_session() as db_session:
            # 根據用戶名查詢
            user = db_session.query(UserTable).filter_by(username=username).first()
            if user and user.password == encrypt_password(password):
                session['username'] = username
                session['role'] = user.role

                if user.role == 1:
                    # print("顧客登入成功，將跳轉到菜單頁面。")
                    return redirect(url_for('customers.menu'))
                elif user.role == 2:
                    # print("店家登入成功，將跳轉到管理頁面。")
                    return redirect(url_for('restaurants.management'))
            else:
                flash('帳號或密碼錯誤！')
                return redirect(url_for('auth.login'))

    return render_template('auth/login.html')  


# 通用的註冊邏輯
@auth_blueprints.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        with get_session() as db_session:
            is_user_exist = db_session.query(UserTable).filter_by(username=username).first() is not None
            if is_user_exist:
                flash('帳號已存在')
                return redirect(url_for('auth.register'))

            if role == 'customer':
                name = request.form['name']
                phone = request.form['phone']
                email = request.form['email']

                new_user = UserTable(username=username, password=encrypt_password(password), role=1)
                new_customer = Customer(name=name, phone=phone, email=email, username=username)

                db_session.add(new_user)
                db_session.add(new_customer)
                db_session.commit()
                print('顧客註冊成功！')

                return redirect(url_for('customers.menu'))

            elif role == 'restaurant':
                restaurant_name = request.form['restaurant_name']
                phone = request.form['phone']
                address = request.form['address']
                business_hours = request.form['business_hours']

                new_user = UserTable(username=username, password=encrypt_password(password), role=2)
                new_restaurant = Restaurant(restaurant_name=restaurant_name, phone=phone, address=address, business_hours=business_hours, username=username)

                db_session.add(new_user)
                db_session.add(new_restaurant)
                db_session.commit()
                print('店家註冊成功！')

                return redirect(url_for('restaurants.management'))

    return render_template('auth/register.html')

