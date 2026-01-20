from faster_whisper import WhisperModel

model_size= "small"

model = WhisperModel(model_size, device="cpu", compute_type="int8")

segments, info = model.transcribe("audio/brandon-2x.wav", beam_size=5)


print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

for segment in segments:
    print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))


#  Detected language 'en' with probability 0.986499 - normal speed
# [0.00s -> 7.92s]  like I was saying it's not the things that are going on it's also what was
# [7.92s -> 14.72s]  happening in here I would appreciate that you've been taking care of me so
# [14.72s -> 17.20s]  thank you


# Detected language 'en' with probability 0.684765 - 2x
# [0.00s -> 5.00s]  It's not the things that are going on, it's also what was happening here.
# [5.00s -> 8.00s]  I would appreciate that you've been taking care of me, so thank you.


# Detected language 'en' with probability 0.986080 - 1.5x
# [0.00s -> 6.00s]  Like I was saying, it's not the things that are going on, it's also what was happening in here.
# [6.00s -> 10.00s]  I would appreciate that you've been taking care of me, so thank you.