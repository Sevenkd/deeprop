"""
    login.py: 管理用户登录
"""
from flask import render_template, redirect, request, url_for, session, jsonify, abort
from flask_login import login_user, logout_user, current_user, login_required

from app import app, login_manager, db, logger, dbHelper
from app.main import main

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
                return jsonify(res="success", desc="用户登录成功", role=user.role, next=session["next"])
            else:
                return jsonify(res="error", desc="登录错误:用户名密码错误")
        except Exception as e:
            return jsonify(res="error", desc="服务器内部错误:{}".format(str(e)))
    else:
        session["next"] = request.args.get("next", url_for("main.index"))
        return render_template("login.html")

""" user_loader """
@login_manager.user_loader
def load_user(id):
    return dbHelper.queryUserByID(id)

""" logout """
@main.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    if request.method == "POST":
        return jsonify(res="success")
    else:
        return "user logout"

""" 未授权用户登录处理(触发login_required执行逻辑) """
@login_manager.unauthorized_handler
def unauthorized():
    if request.method == "POST" or request.method == "post":
        return jsonify(res="error", desc="please login first")
    else:
        login_view = login_manager.login_view
        if not login_view:
            abort(401)

        redirect_url = url_for(login_view, next=request.url)
        return redirect(redirect_url)





