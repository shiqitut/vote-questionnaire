#项目配置文件
#导入数据操作类
from flask_sqlalchemy import SQLAlchemy
# 导入pymysql驱动
import pymysql
# 安装驱动
pymysql.install_as_MySQLdb()
# 创建数据库对象
db = SQLAlchemy()
# 创建配置项
class Config(object):
    # 打开调试模式
    DEBUG = True
    # 设置密钥
    SECRET_KEY = 'xiqiguguai'
    # 数据库配置URI
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@localhost:3306/question'
    #关闭数据表修改提示
    SQLALCHEMY_TRACK_MODIFICATIONS = False