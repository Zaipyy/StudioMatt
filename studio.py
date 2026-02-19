import sys
import numpy as np
import sounddevice as sd
from scipy.io import wavfile
from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                             QPushButton, QLabel, QScrollArea, QHBoxLayout, QMessageBox, 
                             QFileDialog, QSlider, QFrame)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
import pyqtgraph as pg

# --- CONFIGURAÇÕES ---
FS = 44100  
DEVICE_INDEX = (3, 5) # (Seu Mic, Seu Fone) - CONFIRA SEUS NÚMEROS AQUI
CHUNK = 1024  
LATENCIA_CORRECAO = 0.33 

# --- CLASSE DE BOTÃO ANIMADO ---
class BotaoAnimado(QPushButton):
    def __init__(self, texto="", parent=None):
        super().__init__(texto, parent)
        self._original_geometry = None
        
    def mousePressEvent(self, event):
        self._animate_click(direction="in")
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._animate_click(direction="out")
        super().mouseReleaseEvent(event)

    def _animate_click(self, direction="in"):
        if not self._original_geometry:
            self._original_geometry = self.geometry()
        rect = self.geometry()
        anim = QPropertyAnimation(self, b"geometry", self)
        anim.setDuration(100)
        
        if direction == "in":
            end_rect = QRect(rect.x() + 2, rect.y() + 2, rect.width() - 4, rect.height() - 4)
            anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        else:
            end_rect = QRect(rect.x() - 2, rect.y() - 2, rect.width() + 4, rect.height() + 4)
            anim.setEasingCurve(QEasingCurve.Type.OutElastic)

        anim.setStartValue(rect)
        anim.setEndValue(end_rect)
        anim.start()

