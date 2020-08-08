"""
    fileOPHelper.py
    对文件的一些操作, 如保存文件, 读取ROP病例中txt文件信息等
"""

from flask import session, send_from_directory, flash, render_template
from flask_login import current_user

from app import app, logger, db
from app.detect.ropDetectHelper import rop_detect, rop_detect_1, draw_report, draw_diagnose_report
# from ..query import query_multi, query_range, query_range, update_report, query_id
import utils.utils as myTools
from app import dbHelper

from email.mime.text import MIMEText
import numpy as np
from threading import Thread
import json, pdb, traceback, hashlib, smtplib, time, xlwt, os, re, datetime, shutil
try:
    import cPickle as pickle
except:
    import pickle


""" 保存用户上传的图像(仅保存, 不对图像进行分类移动等操作) """
def save_folder(dfile_list, path):
    savedRecoerds = [] # 将被成功保存的病例绝对路径保存下来, 后续将作为参数传递给ROP诊断功能模块
    for f in dfile_list:
        try:
            foldername = os.path.split(os.path.split(f.filename)[0])[1]
            folderPath = os.path.join(path, foldername) # full path
            if not os.path.exists(folderPath):
                os.makedirs(folderPath, exist_ok=True)
                savedRecoerds.append(folderPath) # 保存每例检查的第一个文件时会新建文件夹, 此时将文件夹路径保存在待检测列表中
            f.save(os.path.join(folderPath, os.path.split(f.filename)[1]))
        except Exception as e:
            logger.info("文件保存异常: [{}]: {}".format(os.path.split(f.filename)[1], str(e)))
    return savedRecoerds

""" 记录上传的病例信息 """
def recordRopData(folderPath):
    # 读取病例信息
    record = getRecordInfo(folderPath)
    if record is None:
        return "病例 [{}] 格式错误, 无法读取病例信息".format(os.path.split(f.filename)[1])

    # 将图像移动到对应的文件夹
    for filename in os.listdir(folderPath):
        if os.path.splitext(filename)[1].lower() in app.config["IMG_FORMAT"]:
            sampleName = os.path.splitext(filename)[0]
            txtName = sampleName + ".txt"
            eyeType = getRL(txtName, folderPath)
            if eyeType is not None:
                lpath = os.path.join(folderPath, eyeType)
                if not os.path.exists(lpath):
                    os.mkdir(lpath)
                shutil.move(os.path.join(folderPath, txtName), os.path.join(lpath, txtName))
                shutil.move(os.path.join(folderPath, filename), os.path.join(lpath, filename))
            else:
                logger.info('{}: can not gain right or left information'.format(filename))

    # 诊断ROP病例
    uploadRecord = dbHelper.insertUploadRecord(folderPath, record)
    if uploadRecord is None:
        return "病例 [{}] 保存失败, 数据库保存错误".format(os.path.split(f.filename)[1])
    return None

""" 从病例图像的描述文件中读取病例相关信息 """
def getRecordInfo(folderPath):
    info = dict()
    readFlag = False # readFlag标记后续过程是否成功读取到病例信息
    for filename in os.listdir(folderPath):
        if os.path.splitext(filename)[1] == '.txt':
            try:
                f = open(os.path.join(folderPath, filename), 'r', encoding='utf-8')
                content = f.read()
                f.close()
            except Exception as e:
                logger.error('{}: read txt file error {}'.format(filename, str(e)))
                continue

            try: # 病人姓名
                m = re.search('Name:.*', content)
                info['patient_name'] = re.sub('(Name:)|[,\n]', '', m.group(0)).strip()
                readFlag = True
            except:
                info['patient_name'] = '未知'

            try: # 病人ID
                m = re.search('Patient ID:.*', content)
                info['patient_id'] = re.sub('(Patient ID:)|[,\n]', '', m.group(0)).strip()
                readFlag = True
            except:
                info['patient_id'] = '未知'

            try: # 病人性别
                gender_m = dict({'female': '女', 'male': '男'})
                m = re.search('Gender:.*', content)
                info['gender'] = re.sub('(Gender:)|[,\n]', '', m.group(0)).strip()
                if info['gender'].lower() in gender_m.keys():
                    info['gender'] = gender_m[info['gender'].lower()]
                else:
                    info['gender'] = '未知'
                readFlag = True
            except:
                info['gender'] = '未知'

            try: # 婴儿出生体重
                m = re.search('Birth Weight:.*', content)
                info['birth_weight'] = int(re.sub('(Birth Weight:)|[,\n]', '', m.group(0)).strip())
                readFlag = True
            except:
                info['birth_weight'] = 0

            try: # 检查日期
                m = re.search('Started:.*', content)
                date = re.sub('(Started:)|[,\n]', '', m.group(0)).strip()
                info['check_date'] = myTools.str2time(date, '%A %B %d %Y %I:%M:%S %p') 
                readFlag = True
            except:
                info['check_date'] = app.config["UNKOWN_DATE"]

            try: # 婴儿出生日期, 年龄
                m = re.search('Date of Birth:.*', content)
                date = re.sub('(Date of Birth:)|[,\n]', '', m.group(0)).strip()
                info['birth_date'] = myTools.str2time(date, '%A %B %d %Y')
                if myTools.time_delta(info['check_date'], app.config["UNKOWN_DATE"]).days != 0:
                    info['check_age'] = caculate_age(info['check_date'], info['birth_date'])
                else:
                    info['check_age'] = "未知"
                readFlag = True
            except:
                info['birth_date'] = app.config["UNKOWN_DATE"]
                info['check_age'] = '未知'

            try: # 母亲孕周
                m = re.search('Gestation Age:.*', content)
                info['gestation_age'] = int(re.sub('(Gestation Age:)|[,\n]', '', m.group(0)).strip())
                readFlag = True # 如果readFlag为真, 说明至少有一项成功读取到了数据, txt文件符合格式要求
            except:
                info['gestation_age'] = 0
            
            if readFlag: # 如果readFlag不为真, 说明没有成功读取到数据, 继续尝试读取, 否则跳出循环
                break
    
    if not readFlag: # 如果没有成功读取到病例信息, 则返回None
        return None
    return info

""" 根据生日计算小孩的年龄(天) """
def caculate_age(today, birthday):
    days = myTools.time_delta(today, birthday).days
    return str(days) + "天"

""" 判断一张图像属于左眼还是右眼 """
def getRL(filename, path):
    try:
        f = open(os.path.join(path, filename), 'r', encoding='utf-8')
        content = f.read()
        f.close()
        try:
            m = re.search('SessionItem.ImageOf=.*', content)
            return re.sub('SessionItem.ImageOf=|[\n]', '', m.group(0)).strip()
        except:
            return None
    except Exception as e:
        logger.error('{}: read txt file error {}'.format(filename, str(e)))
        return None















period_t = dict(
    {'normal': '正常', 'stage1': 'rop1期', 'stage2': 'rop2期', 'stage3': 'rop3期', 'stage4': 'rop4期', 'stage5': 'rop5期',
     'other': '其它病症', '': ''})
area_t = dict({'area1': '1区', 'area2': '2区', 'area3': '3区', '': ''})
plus_t = dict({'true': '有plus病症', 'false': '', '': ''})

def translate_result(result):
    tr = result.split('_')
    if len(tr) == 3:
        return(period_t.get(tr[0], '') + ' ' + area_t.get(tr[1], '') + ' ' + plus_t.get(tr[2], ''))
    elif len(tr) == 2:
        return(period_t.get(tr[0], '') + ' ' + tr[1])
    else:
        return 

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
