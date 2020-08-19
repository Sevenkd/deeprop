"""
    fileOPHelper.py
    对文件的一些操作, 如保存文件, 读取ROP病例中txt文件信息等
"""

from flask import session, send_from_directory, flash, render_template
from flask_login import current_user

from app import app, logger
import utils.utils as myTools
from app.dbHelper import dbHelper

import numpy as np
import json, pdb, traceback, hashlib, smtplib, time, xlwt, os, re, datetime, shutil


""" 
    保存用户上传的图像(仅保存, 不对图像进行分类移动等操作) 
    input: 
        dfile_list: 用户上传的dfile列表
        path: 文件存储路径
    return
        savedRecoerds: 成功保存的文件列表
"""
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

""" 
    解析上传病例数据的的信息, 将文件按照左右眼分别保存并将病例信息记录在数据库中 
    input:
        folderPath: 病例文件夹的路径
    return:
        folderPath: 成功解析的文件路径, 用于后续模型进行ROP诊断
        resolveDesc: 解析结果, 如果成功解析文件则返回空, 否则返回错误描述, 用于向前端返回上传结果
"""
def resolveRecord(folderPath):
    # 读取病例信息
    record = getRecordInfo(folderPath)
    if record is None:
        return None, "病例 [{}] 格式错误, 无法读取病例信息".format(os.path.split(f.filename)[1])

    # 将图像移动到对应的文件夹
    try:
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
    except Exception as e:
        return None, "病例 [{}] 格式错误, 无法读取病例信息: {}".format(os.path.split(f.filename)[1], str(e))

    # 保存病例信息
    uploadRecord = dbHelper.insertUploadRecord(folderPath, record)
    if uploadRecord is None:
        return None, "病例 [{}] 保存失败, 数据库保存错误".format(os.path.split(f.filename)[1])
    return folderPath, None

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

















