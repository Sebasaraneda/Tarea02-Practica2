import sys
import random
import serial
import struct
import binascii
import csv
import os
from datetime import datetime
import threading
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QGridLayout, QComboBox, QTabWidget, QFrame
)
import pyqtgraph as pg
from collections import deque
import firebase_admin
from firebase_admin import credentials, db

# Inicialización Firebase
cred = credentials.Certificate("v2/creds.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://realtime-t2-default-rtdb.firebaseio.com/'
})

#
def subir_datos_a_firebase(nombre_multiplexor, datos_sensores):
    ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ref = db.reference(f"/{nombre_multiplexor}/{ahora}")
    ref.set(datos_sensores)
    print(f"Datos subidos a Firebase: {nombre_multiplexor} - {ahora} - {datos_sensores}")

# Función para generar datos ficticios
def generar_datos_ficticios():
    return {f"Sensor_{i+1}": random.uniform(0, 100) for i in range(16)}

# ====== Funciones de separación ======

def definirvalores(d):
    separado = separar(d)
    return separado


def separar(x):
    cadena = x
    g1 = cadena[12:20]
    g2 = cadena[21:29]
    g3 = cadena[30:38]
    g4 = cadena[39:47]

    uno = "{0:.2f}".format(struct.unpack('>f', binascii.unhexlify(g1))[0])
    dos = "{0:.2f}".format(struct.unpack('>f', binascii.unhexlify(g2))[0])
    tres = "{0:.2f}".format(struct.unpack('>f', binascii.unhexlify(g3))[0])
    cuatro = "{0:.2f}".format(struct.unpack('>f', binascii.unhexlify(g4))[0])

    separado = [uno, dos, tres, cuatro]
    return separado


# ====== QThread de Lectura Serial ======

