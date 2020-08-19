
"""
    views.py
"""

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



"""
    file_op.py
"""

def get_result(infos):
    result = dict()
    result['id'] = infos.id
    result['patient_id'] = infos.patient_id
    result['patient_name'] = infos.patient_name
    result['birth_weight'] = infos.birth_weight
    result['gestation_age'] = infos.gestation_age
    result['birth_date'] = infos.birth_date.strftime('%Y年%m月%d日')
    result['age'] = infos.age
    result['gender'] = infos.gender
    result['birth_way'] = "" if infos.birth_way is None else infos.birth_way
    result['l_path'] = infos.lpath
    result['r_path'] = infos.rpath
    try:
        result['l_path_split'] = re.split('app', infos.lpath)[1]
    except:
        result['l_path_split'] = ''
    try:
        result['r_path_split'] = re.split('app', infos.rpath)[1]
    except:
        result['r_path_split'] = ''
    result['left_img'] = infos.left_img
    result['right_img'] = infos.right_img
    result['left_model_result'] = infos.left_model_result
    result['right_model_result'] = infos.right_model_result
    result['d_advice'] = "" if infos.d_advice is None else infos.d_advice
    return result

""" 在生成诊断报告过程中统一数据格式 """
def clear_format(infos):
    infos['birth_date'] = datetime.datetime.strptime(infos['birth_date'], '%Y年%m月%d日')
    try:
        infos['left_img'] = os.path.split(infos['left_img'])[1]
    except:
        infos['left_img'] = infos['left_img']
    try:
        infos['right_img'] = os.path.split(infos['right_img'])[1]
    except:
        infos['right_img'] = infos['right_img']
    return infos

""" 绘制医生诊断报告 """
def draw_dreport(infos):
    result = query_id(int(infos['id']))
    infos['l_path'] = result.lpath
    infos['r_path'] = result.rpath
    filename = draw_diagnose_report(infos, left_img=infos['left_img'], right_img=infos['right_img'])
    return filename

""" 导出数据 """
def export(infos):
    

    workbook = xlwt.Workbook(encoding='utf-8')
    worksheet = workbook.add_sheet('My Worksheet')
    font = xlwt.Font()  # Create the Font
    font.name = 'Times New Roman'
    font.height = 12 * 15
    style = xlwt.XFStyle()  # Create the Style
    style.font = font  # Apply the Font to the Style
    worksheet.col(0).width = 256 * 30
    worksheet.col(1).width = 256 * 15
    worksheet.col(2).width = 256 * 20
    worksheet.col(7).width = 256 * 40
    worksheet.col(8).width = 256 * 30
    worksheet.col(9).width = 256 * 40
    worksheet.write(0, 0, 'DeepRop导出记录', style)
    worksheet.write(1, 0, '导出时间：' + time.strftime('%Y-%m-%d %T'), style)
    worksheet.write(1, 1, '导出用户：' + session['USERNAME'], style)
    worksheet.write(2, 0, '病人姓名', style)
    worksheet.write(2, 1, '病人ID', style)
    worksheet.write(2, 2, '出生距检查天数', style)
    worksheet.write(2, 3, '母亲孕周', style)
    worksheet.write(2, 4, '出生体重(g)', style)
    worksheet.write(2, 5, '性别', style)
    worksheet.write(2, 6, '出生日期', style)
    worksheet.write(2, 7, '医生诊断', style)
    worksheet.write(2, 8, '系统诊断', style)
    worksheet.write(2, 9, '备注', style)
    for i, info in enumerate(infos):
        row = i + 3
        worksheet.write(row, 0, info.patient_name, style)
        worksheet.write(row, 1, info.patient_id, style)
        worksheet.write(row, 2, str((info.date - info.birth_date).days), style)
        worksheet.write(row, 3, info.gestation_age, style)
        worksheet.write(row, 4, info.birth_weight, style)
        worksheet.write(row, 5, info.gender, style)
        worksheet.write(row, 6, info.birth_date.strftime('%Y-%m-%d'), style)
        worksheet.write(row, 7, '左眼：' + translate_result(info.doctor_left_result) + ' 右眼：' + translate_result(
            info.doctor_right_result), style)
        if info.left_model_result == '' or info.left_model_result == None:
            left_model_result = '无信息'
        else:
            left_model_result = info.left_model_result
        if info.right_model_result == '' or info.right_model_result == None:
            right_model_result = '无信息'
        else:
            right_model_result = info.right_model_result
        worksheet.write(row, 8, '左眼：' + left_model_result + ' 右眼：' + right_model_result, style)
        worksheet.write(row, 9, info.remarks)
    # worksheet.write(1, 0, label = 'Formatted value', style) # Apply the Style to the Cell
    if not os.path.exists(os.path.join(app.config['EXPORT'], session['USERNAME'])):
        os.makedirs(os.path.join(app.config['EXPORT'], session['USERNAME']), exist_ok=True)
    filename = 'export' + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.xls'
    i = 0
    while os.path.exists(os.path.join(app.config['EXPORT'], session['USERNAME'], filename)):
        i = i + 1
        filename = 'export' + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_' + str(i) + '.xls'
    workbook.save(os.path.join(app.config['EXPORT'], session['USERNAME'], filename))
    return filename


