""" 前端datatable从这个接口获取每页显示的数据 """
@main.route('/serverside', methods=["GET", "POST"])
@login_required
def serverside():
    try:
        # 从数据库查询原始记录
        if session["searchcontent"]["search"] is True:
            keyWords = getSearchKeyWord(session["searchcontent"])
            infos = queryAW(session['USERNAME'], **keyWords)
        else:
            infos = []
        
        # 分页
        total_length = len(infos)
        page_start = int(request.values.get("iDisplayStart"))
        page_length = int(request.values.get("iDisplayLength"))
        if total_length > page_length:
            result = infos[page_start: page_start + page_length]
        else:
            result = infos

        # 准备数据格式
        result = serverSideOutput(result)
        output = {}
        output['sEcho'] = str(int(request.values['sEcho']))
        output['iTotalRecords'] = str(total_length)
        output['iTotalDisplayRecords'] = str(total_length)
        output['data'] = result
    except Exception as e:
        traceback.print_exc()
        output = {}
        output['sEcho'] = str(int(request.values['sEcho']))
        output['iTotalRecords'] = str(0)
        output['iTotalDisplayRecords'] = str(0)
        output['data'] = []
        
    return jsonify(output)

"""根据孕周和体重等综合查询数据"""
@main.route('/searchAW', methods=["GET"])
@login_required
def searchAW():
    searchcontent = {}
    try:
        searchcontent["patient_id"] = request.args.get("patient_id").strip()
        searchcontent["patient_name"] = request.args.get("patient_name").strip()
        searchcontent["date_start"] = request.args.get("date_start").strip()
        searchcontent["date_end"] = request.args.get("date_end").strip()
        searchcontent["upload_time_start"] = request.args.get("upload_time_start").strip()
        searchcontent["upload_time_end"] = request.args.get("upload_time_end").strip()
        searchcontent["gestation_start"] = request.args.get("gestation_start").strip()
        searchcontent["gestation_end"] = request.args.get("gestation_end").strip()
        searchcontent["weight_min"] = request.args.get("weight_min").strip()
        searchcontent["weight_max"] = request.args.get("weight_max").strip()
        searchcontent["search_way"] = request.args.get("search_way").strip()
        searchcontent["check"] = request.args.get("check").strip()
        
        if searchcontent["gestation_start"] == "" or searchcontent["gestation_start"] is None:
            searchcontent["gestation_start"] = 0
        if searchcontent["gestation_end"] == "" or searchcontent["gestation_end"] is None:
            searchcontent["gestation_end"] = 10000
        if searchcontent["weight_min"] == "" or searchcontent["weight_min"] is None:
            searchcontent["weight_min"] = 0
        if searchcontent["weight_max"] == "" or searchcontent["weight_max"] is None:
            searchcontent["weight_max"] = 10000000
    except:
        traceback.print_exc()
        searchcontent["patient_id"] = None
        searchcontent["patient_name"] = None
        searchcontent["date_start"] = None
        searchcontent["date_end"] = None
        searchcontent["upload_time_start"] = None
        searchcontent["upload_time_end"] = None
        searchcontent["gestation_start"] = None
        searchcontent["gestation_end"] = None
        searchcontent["weight_min"] = None
        searchcontent["weight_max"] = None
        searchcontent["search_way"] = None
        searchcontent["check"] = None
    return redirect(url_for('main.search'))

""" 下载导出后的数据 """
@main.route('/download', methods=["GET"])
@login_required
def download():
    if session['DATA']['multi'] != '':
        infos = query_multi(session['DATA']['multi'], session['USERNAME'])
    elif session['DATA']['timerange'] != '':
        infos = query_range(session['DATA'], session['USERNAME'])
    elif session['DATA']['date_start'] != '' and session['DATA']['date_end'] != '':
        infos = query_range(session['DATA'], session['USERNAME'])
    else:
        flash('请在右端输入需要导出的日期', 'warning')
        return redirect(url_for('main.export'))
    if len(infos) > 0:
        filename = file_op.export(infos)
        directory = os.path.join(app.config['EXPORT'], session['USERNAME'])
        return send_from_directory(directory, filename, as_attachment=True)
    else:
        flash('无数据可导出！', 'warning')
        return redirect(url_for('main.export'))


