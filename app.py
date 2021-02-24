from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QDialog,
    QApplication,
    QFileDialog,
    QMainWindow,
    QPushButton,
    QLabel,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QHBoxLayout,
    QGridLayout,
)
from PyQt5.QtGui import QPixmap, QDrag, QStandardItemModel
from PyQt5.uic import loadUi
from PyQt5 import Qt
import sys
import cv2
from PyQt5.QtCore import QSize, pyqtSignal, pyqtSlot, Qt, QThread, QTime, QTimer,Qt, QMimeData, QByteArray, QDataStream, QIODevice, QAbstractTableModel, QDateTime
import numpy as np
import face_recognition
import pickle
import pandas as pd
from datetime import date, datetime
from threading import Event
from face_registeration import register_face
import uuid
import os
from go_api import checkin_teamhero_go
from rq import Queue
from redis import Redis

class face_db():
    def __init__(self):
        self.known_face_names, self.known_face_encodings = pickle.load(open('face/faces.p', 'rb'))
    
    def update(self):
        known_faces = []
        known_face_names = []
        file = open("face/staff.txt", "r")
        lines = file.readlines()
        for line in lines:
            known_faces.append((f"{line.strip().split(' ')[0]}", f"face/{line.strip().split(' ')[0]}.jpg"))
            known_face_names.append(f"{line.strip()}")
        known_face_encodings = []
        for face in known_faces:
            # known_face_names.append(face[0])
            face_image = face_recognition.load_image_file(face[1])
            face_encoding = face_recognition.face_encodings(face_image)[0]
            known_face_encodings.append(face_encoding)
            # Dump face names and encoding to pickle
            pickle.dump((known_face_names, known_face_encodings), open("face/faces.p", "wb"))
        
    def load_data(self):
        self.known_face_names, self.known_face_encodings = pickle.load(open('face/faces.p', 'rb'))
        
        
        
class history_db():
    def __init__(self):
        try:
            self.history_df = pd.read_pickle("history/history.pkl")
        except:
            self.history_df = pd.DataFrame(columns=['name','date','time','check-in','img'])
            self.history_df.to_pickle("history/history.pkl")
        
    def load_data(self):
        self.history_df = pd.read_pickle("history/history.pkl")
        
face_db =  face_db()
face_db.update()
face_db.load_data()
history_db = history_db()

class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, frame):
        super().__init__()
        # self._run_flag = True
        self.running = Event()
        self.running.set()
        self.actionTaken = Event()
        self.playing = True
        
        self.frame = frame

    def run(self):
        while self.running.is_set():
            self.actionTaken.clear()
            while self.playing:
                self.read_frame()
            self.actionTaken.wait()
    
    def read_frame(self):
        # capture from web cam
        cap = cv2.VideoCapture("rtsp://admin:Sennalabs_@192.168.0.63/Streaming/Channels/101")
        while self.playing:
            ret, cv_img = cap.read()
            if ret:
                self.frame += 1
                self.change_pixmap_signal.emit(cv_img)
        # shut down capture system
        cap.release()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self.playing = False

    
    def get_current_frame(self):
        return self.frame

    def start_playing(self):
        self.playing = True
        self.actionTaken.set()
        
        
class DragButton(QPushButton):
    def __init__(self, text):
        super().__init__()
        self.setObjectName(text)
        self.setText(text)
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.RightButton:
            print('press')
        elif event.button() == Qt.LeftButton:
            # save the click position to keep it consistent when dragging
            self.mousePos = event.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() != Qt.LeftButton:
            return
        mimeData = QMimeData()
        # create a byte array and a stream that is used to write into
        byteArray = QByteArray()
       
        mimeData.setData('myApp/QtWidget', byteArray)
        drag = QDrag(self)
        # add a pixmap of the widget to show what's actually moving
        drag.setPixmap(self.grab())
        drag.setMimeData(mimeData)
        # set the hotspot according to the mouse press position
        drag.setHotSpot(self.mousePos - self.rect().topLeft())
        drag.exec_()
        
        
