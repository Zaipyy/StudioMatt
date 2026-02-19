import matplotlib.pyplot as plt
from scipy.io import wavfile
import numpy as np

print("Lendo o arquivo de áudio...")

# 1. Carrega o arquivo que a gente gravou antes
taxa_amostragem, dados_audio = wavfile.read('meu_audio_teste.wav')

# 2. Cria o tempo (o eixo X do gráfico)
# Isso aqui é matemática pra saber quantos segundos tem o áudio
duracao = len(dados_audio) / taxa_amostragem
tempo = np.linspace(0., duracao, len(dados_audio))

print(f"Áudio carregado! Duração: {duracao:.2f} segundos.")

# 3. Desenha o Gráfico (A Onda)
plt.figure(figsize=(10, 4)) # Tamanho da janela
plt.plot(tempo, dados_audio, label="Minha Voz", color="blue")
plt.title("Forma de Onda (Igual ao Audacity!)")
plt.xlabel("Tempo (s)")
plt.ylabel("Volume (Amplitude)")
plt.grid(True) # Coloca aquela gradezinha no fundo

# 4. Mostra na tela
print("Abrindo o gráfico...")
plt.show()