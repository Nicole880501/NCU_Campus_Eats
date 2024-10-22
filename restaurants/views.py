import os
from contextlib import contextmanager
from flask import Blueprint, render_template
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from campus_eats import Restaurant, UserTable, Customer

# 建立實體
restaurants_blueprints = Blueprint('restaurants', __name__, template_folder='templates/restaurants', static_folder='./static')

restaurants_blueprints.secret_key = os.urandom(24)  # Session 加密用

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

@restaurants_blueprints.route('/management')
def management():
    # 返回菜單頁面
    return render_template('restaurants/management.html')