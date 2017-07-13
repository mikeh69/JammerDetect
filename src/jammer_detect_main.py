from rtlsdr import RtlSdr
import math
import curses
from curses import wrapper
from audio_tones import AudioTones

NUM_SAMPLES = 32768
BARGRAPH = "################################################################################" \
            + "                                                                                "

def main(stdscr):

    sdr = RtlSdr()

    # configure device
    sdr.sample_rate = 1.024e6  # Hz
    sdr.center_freq = 433.9e6     # Hz
    sdr.freq_correction = 20   # PPM
    sdr.gain = 'auto'

    tones = AudioTones()
    tones.init()

    curses.noecho()
    curses.cbreak()
    curses.curs_set(0)

    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLACK)

    stdscr.clear()  # Clear screen

    bargraph_str = chr(0x2588) * 80 + ' ' * 80  # "block" character

    for i in range(0, 10):
        rssi = MeasureRSSI(sdr)

    # Measure minimum RSSI over a few readings, auto-adjust for dongle gain
    min_rssi = 1000
    for i in range(0, 10):
        rssi = MeasureRSSI(sdr)
        min_rssi = min(min_rssi, rssi)
    ampl_offset = min_rssi
    max_rssi = MeasureRSSI(sdr) - ampl_offset
    avg_rssi = max_rssi + 20;
    counter = 0
 #   redirect_stderr()

    while(True):
        rssi = MeasureRSSI(sdr) - ampl_offset
        if rssi - avg_rssi > 10:
            stdscr.addch(3, 3,'*')
        else:
            stdscr.addch(3, 3,' ')
        avg_rssi = ((15 * avg_rssi) + rssi) / 16
        stdscr.addstr(0, 0, "{0:4.0f} : {1:4.0f}".format(rssi, avg_rssi))
        stdscr.addstr(20, 0, "{0:4.1f}".format(rssi))

# select the bargraph's colour:
        if rssi > 30:
            bargraph_color = 4
        elif rssi > 20:
            bargraph_color = 3
        elif rssi > 15:
            bargraph_color = 2
        else:
            bargraph_color = 1
# draw the bargraph:
        bargraph_idx = min(int(78 - rssi), 80)
        stdscr.addstr(7, 0, bargraph_str[bargraph_idx:bargraph_idx+80], curses.color_pair(bargraph_color))
        stdscr.addstr(8, 0, bargraph_str[bargraph_idx:bargraph_idx+80], curses.color_pair(bargraph_color))

        stdscr.refresh()

        max_rssi = max(max_rssi, rssi)
        counter += 1
        if counter & 0x1F == 0:
            tone_idx = max_rssi
            tone_idx = max(0, tone_idx)
            tone_idx = min(40, tone_idx)
            tones.play(tone_idx)
            max_rssi = rssi
            stdscr.addstr(21, 0, "{0:4.1f}".format(max_rssi))

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


if __name__ == "__main__":
    import os, sys
    wrapper(main)
