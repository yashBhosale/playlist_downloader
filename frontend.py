import sys
from PySide6.QtWidgets import (QWidget, QListWidget, QListWidgetItem, QLabel, 
                                QToolButton, QPushButton, QLineEdit, QStackedWidget, 
                                QHBoxLayout, QVBoxLayout, QSpacerItem,
                                QMenuBar, QMenu, QMainWindow, QFileDialog)
from PySide6.QtGui import QAction
from PySide6.QtCore import Signal
from downloader import Downloader
import qasync
from qasync import asyncSlot, QApplication
import asyncio
from functools import partial

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
        self.urlbar.setText("https://www.youtube.com/playlist?list=PLrGvezF6PokaPsPZn2TdL5pGc0Clm1rM-")
        self.fetch_button = QPushButton("Fetch")
        self.fetch_button.clicked.connect(self.fetch)

        self.urlbar_layout.addWidget(self.urlbar)
        self.urlbar_layout.addWidget(self.fetch_button)
        self.w.setLayout(self.urlbar_layout)

        self.list = QListWidget()
        
        self.add_item_to_list({ 'title': "test_item"})
        self.setLayout(QVBoxLayout(self))
        self.layout().addWidget(self.w)
        self.layout().addWidget(self.list)
  
    
    def add_item_to_list(self, item_data):
        item = QListWidgetItem()
        lwi = VideoListing( item_data["title"] )
        
        item.setSizeHint(lwi.sizeHint())
        self.list.addItem(item)
        self.list.setItemWidget(item, lwi )

    @asyncSlot()
    async def fetch(self):
        url = self.urlbar.text()
        add_func = self.add_item_to_list
        await self.youtube.fetch_playlist_item_ids(url, add_func)

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
    
    @asyncSlot()
    async def login(self):
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
       
    @asyncSlot()
    async def set_download_path(self):
        fd = QFileDialog(self)

        fd.setFileMode(QFileDialog.Directory)
        fd.setOption(QFileDialog.ShowDirsOnly)
        fd.exec()
        files = fd.selectedUrls()
        self.downloader.set_download_path(files[0].path())

    @asyncSlot()
    async def login(self):
        try:
            self.downloader.set_up_youtube()
            self.stack.setCurrentIndex(1)
        except:
            pass # create some kind of error

async def main():
    def close_future(future, loop):
        loop.call_later(10, future.cancel)
        future.cancel()

    loop = asyncio.get_event_loop()
    future = asyncio.Future()

    app = QApplication.instance()
    if hasattr(app, "aboutToQuit"):
        getattr(app, "aboutToQuit").connect(
            partial(close_future, future, loop)
        )

    widget = App()
    widget.resize(800, 600)
    widget.show()

    await future
    return True


if __name__ == "__main__":
    try:
        qasync.run(main())
    except asyncio.exceptions.CancelledError:
        sys.exit(0)
