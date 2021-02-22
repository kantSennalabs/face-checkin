import sys

from PyQt5.QtCore import Qt, QMimeData, QByteArray, QDataStream, QIODevice
from PyQt5.QtGui import QDrag
from PyQt5.QtWidgets import QPushButton, QWidget, QApplication, QGridLayout


class MyButton(QPushButton):
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
        
 

class Example(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()
        self.current_pos = 0

    def initUI(self):

        self.setAcceptDrops(True)

        self.addButton = QPushButton("add")
        #once click the addButton, call add() function
        self.addButton.clicked.connect(self.add)

        self.layout = QGridLayout()
        self.layout.addWidget(self.addButton, 0, 0)

        self.setLayout(self.layout)

        self.setWindowTitle('add')
        self.setGeometry(300, 300, 550, 450)
        self.show()
        
    
    def add(self):
        self.current_pos += 1
        button = MyButton(str(self.current_pos), self)
        
        self.layout.addWidget(button, 1 + self.current_pos, 0 + self.current_pos)

    def dragEnterEvent(self, e):
        if e.mimeData().hasFormat('myApp/QtWidget'):
            print("except")
            e.accept()

    def dropEvent(self, e):
        print("source", e.source())
        position = e.pos()
        print("position",position.x(),position.y())
        if position.x() > 400 and position.y() > 400 :
            print("del")
            e.source().deleteLater()

        e.source().move(e.pos())
        e.setDropAction(Qt.MoveAction)
        e.accept()


def main():
    
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    app.exec_()


if __name__ == '__main__':
    main()