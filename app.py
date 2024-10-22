import os
from flask import Flask, render_template
from customers.views import customers_blueprints
from restaurants.views import restaurants_blueprints
from auth.views import auth_blueprints
import campus_eats

app = Flask(__name__)
app.secret_key = os.urandom(24) 

# 註冊藍圖
app.register_blueprint(customers_blueprints, url_prefix='/customers')
app.register_blueprint(restaurants_blueprints, url_prefix='/restaurants')
app.register_blueprint(auth_blueprints)
 
# 首頁 
@app.route('/')
def home():
    return render_template('auth/login.html')

if __name__ == '__main__':
    app.run(debug=True)
