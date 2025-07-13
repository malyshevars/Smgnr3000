import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QGridLayout, QMessageBox
)
from PyQt5.QtCore import Qt

def calculate_water_to_add(V_initial, C_initial, C_target):
    if C_target <= 0 or C_target >= C_initial:
        raise ValueError("Целевая концентрация должна быть >0 и < начальной.")
    c0 = C_initial / 100.0
    ct = C_target / 100.0
    return V_initial * (c0 / ct - 1)

def calculate_charcoal_mass(V_total, rate_g_per_l=25):
    return V_total * rate_g_per_l

class DilutionCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Калькулятор разведения спирта")
        self.init_ui()

    def init_ui(self):
        layout = QGridLayout()

        # Метки и поля ввода
        layout.addWidget(QLabel("Объём исходного раствора (л):"), 0, 0)
        self.input_volume = QLineEdit()
        self.input_volume.setPlaceholderText("например, 1.0")
        layout.addWidget(self.input_volume, 0, 1)

        layout.addWidget(QLabel("Начальная концентрация (%):"), 1, 0)
        self.input_c0 = QLineEdit()
        self.input_c0.setPlaceholderText("например, 40")
        layout.addWidget(self.input_c0, 1, 1)

        layout.addWidget(QLabel("Желаемая концентрация (%):"), 2, 0)
        self.input_ct = QLineEdit()
        self.input_ct.setPlaceholderText("например, 20")
        layout.addWidget(self.input_ct, 2, 1)

        # Кнопка расчёта
        self.btn_calc = QPushButton("Рассчитать")
        self.btn_calc.clicked.connect(self.on_calculate)
        layout.addWidget(self.btn_calc, 3, 0, 1, 2)

        # Вывод результатов
        self.result_water = QLabel("")
        self.result_charcoal = QLabel("")
        self.result_water.setAlignment(Qt.AlignCenter)
        self.result_charcoal.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.result_water, 4, 0, 1, 2)
        layout.addWidget(self.result_charcoal, 5, 0, 1, 2)

        self.setLayout(layout)

    def on_calculate(self):
        try:
            V0 = float(self.input_volume.text().replace(',', '.'))
            C0 = float(self.input_c0.text().replace(',', '.'))
            Ct = float(self.input_ct.text().replace(',', '.'))

            Vw = calculate_water_to_add(V0, C0, Ct)
            Vfinal = V0 + Vw
            Mchar = calculate_charcoal_mass(Vfinal)

            self.result_water.setText(
                f"Добавить воды: {Vw:.3f} л  (итог: {Vfinal:.3f} л)"
            )
            self.result_charcoal.setText(
                f"Угля для фильтрации: {Mchar:.1f} г"
            )
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
        except Exception:
            QMessageBox.warning(self, "Ошибка", "Неверный формат данных")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DilutionCalculator()
    window.show()
    sys.exit(app.exec_())
