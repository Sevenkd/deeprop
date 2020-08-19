"""
    statisiticHelper.py
    数据统计相关函数, 如每日上传统计等
"""
from app import db

""" 每日上传统计 """
def dailyUpload(startDate, endDate):
    sqlStr = """
        SELECT from_unixtime(upload_time, "%Y-%m-%d") as days, count(*) as uploadCount FROM deeprop.upload where "{}" <= upload_time <= "{}" group by days;
    """.format(startDate, endDate)
    return