def translate_result(result):
    period_t = dict(
        {'normal': '正常', 'stage1': 'rop1期', 'stage2': 'rop2期', 'stage3': 'rop3期', 'stage4': 'rop4期', 'stage5': 'rop5期',
        'other': '其它病症', '': ''})
    area_t = dict({'area1': '1区', 'area2': '2区', 'area3': '3区', '': ''})
    plus_t = dict({'true': '有plus病症', 'false': '', '': ''})
    tr = result.split('_')
    if len(tr) == 3:
        return(period_t.get(tr[0], '') + ' ' + area_t.get(tr[1], '') + ' ' + plus_t.get(tr[2], ''))
    elif len(tr) == 2:
        return(period_t.get(tr[0], '') + ' ' + tr[1])
    else:
        return 


""" 异步发送邮件 """
def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

""" 向开发人员发送邮件 """
def send_email(subject, template, **kwargs):
    # #msg = MIMEText(render_template(template + '.html', **kwargs), 'html', 'utf-8')
    # msg = MIMEText("开始test...")
    # msg['Subject'] = subject
    # msg['From'] = app.config['MAIL_USERNAME']
    # msg['To'] = ";".join(app.config['ADMINS'])
    # try:
    #     send_smtp = smtplib.SMTP()
    #     send_smtp.connect(app.config['MAIL_SERVER'])
    #     send_smtp.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
    #     send_smtp.sendmail(app.config['MAIL_USERNAME'], app.config['ADMINS'], msg.as_string())
    #     return True
    # except Exception as e:
    #     logger.error('user {} send email errer {}'.format(session['USERNAME'], str(e)))
    #     return False
    try:
        msg = Message(subject, sender=app.config['MAIL_USERNAME'], recipients=app.config['ADMINS'])
        msg.html = render_template(template + '.html', **kwargs)
        msg.body = render_template(template + '.txt', **kwargs)
        thr = Thread(target=send_async_email, args=[app, msg])
        thr.start()
        return thr
    except Exception as e:
        logger.error('user {} send email errer {}'.format(session['USERNAME'], str(e)))


"""
    detect.py
"""


