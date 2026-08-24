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
TARGET_DURATION_MS = 294_000  # Mantener margen por debajo de cinco minutos.

# El título y las indicaciones de producción no forman parte de la locución.
# Las pausas originales se conservan proporcionalmente, pero se ajustan de
# manera automática si fueran incompatibles con el límite total de 5 minutos.
SEGMENTS: list[tuple[str, float]] = [
    (
        "Buscá una posición estable. "
        "Podés estar sentado… o acostado, con el cuerpo bien sostenido. "
        "Dejá que las manos descansen… aflojá los hombros… "
        "y permití que la respiración encuentre su propio ritmo.",
        5.0,
    ),
    (
        "Antes de comenzar, recordá algo importante. "
        "Agradecer no significa negar lo difícil. "
        "Tampoco significa convencerte de que todo está bien. "
        "Significa ampliar la mirada… "
        "para que aquello que falta no borre todo lo que ya está.",
        7.0,
    ),
    (
        "Sentí una inhalación completa… y una exhalación.",
        5.0,
    ),
    (
        "Reconocé, por un instante, el hecho simple de estar acá. "
        "Hay un cuerpo respirando. "
        "Un nuevo día comenzando. "
        "Y una parte de vos que todavía puede elegir cómo habitarlo.",
        7.0,
    ),
    (
        "Llevá la atención hacia algo concreto que hoy te sostiene. "
        "Puede ser la cama donde descansaste… "
        "el techo que te protege… "
        "el agua que podés tomar… "
        "la luz que entra… "
        "o el aire que llega al cuerpo sin que tengas que pedirlo.",
        7.0,
    ),
    (
        "No lo conviertas solamente en una idea. "
        "Percibilo. "
        "Permití que algo cotidiano… vuelva a mostrar su valor.",
        7.0,
    ),
    (
        "Ahora traé a la mente a una persona… "
        "un vínculo… o una presencia que forme parte de tu vida. "
        "Alguien que te acompañó… que te enseñó algo… "
        "que confió en vos… "
        "o cuya existencia hace que tu mundo sea distinto.",
        8.0,
    ),
    (
        "No necesitás sentir una emoción intensa. "
        "Solamente reconocer: "
        "Esta persona forma parte de lo bueno que existe en mi vida.",
        7.0,
    ),
    (
        "Pensá ahora en algo que hoy sí podés hacer. "
        "Moverte… aprender… trabajar… cuidar… pedir ayuda… "
        "volver a intentar… o elegir una dirección.",
        7.0,
    ),
    (
        "Quizá no tengas todas las condiciones que desearías. "
        "Pero hay recursos… aprendizajes… "
        "y posibilidades que ya están disponibles. "
        "Reconocelos sin minimizar su valor.",
        7.0,
    ),
    (
        "La abundancia no significa tenerlo todo. "
        "Significa no vivir únicamente mirando lo que falta.",
        6.0,
    ),
    (
        "Es recordar que una vida puede contener pendientes… "
        "dolor… incertidumbre… "
        "y, al mismo tiempo… vínculos… capacidades… oportunidades… "
        "y momentos valiosos.",
        8.0,
    ),
    (
        "Dejá que ambas cosas sean verdad. "
        "Hay cosas que todavía querés construir. "
        "Y también hay algo que ya merece ser recibido.",
        7.0,
    ),
    (
        "Preguntate ahora: "
        "¿Qué no quiero dar por sentado hoy?",
        7.0,
    ),
    (
        "Puede ser una persona… una oportunidad… tu salud… "
        "tu trabajo… tu familia… tu cuerpo… "
        "o simplemente este día. "
        "Elegí una sola cosa.",
        7.0,
    ),
    (
        "Y decí internamente: "
        "Gracias por esto que sí está.",
        8.0,
    ),
    (
        "Sentí una última respiración completa.",
        5.0,
    ),
    (
        "Antes de comenzar el día, recordá: "
        "No necesitás esperar a tener todo… "
        "para reconocer lo que ya tenés.",
        5.0,
    ),
    (
        "Que lo que falta no borre lo que existe. "
        "Que lo difícil no te impida recibir lo bueno. "
        "Y que hoy puedas mirar la vida… también… desde lo que sí.",
        7.0,
    ),
    (
        "Cuando estés listo… abrí los ojos.",
        5.0,
    ),
    ("La práctica terminó.", 1.5),
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
    output_dir = Path("output_lo_que_si_esta")
    output_dir.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="lo-que-si-esta-render-") as temp_dir:
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

        intro_ms = 900
        speech_ms = sum(len(clip) for clip in speech_segments)
        desired_pause_ms = round(sum(pause for _, pause in SEGMENTS) * 1000)
        available_pause_ms = TARGET_DURATION_MS - intro_ms - speech_ms
        if available_pause_ms <= 0:
            raise RuntimeError(
                "La locución por sí sola supera la duración objetivo; "
                "es necesario condensar el texto."
            )

        pause_scale = min(1.0, available_pause_ms / desired_pause_ms)
        actual_pauses_ms = [
            max(800, round(pause_seconds * 1000 * pause_scale))
            for _, pause_seconds in SEGMENTS
        ]

        # Corregir cualquier diferencia de redondeo para mantener el objetivo.
        projected_ms = intro_ms + speech_ms + sum(actual_pauses_ms)
        overflow_ms = max(0, projected_ms - TARGET_DURATION_MS)
        index = len(actual_pauses_ms) - 1
        while overflow_ms > 0 and index >= 0:
            reducible = max(0, actual_pauses_ms[index] - 800)
            reduction = min(reducible, overflow_ms)
            actual_pauses_ms[index] -= reduction
            overflow_ms -= reduction
            index -= 1

        track = AudioSegment.silent(duration=intro_ms, frame_rate=44_100)
        for clip, pause_ms in zip(speech_segments, actual_pauses_ms):
            track += clip
            track += AudioSegment.silent(duration=pause_ms, frame_rate=44_100)

        track = effects.normalize(track, headroom=3.0)
        track = track.fade_in(350).fade_out(1_000)
        track = track.set_sample_width(2)

        mp3_path = output_dir / "Lo_que_si_esta_comenzar_el_dia_desde_la_abundancia.mp3"
        wav_path = output_dir / "Lo_que_si_esta_voz_limpia.wav"

        track.export(
            mp3_path,
            format="mp3",
            bitrate="192k",
            tags={
                "title": "Lo que sí está — Comenzar el día desde la abundancia",
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
            "desired_pause_seconds": round(desired_pause_ms / 1000, 2),
            "actual_pause_seconds": round(sum(actual_pauses_ms) / 1000, 2),
            "pause_scale": round(pause_scale, 4),
            "mp3": mp3_path.name,
            "wav": wav_path.name,
        }
        (output_dir / "render_metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(metadata, ensure_ascii=False, indent=2))

        if len(track) > 300_000:
            raise RuntimeError(
                f"El audio supera los 5 minutos: {len(track) / 1000:.2f} segundos"
            )


if __name__ == "__main__":
    asyncio.run(main())
