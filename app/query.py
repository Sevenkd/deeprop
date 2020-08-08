from .models import Rop_info, User
import datetime
from app import app, db
import time
from sqlalchemy import and_, or_, func
import pdb
period_time = {'day':1, 'week':7, 'month':30, 'trimonth':90}

""" 查询今日诊断病例 """
def query_today(doctor_name):#查询今日诊断
    return Rop_info.query.filter(
        and_(Rop_info.upload_time.like('%' + time.strftime('%Y-%m-%d') + '%'),
             Rop_info.doctor_name == doctor_name)
    ).order_by(db.desc(Rop_info.upload_time)).all()

def query_username():
    return User.query.filter(User.role=='normal').all()

""" 根据id查询rop_info记录 """
def query_id(id):
    return Rop_info.query.filter_by(id=id).first()

def query_report(foldername):
    return Rop_info.query.filter_by(right_report=foldername).first()

def insert_model_result(id, l_model_result, l_report, r_model_result, r_report, iris_imgs):
    Rop_info.query.filter_by(id=id).update({Rop_info.left_model_result:l_model_result,
                                            Rop_info.left_report: l_report,
                                            Rop_info.right_model_result: r_model_result,
                                            Rop_info.right_report: r_report,
                                            Rop_info.iris_img: iris_imgs})

def update_info(id, left_result, right_result, diff_result, remarks):
    return Rop_info.query.filter(Rop_info.id == id).\
        update({Rop_info.doctor_left_result: left_result,
                Rop_info.doctor_right_result: right_result,
                Rop_info.diff_result: diff_result,
                Rop_info.remarks: remarks})

def update_report(id, filename):
    return Rop_info.query.filter(Rop_info.id == id).\
        update({Rop_info.right_report: filename})
    
def doctor_update(infos, filename):
    return Rop_info.query.filter(Rop_info.id == infos['id']).\
        update({Rop_info.patient_id:infos['patient_id'],
                Rop_info.patient_name:infos['patient_name'],
                Rop_info.gender:infos['gender'],
                Rop_info.age:infos['age'],
                Rop_info.birth_weight:infos['birth_weight'],
                Rop_info.gestation_age:infos['gestation_age'],
                Rop_info.birth_way:infos['birth_way'],
                Rop_info.birth_date:infos['birth_date'],
                Rop_info.left_img:infos['left_img'],
                Rop_info.right_img:infos['right_img'],
                Rop_info.right_report:filename,
                Rop_info.advice:infos['advice']})
    
def update_diagnose(infos, filename):
    Rop_info.query.filter(Rop_info.id == infos['id']).update(
        {Rop_info.patient_id:infos['patient_id'],
        Rop_info.patient_name:infos['patient_name'],
        Rop_info.gender:infos['gender'],
        Rop_info.age:infos['age'],
        Rop_info.birth_weight:infos['birth_weight'],
        Rop_info.gestation_age:infos['gestation_age'],
        Rop_info.birth_way:infos['birth_way'],
        Rop_info.birth_date:infos['birth_date'],
        Rop_info.left_img:infos['left_img'],
        Rop_info.right_img:infos['right_img'],
        Rop_info.d_report:filename,
        Rop_info.d_advice:infos['advice'],
        Rop_info.diagnosed:0})
    db.session.commit()
    return 

def confirm_diagnose(id):
    Rop_info.query.filter(Rop_info.id==id).update({Rop_info.diagnosed:1})
    db.session.commit()
    return
    
""" 通过id列表批量查询rop_info数据 """
def query_upload(id_list):
    infos = []
    for id in id_list:
        result = Rop_info.query.filter_by(id=id).first()
        infos.append(result)
    return infos

def query_multi(multi, doctor_name):
    multi = multi.split(',')
    results = []
    counter = 0
    for _, date in enumerate(multi):
        result = Rop_info.query.filter(
            and_(Rop_info.upload_time.like('%' + datetime.datetime.strptime(date.strip(), '%m/%d/%Y').strftime('%Y-%m-%d') + '%'),
                 Rop_info.doctor_name == doctor_name)).order_by(db.desc(Rop_info.upload_time)).all()
        length = len(result)
        results[counter:counter + length] =  result
        counter = counter + length
    return results