class SerialReaderThread(QThread):
    data_received = pyqtSignal(list, int)
    comms_status = pyqtSignal(bool, int)
    last_read_time = pyqtSignal(str, int)
    request_read = pyqtSignal()

    def __init__(self, port, baudrate, multiplexor_id):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.multiplexor_id = multiplexor_id
        self.ser = None
        self.request_read.connect(self.read_serial)

    def run(self):
        self.connect_serial()
        self.exec_()

    def connect_serial(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=1
            )
            print(f"[OK] Conectado a {self.port} (Multiplexor {self.multiplexor_id + 1})")
            self.comms_status.emit(True, self.multiplexor_id)
        except Exception as e:
            print(f"[ERROR] No se pudo conectar a {self.port} (Multiplexor {self.multiplexor_id + 1}): {e}")
            self.comms_status.emit(False, self.multiplexor_id)
            self.ser = None
            self.quit()

    def read_serial(self):
        if self.ser is None or not self.ser.is_open:
            print(f"[ERROR] Puerto cerrado. No se leerá (Multiplexor {self.multiplexor_id + 1})")
            self.comms_status.emit(False, self.multiplexor_id)
            return
        try:
            commands = [
                b'@02EX E5 00:53\r',
                b'@02EX E5 01:54\r',
                b'@02EX E5 02:55\r',
                b'@02EX E5 03:56\r'
            ]

            all_data = []
            for cmd in commands:
                if self.ser:
                    self.ser.write(cmd)
                    self.msleep(200)
                    data = self.ser.readline().decode("utf-8").strip()
                    if len(data) > 1:
                        values = definirvalores(data)
                        all_data.extend(values)

            if len(all_data) == 16:
                self.data_received.emit(all_data, self.multiplexor_id)
                self.comms_status.emit(True, self.multiplexor_id)
                self.last_read_time.emit(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.multiplexor_id)
                self.save_to_csv(all_data)
            else:
                self.comms_status.emit(False, self.multiplexor_id)

        except Exception as e:
            print(f"[ERROR] Fallo en la lectura (Multiplexor {self.multiplexor_id + 1}): {e}")
            self.comms_status.emit(False, self.multiplexor_id)

    def save_to_csv(self, data):
        filename = f"registro_intech_multiplexor_{self.multiplexor_id + 1}.csv"
        file_exists = os.path.isfile(filename)

        with open(filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            if not file_exists:
                header = ['FechaHora'] + [f"Canal_{i + 1}" for i in range(16)]
                writer.writerow(header)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S")] + data)

    def stop(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
        self.quit()

class FakeReaderThread(QThread):
    data_received = pyqtSignal(list, int)
    comms_status = pyqtSignal(bool, int)
    last_read_time = pyqtSignal(str, int)
    request_read = pyqtSignal()

    def __init__(self, multiplexor_id):
        super().__init__()
        self.multiplexor_id = multiplexor_id
        self.request_read.connect(self.read_fake)
        self._running = True

    def run(self):
        self.comms_status.emit(True, self.multiplexor_id)
        self.exec_()

    def read_fake(self):
        if not self._running:
            return
        # Simula 16 lecturas ficticias como strings con dos decimales
        data = ["{:.2f}".format(random.uniform(0, 100)) for _ in range(16)]
        self.data_received.emit(data, self.multiplexor_id)
        self.comms_status.emit(True, self.multiplexor_id)
        self.last_read_time.emit(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self.multiplexor_id)

    def stop(self):
        self._running = False
        self.quit()

def start_reading(interval):
    reader = FakeReaderThread()
    reader.set_interval(interval)
    reader.start()
    return reader

# ====== Ventana Principal ======

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Lectura Multiplexores Intech A16 (2 dispositivos)")
        self.resize(1200, 800)

        # Layout Principal
        self.layout = QVBoxLayout(self)
        self.setStyleSheet("background-color: #f4f6f9;")  # Color de fondo suave

        # Botones con diseño moderno
        button_layout = QHBoxLayout()
        self.start_button = QPushButton("Iniciar")
        self.stop_button = QPushButton("Detener")
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)

        # Personalización de botones
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                min-width: 200px;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #1c5985;
            }
        """)

        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                min-width: 200px;
                border-radius: 8px;
                padding: 12px 30px;
                font-size: 14px;
                font-weight: bold;
                transition: background-color 0.3s ease;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #9b2c2c;
            }
        """)

        # Agregar espaciado entre los botones
        button_layout.addStretch()

        # LED indicadores de estado de comunicación
        led_layout1 = QHBoxLayout()
        self.led_label1 = QLabel()
        self.led_label1.setFixedSize(20, 20)
        self.last_time_label1 = QLabel("Multiplexor 1 - Última lectura: ---")
        led_layout1.addWidget(QLabel("Estado Comunicación Multiplexor 1:"))
        led_layout1.addWidget(self.led_label1)
        led_layout1.addWidget(self.last_time_label1)
        led_layout1.addStretch()

        led_layout2 = QHBoxLayout()
        self.led_label2 = QLabel()
        self.led_label2.setFixedSize(20, 20)
        self.last_time_label2 = QLabel("Multiplexor 2 - Última lectura: ---")
        led_layout2.addWidget(QLabel("Estado Comunicación Multiplexor 2:"))
        led_layout2.addWidget(self.led_label2)
        led_layout2.addWidget(self.last_time_label2)
        led_layout2.addStretch()

        # ComboBox intervalo con estilo moderno
        self.interval_box = QComboBox()
        self.interval_box.addItems(["10 segundos", "20 segundos", "30 segundos"])
        self.interval_box.setCurrentIndex(1)  # 20 segundos por defecto
        self.interval_box.setStyleSheet("""
            QComboBox {
                background-color: white;
                color: #555;
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 5px;
            }
            QComboBox:hover {
                border-color: #3498db;
            }
        """)

        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Intervalo de lectura:"))
        interval_layout.addWidget(self.interval_box)
        interval_layout.addStretch()

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget {
                background-color: #ffffff;
                border-radius: 8px;
                border: 1px solid #ddd;
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: gray;
                color: white;
                min-width: 200px;
                padding: 12px;
                margin-right: 4px;
                font-weight: bold;
                border-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: #2ecc71; /* verde bonito */
                color: white;
            }
        """)

        # Pestaña 1: Valores numéricos
        self.tab1 = QWidget()
        self.tab1_layout = QVBoxLayout(self.tab1)

        # Contenedor Multiplexor 1
        self.multiplexor1_container = QWidget()
        self.grid1 = QGridLayout(self.multiplexor1_container)
        self.value_labels1 = []
        for i in range(16):
            lbl = QLabel("----")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background-color: #ecf0f1;")
            self.grid1.addWidget(QLabel(f"M1 Canal {i + 1}:"), i // 4, (i % 4) * 2)
            self.grid1.addWidget(lbl, i // 4, (i % 4) * 2 + 1)
            self.value_labels1.append(lbl)

        # Contenedor Multiplexor 2
        self.multiplexor2_container = QWidget()
        self.grid2 = QGridLayout(self.multiplexor2_container)
        self.value_labels2 = []
        for i in range(16):
            lbl = QLabel("----")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px; background-color: #ecf0f1;")
            self.grid2.addWidget(QLabel(f"M2 Canal {i + 1}:"), i // 4, (i % 4) * 2)
            self.grid2.addWidget(lbl, i // 4, (i % 4) * 2 + 1)
            self.value_labels2.append(lbl)

        # Espaciado entre los contenedores
        self.tab1_layout.addWidget(self.multiplexor1_container)
        self.tab1_layout.addWidget(self.multiplexor2_container)

        # Pestaña 2: Gráfico en vivo
        self.tab2 = QWidget()
        self.graph_layout = QVBoxLayout(self.tab2)

        # Gráfico para Multiplexor 1
        self.plot_widget1 = pg.PlotWidget(title="Multiplexor 1")
        self.plot_widget1.setBackground('w')
        self.plot_widget1.addLegend()
        self.plot_widget1.showGrid(x=True, y=True)
        self.plot_widget1.setLabel('left', 'Valor')
        self.plot_widget1.setLabel('bottom', 'Lecturas')

        # Gráfico para Multiplexor 2
        self.plot_widget2 = pg.PlotWidget(title="Multiplexor 2")
        self.plot_widget2.setBackground('w')
        self.plot_widget2.addLegend()
        self.plot_widget2.showGrid(x=True, y=True)
        self.plot_widget2.setLabel('left', 'Valor')
        self.plot_widget2.setLabel('bottom', 'Lecturas')

        self.curves1 = []
        self.curves2 = []
        self.data_queues1 = [deque(maxlen=60) for _ in range(16)]
        self.data_queues2 = [deque(maxlen=60) for _ in range(16)]
        self.time_queues1 = deque(maxlen=60)
        self.time_queues2 = deque(maxlen=60)

        # Colores personalizados para cada curva
        colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k', 'orange', 'purple', 'brown',
                  'pink', 'gray', 'olive', 'navy', 'teal', 'maroon']

        for i in range(16):
            pen1 = pg.mkPen(colors[i % len(colors)], width=2)
            pen2 = pg.mkPen(colors[i % len(colors)], width=2)
            curve1 = self.plot_widget1.plot(pen=pen1, name=f"M1 Canal {i + 1}")
            curve2 = self.plot_widget2.plot(pen=pen2, name=f"M2 Canal {i + 1}")
            self.curves1.append(curve1)
            self.curves2.append(curve2)

        # Añadir los gráficos en una distribución flexible
        graphs_layout = QHBoxLayout()
        graphs_layout.addWidget(self.plot_widget1)
        graphs_layout.addWidget(self.plot_widget2)
        self.graph_layout.addLayout(graphs_layout)

        self.tabs.addTab(self.tab1, "Lecturas")
        self.tabs.addTab(self.tab2, "Gráfico en Vivo")

        # Multiplexor 1
        try:
            # Intentamos abrir el puerto para verificar que existe
            test_serial = serial.Serial('COM3', 9600)
            test_serial.close()
            self.thread1 = SerialReaderThread(port='COM3', baudrate=9600, multiplexor_id=0)
            print("[INFO] Multiplexor 1 detectado en COM3")
        except Exception as e:
            print(f"[WARN] COM3 no disponible ({e}). Usando datos ficticios para Multiplexor 1.")
            self.thread1 = FakeReaderThread(multiplexor_id=0)

        # Multiplexor 2
        try:
            test_serial = serial.Serial('/dev/ttyUSB1', 9600)
            test_serial.close()
            self.thread2 = SerialReaderThread(port='/dev/ttyUSB1', baudrate=9600, multiplexor_id=1)
            print("[INFO] Multiplexor 2 detectado en /dev/ttyUSB1")
        except Exception as e:
            print(f"[WARN] /dev/ttyUSB1 no disponible ({e}). Usando datos ficticios para Multiplexor 2.")
            self.thread2 = FakeReaderThread(multiplexor_id=1)

        self.read_timer = QTimer()
        self.read_timer.timeout.connect(self.trigger_reads)

        self.change_interval(1)

        self.start_button.clicked.connect(self.start_threads)
        self.stop_button.clicked.connect(self.stop_threads)
        self.interval_box.currentIndexChanged.connect(self.change_interval)

        self.thread1.data_received.connect(lambda data, id=0: self.update_values(data, id))
        self.thread1.comms_status.connect(lambda status, id=0: self.update_led(status, id))
        self.thread1.last_read_time.connect(lambda time, id=0: self.update_last_time(time, id))

        self.thread2.data_received.connect(lambda data, id=1: self.update_values(data, id))
        self.thread2.comms_status.connect(lambda status, id=1: self.update_led(status, id))
        self.thread2.last_read_time.connect(lambda time, id=1: self.update_last_time(time, id))

        self.layout.addLayout(button_layout)
        self.layout.addLayout(led_layout1)
        self.layout.addLayout(led_layout2)
        self.layout.addLayout(interval_layout)
        self.layout.addWidget(self.tabs)

    def update_values(self, data, multiplexor_id):
        current_time = datetime.now().strftime("%H:%M:%S")  # HH:MM:SS
        if multiplexor_id == 0:  # Multiplexor 1
            self.time_queues1.append(current_time)
            for i in range(min(16, len(data))):
                self.value_labels1[i].setText(data[i])
                try:
                    self.data_queues1[i].append(float(data[i]))
                    # Aquí actualizamos el gráfico
                    self.curves1[i].setData(list(range(len(self.data_queues1[i]))), list(self.data_queues1[i]))
                except ValueError:
                    pass
            datos_dict = {f"Sensor_{i+1}": float(data[i]) for i in range(min(16, len(data)))}
            subir_datos_a_firebase("Multiplexor_1", datos_dict)
        else:  # Multiplexor 2
            self.time_queues2.append(current_time)
            for i in range(min(16, len(data))):
                self.value_labels2[i].setText(data[i])
                try:
                    self.data_queues2[i].append(float(data[i]))
                    self.curves2[i].setData(list(range(len(self.data_queues2[i]))), list(self.data_queues2[i]))
                except ValueError:
                    pass
            datos_dict = {f"Sensor_{i+1}": float(data[i]) for i in range(min(16, len(data)))}
            subir_datos_a_firebase("Multiplexor_2", datos_dict)

    def trigger_reads(self):
        if hasattr(self, 'thread1') and self.thread1.isRunning():
            self.thread1.request_read.emit()
        if hasattr(self, 'thread2') and self.thread2.isRunning():
            self.thread2.request_read.emit()

    def start_threads(self):
        if not self.thread1.isRunning():
            self.thread1.start()
        if not self.thread2.isRunning():
            self.thread2.start()
        self.read_timer.start()

    def stop_threads(self):
        self.read_timer.stop()
        if self.thread1.isRunning():
            self.thread1.stop()
        if self.thread2.isRunning():
            self.thread2.stop()

    def change_interval(self, index):
        intervals = [10, 20, 30]  # Segundos
        if 0 <= index < len(intervals):
            selected = intervals[index]
            self.read_timer.setInterval(selected * 1000)

    def update_led(self, status_ok, multiplexor_id):
        color = "green" if status_ok else "red"
        if multiplexor_id == 0:
            self.led_label1.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
        else:
            self.led_label2.setStyleSheet(f"background-color: {color}; border-radius: 10px;")

    def update_last_time(self, timestamp, multiplexor_id):
        if multiplexor_id == 0:
            self.last_time_label1.setText(f"Multiplexor 1 - Última lectura: {timestamp}")
        else:
            self.last_time_label2.setText(f"Multiplexor 2 - Última lectura: {timestamp}")

    def closeEvent(self, event):
        self.stop_threads()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
