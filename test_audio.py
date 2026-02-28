import sys
sys.path.append("/home/fred/toniepi/app")

from AudioPlayer import AudioPlayer

ap = AudioPlayer()

ap.load_folder("/home/fred/toniepi/audio")

ap.volume_down()