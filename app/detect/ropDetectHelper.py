"""
    ropDetectHelper.py
    模型诊断ROP相关功能
"""
from app import app, logger
from flask import session
from PIL import Image, ImageDraw, ImageFont
import time, pdb, json, math, socket, hashlib, urllib, os, re, datetime, shutil
try:
    import cPickle as pickle
except:
    import pickle

timeout = 90
socket.setdefaulttimeout(timeout)

def detectROP(eyeFolderPath):
    request_url = app.config["ROP_SERVICE"]
    input_data = {'data_folder': eyeFolderPath, 'check_iris': 1}
    req = urllib.request.Request(url=request_url, data=urllib.parse.urlencode(input_data).encode("utf-8"))
    logger.info('Detecting: [{}]'.format(str(eyeFolderPath)))
    try:
        res_data = urllib.request.urlopen(req)
    except Exception as e:
        logger.error('Can not get result from model: {}'.format(str(e)))
        return None

    res_dict = eval(res_data.read())
    return res_dict

def rop_detect(dest_dir, info, rl):

    request_url = app.config["ROP_SERVICE"]
    msg_key = 'msg'
    # input_list = [input_data.tolist() for input_data in all_imgs]
    
    # input_list_json = json.dumps(input_list)
    input_data = {'data_folder': dest_dir, 'check_iris': 1}
    print('________________________dest_dir:' + dest_dir)
    req = urllib.request.Request(url=request_url, data=urllib.parse.urlencode(input_data).encode("utf-8"))
    try:
        res_data = urllib.request.urlopen(req)
    except Exception as e:
        logger.error('user {} no result from model: {}'.format(session['USERNAME'], str(e)))
        return('', '', '')

    res_dict = eval(res_data.read())
    print(res_dict)
    if int(res_dict['code']) == 1:
        if res_dict['diagnose'] == 'normal':
            pred_result = "正常"
            confidence_0 = res_dict['y_rop_normal'][0]
            confidence_1 = res_dict['y_rop_normal'][1]
        else:
            if res_dict['diagnose'] == "stage2":
                pred_result = "ROP 1/2期"
            else:
                pred_result = "ROP 3/4/5期"
            confidence = res_dict['y_rop_normal'][0]
            confidence_0 = res_dict['y_rop_normal'][1]
            confidence_2 = res_dict['y_stage_2_3'][0]
            confidence_3 = res_dict['y_stage_2_3'][1]
        iris_img = '$$'.join(res_dict['iris_imgs'])
    else:
        pred_result = res_dict[msg_key]
        return ('', '', '')

    #生成诊断报告
    img_name = set()
    for filename in os.listdir(dest_dir):
        if os.path.splitext(filename)[1].lower() in img_format and filename not in res_dict['iris_imgs']:
            img_name.add(filename)
        
    img_num = len(img_name)

    all_imgs = [0] * img_num
    size =  (352, 264)
    loc_x = 50
    loc_y = 400
    background = Image.open(app.config['BACKGROUND'])
    num = 0
    for i, filename in enumerate(img_name):
        # im_np = cv2.imread(app.config['UPLOADED_PATH']+"/"+ filename)
        # im_np = cv2.resize(im_np, (0,0), fx=0.2, fy=0.2)
        # all_imgs[i] = np.copy(im_np)
        # shutil.move(app.config['UPLOADED_PATH']+"/"+ filename, dest_dir+"/"+filename)
        im = Image.open(dest_dir + "/" + filename)
        # im1 = im.resize((320, 240), Image.ANTIALIAS)
        # im_np = np.asarray(im1, dtype='float32')
        # print(im_np.shape)
        # Use newaxis object to create an axis of length one
        # all_imgs[i] = np.copy(im_np)
        im = im.resize(size, Image.ANTIALIAS)
        # print(im)
        # print(im)
        if num < 9:
            background.paste(im, (loc_x, loc_y, loc_x + size[0], loc_y + size[1]))
            loc_x = loc_x + size[0] + 20
        num += 1
        if num % 3 == 0:
            loc_x = 50
            loc_y = loc_y + size[1] + 40


    ttfont = ImageFont.truetype(app.config['FONTS'], 36)
    # ttfont = ImageFont.truetype("uming.ttc",45)
    # ttfont = None
    draw = ImageDraw.Draw(background)
    if info['patient_name']:
        draw.text((50, 250), u'姓名: ' + info['patient_name'], fill=(0,0,0), font=ttfont)
    else:
        draw.text((50, 250), u'姓名: ', fill=(0,0,0), font=ttfont)
    if info['date']:
        draw.text((450, 250), u'检查日期: ' + info['date'].strftime('%Y-%m-%d %H:%M:%S'), fill=(0, 0, 0), font=ttfont)
    else:
        draw.text((450, 250), u'检查日期:', fill=(0, 0, 0), font=ttfont)
    draw.text((1000, 250), u'眼: ' + rl, fill=(0, 0, 0), font=ttfont)
    if info['date'] and info['birth_date']:
        draw.text((50, 300), u'出生距检查天数: ' + str((info['date'] - info['birth_date']).days), fill=(0,0,0), font=ttfont)
    else:
        draw.text((50, 300), u'出生距检查天数: ', fill=(0,0,0), font=ttfont)
    if info['gestation_age']:
        draw.text((450, 300), u'母亲孕周(天): ' + str(info['gestation_age']), fill=(0,0,0), font=ttfont)
    else:
        draw.text((450, 300), u'母亲孕周(天): ', fill=(0,0,0), font=ttfont)
    if info['birth_weight']:
        draw.text((800, 300), u'出生体重(克): ' + str(info['birth_weight']), fill=(0,0,0), font=ttfont)
    else:
        draw.text((800, 300), u'出生体重(克): ', fill=(0,0,0), font=ttfont)
    draw.text((50, 1280), u'诊断意见 :' + pred_result, fill=(0, 0, 0), font=ttfont)
    draw.text((100, 1370), u'类型', fill=(0, 0, 0), font=ttfont)
    draw.text((100, 1500), u'置信度', fill=(0, 0, 0), font=ttfont)
    if res_dict['diagnose'] == 'normal':
        draw.text((300, 1370), u'正常', fill=(0, 0, 0), font=ttfont)
        draw.text((500, 1370), u'ROP', fill=(0, 0, 0), font=ttfont)
        draw.text((300, 1500), u'%.2f%%' % (confidence_0 * 100.), fill=(0, 0, 0), font=ttfont)
        draw.text((500, 1500), u'%.2f%%' % (confidence_1 * 100.), fill=(0, 0, 0), font=ttfont)
    else:
        #print(confidence, confidence_2, confidence_3, confidence_2 * confidence * 100., str(confidence),
        #      str(confidence)[:6])
        draw.text((300, 1370), u'正常', fill=(0, 0, 0), font=ttfont)
        draw.text((500, 1370), u'ROP 1/2期', fill=(0, 0, 0), font=ttfont)
        draw.text((750, 1370), u'ROP 3/4/5期', fill=(0, 0, 0), font=ttfont)
        draw.text((300, 1500), u'%.2f%%' % (confidence * 100.), fill=(0, 0, 0), font=ttfont)
        draw.text((500, 1500), u'%.2f%%' % (confidence_2 * confidence_0 * 100.), fill=(0, 0, 0), font=ttfont)
        draw.text((750, 1500), u'%.2f%%' % (confidence_3 * confidence_0 * 100.), fill=(0, 0, 0), font=ttfont)
    filename = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()[:20]
    while(os.path.exists(os.path.join(app.config['REPORT'], filename + '.jpg'))):
        filename = hashlib.md5(str(time.time()).encode('utf-8')).hexdigest()[:20]
    background.save(app.config['REPORT'] + '/' + filename + '.jpg')
    img_name.clear()

    return pred_result, filename, iris_img


def rop_detect_1(dest_dir):
    request_url = app.config["ROP_SERVICE"]
    msg_key = 'msg'
    input_data = {'data_folder': dest_dir, 'check_iris': 1}
    req = urllib.request.Request(url=request_url, data=urllib.parse.urlencode(input_data).encode("utf-8"))
    logger.info('user {} dest_dir:{}'.format(session['USERNAME'], str(dest_dir)))
    try:
        res_data = urllib.request.urlopen(req)
    except Exception as e:
        logger.error('user {} no result from model: {}'.format(session['USERNAME'], str(e)))
        return ''

    res_dict = eval(res_data.read())
    print(res_dict)
    return res_dict

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
