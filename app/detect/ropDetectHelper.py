"""
    ropDetectHelper.py
    模型诊断ROP相关功能
"""
from app import app, logger
from app.dbHelper import dbHelper
import time, pdb, json, math, socket, hashlib, urllib, os, re, datetime, shutil, traceback


timeout = 90
socket.setdefaulttimeout(timeout)

""" 异步诊断眼底病例, 解析模型诊断结果, 将结果保存在数据库中 """
def diagnoseRecords(recordList):
    for record in recordList:
        try:
            logger.info("开始诊断病例[{}]...".format(record))
            if os.path.exists(record.lpath):
                logger.info("__左眼, folder path: [{}]".format(record.lpath))
                # step 1: 诊断病例
                resultDict = detectROP(record.lpath)
                # step 2: 解析模型诊断结果
                l_pred_result, l_confidence, l_typicalImg = resolveROPResult(resultDict)
            else:
                l_pred_result, l_confidence, l_typicalImg = None, None, None
            
            if os.path.exists(record.rpath):
                logger.info("__右眼, folder path: [{}]".format(record.rpath))
                # step 1: 诊断病例
                resultDict = detectROP(record.rpath)
                # step 2: 解析模型诊断结果
                r_pred_result, r_confidence, r_typicalImg = resolveROPResult(resultDict)
            else:
                r_pred_result, r_confidence, r_typicalImg = None, None, None

            # step 3: 将诊断结果插入数据库
            dbHelper.insertROPResult(record.id, l_pred_result, l_confidence, l_typicalImg, r_pred_result, r_confidence, r_typicalImg)

            logger.info("诊断完成.")
        except Exception as e:
            logger.info("病例 [{}] 诊断异常: {}".format(record.id, str(e)))
            logger.info(traceback.format_exc())
            logger.info("诊断完成.")
    return

""" 向模型服务器提交诊断请求, 返回诊断结果 """
def detectROP(dest_dir):
    try:
        request_url = app.config["ROP_SERVICE_URL"]
        input_data = {'data_folder': dest_dir, 'check_iris': 1}
        req = urllib.request.Request(url=request_url, data=urllib.parse.urlencode(input_data).encode("utf-8"))

        logger.info('start diagnose folder: [{}]'.format(str(dest_dir)))
        try:
            res_data = urllib.request.urlopen(req)
        except Exception as e:
            logger.error('no result from model: {}'.format(str(e)))
            return {"err_msg": str(e)}

        res_dict = eval(res_data.read())
    except Exception as e:
        res_dict = {"code": 0, "desc": "Exception in detectROP: "+str(e)}
        logger.info("Exception in detectROP for record [{}]".format(dest_dir))
        logger.info(traceback.format_exc())
    return res_dict

""" 解析服务器返回的结果json数组, 返回系统诊断结果, 置信度, 和典形图像 """
def resolveROPResult(resultDict):
    try:
        if not int(resultDict.get("code", 0)) != 1: # 诊断错误, 无结果
            desc = resultDict.get(desc)
            logger.info("获取后台诊断结果, 服务器无法诊断病例: {}".format(desc))
            return "无法诊断", None, None

        confidence = {}
        if resultDict['diagnose'] == 'normal':
            pred_result = "正常"
            confidence["正常"] = resultDict['y_rop_normal'][0]
            confidence["ROP"] = resultDict['y_rop_normal'][1]
        elif resultDict['diagnose'] == "anomaly":
            pred_result = "异常病例(不属于ROP筛查范围)"
        else:
            if resultDict['diagnose'] == "stage2":
                pred_result = "ROP轻度"
            else:
                pred_result = "ROP重度"
            confidence_0 = resultDict['y_rop_normal'][0]
            confidence_1 = resultDict['y_rop_normal'][1]
            confidence_2 = resultDict['y_stage_2_3'][0]
            confidence_3 = resultDict['y_stage_2_3'][1]
            confidence["正常"] = confidence_0
            confidence["ROP轻度"] = confidence_2 * confidence_1
            confidence["ROP重度"] = confidence_3 * confidence_1

        typicalImg = resultDict['imgs'][0]
    except Exception as e:
        logger.info("Exception in resolveROPResult: {}".format(str(e)))
        logger.info(traceback.format_exc())
        pred_result, confidence, typicalImg = "无法诊断", None, None
    
    return pred_result, confidence, typicalImg