# --- FAIXA DE ÁUDIO ---
class FaixaAudio(QWidget):
    def __init__(self, nome, dados_audio, parent=None):
        super().__init__(parent)
        self.dados_audio = dados_audio
        self.parent_studio = parent 
        self.volume = 1.0 
        self.is_muted = False
        self.is_solo = False

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)
        self.setStyleSheet("background-color: #222; border-radius: 5px;")

        # Controles
        controles_layout = QVBoxLayout()
        controles_layout.setSpacing(2) 
        
        self.lbl_nome = QLabel(nome)
        self.lbl_nome.setFixedWidth(100)
        self.lbl_nome.setStyleSheet("font-weight: bold; color: #00e5ff; font-size: 12px;")
        controles_layout.addWidget(self.lbl_nome)

        segundos_total = len(dados_audio) / FS
        mins = int(segundos_total // 60)
        secs = int(segundos_total % 60)
        self.lbl_duracao = QLabel(f"{mins:02}:{secs:02}")
        self.lbl_duracao.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        controles_layout.addWidget(self.lbl_duracao)

        controles_layout.addSpacing(5) 

        botoes_layout = QHBoxLayout()
        self.btn_mute = BotaoAnimado("M")
        self.btn_mute.setFixedSize(30, 30)
        self.btn_mute.setCheckable(True)
        self.btn_mute.setStyleSheet("QPushButton { background-color: #444; color: white; border: none; border-radius: 5px; } QPushButton:checked { background-color: #ffaa00; color: black; }")
        self.btn_mute.clicked.connect(self.toggle_mute)
        botoes_layout.addWidget(self.btn_mute)

        self.btn_solo = BotaoAnimado("S")
        self.btn_solo.setFixedSize(30, 30)
        self.btn_solo.setCheckable(True)
        self.btn_solo.setStyleSheet("QPushButton { background-color: #444; color: white; border: none; border-radius: 5px; } QPushButton:checked { background-color: #00ff00; color: black; }")
        self.btn_solo.clicked.connect(self.toggle_solo)
        botoes_layout.addWidget(self.btn_solo)
        controles_layout.addLayout(botoes_layout)

        self.slider_vol = QSlider(Qt.Orientation.Horizontal)
        self.slider_vol.setRange(0, 120) 
        self.slider_vol.setValue(100)
        self.slider_vol.setFixedWidth(100)
        self.slider_vol.valueChanged.connect(self.mudar_volume)
        controles_layout.addWidget(self.slider_vol)

        self.layout.addLayout(controles_layout)

        # Gráfico
        self.graph = pg.PlotWidget()
        self.graph.setBackground('#1e1e1e')
        self.graph.setYRange(-1, 1)
        self.graph.hideAxis('left')
        self.graph.hideAxis('bottom')
        self.graph.setFixedHeight(100)
        self.graph.setMouseEnabled(x=False, y=False)
        
        self.curve = self.graph.plot(pen=pg.mkPen(color='#00ff00', width=1))
        passo = max(1, len(dados_audio) // 4000) 
        self.curve.setData(dados_audio[::passo])

        self.cursor_line = pg.InfiniteLine(pos=0, angle=90, pen=pg.mkPen('y', width=2))
        self.graph.addItem(self.cursor_line)

        self.graph.scene().sigMouseClicked.connect(self.clique_no_grafico)
        self.layout.addWidget(self.graph)

        # Deletar
        self.btn_delete = BotaoAnimado("❌")
        self.btn_delete.setFixedSize(30, 80)
        self.btn_delete.setStyleSheet("background-color: #ff4444; border-radius: 5px; border: none;")
        self.layout.addWidget(self.btn_delete)

    def toggle_mute(self):
        self.is_muted = self.btn_mute.isChecked()
        self.parent_studio.atualizar_mix()

    def toggle_solo(self):
        self.is_solo = self.btn_solo.isChecked()
        self.parent_studio.atualizar_solo(self)

    def mudar_volume(self):
        self.volume = self.slider_vol.value() / 100.0
        self.parent_studio.atualizar_mix()

    def clique_no_grafico(self, event):
        if self.graph.sceneBoundingRect().contains(event.scenePos()):
            mouse_point = self.graph.plotItem.vb.mapSceneToView(event.scenePos())
            proporcao = mouse_point.x() / len(self.curve.xData)
            amostra_real = int(proporcao * len(self.dados_audio))
            self.parent_studio.navegar_para(amostra_real)

# --- STUDIO PRINCIPAL ---
class StudioMatt(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Studio do Matt - Versão Completa 🚀")
        self.setGeometry(100, 100, 1100, 750)
        self.setStyleSheet("background-color: #111; color: white;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # --- Topo (Botões de Arquivo) ---
        topo_layout = QHBoxLayout()
        
        self.btn_importar = BotaoAnimado("📂 IMPORTAR")
        self.btn_importar.setStyleSheet("background-color: #ffaa00; color: black; font-weight: bold; padding: 8px; border-radius: 5px;")
        self.btn_importar.clicked.connect(self.importar_audio)
        topo_layout.addWidget(self.btn_importar)

        self.btn_salvar = BotaoAnimado("💾 SALVAR")
        self.btn_salvar.setStyleSheet("background-color: #00aaaa; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        self.btn_salvar.clicked.connect(self.salvar_projeto)
        topo_layout.addWidget(self.btn_salvar)

        # --- BOTÃO NOVO: LIMPAR TUDO 🗑️ ---
        self.btn_limpar = BotaoAnimado("🗑️ LIMPAR TUDO")
        self.btn_limpar.setStyleSheet("background-color: #aa0000; color: white; font-weight: bold; padding: 8px; border-radius: 5px;")
        self.btn_limpar.clicked.connect(self.limpar_projeto)
        topo_layout.addWidget(self.btn_limpar)

        main_layout.addLayout(topo_layout)

        # --- Área de Faixas ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background-color: #1a1a1a; border: none;")
        self.container_faixas = QWidget()
        self.layout_faixas = QVBoxLayout(self.container_faixas)
        self.layout_faixas.addStretch()
        self.scroll.setWidget(self.container_faixas)
        main_layout.addWidget(self.scroll)

        # --- Controles ---
        controles = QHBoxLayout()
        
        self.btn_gravar = BotaoAnimado("🔴 REC")
        self.btn_gravar.setFixedSize(80, 80)
        self.btn_gravar.setStyleSheet("QPushButton { background-color: #ff4444; border-radius: 40px; font-weight: bold; font-size: 16px; border: 2px solid #fff; } QPushButton:checked { background-color: #880000; border: 2px solid #f00; }")
        self.btn_gravar.setCheckable(True)
        self.btn_gravar.clicked.connect(self.toggle_recording)
        controles.addWidget(self.btn_gravar)
        
        controles.addSpacing(20)

        self.btn_play = BotaoAnimado("▶️")
        self.btn_play.setFixedSize(60, 60)
        self.btn_play.setStyleSheet("background-color: #44ff44; border-radius: 30px; font-size: 24px; color: black; border: none;")
        self.btn_play.clicked.connect(self.play_mix)
        controles.addWidget(self.btn_play)

        self.btn_stop = BotaoAnimado("⏹️")
        self.btn_stop.setFixedSize(60, 60)
        self.btn_stop.setStyleSheet("background-color: #4444ff; border-radius: 30px; font-size: 24px; border: none;")
        self.btn_stop.clicked.connect(self.stop_mix)
        controles.addWidget(self.btn_stop)

        self.lbl_tempo = QLabel("00:00")
        self.lbl_tempo.setStyleSheet("font-size: 20px; color: yellow; margin-left: 20px; font-family: Consolas;")
        controles.addWidget(self.lbl_tempo)

        controles.addStretch()
        main_layout.addLayout(controles)

        # --- Variáveis ---
        self.faixas = [] 
        self.current_recording = []
        self.backing_track = None 
        self.rec_stream = None
        self.play_stream = None
        self.mix_final = None
        self.cursor_playback = 0 
        self.is_playing = False

        self.timer_visual = QTimer()
        self.timer_visual.interval = 30 
        self.timer_visual.timeout.connect(self.atualizar_interface_grafica)
        self.timer_visual.start()

    # --- FUNÇÃO NOVA: LIMPAR TUDO 🗑️ ---
    def limpar_projeto(self):
        # Pergunta de segurança para evitar acidentes
        resposta = QMessageBox.question(
            self, "Confirmar Limpeza", 
            "Tem certeza que quer apagar TODAS as faixas?\nIsso não pode ser desfeito.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if resposta == QMessageBox.StandardButton.Yes:
            self.stop_mix() # Para tudo antes de apagar
            
            # Remove todas as faixas da tela e da lista
            for faixa in self.faixas:
                faixa.deleteLater() # Remove visualmente
            
            self.faixas.clear() # Limpa a lista
            self.mix_final = None # Limpa o áudio
            self.cursor_playback = 0 # Reseta o tempo
            self.atualizar_interface_grafica()
            
            QMessageBox.information(self, "Limpo", "Projeto zerado com sucesso! ✨")

    # --- RESTANTE DAS FUNÇÕES (IGUAIS) ---
    def get_mix_audio(self):
        if not self.faixas: return np.array([0.0])
        tem_solo = any(f.is_solo for f in self.faixas)
        max_len = max(len(f.dados_audio) for f in self.faixas)
        mix = np.zeros(max_len)
        for faixa in self.faixas:
            deve_tocar = (tem_solo and faixa.is_solo) or (not tem_solo and not faixa.is_muted)
            if deve_tocar:
                audio = faixa.dados_audio * faixa.volume 
                mix[:len(audio)] += audio
        return np.clip(mix, -1.0, 1.0)

    def atualizar_mix(self):
        self.mix_final = self.get_mix_audio()

    def atualizar_solo(self, faixa_solicitante):
        self.atualizar_mix()

    def navegar_para(self, sample_index):
        self.cursor_playback = max(0, sample_index)
        self.atualizar_interface_grafica()

    def atualizar_interface_grafica(self):
        segundos = self.cursor_playback / FS
        mins = int(segundos // 60)
        secs = int(segundos % 60)
        self.lbl_tempo.setText(f"{mins:02}:{secs:02}")
        for faixa in self.faixas:
            passo = max(1, len(faixa.dados_audio) // 4000)
            posicao_visual = self.cursor_playback / passo
            faixa.cursor_line.setValue(posicao_visual)

    def play_mix(self):
        if self.is_playing: 
            self.pause_mix()
            return
        if self.mix_final is None: self.mix_final = self.get_mix_audio()
        if len(self.mix_final) > 0 and self.cursor_playback >= len(self.mix_final):
            self.cursor_playback = 0
        try:
            self.play_stream = sd.OutputStream(
                samplerate=FS, channels=1, device=DEVICE_INDEX[1],
                blocksize=CHUNK, callback=self.playback_callback
            )
            self.play_stream.start()
            self.is_playing = True
            self.btn_play.setText("⏸️")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao tocar:\n{e}")

    def pause_mix(self):
        if self.play_stream:
            self.play_stream.stop()
            self.play_stream.close()
            self.is_playing = False
            self.btn_play.setText("▶️")

    def stop_mix(self):
        self.pause_mix()
        self.cursor_playback = 0 
        self.mix_final = None 
        self.atualizar_interface_grafica()

    def playback_callback(self, outdata, frames, time, status):
        if self.mix_final is None:
            outdata.fill(0)
            return
        remaining = len(self.mix_final) - self.cursor_playback
        if remaining <= 0: raise sd.CallbackStop()
        chunk_size = min(frames, remaining)
        chunk = self.mix_final[self.cursor_playback : self.cursor_playback + chunk_size]
        outdata[:chunk_size] = chunk.reshape(-1, 1)
        if chunk_size < frames: outdata[chunk_size:] = 0
        self.cursor_playback += chunk_size

    def toggle_recording(self):
        if self.btn_gravar.isChecked():
            self.stop_mix() 
            self.btn_play.setEnabled(False) 
            self.current_recording = []
            self.backing_track = self.get_mix_audio()
            try:
                self.rec_stream = sd.Stream(
                    samplerate=FS, channels=(1, 2), device=DEVICE_INDEX,
                    blocksize=CHUNK, callback=self.rec_callback
                )
                self.rec_stream.start()
            except Exception as e:
                self.btn_gravar.setChecked(False)
                QMessageBox.critical(self, "Erro", f"Erro no Mic:\n{e}")
        else:
            if self.rec_stream:
                self.rec_stream.stop()
                self.rec_stream.close()
            self.btn_play.setEnabled(True) 
            if len(self.current_recording) > 0:
                audio_bruto = np.concatenate(self.current_recording).flatten()
                corte = int(LATENCIA_CORRECAO * FS)
                if len(audio_bruto) > corte: novo_audio = audio_bruto[corte:]
                else: novo_audio = audio_bruto
                self.adicionar_faixa_visual(novo_audio)
            self.cursor_playback = 0
            self.mix_final = None

    def rec_callback(self, indata, outdata, frames, time, status):
        self.current_recording.append(indata.copy())
        chunk_end = self.cursor_playback + frames
        if self.backing_track is not None and self.cursor_playback < len(self.backing_track):
            chunk = self.backing_track[self.cursor_playback:chunk_end]
            if len(chunk) < frames: chunk = np.pad(chunk, (0, frames - len(chunk)))
            outdata[:] = chunk.reshape(-1, 1) 
        else: outdata[:] = np.zeros((frames, 2)) 
        self.cursor_playback += frames

    def adicionar_faixa_visual(self, audio_data, nome_arquivo=None):
        num = len(self.faixas) + 1
        nome = nome_arquivo if nome_arquivo else f"Faixa {num}"
        widget = FaixaAudio(nome, audio_data, parent=self)
        widget.btn_delete.clicked.connect(lambda: self.deletar_faixa(widget))
        self.layout_faixas.insertWidget(len(self.faixas), widget)
        self.faixas.append(widget)

    def deletar_faixa(self, widget):
        widget.deleteLater()
        self.faixas.remove(widget)
        self.mix_final = None 

    def importar_audio(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", "Audio Files (*.wav)")
        if arquivo:
            try:
                rate, dados = wavfile.read(arquivo)
                if len(dados.shape) > 1: dados = np.mean(dados, axis=1)
                if dados.dtype == np.int16: dados = dados / 32768.0
                elif dados.dtype == np.int32: dados = dados / 2147483648.0
                elif dados.dtype == np.uint8: dados = (dados - 128) / 128.0
                self.adicionar_faixa_visual(dados, nome_arquivo=arquivo.split("/")[-1])
                self.mix_final = None 
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não consegui ler o arquivo:\n{e}")

    def salvar_projeto(self):
        if not self.faixas: return
        arquivo, _ = QFileDialog.getSaveFileName(self, "Salvar Mix", "meu_hit.wav", "WAV Files (*.wav)")
        if arquivo:
            try:
                mix = self.get_mix_audio()
                mix_int16 = (mix * 32767).astype(np.int16)
                wavfile.write(arquivo, FS, mix_int16)
                QMessageBox.information(self, "Sucesso", "Arquivo salvo! 🎵")
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao salvar:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StudioMatt()
    window.show()
    sys.exit(app.exec())