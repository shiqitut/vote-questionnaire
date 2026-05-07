    # 导入flask
from flask import Flask, render_template
    # 导入配置项
from settings import Config, db
   # 导入蓝图
# from index_page import index_page
# from list_page import list_page

app = Flask(__name__)
    # 加载配置项
app.config.from_object(Config)
    # 初始化数据库，连接数据库和flask
db.init_app(app)

# 登录页面路由
@app.route('/')
@app.route('/login')
def login():
    """渲染登录页面"""
    return render_template('login.html')


    # 注册页面路由
@app.route('/register')
def register():
    return render_template('register.html')
if __name__ == '__main__':
        app.run()