""" 生成医生诊断报告 """
def draw_diagnose_report(info, left_img=None, right_img=None):
    os_p = (100, 1100); os_nor_p = (280, 1100); os_rop_mid_p = (550, 1100); os_rop_ser_p = (830, 1100);
    od_p = (100, 1200); od_nor_p = (280, 1200); od_rop_mid_p = (550, 1200); od_rop_ser_p = (830, 1200);
    background = Image.open(app.config['D_BACKGROUND'])
    ttfont = ImageFont.truetype(app.config['FONTS'], 28)
    draw = ImageDraw.Draw(background)
    size = (500, 400)
    """ 绘制病人基本信息 """
    try:
        draw.text((125, 245), info.get('patient_name','---'), fill=(0,0,0), font=ttfont)
        draw.text((425, 245), info.get('gender','---'), fill=(0,0,0), font=ttfont)
        draw.text((675, 245), str(info.get('birth_weight','---')), fill=(0,0,0), font=ttfont)
        draw.text((1000, 245), info.get('patient_id','---'), fill=(0,0,0), font=ttfont)
        draw.text((125, 315), info.get('age','---'), fill=(0,0,0), font=ttfont)
        draw.text((425, 315), str(info.get('gestation_age','---')), fill=(0,0,0), font=ttfont)
        draw.text((675, 315), info.get('birth_way','---'), fill=(0,0,0), font=ttfont)
        draw.text((900, 315), info['birth_date'].strftime('%Y年%m月%d日'), fill=(0,0,0), font=ttfont)
    except Exception as e:
        logger.error('user {} draw some infos on report error: {}'.format(session['USERNAME'], str(e)))

    """ 绘制眼底图像 """
    try:
        if not left_img:
            im = Image.open(os.path.join(app.config['UPLOAD'], session['USERNAME'], info['l_path'], info['left_img']))
        else:
            im = Image.open(os.path.join(app.config['UPLOAD'], session['USERNAME'], info['l_path'], info['left_img']))
        im = im.resize(size, Image.ANTIALIAS)
        background.paste(im, (40, 450, 540, 850))
    except Exception as e:
        logger.info('user {} read photos error when draw report: {}'.format(session['USERNAME'], str(e)))
    try:
        if not right_img:
            im = Image.open(os.path.join(app.config['UPLOAD'], session['USERNAME'], info['r_path'], info['right_img']))
        else:
            im = Image.open(os.path.join(app.config['UPLOAD'], session['USERNAME'], info['r_path'], info['right_img']))
        im = im.resize(size, Image.ANTIALIAS)
        background.paste(im, (640, 450, 1140, 850))
    except Exception as e:
        logger.info('user {} read photos error when draw report: {}'.format(session['USERNAME'], str(e)))
        
    """ 绘制医生诊断意见 """
    line_height = 920
    line_width = 39
    try:
        advice = info.get('advice')
        for j in range(math.ceil(len(advice)+2 / line_width)):
            if j == 0:
                draw.text((100, line_height), advice[0:line_width-2], fill=(0,0,0), font=ttfont)
            elif j == math.ceil(len(advice)+2 / line_width) - 1:
                draw.text((45, line_height), advice[j*line_width-2:len(advice)], fill=(0,0,0), font=ttfont)
            else:
                draw.text((45, line_height), advice[j*line_width-2:(j+1)*line_width-2], fill=(0,0,0), font=ttfont)
            line_height += 40
    except:
        logger.error('split string error')

    # 文件名等
    filename = 'dreport' + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.png'
    if not os.path.exists(os.path.join(app.config['DREPORT'], session['USERNAME'])):
        os.makedirs(os.path.join(app.config['DREPORT'], session['USERNAME']), exist_ok=True)
    num = 0
    while os.path.exists(os.path.join(app.config['DREPORT'], session['USERNAME'], filename)):
        num = num + 1
        filename = 'dreport' + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_' + str(num) + '.png'
    background.save(os.path.join(app.config['DREPORT'], session['USERNAME'], filename))
    return filename

