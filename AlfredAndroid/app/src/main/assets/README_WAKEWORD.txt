ALFRED LOCAL WAKE WORD MODELS

This directory is intentionally shipped without a fabricated "Alfred" model.

Required production model:
  alfred.onnx

The OpenWakeWord Android adapter also requires the feature models expected by
the selected library version (currently melspectrogram.onnx and
embedding_model.onnx). Add the verified model files here before enabling
production wake detection.

IMPORTANT:
The upstream openWakeWord project provides models such as "hey_jarvis",
but that is NOT an Alfred model. Do not rename another model to alfred.onnx.
A real Alfred classifier must be trained/exported and validated first.
