# coding=utf-8
from flask import render_template, redirect, request, url_for, session, jsonify, send_file
from flask_login import login_user, logout_user, current_user, login_required

from app import app, login_manager, db, logger, dbHelper
from app.main import main
from app.detect import fileOPHelper, ropDetectHelper
import utils.utils as myTools

import time, json, datetime, io, traceback, os, pdb, threading, hashlib
from urllib.parse import urlparse, urljoin
from PIL import Image

""" 跨域访问配置 """
@app.after_request
def cors(environ):
    environ.headers['Access-Control-Allow-Origin'] = request.environ.get('HTTP_ORIGIN', '*')
    environ.headers['Access-Control-Allow-Method'] = '*'
    environ.headers['Access-Control-Allow-Headers'] = '*'
    environ.headers['Access-Control-Allow-Credentials'] = 'true'
    return environ

# 主页
@main.route('/', methods=["GET"])
@login_required
def index():
    return render_template("index.html")

""" 用户登录 """
@main.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        try:
            username = request.form.get("username", None)
            password = request.form.get("password", None)
            if username is None or password is None:
                return jsonify(res="error", desc="交互错误:后台未收到用户名或密码")
            user = dbHelper.userLogin(username.strip(), password)
            if user is not None:
                login_user(user)
                print(user)
                return jsonify(res="success", desc="用户登录成功", role=user.role)
            else:
                return jsonify(res="error", desc="登录错误:用户名密码错误")
        except Exception as e:
            return jsonify(res="error", desc="服务器内部错误:{}".format(str(e)))
    else:
        return render_template("login.html")

""" user_loader """
@login_manager.user_loader
def load_user(id):
    return dbHelper.queryUserByID(id)

""" 通过deep　ROP网站上传病例 """
@main.route('/uploadInWeb', methods=["POST"])
@login_required
def uploadInWeb():
    try:
        # step 1: 先将文件存下来
        foldername = 'upload' + '_' + myTools.current_time(time_format='%Y%m%d%H%M%S')[1]
        path = os.path.join(app.config['UPLOADBASEPATH'], current_user.username, foldername)
        path = myTools.uniqueFileName(path)
        savedReocrds = fileOPHelper.save_folder(request.files.getlist("dfile"), path)
        
        # step 2: 检查文件格式, 将病例信息保存在数据库
        uploadState = []
        for recordPath in savedReocrds:
            desc = fileOPHelper.recordRopData(recordPath)
            if desc is not None:
                uploadState.append(desc)

        # TODO: step 3: 多线程诊断上传的ROP病例

        return jsonify(res="success", desc="上传完成", uploadState=uploadState)
    except Exception as e:
        return jsonify(res="error", desc="服务器内部错误:{}".format(str(e)))