""" 通过网页上传数据 """
@main.route('/uploading', methods=['POST'])
@login_required
def uploading():
    foldername = 'upload' + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    num = 0
    while os.path.exists(os.path.join(app.config['UPLOAD'], session['USERNAME'], foldername)):
        num = num + 1
        foldername = 'upload' + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_' + str(num)
    path = os.path.join(app.config['UPLOAD'], session['USERNAME'], foldername)
    file_op.save_folder(request.files.getlist("dfile"), path)
    return jsonify(res="Success")

""" 通过自动上传系统上传数据 """
@main.route('/uploading_2', methods=['POST'])
def uploading_2():
    # 登录
    user_name = request.form.get("username").strip()
    password = request.form.get("password").strip()
    user = User.query.filter_by(username=user_name).first()
    if user is not None and user.verify_password(password):
        login_user(user)
        session['USERNAME'] = user_name
        session["searchcontent"] = {"search": False}
    
        # 保存数据
        foldername = 'upload' + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        num = 0
        while os.path.exists(os.path.join(app.config['UPLOAD'], session['USERNAME'], foldername)):
            num = num + 1
            foldername = 'upload' + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_' + str(num)
        path = os.path.join(app.config['UPLOAD'], session['USERNAME'], foldername)
        file_list = []
        for i in range(len(request.files)):
            file_list.append(request.files.get("file" + str(i)))
        dest_dirs = file_op.save_folder(file_list, path)

        # 诊断数据
        rop_result = dict()
        for dest_dir in dest_dirs:
            rop_result[dest_dir] = file_op.record_rop_data(dest_dir)
            
        return jsonify(res="upload success", data=rop_result)
    else:
        return jsonify(res="login error")
    return jsonify(res="unknown error")

""" 医生诊断过程中获取当前病例的眼底图像列表 """
@main.route('/getimg_list', methods=["GET"])
@login_required
def getimg_list():
    img_list = []
    if request.method == "GET":
        filepath = request.args.get("filepath")
        foldername = app.config['UPLOAD'] + '/' + session['USERNAME'] + '/' + filepath
        for filename in os.listdir(foldername):
            if os.path.isfile(foldername + '/' + filename) and os.path.splitext(filename)[1] in img_format:
                img_list.append([filepath + '/' + filename, 'normal'])
            elif os.path.isdir(foldername + '/' + filename):
                subfolder = filename
                for file in os.listdir(foldername + '/' + subfolder):
                    if os.path.isfile(foldername + '/' + subfolder + '/' + file) and os.path.splitext(file)[1] in img_format:
                        img_list.append([filepath + '/' + subfolder + '/' + file, subfolder])
    return jsonify(img_list)

""" 请求一张眼底图片 """
@main.route('/getimg', methods=["GET"])
@login_required
def getimg():
    imgID = request.args.get('imgID')
    imgpath = app.config['UPLOAD'] + '/' + session['USERNAME'] + '/' + imgID
    try:
        with open(imgpath, 'rb') as bites:
            return send_file(io.BytesIO(bites.read()), mimetype='image/jpg')
    except:
        return send_file('static/img/error_img.png',mimetype='image/jpg')

""" 请求系统诊断报告 """
@main.route('/get_reportimg', methods=["GET"])
@login_required
def get_reportimg():
    imgID = request.args.get('imgID')
    imgpath = app.config['REPORT'] + '/' + session['USERNAME'] + '/' + imgID
    try:
        with open(imgpath, 'rb') as bites:
            return send_file(io.BytesIO(bites.read()), mimetype='image/jpg')
    except:
        return send_file('static/img/error_img.png', mimetype='image/jpg')