class RegisterPopup(QWidget):
    def __init__(self, main_thred):
        super().__init__()
        loadUi("ui/registration.ui", self)
        self.setStyleSheet("background-color: white;")
        self.thread = main_thred
        self.current_frame = 0
        self.disply_width = 431
        self.display_height = 351
        
        self.capture_button.clicked.connect(self.regis_face)
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()
        
    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        self.showimg = cv_img
        self.qt_img = self.convert_cv_qt(cv_img)
        self.register_image.setPixmap(self.qt_img)

    def convert_cv_qt(self, image):    
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = cv2.resize(image, (960, 720))
        
        h, w, ch = image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(
            image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888
        )
        p = convert_to_Qt_format.scaled(
            self.disply_width, self.display_height, Qt.KeepAspectRatio
        )
        return QPixmap.fromImage(p)
    
    def regis_face(self):
        print(self.timeEdit.time().toString())
        if register_face(str(self.register_name.toPlainText()), self.showimg, self.timeEdit.time().toString()):
            face_db.load_data()
            print("success")
            self.checkin_label.setText("Success")
            self.checkin_label.setAlignment(Qt.AlignCenter)
            self.checkin_label.setStyleSheet("""QLabel{
                                            color:green;
                                            }""")
            self.checkin_label.repaint()

        else:
            print('fail')
            self.checkin_label.setText("Face not found")
            self.checkin_label.setAlignment(Qt.AlignCenter)
            self.checkin_label.setStyleSheet("""QLabel{
                                            color:red;
                                            }""")
            self.checkin_label.repaint()
            
# class MemberFrame()

class MemberPopup(QWidget):
    def __init__(self):
        super().__init__()
        loadUi("ui/member.ui", self)
        self.setStyleSheet("background-color: white;")
        
        self.member_layout = QGridLayout(self.member_widget)
        self.scrollArea = QScrollArea(self.member_widget)
        self.scrollArea.setWidgetResizable(True)
        self.member_layout.addWidget(self.scrollArea)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.member_layout = QGridLayout(self.scrollAreaWidgetContents)
        self.member_layout.setAlignment(Qt.AlignTop)
        self.member_list = []
        
        self.file = open("face/staff.txt", "r")
        self.lines = self.file.readlines()
        i,j =0,0
        for line in self.lines:
            self.member_list.append(f"{line.strip().split(' ')[0]}")
            self.member_layout.addWidget(self.create_frame_widget(f"{line.strip().split(' ')[0]}", f"{line.strip().split(' ')[1]}"),i,j)
            j+=1
            if j >= 4:
                i += 1
                j = 0
    
    def create_frame_widget(self, name, checkin_time):
        def remove_member(name, frame_widget):
            print("Remove ",name)
            with open("face/staff.txt", "r") as f:
                lines = f.readlines()
            with open("face/staff.txt", "w") as f:
                for line in lines:
                    if name not in line.strip("\n"):
                        f.write(line)
            face_db.update()
            face_db.load_data()
            
            
            self.member_layout.removeWidget(frame_widget)
            frame_widget.deleteLater()

            
            
        frame_layout = QVBoxLayout()
        frame_widget = QWidget()
        
        label_image = QLabel()
        pixmap = QPixmap(f'face/{name}.jpg')
        pixmap = pixmap.scaled(QSize(200,200))
        
        
        removebutton = QPushButton("Remove",self)
        removebutton.setStyleSheet("""QPushButton{
                                    color: white;
                                    background-color: red;
                                    border-style: outset;
                                    border-width: 2px;
                                    border-radius: 10px;
                                    border-color: beige;
                                    font: bold 14px;
                                    min-width: 10em;
                                    padding: 6px;
                                    max-width: 20px;
                                    margin-left: 5px;
                                }""")
        label_image.setPixmap(pixmap)
        label_text = QLabel()
        label_text.setText(f"{name} ({checkin_time})")
        label_text.setStyleSheet("""QLabel{
                                font: bold 15px;
                                margin-left: 45px;
                                }""")
        # label_text.setAlignment(Qt.AlignCenter)
        
        frame_layout.addWidget(removebutton)
        frame_layout.addWidget(label_image)
        frame_layout.addWidget(label_text)
        frame_widget.setLayout(frame_layout)
        removebutton.clicked.connect(lambda: remove_member(name, frame_widget))

        return frame_widget
        
