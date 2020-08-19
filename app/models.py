from app import db, app
from werkzeug.security import generate_password_hash, check_password_hash
import utils.utils as myTools
from flask_login import current_user


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(10))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User %r>' % (self.username)

# 上传表
class Upload(db.Model):
    __tablename__ = "upload"
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(16))
    patient_name = db.Column(db.String(32))
    gender = db.Column(db.String(10))
    birth_weight = db.Column(db.Integer)
    birth_date = db.Column(db.DateTime())
    gestation_age = db.Column(db.Integer)
    birth_way = db.Column(db.String(16))
    check_date = db.Column(db.DateTime())
    check_age = db.Column(db.String(16))
    lpath = db.Column(db.String(256))
    rpath = db.Column(db.String(256))
    left_model_result = db.Column(db.String(32))
    right_model_result = db.Column(db.String(32))
    iris_img = db.Column(db.String(128))             # 虹膜图像路径, 弃用
    left_img = db.Column(db.String(64))
    right_img = db.Column(db.String(64))
    model_report_path = db.Column(db.String(64))
    uploader = db.Column(db.String(16))
    upload_time = db.Column(db.DateTime())

    def __init__(self, recordDict):
        self.patient_id = recordDict.get("patient_id", "unkown")
        self.patient_name = recordDict.get("patient_name", "unkown")
        self.gender = recordDict.get("gender", "unkown")
        self.birth_weight = recordDict.get("birth_weight", "0")
        self.birth_date = recordDict.get("birth_date", app.config["UNKOWN_DATE"])
        self.gestation_age = recordDict.get("gestation_age", 0)
        self.birth_way = recordDict.get("birth_way", "unkwon")
        self.check_date = recordDict.get("check_date", app.config["UNKOWN_DATE"])
        self.check_age = recordDict.get("check_age", "unkown")
        self.lpath = recordDict.get("lpath", "")
        self.rpath = recordDict.get("rpath", "")
        self.uploader = recordDict.get("uploader", current_user.username)
        self.upload_time = myTools.current_time()[0]

        self.left_model_result = "diagnoseing"
        self.right_model_result = "diagnoseing"
        self.l_confidence = ""
        self.r_confidence = ""
        self.iris_img = ""
        self.left_img = ""
        self.right_img = ""
        self.model_report_path = ""

    def obj2dict(self):
        return{'id': self.id,
               'patient_id': self.patient_id,
               'patient_name': self.patient_name,
               'gender': self.gender,
               'birth_weight': self.birth_weight,
               'birth_date': myTools.time2str(self.birth_date, "%Y-%m-%d"),
               'gestation_age': self.gestation_age,
               'birth_way': self.birth_way,
               'check_date': myTools.time2str(self.check_date),
               'check_age': self.check_age,
               'lpath': self.lpath,
               'rpath': self.rpath,
               'left_model_result': self.left_model_result,
               'right_model_result': self.right_model_result,
               'iris_img': self.iris_img,
               'left_img': self.left_img,
               'right_img': self.right_img,
               'model_report_path': self.model_report_path,
               'uploader': self.uploader,
               'upload_time': myTools.time2str(self.upload_time)}

    def __repr__(self):
        return '<patient_name: {}, check_date: {}>',format(self.patient_name, self.check_date)

    def get_id(self):
        return self.id
