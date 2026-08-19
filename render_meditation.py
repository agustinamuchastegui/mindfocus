from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

import edge_tts
from pydub import AudioSegment, effects, silence

VOICE = "es-AR-ElenaNeural"
RATE = "-12%"
PITCH = "-1Hz"
VOLUME = "+0%"

SEGMENTS: list[tuple[str, float]] = [
    (
        "Tomate un momento para detenerte. "
        "No necesitás resolver nada ahora. "
        "Tampoco necesitás alcanzar un estado especial.",
        5.0,
    ),
    (
        "Buscá una posición estable… "
        "Cómoda, pero despierta. "
        "Podés cerrar los ojos… "
        "o dejar la mirada apoyada suavemente en un punto.",
        5.0,
    ),
    (
        "Esta práctica no busca dejar la mente en blanco. "
        "Tampoco busca obligarte a estar tranquilo. "
        "Se trata de observar lo que está ocurriendo… "
        "y entrenar la capacidad de volver.",
        5.0,
    ),
    (
        "Llevá ahora la atención hacia la respiración. "
        "No hace falta respirar más lento… "
        "ni más profundo. "
        "Dejá que el cuerpo respire a su propio ritmo.",
        8.0,
    ),
    (
        "Elegí el lugar donde la respiración se perciba con mayor claridad. "
        "Puede ser el aire entrando y saliendo por la nariz… "
        "el movimiento del pecho… "
        "o la expansión y contracción del abdomen. "
        "No necesitás sentir todo. "
        "Elegí un solo punto y quedate ahí.",
        10.0,
    ),
    (
        "Observá una inhalación desde que comienza… "
        "hasta que termina. "
        "Y después, una exhalación completa.",
        12.0,
    ),
    (
        "En algún momento, tu atención se va a ir. "
        "Puede aparecer un pensamiento… "
        "un sonido… "
        "una sensación… "
        "o algo que tenés que hacer después. "
        "Cuando lo notes, no necesitás pelearte con eso. "
        "Simplemente reconocé que tu atención se fue… "
        "y volvé a sentir la próxima respiración.",
        12.0,
    ),
    (
        "Distraerte no significa que estés haciendo mal la práctica. "
        "El momento en que reconocés que te fuiste… "
        "es el momento en que podés volver. "
        "Y cada vez que volvés… "
        "estás entrenando.",
        15.0,
    ),
    (
        "Una vez más… "
        "Notá dónde está tu atención. "
        "Y si se fue… "
        "soltá lo que apareció… "
        "y volvé a la respiración.",
        12.0,
    ),
    (
        "En el entrenamiento y en la competencia tampoco vas a poder evitar "
        "que aparezcan pensamientos, emociones o distracciones. "
        "Pero podés entrenar tu capacidad de reconocerlos… "
        "y regresar a lo que importa.",
        7.0,
    ),
    ("Sentí una última respiración completa.", 6.0),
    ("Y cuando estés listo… abrí los ojos.", 1.8),
    ("No necesitás controlar todo lo que aparece.", 1.4),
    ("Necesitás aprender a volver.", 3.0),
]


def trim_outer_silence(audio: AudioSegment) -> AudioSegment:
    ranges = silence.detect_nonsilent(
        audio,
        min_silence_len=90,
        silence_thresh=max(-52.0, audio.dBFS - 28.0),
        seek_step=5,
    )
    if not ranges:
        return audio
    start = max(0, ranges[0][0] - 130)
    end = min(len(audio), ranges[-1][1] + 180)
    return audio[start:end]


async def synthesize(text: str, destination: Path) -> None:
    last_error: Exception | None = None
    for attempt in range(5):
        try:
            communicator = edge_tts.Communicate(
                text=text,
                voice=VOICE,
                rate=RATE,
                pitch=PITCH,
                volume=VOLUME,
            )
            await communicator.save(str(destination))
            if destination.exists() and destination.stat().st_size > 1_000:
                return
        except Exception as exc:
            last_error = exc
        await asyncio.sleep(2.0 + attempt * 2.0)
    raise RuntimeError(f"No se pudo sintetizar el segmento: {last_error}")


async def main() -> None:
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="meditation-render-") as temp_dir:
        temp_path = Path(temp_dir)
        speech_segments: list[AudioSegment] = []

        for index, (text, _) in enumerate(SEGMENTS, start=1):
            mp3_path = temp_path / f"segment_{index:02d}.mp3"
            print(f"Sintetizando {index}/{len(SEGMENTS)}")
            await synthesize(text, mp3_path)

            clip = AudioSegment.from_file(mp3_path, format="mp3")
            clip = trim_outer_silence(clip)
            clip = clip.set_frame_rate(44_100).set_channels(1)

            if clip.dBFS != float("-inf"):
                clip = clip.apply_gain(-20.0 - clip.dBFS)
            clip = effects.compress_dynamic_range(
                clip,
                threshold=-24.0,
                ratio=1.65,
                attack=12.0,
                release=170.0,
            )
            clip = clip.fade_in(55).fade_out(105)
            speech_segments.append(clip)

        track = AudioSegment.silent(duration=900, frame_rate=44_100)
        for clip, (_, pause_seconds) in zip(speech_segments, SEGMENTS):
            track += clip
            track += AudioSegment.silent(
                duration=round(pause_seconds * 1000), frame_rate=44_100
            )

        track = effects.normalize(track, headroom=3.0)
        track = track.fade_in(350).fade_out(1_000)
        track = track.set_sample_width(2)

        mp3_path = output_dir / "Volver_a_la_respiracion_Elena.mp3"
        wav_path = output_dir / "Volver_a_la_respiracion_Elena_voz_limpia.wav"

        track.export(
            mp3_path,
            format="mp3",
            bitrate="192k",
            tags={
                "title": "Volver a la respiración",
                "artist": "SAMUKA",
                "album": "Mindfulness",
                "comment": f"Voz {VOICE}; velocidad {RATE}; sin música",
            },
        )
        track.export(wav_path, format="wav")

        metadata = {
            "voice": VOICE,
            "rate": RATE,
            "pitch": PITCH,
            "duration_seconds": round(len(track) / 1000, 2),
            "segments": len(SEGMENTS),
            "mp3": mp3_path.name,
            "wav": wav_path.name,
        }
        (output_dir / "render_metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