class TableModel(QAbstractTableModel):

    def __init__(self, data):
        super(TableModel, self).__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.DisplayRole:
            value = self._data.iloc[index.row(), index.column()]
            return str(value)

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, index):
        return self._data.shape[1]

    def headerData(self, section, orientation, role):
        # section is the index of the column/row.
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:

                return str(self._data.columns[section])

            if orientation == Qt.Vertical:
                return str(self._data.index[section])


class HistoryPopup(QMainWindow):
    def __init__(self):
        super().__init__()
        loadUi("ui/history.ui", self)
        self.setStyleSheet("background-color: white;")
        
        history_db.history_df = pd.read_pickle("history/history.pkl")
        self.dateEdit.setDateTime(QDateTime.currentDateTime())

        self.history_df_filter = history_db.history_df[history_db.history_df['date'] == self.dateEdit.date().toPyDate()]
        self.model = TableModel(self.history_df_filter)
        self.tableView.setModel(self.model)
        self.tableView.resizeColumnsToContents()
        
        self.tableView.clicked.connect(self.table_clicked)
        
        self.search_button.clicked.connect(self.change_date)
        
    def change_date(self):
        self.history_df_filter = history_db.history_df[history_db.history_df['date'] == self.dateEdit.date().toPyDate()]
        self.model = TableModel(self.history_df_filter)
        self.tableView.setModel(self.model)
        self.tableView.clicked.connect(self.table_clicked)
        
        
    def table_clicked(self, item):
        cellContent = item.data()
        print("You clicked on {}".format(cellContent))
        self.mamber_popup = MemberHistoryPopup(str(cellContent),self.history_df_filter, self)
        self.mamber_popup.show()
    
    
        

class MemberHistoryPopup(QWidget):
    def __init__(self, name ,df, history_obj):
        super(MemberHistoryPopup, self).__init__()
        loadUi("ui/member_history_popup.ui", self)
        self.name = name
        self.date = date
        self.history = df
        self.history_obj = history_obj
        
        self.img_name = self.history[self.history['name'] == self.name].iloc[0]['img']

        
        self.name_label.setText(self.name)
        pixmap = QPixmap(f'history/capture/{self.img_name}.jpg')
        pixmap = pixmap.scaled(QSize(200,200))
        self.member_image.setPixmap(pixmap)
        
        self.delete_history.clicked.connect(lambda : self.delete_record())
        
    
    def delete_record(self):
        del_idx= self.history.index[(self.history['name'] == self.name)]
        self.history.drop(del_idx, inplace=True)
        self.history.to_pickle('history/history.pkl')
        print(self.history)
        os.remove(f'history/capture/{self.img_name}.jpg')
        self.close()
        
    def closeEvent(self, event):
        history_db.load_data()
        
        self.history_obj.model = TableModel(history_db.history_df)
        self.history_obj.tableView.setModel(self.history_obj.model)
        self.history_obj.tableView.clicked.connect(self.history_obj.table_clicked)
        
        
