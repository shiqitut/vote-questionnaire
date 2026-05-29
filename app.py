
from flask import Flask, redirect, url_for
from flask_cors import CORS
from settings import db, Config


# 创建Flask应用
app = Flask(__name__)
app.config.from_object(Config)

# 初始化数据库
db.init_app(app)

# 启用CORS
CORS(app, resources={r"/*": {"origins": "*"}})


# 创建数据库表
def create_tables():
    """创建数据库表"""
    with app.app_context():
        import model
        db.create_all()


# 注册蓝图
def register_blueprints():
    from login import login_page
    from register import register_page
    from views import survey_bp
    
    app.register_blueprint(login_page)
    app.register_blueprint(register_page)
    app.register_blueprint(survey_bp)


if __name__ == '__main__':
    # 创建数据库表
    create_tables()
    
    # 注册蓝图
    register_blueprints()
    
    app.run(host='0.0.0.0', port=5000, debug=True)