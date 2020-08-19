import datetime

class Config(object):
    SECRETE_KEY = 'faiowjfjiijwjfiisfhohhoq'

    #DataBase
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    IMG_FORMAT = ['.png', '.jpg', '.jpeg'] # 系统支持的图像格式

    UNKOWN_DATE = datetime.datetime(1980, 1, 1) # 当无法从txt文化中读取到日期数据时, 默认显示的日期

    UPLOADBASEPATH = '/root/dataspace/upload' # 上传文件储存路径

    ROP_SERVICE_URL = "http:/127.0.0.1:5006/tf/rop_predict_folder" # 模型诊断服务器的地址

    



    REPORT = '/root/ROP/database/report'
    DREPORT = '/root/ROP/database/dreport'
    STATIC_BASEDIR = ""
    EXPORT = STATIC_BASEDIR + '/root/ROP/database/export'
    BACKGROUND = STATIC_BASEDIR + '/app/static/img/DeepRop_diagnosis.png'
    D_BACKGROUND = STATIC_BASEDIR + '/app/static/img/diagnose_bg.png'
    FONTS = STATIC_BASEDIR + '/app/static/fonts/wqy-microhei.ttc'

    #pagination
    POSTS_PER_PAGE = 10

    #resource

    @staticmethod
    def init_app(app):
        pass

class DevelopmentConfig(Config):
    SQLALCHEMY_DATABASE_URI='mysql+pymysql://root:123456@47.102.130.25:3306/deeprop'


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI='mysql+pymysql://root:123456@47.102.130.25:3306/deeprop_origin'


config = {"development": DevelopmentConfig,
          "production": ProductionConfig,

          "default": DevelopmentConfig}









