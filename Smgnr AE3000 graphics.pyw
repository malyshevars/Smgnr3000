# SAMOGONER AE 3000 графики разгонки 09.07.2025
# pip install PyQt5 psycopg2-binary pandas matplotlib

import sys
import os
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QDateTimeEdit,  # ИСПРАВЛЕНИЕ: заменили QDateEdit на QDateTimeEdit
    QFileDialog, QCheckBox
)
from PyQt5.QtCore import QDateTime  # ИСПРАВЛЕНИЕ: импорт для QDateTime

import config  # PG_HOST, PG_PORT, PG_DB, PG_USER, PG_PASSWORD

class TempPlotter(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("График температур")
        self.setGeometry(300, 300, 600, 250)  # ИСПРАВЛЕНИЕ: увеличили окно для удобства выбора времени
        self.df = None
        self.current_dir = None
        self.init_ui()
        self.check_db_availability()

    def init_ui(self):
        layout = QVBoxLayout()

        # Даты и время
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("С:"))
        self.start_datetime = QDateTimeEdit(calendarPopup=True)  # ИСПРАВЛЕНИЕ: QDateTimeEdit вместо QDateEdit
        self.start_datetime.setDateTime(QDateTime.currentDateTime())  # ИСПРАВЛЕНИЕ: по умолчанию текущее время
        self.start_datetime.setDisplayFormat("yyyy-MM-dd HH:mm")    # ИСПРАВЛЕНИЕ: формат с часами и минутами
        date_layout.addWidget(self.start_datetime)

        date_layout.addWidget(QLabel("По:"))
        self.end_datetime = QDateTimeEdit(calendarPopup=True)  # ИСПРАВЛЕНИЕ
        self.end_datetime.setDateTime(QDateTime.currentDateTime())  # ИСПРАВЛЕНИЕ
        self.end_datetime.setDisplayFormat("yyyy-MM-dd HH:mm")     # ИСПРАВЛЕНИЕ
        date_layout.addWidget(self.end_datetime)

        layout.addLayout(date_layout)

        # Чекбокс
        self.save_checkbox = QCheckBox("Сохранять график при построении")
        self.save_checkbox.setChecked(False)
        layout.addWidget(self.save_checkbox)

        # Загрузка из CSV
        self.load_csv_btn = QPushButton("Загрузить из CSV")
        self.load_csv_btn.clicked.connect(self.load_and_plot_csv)
        layout.addWidget(self.load_csv_btn)

        # Загрузка из БД
        self.load_db_btn = QPushButton("Загрузить из БД")
        self.load_db_btn.clicked.connect(self.load_and_plot_db)
        layout.addWidget(self.load_db_btn)

        self.setLayout(layout)

    def check_db_availability(self):
        try:
            conn = psycopg2.connect(
                host=config.PG_HOST,
                port=config.PG_PORT,
                dbname=config.PG_DB,
                user=config.PG_USER,
                password=config.PG_PASSWORD,
                connect_timeout=3
            )
            conn.close()
        except Exception:
            self.load_db_btn.setEnabled(False)
            QMessageBox.warning(
                self,
                "База данных недоступна",
                "Не удалось подключиться к PostgreSQL.\n"
                "Будет доступна только загрузка из CSV."
            )

    def load_and_plot_db(self):
        # ИСПРАВЛЕНИЕ: используем дату и время для фильтрации
        start_str = self.start_datetime.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        end_str   = self.end_datetime.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        try:
            conn = psycopg2.connect(
                host=config.PG_HOST,
                port=config.PG_PORT,
                dbname=config.PG_DB,
                user=config.PG_USER,
                password=config.PG_PASSWORD,
                connect_timeout=5
            )
            query = """
                SELECT timestamp, temperature_cube, temperature_cool
                FROM smgnLogs
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp
            """
            df = pd.read_sql(query, conn, params=(start_str, end_str), parse_dates=["timestamp"])
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка подключения к БД", str(e))
            return

        if df.empty:
            QMessageBox.information(
                self,
                "Нет данных",
                f"Нет записей за период {start_str} – {end_str}."
            )
            return

        df.set_index("timestamp", inplace=True)
        self.df = df
        # ИСПРАВЛЕНИЕ: в суффикс добавляем дату и время запроса
        now = datetime.now()
        suffix = f"{now.strftime('%Y-%m-%d_%H%M')}"
        self.plot_temp(f"DB_{suffix}")

    def load_and_plot_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        try:
            df = pd.read_csv(path, parse_dates=["timestamp"])
            df.set_index("timestamp", inplace=True)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка чтения CSV", str(e))
            return

        if df.empty:
            QMessageBox.information(self, "Пустой CSV", "Выбранный файл не содержит данных.")
            return

        self.df = df
        # запомним папку для автосохранения
        self.current_dir = os.path.dirname(path)
        filename = os.path.basename(path)
        # ИСПРАВЛЕНИЕ: добавляем время запроса к имени
        now = datetime.now()
        self.file_suffix = f"CSV_{filename}_{now.strftime('%Y-%m-%d_%H%M')}"
        self.plot_temp(self.file_suffix)

    def plot_temp(self, title_suffix=""):
        if self.df is None or self.df.empty:
            QMessageBox.information(self, "Нет данных", "Нет данных для отображения.")
            return

        plt.figure(figsize=(10, 5))
        plt.plot(self.df.index, self.df["temperature_cube"], label="Куб (°C)")
        plt.plot(self.df.index, self.df["temperature_cool"], label="Охлаждение (°C)")
        plt.xlabel("Время")
        plt.ylabel("Температура, °C")
        plt.title(f"Температуры {title_suffix}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()

        # автосохранение, если чекбокс установлен
        if self.save_checkbox.isChecked():
            filename = f"temperatures_{title_suffix}.png"
            if self.current_dir:
                out_path = os.path.join(self.current_dir, filename)
            else:
                out_path = filename
            # ИСПРАВЛЕНИЕ: сохраняем с уникальным именем, включающим время, чтобы избежать перезаписи
            plt.savefig(out_path, dpi=300)
            QMessageBox.information(self, "Сохранено", f"График сохранён в\n{out_path}")

        plt.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = TempPlotter()
    win.show()
    sys.exit(app.exec_())
