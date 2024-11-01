import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db
from firebase_admin import storage
from datetime import datetime

# Initialize Firebase Admin SDK
cred = credentials.Certificate("")
firebase_admin.initialize_app(cred, {
    'databaseURL': "",
    'storageBucket': ""
})

bucket = storage.bucket()

cap = cv2.VideoCapture(0)
cap.set(3, 680)
cap.set(4, 480)

imgBackground = cv2.imread('Resources/background.png')

# Load the encoding file
print("Loading Encode File ...")
with open('EncodeFile.p', 'rb') as file:
    encodeListKnownWithIds = pickle.load(file)

encodeListKnown, studentIds = encodeListKnownWithIds
print("Encode File Loaded")

modeType = 0
counter = 0
id = -1
imgStudent = []
lastId = -1  # Variable to store the last recognized student ID
studentInfo = {}
currentStudentInfo = {}  # Variable to store current student info

def download_student_info(student_id):
    try:
        # Get student data from the database
        studentInfo = db.reference(f'Students/{student_id}').get()
        if studentInfo is None:
            print(f"No data found for student ID: {student_id}")
            return None, None

        # Get student image from storage
        blob = bucket.get_blob(f'Images/{student_id}.png')
        if blob is None:
            print(f"No image found for student ID: {student_id}")
            return studentInfo, None

        array = np.frombuffer(blob.download_as_string(), np.uint8)
        imgStudent = cv2.imdecode(array, cv2.IMREAD_COLOR)
        return studentInfo, imgStudent
    except Exception as e:
        print(f"Error downloading student info: {e}")
        return None, None

def clear_student_info():
    global currentStudentInfo, imgStudent
    currentStudentInfo = {}
    imgStudent = []

while True:
    success, img = cap.read()

    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)

    imgBackground[162:162 + 480, 55:55 + 640] = img

    # Draw a purple rectangle (not filled) on the screen
    top_left = (750, 10)
    bottom_right = (1200, 705)
    color = (242, 65, 110)  # BGR format for purple
    thickness = 100  # Thickness of the border
    cv2.rectangle(imgBackground, top_left, bottom_right, color, thickness)

    if faceCurFrame:
        for encodeFace, faceLoc in zip(encodeCurFrame, faceCurFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)

            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                id = studentIds[matchIndex]

                if id != lastId:
                    clear_student_info()
                    lastId = id
                    studentInfo, imgStudent = download_student_info(id)
                    if studentInfo is None:
                        continue
                    currentStudentInfo = studentInfo  # Update current student info

                    if 'last_attendance_time' in studentInfo:
                        datetimeObject = datetime.strptime(studentInfo['last_attendance_time'], "%Y-%m-%d %H:%M:%S")
                        secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                        if secondsElapsed > 30:
                            ref = db.reference(f'Students/{id}')
                            studentInfo['total_attendance'] += 1
                            ref.child('total_attendance').set(studentInfo['total_attendance'])
                            ref.child('last_attendance_time').set(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

                    modeType = 1
                    counter = 1

                # Display the student's name near the bounding box
                if currentStudentInfo and 'name' in currentStudentInfo:
                    print(studentInfo)
                    cv2.putText(imgBackground, currentStudentInfo['name'], (bbox[0], bbox[1] - 10),
                                cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 0, 255), 2)
                    cv2.putText(imgBackground, str(id), (bbox[0], bbox[1] + bbox[3] +30),
                                cv2.FONT_HERSHEY_COMPLEX, 0.6, (255, 0, 255), 2)

    if currentStudentInfo:  # If there is current student info, display it
        if counter <= 10:


            if imgStudent is not None:
                imgBackground[175:175 + 216, 875:875 + 216] = imgStudent

        counter += 1

        if counter >= 20:
            counter = 0

    else:
        counter = 0
        lastId = -1  # Reset lastId to allow new detection

    cv2.imshow("Face Attendance", imgBackground)
    cv2.waitKey(1)