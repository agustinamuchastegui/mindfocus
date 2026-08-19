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
        "Tomate un momento para detenerte.",
        4.0,
    ),
    (
        "El error ya ocurrió. "
        "No necesitás negarlo… justificarlo… ni resolverlo inmediatamente. "
        "Ahora, simplemente, observá qué apareció después.",
        6.0,
    ),
    (
        "Buscá una posición estable. "
        "Apoyá bien el cuerpo… soltá un poco los hombros… "
        "y llevá la atención hacia la respiración.",
        6.0,
    ),
    (
        "No intentes respirar de una manera especial. "
        "Sentí el aire entrar… y sentí el aire salir.",
        8.0,
    ),
    (
        "Ahora observá qué dejó el error en el cuerpo. "
        "Quizás aparezca tensión… calor… presión en el pecho… "
        "un nudo en el estómago… o una necesidad urgente de corregir lo que pasó.",
        8.0,
    ),
    (
        "No necesitás eliminar esa sensación. "
        "Reconocé que está ahí… y permitite sentirla durante unos segundos.",
        10.0,
    ),
    (
        "Tal vez tu mente vuelva a reproducir la jugada. "
        "Quizás aparezcan frases como… "
        "¿Cómo pude hacer eso?… "
        "Siempre me pasa lo mismo… "
        "Arruiné todo.",
        6.0,
    ),
    (
        "Notá esas frases por lo que son: "
        "pensamientos que aparecieron después del error. "
        "No son el error en sí mismo.",
        8.0,
    ),
    (
        "Intentá ahora describir lo que ocurrió en una sola frase. "
        "Sin insultarte. Sin exagerar. "
        "Sin convertir una acción en una definición sobre vos. "
        "Solamente el hecho.",
        10.0,
    ),
    (
        "Una decisión llegó tarde. "
        "Una ejecución no salió como esperabas. "
        "Perdiste una oportunidad. "
        "Eso fue lo que ocurrió. "
        "Todo lo demás… es lo que tu mente empezó a construir alrededor.",
        8.0,
    ),
    (
        "Volvé por un momento a la respiración. "
        "Sentí una inhalación completa… y después, una exhalación.",
        10.0,
    ),
    (
        "Un error puede darte información. "
        "Pero castigarte no es lo mismo que aprender. "
        "Para aprender… primero necesitás recuperar claridad.",
        8.0,
    ),
    (
        "Preguntate ahora: ¿Qué necesita de mí la situación que sigue?",
        8.0,
    ),
    (
        "No la acción perfecta. "
        "La próxima acción relevante. "
        "Quizás sea volver a posicionarte… comunicarte… simplificar… "
        "retomar tu plan… o prepararte para la próxima oportunidad.",
        10.0,
    ),
    (
        "Elegí una palabra que te ayude a volver. "
        "Puede ser… Acá… Siguiente… Simple… Firme.",
        8.0,
    ),
    (
        "Repetila internamente una vez.",
        6.0,
    ),
    (
        "Y sentí una última respiración completa.",
        6.0,
    ),
    (
        "El error ya forma parte de lo que ocurrió. "
        "Tu respuesta todavía se está construyendo. "
        "No necesitás borrar el error. "
        "Necesitás evitar que siga decidiendo por vos.",
        5.0,
    ),
    (
        "Cuando estés listo… abrí los ojos… y volvé a la acción que importa.",
        3.0,
    ),
]


def trim_outer_silence(audio: AudioSegment) -> AudioSegment:
    """Remove encoder padding while preserving natural breath room."""
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
    output_dir = Path("output_despues_error")
    output_dir.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="despues-error-render-") as temp_dir:
        temp_path = Path(temp_dir)
        speech_segments: list[AudioSegment] = []

        for index, (text, _) in enumerate(SEGMENTS, start=1):
            mp3_path = temp_path / f"segment_{index:02d}.mp3"
            print(f"Sintetizando {index}/{len(SEGMENTS)}")
            await synthesize(text, mp3_path)

            clip = AudioSegment.from_file(mp3_path, format="mp3")
            clip = trim_outer_silence(clip)
            clip = clip.set_frame_rate(44_100).set_channels(1)

            # Same SAMUKA preset approved in “Volver a la respiración”.
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

        mp3_path = output_dir / "Despues_del_error_volver_a_la_accion_relevante.mp3"
        wav_path = output_dir / "Despues_del_error_voz_limpia.wav"

        track.export(
            mp3_path,
            format="mp3",
            bitrate="192k",
            tags={
                "title": "Después del error — Volver a la acción relevante",
                "artist": "SAMUKA",
                "album": "Mindfulness",
                "comment": f"Voz {VOICE}; velocidad {RATE}; tono {PITCH}; sin música",
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