""" 请求医生诊断报告 """
@main.route('/get_dreportimg', methods=["GET"])
@login_required
def get_dreportimg():
    imgID = request.args.get('imgID')
    imgpath = app.config['DREPORT'] + '/' + session['USERNAME'] + '/' + imgID
    try:
        with open(imgpath, 'rb') as bites:
            return send_file(io.BytesIO(bites.read()), mimetype='image/jpg')
    except:
        return send_file('static/img/error_img.png', mimetype='image/jpg')

""" 医生提交诊断, 并预览结果 """
@main.route('/give_diagnose', methods=["POST"])
@login_required
def give_diagnose():
    infos = dict()
    infos['id'] =request.form.get("id")
    result = request.form.getlist('infos')
    infos['patient_id'] = result[0].strip()
    infos['patient_name'] = result[1].strip()
    infos['gender'] = result[2].strip()
    infos['age'] = result[3].strip()
    infos['birth_weight'] = result[4].strip()
    infos['gestation_age'] = result[5].strip()
    infos['birth_way'] = result[6].strip()
    infos['birth_date'] = result[7].strip()
    infos['left_img'] = request.form.get("l_img").strip()
    infos['right_img'] = request.form.get("r_img").strip()
    infos['advice'] = request.form.get("advice").strip()
    try:
        infos = file_op.clear_format(infos)
        filename = file_op.draw_dreport(infos)
        update_diagnose(infos, filename)
        return jsonify(res="Success", report_name=filename)
    except Exception as e:
        logger.error('user {} update report error:{}'.format(session['USERNAME'], str(e)))
        return jsonify(res="Error", desc='user {} update report error:{}'.format(session['USERNAME'], str(e)))

""" 医生确认诊断 """
@main.route('/confirm_diagnose', methods=["POST"])
@login_required
def confirm_diagnose_2():
    record_id = int(request.form.get('record_id'))
    try:
        # 更新数据库
        confirm_diagnose(record_id)
        record = query_id(record_id)

        # 将结果发送给综合系统
        request_url = "http://47.102.130.25:5000/platform/get_rop_report"
        report_path = app.config['DREPORT'] + '/' + session['USERNAME'] + '/' + record.d_report
        input_data = {'patient_id': record.patient_id, 'report_path': report_path}
        req = urllib.request.Request(url=request_url, data=urllib.parse.urlencode(input_data).encode("utf-8"))
        try:
            res_data = urllib.request.urlopen(req)
        except Exception as e:
            logger.error('user {} no result from model: {}'.format(session['USERNAME'], str(e)))
        res_dict = res_data.read()

        return jsonify(res="success")
    except Exception as e:
        return jsonify(res="failed", desc='user {} confirm diagnose error:{}'.format(session['USERNAME'], str(e)))

""" 发送反馈意见 """
@main.route('/send_feedback', methods=["POST"])
@login_required
def send_feedback():
    content = request.form.get('content')
    try:
        file_op.send_email('feedback', 'mail/feedback', content=content)
        return jsonify(res="success")
    except:
        return jsonify(res="failed")

""" 自动上传系统等远程登录网站, 登录成功后不返回页面 """
@main.route('/login_outside', methods=['GET'])
def login_outside():
    if request.method == 'GET':
        user_name = request.args.get("user_name").strip()
        password = request.args.get("password").strip()
        user = User.query.filter_by(username=user_name).first()
        if user is not None and user.verify_password(password):
            login_user(user)
            session['USERNAME'] = user_name
            session["searchcontent"] = {"search": False}
            
            if user.role == 'admin':
                return "DeepEyes" + "({code: \"success\", des: \"login success !\", role: \"admin\"})"
            elif user.role == 'normal':
                return "DeepEyes" + "({code: \"success\", des: \"login success !\", role: \"normal\"})"
        else:
            return "DeepEyes" + "({code: \"fail\", des: \"error username or password !\", role: null})"
    return "DeepEyes" + "({code: \"method not allow !\"})"

""" 加载用户 """
@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

""" 用户退出登录 """
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('你已退出登录', 'info')
    return redirect(url_for('main.login'))


""" 页面路由请求 """

