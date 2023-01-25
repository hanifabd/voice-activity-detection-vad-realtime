# **Voice Activity Detection**

## Brief About Voice Activity Detection (VAD)
[[Wikipedia](https://en.wikipedia.org/wiki/Voice_activity_detection)]

Voice activity detection (VAD), also known as speech activity detection or speech detection, is the detection of the presence or absence of human speech, used in speech processing. The main uses of VAD are in speech coding and speech recognition. It can facilitate speech processing, and can also be used to deactivate some processes during non-speech section of an audio session: it can avoid unnecessary coding/transmission of silence packets in Voice over Internet Protocol (VoIP) applications, saving on computation and on network bandwidth.

VAD is an important enabling technology for a variety of speech-based applications. Therefore, various VAD algorithms have been developed that provide varying features and compromises between latency, sensitivity, accuracy and computational cost. Some VAD algorithms also provide further analysis, for example whether the speech is voiced, unvoiced or sustained. Voice activity detection is usually independent of language.

![VAD](https://github.com/hanifabd/voice-activity-detection-vad-realtime/blob/master/assets/q4E6R.png)

## Package Used in this Service
- webrtcvad - [explore here](https://pypi.org/project/webrtcvad/)
- pyaudio - [explore here](https://pypi.org/project/PyAudio/)

## Service Brief (About Service)

This code will monitor voice activity by using 1 (Voice Activity Detected), _ (No Voice Activity), and X (No Voice Activity Detected for N seconds). after X comes up it will stop or doing some sample activity (time.sleep(5)) and save the recorded frames to .wav audio file.
