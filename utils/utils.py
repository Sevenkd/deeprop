"""
    utils.py
    常用基础函数
"""
import platform, datetime, random, os
from pytz import timezone

"""
    getOSType: 获取当前操作系统类别
"""
def getOSType():
    sys = platform.system()
    return sys

"""
    current_time: 获取东八区当前时间
    return:
        0: datetime.datetime类型时间
        1: str类型时间
"""
def current_time(time_format="%Y-%m-%d  %H:%M:%S", CST_TZ='Asia/Shanghai', UTC_TZ="UTC"):
    cst_tz = timezone(CST_TZ)
    utc_tz = timezone(UTC_TZ)
    china_time = datetime.datetime.utcnow().replace(tzinfo=utc_tz).astimezone(cst_tz)
    china_time_str = time2str(china_time, time_format=time_format)
    return china_time, china_time_str

"""
    time_delta: 获取两时间的时间差
    返回datetime.timedelta类型
"""
def time_delta(time1, time2, UTC_TZ="UTC"):
    utc_tz = timezone(UTC_TZ)
    time1 = time1.replace(tzinfo=utc_tz)
    time2 = time2.replace(tzinfo=utc_tz)
    delta = time1 - time2
    return delta

"""
    time2str: datetime格式时间转字符串
"""
def time2str(datetime, time_format="%Y-%m-%d  %H:%M:%S"):
    return datetime.strftime(time_format)

"""
    str2time: 字符串格式日期转datetime格式
"""
def str2time(time_str, time_format="%Y-%m-%d  %H:%M:%S"):
    return datetime.datetime.strptime(time_str, time_format)

"""
    自动监测当前文件名是否已经被占用, 如果占用的话自动为文件名添加数字后缀(1, 2, 3 . . . )
    需提供文件的全路径
"""
def uniqueFileName(filePath):
    postfix = 0
    while os.path.exists(filePath):
        postfix += 1
        filePath = filePath + '_' + str(postfix)
    return filePath

""" 
    get_noice: 获取随机字符串
    length - 随机字符串长度
    rtype - 生成字符串中包含何种字符(数字: digits, 小写字母: schar, 大写字母: lchar, 特殊字符: symbols)
"""
def get_noice_str(length, rtype=["all"]):
    r_str = ""
    if "digits" in rtype:
        r_str += "0123456789"
    if "schar" in rtype:
        r_str += "abcdefghijklmnopqrstuvwxyz"
    if "lchar" in rtype:
        r_str += "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if "symbols" in rtype:
        r_str += "!@#$%^&*()_-+="
    if "all" in rtype:
        r_str = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*()_-+="

    r = ""
    for _ in range(length):
        r += random.choice(r_str)
    return r