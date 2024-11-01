import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
cred = credentials.Certificate("")
firebase_admin.initialize_app(cred, {
    '':""
})
data = {
    "123":
        {
            "name": "Aluno 1",
            "major": "Ciencia da computacao",
            "starting_year" : 2021,
            "total_attendance" : 9,
            "standing" : 3,
            "year" : 3,
            "last_attendance_time" : "2022-06-11 12:00:00",

        },
    "321":
        {
            "name": "Aluno 2",
            "major": "Ciencia da computacao",
            "starting_year": 2021,
            "total_attendance": 4,
            "standing": 3,
            "year": 3,
            "last_attendance_time": "2022-06-11 12:00:00",

        }

}

ref = db.reference('Students')


for key,value in data.items():
    ref.child(key).set(value)