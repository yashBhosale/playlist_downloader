import sys
from PySide6.QtWidgets import (QWidget, QListWidget, QListWidgetItem, QApplication,
                                QLabel, QToolButton, QPushButton, QLineEdit, 
                                QHBoxLayout, QVBoxLayout, QSpacerItem, QStackedWidget,
                                QMenuBar, QMenu, QMainWindow, QFileDialog)
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal
from downloader import Downloader


class VideoListing(QWidget):
    title = ""
    path = ""
    downloaded = False
    
    def set_path(self, path):
        self.path = path
    
    def set_downloaded(self, downloaded):
        self.downloaded = downloaded

    def __init__(self, vid_name):
        super().__init__()

        self._layout = QHBoxLayout()
        
        self.label = QLabel(vid_name)
        self.spacer = QSpacerItem(40, 10)
        
        self.tool_button = QToolButton()
        self.tool_button.setText("X")
        
        self._layout.addWidget(self.label)
        self._layout.addSpacerItem(self.spacer)
        self._layout.addWidget(self.tool_button)
        self.setLayout(self._layout)

class DownloaderScreen(QWidget):
    fetch_signal = Signal(str)
    youtube: Downloader

    def __init__(self, youtube):
        super().__init__()
        self.youtube = youtube

        self.w = QWidget()
        self.urlbar_layout = QHBoxLayout()
        self.urlbar = QLineEdit()
        self.urlbar.setPlaceholderText("Enter playlist URL")
        self.fetch_button = QPushButton("Fetch")
        self.fetch_button.clicked.connect(self.fetch)

        self.urlbar_layout.addWidget(self.urlbar)
        self.urlbar_layout.addWidget(self.fetch_button)
        self.w.setLayout(self.urlbar_layout)

        self.list = QListWidget()
        item = QListWidgetItem()
        lwi = VideoListing( "Lindy focus livestream" )
        
        item.setSizeHint(lwi.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, lwi )

        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.w)
        self.layout().addWidget(self.list)
   
    def fetch(self):
        url = self.urlbar.text()
        self.youtube.fetch_playlist_item_ids(url)

class LoginScreen(QWidget):
    
    logged_in = Signal()

    def __init__(self):
        super().__init__()
        self._layout = QVBoxLayout()
        self.label = QLabel("Please press the button to initiate authentication.")
        self.button = QPushButton("Push me")
        self.button.clicked.connect(self.login)
        self._layout.addWidget(self.label)
        self._layout.addWidget(self.button)
        self.setLayout(self._layout)

    def login(self):
        self.logged_in.emit()

class App(QMainWindow):
    def __init__(self):
        super().__init__()
        
        #backend stuff
        self.downloader = Downloader()
        
        #setting up individual components
        self.login_screen = LoginScreen()
        self.login_screen.logged_in.connect(self.login)
        
        self.download_screen = DownloaderScreen(self.downloader)
        
        #connecting everything
        self.stack = QStackedWidget()
        self.stack.addWidget(self.login_screen)
        self.stack.addWidget(self.download_screen)
        
        self.setCentralWidget(self.stack)
        
        set_download_path_action = QAction("Set Download Path", self)
        set_download_path_action.triggered.connect(self.set_download_path)
        
        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&File")
        fileMenu.addAction(set_download_path_action)
        
    def set_download_path(self):
        fd = QFileDialog(self)

        fd.setFileMode(QFileDialog.Directory)
        fd.setOption(QFileDialog.ShowDirsOnly)
        fd.exec()
        files = fd.selectedUrls()
        self.downloader.set_download_path(files[0].path())


    def login(self):
        try:
            self.downloader.set_up_youtube()
            self.stack.setCurrentIndex(1)
        except:
            pass # create some kind of error

if __name__ == "__main__":
    app = QApplication([])

    widget = App()
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())