""" 医生编辑诊断结果页面 """
@main.route('/edit/<id>', methods=["GET", "POST"])
@login_required
def edit(id):
    infos = query_id(int(id))
    result = file_op.get_result(infos)
    try:
        advice = infos.d_advice
    except:
        advice = ''
    return render_template('edit.html', result=result, advice=advice)

""" 诊断结果页面 """
@main.route('/result', methods=['POST', 'GET'])
@login_required
def result():
    """
        医生上传数据成功后, 通过POST请求该页面对上传数据进行诊断, 并返回诊断结果
    """
    if request.method == 'POST':
        session['MODEL_ID'] = []
        for dest_dir in session['DEST_DIR']:
            file_op.record_rop_data(dest_dir)
        return redirect(url_for('main.result'))
    infos = query_upload(session['MODEL_ID'])
    return render_template('result.html', infos=infos)

""" 用户登录页面 """
@main.route('/', methods=["GET", "POST"])
@main.route('/login', methods=["GET", "POST"])
def login():
    """
        GET: 获取登录页面
        POST: 用户登录
    """
    form = LoginForm()
    if request.method == "POST":
        if form['username'].data is None or form['password'].data is None:
            flash('请输入用户名或密码')
            return render_template('login.html', form=form)
        user = User.query.filter_by(username=form['username'].data.strip()).first()
        if user is not None and user.verify_password(form['password'].data.strip()):
            login_user(user)
            session['USERNAME'] = form['username'].data.strip()
            session["searchcontent"] = {"search": False}
            if user.role == 'admin':
                return redirect(url_for('auth.administer'))
            elif user.role == 'normal':
                return redirect(url_for('main.index'))
        flash('用户名或密码错误')
    return render_template('login.html', form=form)

""" 数据查询页面 """
@app.route('/test', methods=["GET"])
@login_required
def test():
    if session.get("searchcontent", None) is None:
        session["searchcontent"] = {"search": False} # 查询标记位, 标记用户是否提交了查询请求
    return render_template('test.html')

@main.route('/search', methods=["GET", "POST"])
@login_required
def search():
    return redirect(url_for('test'))

""" 今日诊断页面 """
@main.route('/today', methods=["GET", "POST"])
@login_required
def today():
    infos = query_today(session['USERNAME'])
    return render_template('today.html', infos=infos)

""" 数据导出页面 """
@main.route('/export', methods=["GET", "POST"])
@login_required
def export():
    """
        GET: 渲染数据导出页面
        POST: 下载导出的数据
    """
    if request.method == "POST":
        multi = request.form.get('multi')
        timerange = request.form.get('range')
        date_start = request.form.get('start')
        date_end = request.form.get('end')
        session['DATA']={'multi': multi, 'timerange': timerange, 'date_start': date_start, 'date_end': date_end}
        return redirect(url_for('main.download'))
    return render_template('export.html')

""" 联系我们页面 """
@main.route('/contact')
@login_required
def contact():
    return render_template('contact.html')





""" 暂时弃用, 留作数据统计 """
""" 查询系统结果和医生标记不一致的记录 """
@main.route('/searchUnsame', methods=["GET", "POST"])
@login_required
def searchUnsame():
    if request.method == "POST":
        return redirect(url_for('main.searchUnsame'))
    try:
        patient_id = request.args.get("patient_id").strip()
        patient_name = request.args.get("patient_name").strip()
        date_start = request.args.get("date_start").strip()
        date_end = request.args.get("date_end").strip()
        upload_time_start = request.args.get("upload_time_start").strip()
        upload_time_end = request.args.get("upload_time_end").strip()
        
        print("patient_id:", patient_id, "patient_name:", patient_name, "date:", date_start, date_end, "upload_time:", upload_time_start, upload_time_end)
        
        infos = query_unsame(session['USERNAME'], patient_id, patient_name, date_start, date_end, upload_time_start, upload_time_end)
    except:
        infos = []
    return render_template('search.html', infos=infos)


def insertUser():
    username = 'rop_test'
    passwd = '123456'
    role = 'normal'
    pass_hash = generate_password_hash(passwd)
    print(pass_hash) 



