import sounddevice as sd
from scipy.io.wavfile import write

# 1. Configurações (A qualidade do áudio)
fs = 44100  # Frequência de amostragem (padrão de CD)
segundos = 5  # Vamos gravar só 5 segundos pra testar

print("Gravando... Fale alguma coisa, Mah!")

# O segredo está no 'device=3' que força o uso do Logitech
meu_audio = sd.rec(int(segundos * fs), samplerate=fs, channels=1, device=3)
sd.wait()  # O programa espera terminar a gravação antes de continuar

# 3. Salvando o arquivo
print("Salvando arquivo...")
write('meu_audio_teste.wav', fs, meu_audio)

print("Prontinho! Gravação finalizada.")