class App(QMainWindow):
    def __init__(self):
        super(App, self).__init__()
        self.setWindowTitle("Sennalabs check-in")
        loadUi("ui/mainwindow.ui", self)
        self.setStyleSheet("background-color: white;")
        self.setAcceptDrops(True)
        self.disply_width = 1360
        self.display_height = 850
        self.current_pos = 0
        self.checkin_label.setAlignment(Qt.AlignCenter)
        self.time_lcd.setDigitCount(8)  
        self.time_lcd.setStyleSheet("""QLCDNumber{
                                    background-color: white;
                                    border: 2px solid rgb(113, 113, 113);
                                    border-width: 2px;
                                    border-radius: 10px;
                                    color: red;
                                    }""")
        # change the number of digits displayed
        # self.setGeometry(30, 30, 800, 600)
        
        self.check_layout = QVBoxLayout(self.check_widget)
        self.scrollArea = QScrollArea(self.check_widget)
        self.scrollArea.setWidgetResizable(True)
        self.check_layout.addWidget(self.scrollArea)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.check_layout = QVBoxLayout(self.scrollAreaWidgetContents)
        self.check_layout.setAlignment(Qt.AlignTop)
        
        
        # self.add.clicked.connect(self.addButton)
        self.add.hide() 
               
        timer = QTimer(self)
        timer.timeout.connect(self.showlcd)
        timer.start(1000)
        self.showlcd()

        face_db.known_face_names, face_db.known_face_encodings = pickle.load(open('face/faces.p', 'rb'))
        try:
            self.check_in_df = pd.read_pickle("history/history.pkl")
        except:
            self.check_in_df = pd.DataFrame(columns=['name','date','time','check-in','img'])
            self.check_in_df.to_pickle("history/history.pkl")
        
        self.found_faces = []
        self.face_locations = []
        self.found_face_checkin = []
        
        self.register_button.clicked.connect(self.registerPopup)
        self.member_button.clicked.connect(self.memberPopup)
        self.history_button.clicked.connect(self.historyPopup)

        self.redis_conn = Redis()
        self.q = Queue(connection=self.redis_conn)

		
        # create the video capture thread
        self.current_frame = 0
        self.thread = VideoThread(self.current_frame)
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()
    
    def showlcd(self):
        time = QTime.currentTime()
        text = time.toString('hh:mm:ss')
        self.time_lcd.display(text)
        

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.img_window.setPixmap(qt_img)
        
    def draw_border(self, img, pt1, pt2, color, thickness, r, d):
        x1,y1 = pt1
        x2,y2 = pt2

        # Top left
        cv2.line(img, (x1 + r, y1), (x1 + r + d, y1), color, thickness)
        cv2.line(img, (x1, y1 + r), (x1, y1 + r + d), color, thickness)
        cv2.ellipse(img, (x1 + r, y1 + r), (r, r), 180, 0, 90, color, thickness)

        # Top right
        cv2.line(img, (x2 - r, y1), (x2 - r - d, y1), color, thickness)
        cv2.line(img, (x2, y1 + r), (x2, y1 + r + d), color, thickness)
        cv2.ellipse(img, (x2 - r, y1 + r), (r, r), 270, 0, 90, color, thickness)

        # Bottom left
        cv2.line(img, (x1 + r, y2), (x1 + r + d, y2), color, thickness)
        cv2.line(img, (x1, y2 - r), (x1, y2 - r - d), color, thickness)
        cv2.ellipse(img, (x1 + r, y2 - r), (r, r), 90, 0, 90, color, thickness)

        # Bottom right
        cv2.line(img, (x2 - r, y2), (x2 - r - d, y2), color, thickness)
        cv2.line(img, (x2, y2 - r), (x2, y2 - r - d), color, thickness)
        cv2.ellipse(img, (x2 - r, y2 - r), (r, r), 0, 0, 90, color, thickness)
        
        return img

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        image = cv2.resize(rgb_image, (1360, 850))
        self.current_frame = self.thread.get_current_frame()
        if self.current_frame % 29 == 0:
            # print("self.known_face_names", self.known_face_names)
            image = cv2.resize(image, (0,0), fx= 0.5, fy=0.5)
            image, self.found_faces, self.found_face_checkin, self.face_locations = self.find_face(image)
            for found_face, found_face_checkin,face_location in zip(self.found_faces, self.found_face_checkin, self.face_locations ):
                print(date.today())
                if found_face != 'Unknown':
                    self.check_in_df = pd.read_pickle("history/history.pkl")
                    if found_face not in self.check_in_df[self.check_in_df['date'] == date.today()]['name'].tolist():
                        top, right, bottom, left = face_location
                        img_uuid = str(uuid.uuid4().hex)
                        cv2.imwrite(f'history/capture/{img_uuid}.jpg', cv2.cvtColor(image[top:bottom, left:right], cv2.COLOR_BGR2RGB))
                        job = self.q.enqueue(checkin_teamhero_go,found_face, f'history/capture/{img_uuid}.jpg', 'Natural')

                        self.check_in_df = self.check_in_df.append({'name':found_face , 'date':date.today(), 'time':datetime.now().strftime("%H:%M:%S"), 'check-in': found_face_checkin , 'img': img_uuid}, ignore_index=True)
                        button = DragButton(str(found_face))
                        if found_face_checkin == 'late':
                            button.setStyleSheet("""QPushButton{
                                            color: white;
                                            background-color: red;
                                            border-style: outset;
                                            border-width: 2px;
                                            border-radius: 10px;
                                            border-color: beige;
                                            font: bold 14px;}""")
                        else:
                            button.setStyleSheet(f"""QPushButton{{
                                            color: white;
                                            background-color: green;
                                            border-style: outset;
                                            border-width: 2px;
                                            border-radius: 10px;
                                            border-color: beige;
                                            font: bold 14px;}}""")
                            
                        self.check_layout.addWidget(button)
                        self.checkin_label.setText(f'{found_face} has checked in')
                        self.checkin_label.setAlignment(Qt.AlignCenter)
                        self.check_in_df.to_pickle("history/history.pkl")
                    
                    
        for found_face, face_location in zip(self.found_faces, self.face_locations):
            top, right, bottom, left = face_location
            if found_face != 'Unknown':
                image = self.draw_border(image, (left*2-20, top*2-20), (right*2+20, bottom*2+20), (155, 232, 105),4, 15, 10)
                image = cv2.putText(image, found_face, (left*2-10,top*2+30), cv2.FONT_HERSHEY_SIMPLEX, 1, (155, 232, 105), 2, cv2.LINE_AA )
            else:
                image = self.draw_border(image, (left*2-20, top*2-20), (right*2+20, bottom*2+20), (255, 0, 105),4, 15, 10)
                image = cv2.putText(image, found_face, (left*2-10,top*2+30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 105), 2, cv2.LINE_AA )

            
        h, w, ch = image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(
            image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888
        )
        p = convert_to_Qt_format.scaled(
            self.disply_width, self.display_height, Qt.KeepAspectRatio
        )
        return QPixmap.fromImage(p)

    def find_face(self, cv_img):
        found_face = []
        found_face_checkin = []
        face_locations = face_recognition.face_locations(np.array(cv_img))
        face_encodings = face_recognition.face_encodings(np.array(cv_img), face_locations)
        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(face_db.known_face_encodings, face_encoding)
            face_distances = face_recognition.face_distance(face_db.known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)
            if min(face_distances) <= 0.4:
                name = face_db.known_face_names[best_match_index]
                found_face.append(name.split(' ')[0])
                d = datetime.strptime(name.split(' ')[1],'%H:%M:%S')
                dnow = datetime.now()
                if dnow.time() > d.time():
                    found_face_checkin.append("late")
                elif dnow.time() > d.time():
                    found_face_checkin.append("ontime")
            else:
                found_face.append('Unknown')
                found_face_checkin.append("late")
            
        return cv_img, found_face,found_face_checkin, face_locations 

    def addButton(self):
        self.current_pos += 1
        button = DragButton(str(self.current_pos), self)
        button.setStyleSheet("""QPushButton{
                            color: white;
                            background-color: red;
                            border-style: outset;
                            border-width: 2px;
                            border-radius: 10px;
                            border-color: beige;
                            font: bold 14px;""")
        self.check_layout.addWidget(button)
        self.check_in_df = pd.read_pickle("history/history.pkl")
        self.check_in_df = self.check_in_df.append({'name':str(self.current_pos) , 'date':date.today(), 'time':datetime.now().strftime("%H:%M:%S")}, ignore_index=True)
        self.check_in_df.to_pickle("history/history.pkl")
    
    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('myApp/QtWidget'):
            print("except")
            e.accept()

    def dropEvent(self, e):
        position = e.pos()
        print("position",position.x(),position.y())
        if position.x() > 1700 and position.y() > 611 :
            print("del")
            print(e.source().text())
            print(self.check_in_df)
            
            self.check_in_df = pd.read_pickle("history/history.pkl")
            del_idx = self.check_in_df.index[(self.check_in_df['name'] == e.source().text()) & (self.check_in_df['date'] == date.today())]
            self.check_in_df.drop(del_idx, inplace=True)
            self.check_in_df.to_pickle("history/history.pkl")
            self.check_layout.removeWidget(e.source())
            e.source().deleteLater()


        e.source().move(e.pos())
        e.setDropAction(Qt.MoveAction)
        e.accept()
    
    def registerPopup(self):
        # self.thread.stop()
        self.registerPopup = RegisterPopup(self.thread)
        self.registerPopup.show()


    def memberPopup(self):
        self.memPopup = MemberPopup()
        self.memPopup.show()
        
    def historyPopup(self):
        self.hisPopup = HistoryPopup()
        self.hisPopup.show()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())
