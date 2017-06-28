# JammerDetect
Detect jamming on ISM bands using an RTLSDR dongle and a Raspberry Pi or laptop PC.

The primary motivation was to detect (and possibly track down!) car-keyfob jammers being used by criminals, but it could equally well
be used to detect continuous transmissions in any band that the dongle can receive, including the 868MHz and 915MHz ISM bands.

It uses a fork of Steve Markgraf's librtlsdr library, with a simple-as-possible function added to measure RF power in the receiver's bandwidth.
(In order to run it on a battery-powered Raspberry Pi, we want to minimise the processing load).

The main program is written in Python to make it easy to modify, so we also use the pyrtlsdr package (Python bindings to librtlsdr).

Mike H.  June 2017
