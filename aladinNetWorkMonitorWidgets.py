import sys
import psutil
import json
import os
from PySide6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QMenu
from PySide6.QtCore import QTimer, Qt, QPoint
from PySide6.QtGui import QFont, QAction

class AladinDraggableWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        # Konum bilgilerini kaydetmek için dosya
        self.aladin_settings = "aladin_konum.json"
        
        # Pencereyi çerçevesiz, her zaman üstte ve görev çubuğunda görünmez yapıyoruz
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.aladin_layout = QVBoxLayout()
        self.aladin_label = QLabel("Başlatılıyor...")
        self.aladin_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        
        self.aladin_layout.addWidget(self.aladin_label)
        self.setLayout(self.aladin_layout)

        # Sürükleme için değişkenler
        self.aladin_old_pos = None

        # Hız verileri için başlangıç
        self.aladin_last_up = psutil.net_io_counters().bytes_sent
        self.aladin_last_down = psutil.net_io_counters().bytes_recv

        # Kayıtlı konumu yükle (Daha önce nereye bıraktıysan orada açılır)
        self.aladin_konum_yukle()

        self.aladin_timer = QTimer()
        self.aladin_timer.timeout.connect(self.aladin_guncelle)
        self.aladin_timer.start(1000)

    # --- SÜRÜKLEME MANTIĞI ---
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

    # --- SAĞ TIK MENÜSÜ ---
    def contextMenuEvent(self, event):
        menu = QMenu(self)
        kapat_aksiyon = QAction("aladinMonitor - Kapat", self)
        kapat_aksiyon.triggered.connect(QApplication.instance().quit)
        menu.addAction(kapat_aksiyon)
        menu.exec(event.globalPos())

    def format_hiz(self, byte_degeri):
        if byte_degeri < 1024**2:
            return f"{byte_degeri/1024:.0f} KB/s"
        return f"{byte_degeri/1024**2:.1f} MB/s"

    def aladin_guncelle(self):
        try:
            cnt = psutil.net_io_counters()
            up = cnt.bytes_sent - self.aladin_last_up
            down = cnt.bytes_recv - self.aladin_last_down
            self.aladin_last_up, self.aladin_last_down = cnt.bytes_sent, cnt.bytes_recv

            # Widget tasarımı ve renkleri
            self.aladin_label.setText(
                f'<div style="background-color: rgba(0,0,0,180); padding: 8px; border-radius: 8px; border: 1px solid #333;">'
                f'<span style="color:#00FF00;">↑ {self.format_hiz(up)}</span><br>'
                f'<span style="color:#00E5FF;">↓ {self.format_hiz(down)}</span>'
                f'</div>'
            )
        except: pass

    def aladin_konum_kaydet(self):
        with open(self.aladin_settings, "w") as f:
            json.dump({"x": self.x(), "y": self.y()}, f)

    def aladin_konum_yukle(self):
        if os.path.exists(self.aladin_settings):
            with open(self.aladin_settings, "r") as f:
                data = json.load(f)
                self.move(data["x"], data["y"])
        else:
            # İlk açılışta ekranın sağ altına yakın başlasın
            ekran = QApplication.primaryScreen().size()
            self.move(ekran.width() - 200, ekran.height() - 150)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = AladinDraggableWidget()
    widget.show()
    sys.exit(app.exec())
