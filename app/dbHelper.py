from app.models import User
from flask_login import current_user
import utils.utils as myTools
import os


""" 根据用户名查询User """
def queryUserByName(username):
    return User.query.filter(User.username==username).first()

""" 根据ID查询User """
def queryUserByID(id):
    return User.query.filter(User.id==id).first()

""" 用户登录时检查用户名密码是否正确 """
def userLogin(username, password):
    user = queryUserByName(username)
    if user is not None and user.verify_password(password):
        return user
    else:
        return None

""" 用户上传时将病例数据保存到数据库 """
def insertUploadRecord(folderPath, recordDict):
    # 检查左右眼路径
    separator = "/" if myTools.getOSType() == "Linux" else "\\"
    l_path = os.path.join(folderPath, 'OS')
    if os.path.exists(l_path):
        recordDict['lpath'] = l_path.split(current_user.username + separator)[1]
    else:
        recordDict['lpath'] = ''
    r_path = os.path.join(folderPath, 'OD')
    if os.path.exists(r_path):
        recordDict['rpath'] = r_path.split(current_user.username + separator)[1]
    else:
        recordDict['rpath'] = ''

    # 将病例文件插入数据库
    try:
        info = Upload(recordDict)
        db.session.add(info)
        db.session.commit()
        return info
    except Exception as e:
        db.session.rollback()
        logger.error('folder: [{}] insert error: {}'.format(folderPath, str(e)))
        return None







