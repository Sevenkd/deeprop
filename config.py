import datetime

class Config(object):
    SECRETE_KEY = 'faiowjfjiijwjfiisfhohhoq'

    #DataBase
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    IMG_FORMAT = ['.png', '.jpg', '.jpeg'] # 系统支持的图像格式

    UNKOWN_DATE = datetime.datetime(1980, 1, 1)

    UPLOADBASEPATH = '/root/dataspace/upload'
    
    REPORT = '/root/ROP/database/report'
    DREPORT = '/root/ROP/database/dreport'
    STATIC_BASEDIR = ""
    EXPORT = STATIC_BASEDIR + '/root/ROP/database/export'
    BACKGROUND = STATIC_BASEDIR + '/app/static/img/DeepRop_diagnosis.png'
    D_BACKGROUND = STATIC_BASEDIR + '/app/static/img/diagnose_bg.png'
    ROP_SERVICE = "http:/127.0.0.1:5006/tf/rop_predict_folder"
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

if __name__ == "__main__":
    config = Config()








