import sys
import numpy as np
import sounddevice as sd
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLabel
from PyQt6.QtCore import QTimer
import pyqtgraph as pg

# --- CONFIGURAÇÕES ---
FS = 44100  # Qualidade de CD
DEVICE_INDEX = 3  # Seu Logitech G935
CHUNK = 1024  # O tamanho do "bloquinho" de áudio que o PC processa por vez

class MiniAudacity(QMainWindow):
    def __init__(self):
        super().__init__()

        # 1. Configurando a Janela
        self.setWindowTitle("Mini Audacity do Matt 🎤")
        self.setGeometry(100, 100, 800, 400) # Tamanho da tela
        self.setStyleSheet("background-color: #2b2b2b; color: white;") # Tema Escuro (Dark Mode)

        # Layout Principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 2. O Gráfico (A Onda Sonora)
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground('#1e1e1e')
        self.graph_widget.setYRange(-1, 1) # O volume vai de -1 a 1
        self.graph_widget.showGrid(x=True, y=True, alpha=0.3)
        self.data_line = self.graph_widget.plot(pen=pg.mkPen(color='#00ff00', width=2)) # Linha Verde Matrix
        layout.addWidget(self.graph_widget)

        # 3. Os Botões
        self.btn_gravar = QPushButton("🔴 GRAVAR")
        self.btn_gravar.setStyleSheet("background-color: #ff4444; font-weight: bold; padding: 10px;")
        self.btn_gravar.clicked.connect(self.toggle_recording)
        layout.addWidget(self.btn_gravar)

        self.btn_tocar = QPushButton("▶️ OUVIR O QUE GRAVEI")
        self.btn_tocar.setStyleSheet("background-color: #4444ff; font-weight: bold; padding: 10px;")
        self.btn_tocar.clicked.connect(self.play_audio)
        self.btn_tocar.setEnabled(False) # Começa desativado
        layout.addWidget(self.btn_tocar)
        
        self.lbl_status = QLabel("Pronto para gravar...")
        self.lbl_status.setStyleSheet("color: #aaaaaa;")
        layout.addWidget(self.lbl_status)

        # Variáveis de Controle
        self.is_recording = False
        self.audio_data = [] # Aqui vamos guardar o áudio gravado
        self.stream = None

    def toggle_recording(self):
        if not self.is_recording:
            # INICIAR GRAVAÇÃO
            self.is_recording = True
            self.btn_gravar.setText("⏹️ PARAR GRAVAÇÃO")
            self.btn_tocar.setEnabled(False)
            self.audio_data = [] # Limpa gravação anterior
            self.lbl_status.setText("Gravando... (Fale agora!)")
            
            # Inicia o "Ouvido" do computador
            self.stream = sd.InputStream(
                samplerate=FS, channels=1, device=DEVICE_INDEX,
                blocksize=CHUNK, callback=self.audio_callback
            )
            self.stream.start()
        else:
            # PARAR GRAVAÇÃO
            self.is_recording = False
            self.btn_gravar.setText("🔴 GRAVAR")
            self.lbl_status.setText("Gravação finalizada!")
            
            if self.stream:
                self.stream.stop()
                self.stream.close()
            
            # Transforma a lista de bloquinhos em um áudio completo
            if len(self.audio_data) > 0:
                self.full_recording = np.concatenate(self.audio_data)
                self.btn_tocar.setEnabled(True)

    def audio_callback(self, indata, frames, time, status):
        """Essa função roda automaticamente centenas de vezes por segundo"""
        if self.is_recording:
            # 1. Guarda o áudio na memória
            self.audio_data.append(indata.copy())
            
            # 2. Atualiza o gráfico (Visualização em Tempo Real)
            # Pegamos só o último pedacinho pra desenhar rápido
            self.data_line.setData(indata[:, 0])

    def play_audio(self):
        if hasattr(self, 'full_recording'):
            self.lbl_status.setText("Tocando áudio...")
            sd.play(self.full_recording, FS)
            sd.wait()
            self.lbl_status.setText("Reprodução terminada.")

# --- INICIALIZAÇÃO ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MiniAudacity()
    window.show()
    sys.exit(app.exec())