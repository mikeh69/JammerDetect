import math     #import needed modules
import pyaudio     #sudo apt-get install python-pyaudio
import struct
import pickle
from time import sleep

PyAudio = pyaudio.PyAudio     #initialize pyaudio

#See http://en.wikipedia.org/wiki/Bit_rate#Audio
BITRATE = 48000  #number of frames per second - 44.1kHz does not work properly on RPi BCM2538!
LENGTH = 0.2     #seconds to play sound
CHUNKSIZE = int(BITRATE * LENGTH)
WAVEDATA_FILE = "/home/pi/wavedata.pickled"

class AudioTones:

    def init(self):

        self.player = PyAudio()
        defaultCapability = self.player.get_default_host_api_info()
        print("Player defaults:")
        print(defaultCapability)
#        fmt = self.player.get_format_from_width(2)
#        fmt = pyaudio.paInt8  # supposedly 8-bit signed-integer
        fmt = pyaudio.paInt16  # 16-bit signed-integer
        print(self.player.is_format_supported(output_format = fmt, output_channels = 1, 
		        rate = BITRATE, output_device = 3))
        self.stream = self.player.open(format = fmt, channels = 1, rate = BITRATE, output = True, frames_per_buffer = CHUNKSIZE)

        try:
            print("Trying to load wavedata from file...")
            f = open(WAVEDATA_FILE, "rb")
            print("  File opened OK")
            self.WAVEDATA = pickle.load(f)
            print("  Wavedata read from file OK")
            f.close()
            return
        except Exception as ex:
            print(ex)
            print("Failed to load wavedata from file, re-generating")

        frequency = 200.0  # start frequency 200Hz
        self.WAVEDATA = []
        
        for index in range(0, 46): # valid index range 0 - 45, ~10log(32768)
            num_fadein_frames = int(BITRATE * LENGTH * 0.05)
            num_loud_frames = int(BITRATE * LENGTH * 0.7)
            num_fadeout_frames = CHUNKSIZE - (num_loud_frames + num_fadein_frames)
            self.WAVEDATA.append(struct.pack( "<H", 0 ))

            for xx in range(num_fadein_frames):
                x = xx
                next_sample = int(math.sin(x/((BITRATE/frequency)/math.pi)) * 32000 * (xx/num_fadein_frames))
                self.WAVEDATA[index] = self.WAVEDATA[index] + struct.pack( "<h", next_sample )  # little-endian int16

            for xx in range(num_loud_frames):
                x = xx + num_fadein_frames
                next_sample = int(math.sin(x/((BITRATE/frequency)/math.pi)) * 32000)
                self.WAVEDATA[index] = self.WAVEDATA[index] + struct.pack( "<h", next_sample )  # little-endian int16

            for xx in range(num_fadeout_frames):
                x = xx + num_loud_frames + num_fadein_frames
                next_sample = int(math.sin(x/((BITRATE/frequency)/math.pi)) * 32000 * (1 - (xx/num_fadeout_frames)))
#                next_sample = 0
                self.WAVEDATA[index] = self.WAVEDATA[index] + struct.pack( "<h", next_sample)

            frequency *= 1.0594631  # semitone ratio

        # Save the newly-generated data to a file using Pickle:
        print("Saving wavedata to file")
        f = open(WAVEDATA_FILE, "wb")
        pickle.dump(self.WAVEDATA, f)
        f.close()
        
    def test(self):
        for index in range(0, 40):
            self.stream.write(self.WAVEDATA[index])
            index += 1
        self.stream.stop_stream()

    def play(self, index):
        self.stream.write(self.WAVEDATA[index])

    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.player.terminate()

if __name__ == "__main__":
    tones = AudioTones()
    tones.init()
    for i in range(0, 40):
        tones.play(i)
        sleep(0.3)

