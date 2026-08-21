from dataclasses import dataclass


@dataclass
class Assistant:
    name: str
    language: str
    voice_model: str


ALFRED = Assistant(
    name="ALFRED",
    language="english",
    voice_model="en_GB-alan-medium.onnx",
)


FRIDAY = Assistant(
    name="F.R.I.D.A.Y.",
    language="urdu",
    voice_model="ur_PK-aegis_female-medium.onnx",
)