def query_range(data, doctor_name):
    if data['timerange'] != '':
        start_time, end_time = data['timerange'].split('-')
        start = datetime.datetime.strptime(start_time.strip(), '%m/%d/%Y')
        end = datetime.datetime.strptime(end_time.strip(), '%m/%d/%Y') + datetime.timedelta(days=1)
        result = Rop_info.query.filter(
                and_(Rop_info.upload_time.between(start.strftime('%Y-%m-%d'),end.strftime('%Y-%m-%d')),
                     Rop_info.doctor_name == doctor_name)).order_by(db.desc(Rop_info.upload_time)).all()
    else:
        result = Rop_info.query.filter(
                and_(Rop_info.upload_time.between(datetime.datetime.strptime(data['date_start'].strip(), '%m/%d/%Y').strftime('%Y-%m-%d'), 
                                                  datetime.datetime.strptime(data['date_end'].strip(), '%m/%d/%Y').strftime('%Y-%m-%d')),
                     Rop_info.doctor_name == doctor_name)).order_by(db.desc(Rop_info.upload_time)).all()
    return result

# 查询不一致标注
def query_unsame(doctor_name, patient_id, patient_name, date_start, date_end, upload_time_start, upload_time_end):
    if doctor_name == "":
        print("no name ")
        return []
    
    sql = "select * from (select * from rop_info where doctor_name = '{}'".format(doctor_name)
    
    if patient_id != "":
        sql += "and patient_id = '{}'".format(patient_id)
        
    if patient_name != "":
        sql += "and patient_name = '{}'".format(patient_name)
        
    if date_start != '' and date_end != '':
        date_time_start = datetime.datetime.strptime(date_start, '%m/%d/%Y')
        date_time_end = datetime.datetime.strptime(date_end, '%m/%d/%Y') + datetime.timedelta(days=1)
        sql += "and date between '{}' and '{}'".format(date_time_start, date_time_end)
    
    if upload_time_start != '' and upload_time_end != '':
        upload_start = datetime.datetime.strptime(upload_time_start, '%m/%d/%Y')
        upload_end = datetime.datetime.strptime(upload_time_end, '%m/%d/%Y') + datetime.timedelta(days=1)
        sql += "and upload_time between '{}' and '{}'".format(upload_start, upload_end)
        
    sql += ") as temp where "
    
    if search_way == "and":
        sql += "gestation_age between {} and {} and birth_weight between {} and {} ".format(gestation_start, gestation_end, weight_min, weight_max)
    else:
        sql += "gestation_age between {} and {} or birth_weight between {} and {} ".format(gestation_start, gestation_end, weight_min, weight_max)
    
    sql += ") as temp2 where doctor_left_result != '__false' or doctor_right_result != '__false' order by upload_time desc;"
    
    print(sql)
    results = db.session.execute(sql)
    results = list(results)
    return results

# 综合查询
def queryAW(doctor_name, patient_id, patient_name, date_start, date_end, upload_time_start, upload_time_end, gestation_start, gestation_end, weight_min, weight_max, search_way, check):
    if doctor_name == '':
        return []
    
    sql = "select * from (select * from rop_info where doctor_name = '{}' ".format(doctor_name)

    if patient_id != "":
        sql += "and patient_id = '{}' ".format(patient_id)

    if patient_name != "":
        sql += "and patient_name = '{}' ".format(patient_name)

    if date_start != '' and date_end != '':
        date_time_start = datetime.datetime.strptime(date_start, '%m/%d/%Y')
        date_time_end = datetime.datetime.strptime(date_end, '%m/%d/%Y') + datetime.timedelta(days=1)
        sql += "and date between '{}' and '{}' ".format(date_time_start, date_time_end)
    
    if upload_time_start != '' and upload_time_end != '':
        upload_start = datetime.datetime.strptime(upload_time_start, '%m/%d/%Y')
        upload_end = datetime.datetime.strptime(upload_time_end, '%m/%d/%Y') + datetime.timedelta(days=1)
        sql += "and upload_time between '{}' and '{}' ".format(upload_start, upload_end)

    sql += ") as temp where "
    
    if search_way == "and":
        sql += "gestation_age between {} and {} and birth_weight between {} and {}".format(gestation_start, gestation_end, weight_min, weight_max)
    else:
        sql += "gestation_age between {} and {} or birth_weight between {} and {}".format(gestation_start, gestation_end, weight_min, weight_max)
        
    if check == "0":
        sql += " order by upload_time desc;"
    else:
        sql = "select * from (" + sql + ") as temp2 where doctor_left_result != '__false' or doctor_right_result != '__false' order by upload_time desc;"
    
    results = db.session.execute(sql);
    results = list(results)
    return results
    
