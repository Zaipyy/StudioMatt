import matplotlib.pyplot as plt
from scipy.io import wavfile
import numpy as np

print("Lendo o arquivo de áudio...")


taxa_amostragem, dados_audio = wavfile.read('meu_audio_teste.wav')


duracao = len(dados_audio) / taxa_amostragem
tempo = np.linspace(0., duracao, len(dados_audio))

print(f"Áudio carregado! Duração: {duracao:.2f} segundos.")


plt.figure(figsize=(10, 4)) 
plt.plot(tempo, dados_audio, label="Minha Voz", color="blue")
plt.title("Forma de Onda (Igual ao Audacity!)")
plt.xlabel("Tempo (s)")
plt.ylabel("Volume (Amplitude)")
plt.grid(True) 


print("Abrindo o gráfico...")
plt.show()
