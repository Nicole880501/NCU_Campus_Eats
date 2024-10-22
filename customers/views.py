import os
from flask import Blueprint, render_template
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from contextlib import contextmanager
from campus_eats import UserTable, Customer  

# 建立實體
customers_blueprints = Blueprint('customers', __name__, template_folder='templates/customers', static_folder='./static')

customers_blueprints.secret_key = os.urandom(24)  # Session 加密用

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

@customers_blueprints.route('/menu')
def menu():
    # 返回菜單頁面
    return render_template('customers/menu.html')