# 弃用
def query_search(query, doctor_name):#按条件搜索查询
        if doctor_name == '':
            return []
        if query.get('date_start', '') != '' and query.get('date_end','') != '':
            start = datetime.datetime.strptime(query['date_start'].strip(), '%m/%d/%Y')
            end = datetime.datetime.strptime(query['date_end'].strip(), '%m/%d/%Y') + datetime.timedelta(days=1)
            results = Rop_info.query.filter(
                        and_(
                            and_(
                                Rop_info.date.between(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')),
                                Rop_info.patient_name.like('%' + query['name'] + '%')),
                            Rop_info.doctor_name == doctor_name)).order_by(db.desc(Rop_info.upload_time)).all()
        elif query.get('upload_time_start','') != '' and query.get('upload_time_end','') != '':
            start = datetime.datetime.strptime(query['upload_time_start'].strip(), '%m/%d/%Y')
            end = datetime.datetime.strptime(query['upload_time_end'].strip(), '%m/%d/%Y') + datetime.timedelta(days=1)
            results = Rop_info.query.filter(
                and_(
                    and_(
                        Rop_info.upload_time.between(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')),
                        Rop_info.patient_name.like('%' + query['name'] + '%')),
                    Rop_info.doctor_name == doctor_name)).order_by(db.desc(Rop_info.upload_time)).all()
        else:
            if query.get('pid','') != '':
                results = Rop_info.query.filter(
                            and_(
                                Rop_info.patient_id == query['pid'],
                                Rop_info.doctor_name == doctor_name)).order_by(db.desc(Rop_info.upload_time)).all()
            elif query.get('name', '') != '':
                results = Rop_info.query.filter(
                            and_(
                                Rop_info.patient_name.like('%' + query['name'] + '%'),
                                Rop_info.doctor_name == doctor_name)).order_by(db.desc(Rop_info.upload_time)).all()
            else:
                results = []
        return results

def query_user(period=None, username=None):
    if period and username:
        start = datetime.datetime.strptime(period[0].strip(), '%m/%d/%Y')
        end = datetime.datetime.strptime(period[1].strip(), '%m/%d/%Y') + datetime.timedelta(days=1)
        duration = int((end - start).days)
        times = [ (start + datetime.timedelta(days=i)).strftime('%Y-%m-%d') for i in range(duration+1)]
        totals = db.session.query(func.DATE_FORMAT(Rop_info.upload_time, '%Y-%m-%d'), func.count()).filter(
            and_(Rop_info.doctor_name == username,
                 Rop_info.upload_time.between(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))).\
            group_by(func.DATE_FORMAT(Rop_info.upload_time, '%Y-%m-%d')).all()
        rops = db.session.query(func.DATE_FORMAT(Rop_info.upload_time, '%Y-%m-%d'), func.count()).filter(
            and_(and_(Rop_info.doctor_name == username,
                      Rop_info.upload_time.between(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))),
                 or_(Rop_info.left_model_result.like('ROP%'),
                     Rop_info.right_model_result.like('ROP%')))).group_by(func.DATE_FORMAT(Rop_info.upload_time, '%Y-%m-%d')).all()
        return times, totals, rops
    elif period:
        if isinstance(period, list):
            start = datetime.datetime.strptime(period[0].strip(), '%m/%d/%Y')
            end = datetime.datetime.strptime(period[1].strip(), '%m/%d/%Y') + datetime.timedelta(days=1)
        else:    
            end = datetime.datetime.now()
            start = end - datetime.timedelta(days=period_time[period])
            end += datetime.timedelta(days=1)
        totals = db.session.query(User.username, func.count()).\
            join(Rop_info, User.username == Rop_info.doctor_name).filter(
            and_(User.role == 'normal',
                 Rop_info.upload_time.between(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))).group_by(User.username).all()
        users = db.session.query(User.username).filter(User.role == 'normal').all()
        rops = db.session.query(User.username, func.count()).\
            join(Rop_info, and_(User.username == Rop_info.doctor_name,
                                Rop_info.upload_time.between(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))).filter(
            and_(User.role == 'normal',
                 or_(Rop_info.left_model_result.like('ROP%'),
                     Rop_info.right_model_result.like('ROP%')))).group_by(User.username).all()
        return users, totals, rops
    elif username:
        end = datetime.datetime.now()
        start = end - datetime.timedelta(days=period_time['week'])
        times = [ (start + datetime.timedelta(days=(i+1))).strftime('%Y-%m-%d') for i in range(period_time['week'])]
        totals = db.session.query(func.DATE_FORMAT(Rop_info.upload_time, '%Y-%m-%d'), func.count()).filter(
            and_(Rop_info.doctor_name == username,
                 Rop_info.upload_time.between(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')))).\
            group_by(func.DATE_FORMAT(Rop_info.upload_time, '%Y-%m-%d')).all()
        rops = db.session.query(func.DATE_FORMAT(Rop_info.upload_time, '%Y-%m-%d'), func.count()).filter(
            and_(and_(Rop_info.doctor_name == username,
                      Rop_info.upload_time.between(start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d'))),
                 or_(Rop_info.left_model_result.like('ROP%'),
                     Rop_info.right_model_result.like('ROP%')))).group_by(func.DATE_FORMAT(Rop_info.upload_time, '%Y-%m-%d')).all()
        return times, totals, rops

    