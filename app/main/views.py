"""
    main.py
"""
from flask import render_template, redirect, request, url_for, session, jsonify, send_file, abort, current_app
from flask_login import login_user, logout_user, current_user, login_required
from app.main.login import load_user

from app import app, login_manager, db, logger
from app.dbHelper import dbHelper

from app.main import main
from app.utils import fileOPHelper, ropDetectHelper
import myTools.utils as myTools

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

""" 通过deep　ROP网站上传病例 """
@main.route('/uploadInWeb', methods=["POST"])
@login_required
def uploadInWeb():
    try:
        # step 1: 先将文件存下来, 每次上传都会新生成一个单独的文件夹保存文件, 命名为 upload_timestamp
        foldername = 'upload' + '_' + myTools.current_time(time_format='%Y%m%d%H%M%S')[1]
        path = os.path.join(app.config['UPLOADBASEPATH'], current_user.username, foldername)
        path = myTools.uniqueFileName(path)
        savedReocrds = fileOPHelper.save_folder(request.files.getlist("dfile"), path)
        
        # step 2: 检查文件格式, 将病例信息保存在数据库
        records, uploadState = [], []
        for recordPath in savedReocrds:
            record, desc = fileOPHelper.resolveRecord(recordPath)
            if record is None:
                uploadState.append(desc)
            else:
                records.append(record)

        # TODO: step 3: 多线程诊断上传的ROP病例
        diagnoseThread = threading.Thread(target=ropDetectHelper.diagnoseRecords, args=(records,))
        diagnoseThread.setDaemon(True)
        diagnoseThread.start()

        return jsonify(res="success", desc="上传完成", uploadState=uploadState)
    except Exception as e:
        return jsonify(res="error", desc="internal server error:{}".format(str(e)))

""" 今日上传 """
def todayUpload():
    return
