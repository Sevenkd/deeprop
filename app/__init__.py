# encoding: utf-8
import os, logging
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from logging.handlers import RotatingFileHandler

app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig') # ProductionConfig  DevelopmentConfig
app.secret_key = app.config["SECRETE_KEY"]

# login manager 登录管理
login_manager = LoginManager()
login_manager.setup_app(app)
login_manager.login_view = "main.login"
login_manager.login_message = u"您是未授权用户，请先登录系统."

# 数据库
db = SQLAlchemy(app) 

# logger 日志
logger = logging.getLogger()
logger_format = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
file_handler = RotatingFileHandler("logs/webserver.log", 'a', 10 * 1024 * 1024, 10) #日志文件的大小限制1 兆，保留最后 10 个日志文件作为备份
file_handler.setFormatter(logger_format)
file_handler.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logger_format)
logger.setLevel(logging.INFO)
logger.addHandler(file_handler)
logger.addHandler(console)
logger.info('DeepROP wechat startup . . .')


# 路由蓝本
from .main import main
app.register_blueprint(main)
