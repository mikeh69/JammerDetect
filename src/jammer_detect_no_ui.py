from rtlsdr import RtlSdr
import math
from threading import Timer # for watchdog timer
from audio_tones import AudioTones

NUM_SAMPLES = 32768
BARGRAPH = "################################################################################" \
            + "                                                                                "

def main():

    sdr = RtlSdr()

    # configure device
    sdr.sample_rate = 1.024e6  # Hz
    sdr.center_freq = 433.9e6     # Hz
    sdr.freq_correction = 20   # PPM
    sdr.gain = 'auto'

    tones = AudioTones()
    tones.init()

    for i in range(0, 10):
        rssi = MeasureRSSI(sdr)

    # Measure minimum RSSI over a few readings, auto-adjust for dongle gain
    min_rssi = 1000
    avg_rssi = 0
    for i in range(0, 10):
        rssi = MeasureRSSI(sdr)
        min_rssi = min(min_rssi, rssi)
        avg_rssi += rssi
    avg_rssi /= 10
    ampl_offset = avg_rssi
    max_rssi = MeasureRSSI(sdr) - ampl_offset
    avg_rssi = max_rssi + 20;
    counter = 0
 #   redirect_stderr()
 

    while(True):
        wdt = Timer(3.0, watchdog_timeout)
        wdt.start()
        rssi = MeasureRSSI(sdr) - ampl_offset
        wdt.cancel()
        avg_rssi = ((15 * avg_rssi) + rssi) / 16

        max_rssi = max(max_rssi, rssi)
        counter += 1
        if counter & 0x1F == 0:
            tone_idx = int(max_rssi)
            tone_idx = max(0, tone_idx)
            tone_idx = min(45, tone_idx)
            tones.play(tone_idx)
            max_rssi = rssi

# First attempt: using floating-point complex samples
def MeasureRSSI_1(sdr):
    samples = sdr.read_samples(NUM_SAMPLES)
    power = 0.0
    for sample in samples:
        power += (sample.real * sample.real) + (sample.imag * sample.imag)
    return 10 * (math.log(power) - math.log(NUM_SAMPLES))

# Second go: read raw bytes, square and add those
def MeasureRSSI_2(sdr):
    data_bytes = sdr.read_bytes(NUM_SAMPLES * 2)
    power = 0
    for next_byte in data_bytes:
        signed_byte = next_byte + next_byte - 255
        power += signed_byte * signed_byte
    return 10 * (math.log(power) - math.log(NUM_SAMPLES) - math.log(127)) - 70

# Third go: modify librtlsdr, do the square-and-add calculation in C
def MeasureRSSI_3(sdr):
    while(True):
        try:
            return sdr.read_power_dB(NUM_SAMPLES) - 112
        except OSError: # e.g. SDR unplugged...
            pass  # go round and try again, SDR will be replugged sometime...

# Select the desired implementation here:
def MeasureRSSI(sdr):
    return MeasureRSSI_3(sdr)
#    return sdr.read_offset_I(NUM_SAMPLES) / (NUM_SAMPLES / 2)
#    return sdr.read_offset_Q(NUM_SAMPLES) / (NUM_SAMPLES / 2)

def redirect_stderr():
    import os, sys
    sys.stderr.flush()
    err = open('/dev/null', 'a+')
    os.dup2(err.fileno(), sys.stderr.fileno())  # send ALSA underrun error messages to /dev/null
    
def watchdog_timeout():
    print("**** WATCHDOG TIMEOUT ****")
    exit()


if __name__ == "__main__":
    import os, sys
    main()