os_p = (100, 1100); os_nor_p = (280, 1100); os_rop_mid_p = (550, 1100); os_rop_ser_p = (830, 1100);
od_p = (100, 1200); od_nor_p = (280, 1200); od_rop_mid_p = (550, 1200); od_rop_ser_p = (830, 1200);
def draw_report(l_model_result, r_model_result, info, left_img=None, right_img=None):
    background = Image.open(app.config['BACKGROUND'])
    ttfont = ImageFont.truetype(app.config['FONTS'], 28)
    draw = ImageDraw.Draw(background)
    size = (500, 400)
    try:
        draw.text((125, 245), info.get('patient_name','未知'), fill=(0,0,0), font=ttfont)
        draw.text((425, 245), info.get('gender','未知'), fill=(0,0,0), font=ttfont)
        draw.text((675, 245), str(info.get('birth_weight','未知')), fill=(0,0,0), font=ttfont)
        draw.text((1000, 245), info.get('patient_id','未知'), fill=(0,0,0), font=ttfont)
        draw.text((125, 315), info.get('age','未知'), fill=(0,0,0), font=ttfont)
        draw.text((425, 315), str(info.get('gestation_age','未知')), fill=(0,0,0), font=ttfont)
        draw.text((675, 315), info.get('birth_way','未知'), fill=(0,0,0), font=ttfont)
        draw.text((900, 315), info['birth_date'].strftime('%Y年%m月%d日'), fill=(0,0,0), font=ttfont)
    except Exception as e:
        logger.error('user {} draw some infos on report error: {}'.format(session['USERNAME'], str(e)))
    #draw.text((100, 1000), u'类型', fill=(0,0,0), font=ttfont)
    #draw.text((300, 1000), u'正常', fill=(0,0,0), font=ttfont)
    #draw.text((500, 1000), u'ROP 1/2 期', fill=(0,0,0), font=ttfont)
    #draw.text((750, 1000), u'ROP 3/4/5 期', fill=(0,0,0), font=ttfont)
    if l_model_result != '':
        if int(l_model_result['code']) == 1:
            if l_model_result['diagnose'] == 'normal':
                pred_result = "正常"
                confidence_0 = l_model_result['y_rop_normal'][0]
                confidence_1 = l_model_result['y_rop_normal'][1]
                draw.text(os_p, u'OS', fill=(0, 0, 0), font=ttfont)
                draw.text(os_nor_p, u'%.2f%%' % (confidence_0 * 100.), fill=(0, 0, 0), font=ttfont)
                draw.text(os_rop_mid_p, u'%.2f%%' % (confidence_1 * 100.), fill=(0, 0, 0), font=ttfont)
            elif l_model_result['diagnose'] == "anomaly":
                pred_result = "异常"
                draw.text(os_p, u'OS', fill=(0, 0, 0), font=ttfont)
                draw.text(os_nor_p, u'null', fill=(0, 0, 0), font=ttfont)
                draw.text(os_rop_mid_p, u'null', fill=(0, 0, 0), font=ttfont)
                draw.text(os_rop_ser_p, u'null', fill=(0, 0, 0), font=ttfont)
            else:
                if l_model_result['diagnose'] == "stage2":
                    pred_result = "ROP轻度"
                else:
                    pred_result = "ROP重度"
                confidence_0 = l_model_result['y_rop_normal'][0]
                confidence_1 = l_model_result['y_rop_normal'][1]
                confidence_2 = l_model_result['y_stage_2_3'][0]
                confidence_3 = l_model_result['y_stage_2_3'][1]
                draw.text(os_p, u'OS', fill=(0, 0, 0), font=ttfont)
                draw.text(os_nor_p, u'%.2f%%' % (confidence_0 * 100.), fill=(0, 0, 0), font=ttfont)
                draw.text(os_rop_mid_p, u'%.2f%%' % (confidence_2 * confidence_1 * 100.), fill=(0, 0, 0), font=ttfont)
                draw.text(os_rop_ser_p, u'%.2f%%' % (confidence_3 * confidence_1 * 100.), fill=(0, 0, 0), font=ttfont)
            draw.text((250, 865), pred_result, fill=(0, 0, 0), font=ttfont)
            try:
                if not left_img:
                    im = Image.open(os.path.join(app.config['UPLOAD'], session['USERNAME'], info['l_path'], l_model_result['imgs'][0]))
                else:
                    im = Image.open(os.path.join(app.config['UPLOAD'], session['USERNAME'], info['l_path'], info['left_img']))
                l_img = l_model_result['imgs'][0]
                im = im.resize(size, Image.ANTIALIAS)
                background.paste(im, (40, 450, 540, 850))
            except Exception as e:
                logger.info('user {} read photos error when draw report: {}'.format(session['USERNAME'], str(e)))
                l_img = ''
            lr = pred_result
        else:
            draw.text((100, 1100), u'OS', fill=(0, 0, 0), font=ttfont)
            draw.text((250, 865), u'无信息', fill=(0, 0, 0), font=ttfont)
            lr = ''
            l_img = ''
    else:
        draw.text((100, 1100), u'OS', fill=(0, 0, 0), font=ttfont)
        draw.text((250, 865), u'无信息', fill=(0, 0, 0), font=ttfont)
        lr = ''
        l_img = ''

    if r_model_result != '':
        if int(r_model_result['code']) == 1:
            if r_model_result['diagnose'] == 'normal':
                pred_result = "正常"
                confidence_0 = r_model_result['y_rop_normal'][0]
                confidence_1 = r_model_result['y_rop_normal'][1]
                draw.text(od_p, u'OD', fill=(0, 0, 0), font=ttfont)
                draw.text(od_nor_p, u'%.2f%%' % (confidence_0 * 100.), fill=(0, 0, 0), font=ttfont)
                draw.text(od_rop_mid_p, u'%.2f%%' % (confidence_1 * 100.), fill=(0, 0, 0), font=ttfont)
            elif r_model_result['diagnose'] == "anomaly":
                pred_result = "异常"
                draw.text(od_p, u'OD', fill=(0, 0, 0), font=ttfont)
                draw.text(od_nor_p, u'null', fill=(0, 0, 0), font=ttfont)
                draw.text(od_rop_mid_p, u'null', fill=(0, 0, 0), font=ttfont)
                draw.text(od_rop_ser_p, u'null', fill=(0, 0, 0), font=ttfont)
            else:
                if r_model_result['diagnose'] == "stage2":
                    pred_result = "ROP轻度"
                else:
                    pred_result = "ROP重度"
                confidence_0 = r_model_result['y_rop_normal'][0]
                confidence_1 = r_model_result['y_rop_normal'][1]
                confidence_2 = r_model_result['y_stage_2_3'][0]
                confidence_3 = r_model_result['y_stage_2_3'][1]
                draw.text(od_p, u'OD', fill=(0, 0, 0), font=ttfont)
                draw.text(od_nor_p, u'%.2f%%' % (confidence_0 * 100.), fill=(0, 0, 0), font=ttfont)
                draw.text(od_rop_mid_p, u'%.2f%%' % (confidence_2 * confidence_1 * 100.), fill=(0, 0, 0), font=ttfont)
                draw.text(od_rop_ser_p, u'%.2f%%' % (confidence_3 * confidence_1 * 100.), fill=(0, 0, 0), font=ttfont)
            draw.text((850, 865), pred_result, fill=(0, 0, 0), font=ttfont)
            try:
                if not right_img:
                    im = Image.open(os.path.join(app.config['UPLOAD'], session['USERNAME'], info['r_path'], r_model_result['imgs'][0]))
                else:
                    im = Image.open(os.path.join(app.config['UPLOAD'], session['USERNAME'], info['r_path'], info['right_img']))
                r_img = r_model_result['imgs'][0]
                im = im.resize(size, Image.ANTIALIAS)
                background.paste(im, (640, 450, 1140, 850))
            except Exception as e:
                logger.info('user {} read photos error when draw report: {}'.format(session['USERNAME'], str(e)))
                r_img = ''
            rr = pred_result
        else:
            draw.text((100, 1200), u'OD', fill=(0, 0, 0), font=ttfont)
            draw.text((850, 865), u'无信息', fill=(0, 0, 0), font=ttfont)
            rr = ''
            r_img = ''
    else:
        draw.text((100, 1200), u'OD', fill=(0, 0, 0), font=ttfont)
        draw.text((850, 865), u'无信息', fill=(0, 0, 0), font=ttfont)
        rr = ''
        r_img = ''

    line_height = 1375
    if info.get('advice'):
        try:
            advice = info.get('advice').split('__');
        except:
            logger.error('split string error');
        for i in range(len(advice)):
            if advice[i]:
                for j in range(math.ceil(len(advice[i]) / 30)):
                    if j == 0:
                        draw.text((40, line_height), u'{}.'.format(str(i+1)), fill=(0,0,0), font=ttfont)
                    if j == math.ceil(len(advice[i]) / 30) - 1:
                        draw.text((80, line_height), advice[i][j*30:len(advice[i])], fill=(0,0,0), font=ttfont)
                    else:
                        draw.text((80, line_height), advice[i][j*30:(j+1)*30], fill=(0,0,0), font=ttfont)
                    line_height += 40
    filename = 'report' + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '.png'
    if not os.path.exists(os.path.join(app.config['REPORT'], session['USERNAME'])):
        os.makedirs(os.path.join(app.config['REPORT'], session['USERNAME']), exist_ok=True)
    num = 0
    while os.path.exists(os.path.join(app.config['REPORT'], session['USERNAME'], filename)):
        num = num + 1
        filename = 'report' + '_' + datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_' + str(num) + '.png'
    background.save(os.path.join(app.config['REPORT'], session['USERNAME'], filename))
    return filename, lr, rr, l_img, r_img




