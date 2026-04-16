import sys
import psutil
import json
import os
import webbrowser
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QHBoxLayout, QVBoxLayout, QMenu, QFrame
from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtGui import QFont, QAction, QPixmap, QIcon

def aladin_kaynak_yolu(goreceli_yol):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, goreceli_yol)

class AladinDraggableWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.aladin_settings = "aladin_ayarlar.json"
        self.aladin_github_url = "https://github.com/tezalaaddin"

        # Pencere Ayarları
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # Düzen Oluşturma
        self.aladin_main_layout = QHBoxLayout()
        self.aladin_main_layout.setContentsMargins(10, 8, 10, 8)
        self.aladin_main_layout.setSpacing(12)

        # LOGO (aladin_icon_logo.png)
        self.aladin_logo_label = QLabel()
        # DOSYA ADINI BURADA GÜNCELLEDİM
        self.aladin_logo_path = aladin_kaynak_yolu("aladin_icon_logo.png") 
        
        if os.path.exists(self.aladin_logo_path):
            pix = QPixmap(self.aladin_logo_path)
            self.aladin_logo_label.setPixmap(pix.scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            # Logo bulunamazsa terminale hata basar ve emoji gösterir
            print(f"Hata: {self.aladin_logo_path} bulunamadı!")
            self.aladin_logo_label.setText("🧞")
            self.aladin_logo_label.setFont(QFont("Segoe UI", 20))

        self.aladin_main_layout.addWidget(self.aladin_logo_label)

        # HIZ VERİLERİ
        self.aladin_speed_layout = QVBoxLayout()
        self.aladin_speed_layout.setSpacing(0)

        self.aladin_up_label = QLabel("↑ 0 KB/s")
        self.aladin_up_label.setFont(QFont("Consolas", 10, QFont.Bold))
        self.aladin_up_label.setStyleSheet("color: #00FF00; border: none; background: transparent;")

        self.aladin_down_label = QLabel("↓ 0 KB/s")
        self.aladin_down_label.setFont(QFont("Consolas", 10, QFont.Bold))
        self.aladin_down_label.setStyleSheet("color: #00E5FF; border: none; background: transparent;")

        self.aladin_speed_layout.addWidget(self.aladin_up_label)
        self.aladin_speed_layout.addWidget(self.aladin_down_label)
        self.aladin_main_layout.addLayout(self.aladin_speed_layout)

        # TASARIM
        self.aladin_frame = QFrame()
        self.aladin_frame.setStyleSheet("""
            background-color: rgba(15, 15, 15, 220); 
            border-radius: 12px; 
            border: 1px solid #d4af37;  /* Altın rengi ince kenarlık */
        """)
        self.aladin_frame.setLayout(self.aladin_main_layout)
        
        self.aladin_container = QVBoxLayout(self)
        self.aladin_container.setContentsMargins(0, 0, 0, 0)
        self.aladin_container.addWidget(self.aladin_frame)

        # Uygulama İkonunu Ayarla
        if os.path.exists(self.aladin_logo_path):
            self.setWindowIcon(QIcon(self.aladin_logo_path))

        self.aladin_old_pos = None
        self.aladin_last_up = psutil.net_io_counters().bytes_sent
        self.aladin_last_down = psutil.net_io_counters().bytes_recv

        self.aladin_konum_yukle()

        self.aladin_timer = QTimer()
        self.aladin_timer.timeout.connect(self.aladin_guncelle)
        self.aladin_timer.start(1000)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.aladin_old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.aladin_old_pos is not None:
            delta = QPoint(event.globalPos() - self.aladin_old_pos)
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.aladin_old_pos = event.globalPos()
            self.aladin_konum_kaydet()

    def mouseReleaseEvent(self, event):
        self.aladin_old_pos = None

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("background-color: #222; color: white; border: 1px solid #444;")
        
        about_act = QAction("🧞 About tezalaaddin", self)
        about_act.triggered.connect(lambda: webbrowser.open(self.aladin_github_url))
        menu.addAction(about_act)
        
        menu.addSeparator()

        exit_act = QAction("Kapat", self)
        exit_act.triggered.connect(QApplication.instance().quit)
        menu.addAction(exit_act)
        
        menu.exec(event.globalPos())

    def format_hiz(self, b):
        if b < 1024**2: return f"{b/1024:.0f} KB/s"
        return f"{b/1024**2:.1f} MB/s"

    def aladin_guncelle(self):
        try:
            cnt = psutil.net_io_counters()
            up = cnt.bytes_sent - self.aladin_last_up
            down = cnt.bytes_recv - self.aladin_last_down
            self.aladin_last_up, self.aladin_last_down = cnt.bytes_sent, cnt.bytes_recv
            self.aladin_up_label.setText(f"↑ {self.format_hiz(up)}")
            self.aladin_down_label.setText(f"↓ {self.format_hiz(down)}")
        except: pass

    def aladin_konum_kaydet(self):
        with open(self.aladin_settings, "w") as f:
            json.dump({"x": self.x(), "y": self.y()}, f)

    def aladin_konum_yukle(self):
        if os.path.exists(self.aladin_settings):
            with open(self.aladin_settings, "r") as f:
                d = json.load(f)
                self.move(d["x"], d["y"])
        else:
            ekran = QApplication.primaryScreen().size()
            self.move(ekran.width() - 300, ekran.height() - 150)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = AladinDraggableWidget()
    widget.show()
    sys.exit(app.exec())
