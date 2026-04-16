import sys
import psutil
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction, QPixmap, QPainter, QColor, QFont
from PySide6.QtCore import QTimer, Qt

class AladinNetworkMonitor:
    def __init__(self):
        self.aladin_app = QApplication(sys.argv)
        self.aladin_app.setApplicationName("aladinNetWorkMonitor")
        self.aladin_app.setQuitOnLastWindowClosed(False)

        # Durum değişkeni: True = Çift İkon, False = Tek İkon
        self.aladin_dual_mode = False 
        self.aladin_icon_size = 32 
        
        self.aladin_last_up = psutil.net_io_counters().bytes_sent
        self.aladin_last_down = psutil.net_io_counters().bytes_recv

        # Birinci İkon (Upload veya Tekli Mod)
        self.aladin_tray_1 = QSystemTrayIcon(QIcon(), self.aladin_app)
        # İkinci İkon (Sadece Çift Modda Download için)
        self.aladin_tray_2 = QSystemTrayIcon(QIcon(), self.aladin_app)
        
        self.aladin_create_menu()
        
        self.aladin_timer = QTimer()
        self.aladin_timer.timeout.connect(self.aladin_update_info)
        self.aladin_timer.start(1000)

        self.aladin_update_info()
        self.aladin_tray_1.show()

    def aladin_create_menu(self):
        # Ortak menü oluştur (Her iki ikon için de geçerli)
        self.aladin_menu = QMenu()
        
        # Görünüm Değiştirme Seçeneği
        self.aladin_toggle_action = QAction("Görünüm: Yan Yana (Çift İkon)")
        self.aladin_toggle_action.triggered.connect(self.aladin_toggle_mode)
        self.aladin_menu.addAction(self.aladin_toggle_action)
        
        self.aladin_menu.addSeparator()
        
        self.aladin_exit_action = QAction("aladinNetWorkMonitor - Çıkış")
        self.aladin_exit_action.triggered.connect(sys.exit)
        self.aladin_menu.addAction(self.aladin_exit_action)
        
        self.aladin_tray_1.setContextMenu(self.aladin_menu)
        self.aladin_tray_2.setContextMenu(self.aladin_menu)

    def aladin_toggle_mode(self):
        self.aladin_dual_mode = not self.aladin_dual_mode
        if self.aladin_dual_mode:
            self.aladin_toggle_action.setText("Görünüm: Üst Üste (Tek İkon)")
            self.aladin_tray_2.show()
        else:
            self.aladin_toggle_action.setText("Görünüm: Yan Yana (Çift İkon)")
            self.aladin_tray_2.hide()
        self.aladin_update_info()

    def aladin_format(self, aladin_bytes):
        if aladin_bytes < 1024**2:
            return f"{aladin_bytes/1024:.0f}K"
        else:
            return f"{aladin_bytes/1024**2:.1f}M"

    def aladin_draw_text(self, text, color, pos="full"):
        pix = QPixmap(self.aladin_icon_size, self.aladin_icon_size)
        pix.fill(QColor("transparent"))
        painter = QPainter(pix)
        
        # Font büyüklüğü modlara göre ayarlanır
        f_size = 18 if self.aladin_dual_mode else 14
        font = QFont("Segoe UI", f_size, QFont.Bold)
        font.setPixelSize(f_size)
        painter.setFont(font)
        painter.setPen(QColor(color))

        if pos == "top":
            painter.drawText(pix.rect().adjusted(0, 0, 0, -16), Qt.AlignCenter, text)
        elif pos == "bottom":
            painter.drawText(pix.rect().adjusted(0, 16, 0, 0), Qt.AlignCenter, text)
        else:
            painter.drawText(pix.rect(), Qt.AlignCenter, text)
        
        painter.end()
        return QIcon(pix)

    def aladin_update_info(self):
        try:
            counters = psutil.net_io_counters()
            up_speed = counters.bytes_sent - self.aladin_last_up
            down_speed = counters.bytes_recv - self.aladin_last_down
            self.aladin_last_up, self.aladin_last_down = counters.bytes_sent, counters.bytes_recv

            up_txt = self.aladin_format(up_speed)
            down_txt = self.aladin_format(down_speed)

            if self.aladin_dual_mode:
                # Çift İkon Modu: Her veri kendi ikonunda kocaman
                self.aladin_tray_1.setIcon(self.aladin_draw_text(up_txt, "#00FF00"))
                self.aladin_tray_2.setIcon(self.aladin_draw_text(down_txt, "#00E5FF"))
                self.aladin_tray_1.setToolTip(f"Yükleme (UP): {up_txt}/s")
                self.aladin_tray_2.setToolTip(f"İndirme (DOWN): {down_txt}/s")
            else:
                # Tek İkon Modu: Üst üste sığdırılmış
                pix = QPixmap(self.aladin_icon_size, self.aladin_icon_size)
                pix.fill(QColor("transparent"))
                p = QPainter(pix)
                font = QFont("Segoe UI", 14, QFont.Bold)
                font.setPixelSize(14)
                p.setFont(font)
                
                p.setPen(QColor("#00FF00"))
                p.drawText(pix.rect().adjusted(0, 0, 0, -16), Qt.AlignCenter, up_txt)
                p.setPen(QColor("#00E5FF"))
                p.drawText(pix.rect().adjusted(0, 16, 0, 0), Qt.AlignCenter, down_txt)
                p.end()
                
                self.aladin_tray_1.setIcon(QIcon(pix))
                self.aladin_tray_1.setToolTip(f"UP: {up_txt} | DOWN: {down_txt}")

        except Exception as e:
            print(f"aladinError: {e}")

    def aladin_run(self):
        sys.exit(self.aladin_app.exec())

if __name__ == "__main__":
    aladin_monitor = AladinNetworkMonitor()
    aladin_monitor.aladin_run()
