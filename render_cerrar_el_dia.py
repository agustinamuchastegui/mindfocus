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
        "Buscá una posición cómoda. "
        "Podés estar sentado… o acostado, con el cuerpo bien sostenido. "
        "Dejá que las manos descansen… aflojá los hombros… "
        "y permití que la respiración encuentre su propio ritmo.",
        5.0,
    ),
    (
        "No necesitás respirar de una manera especial. "
        "Solamente reconocé que el día está llegando a su final.",
        6.0,
    ),
    (
        "Cerrar el día no significa que todo haya quedado resuelto. "
        "Tampoco significa revisar cada decisión… cada conversación… "
        "o cada cosa que faltó. "
        "Significa reconocer que, por hoy… no necesitás seguir respondiendo.",
        7.0,
    ),
    (
        "Llevá la atención al cuerpo. "
        "Notá el peso… los puntos de apoyo… "
        "y las zonas que todavía conservan tensión. "
        "Quizá el cuerpo siga sosteniendo algo del día. "
        "Cansancio… aceleración… preocupación… "
        "o una conversación que continúa en tu mente.",
        7.0,
    ),
    (
        "No hace falta expulsar nada. "
        "Podés reconocer: Esto está presente. "
        "Y también: No necesito resolverlo ahora.",
        8.0,
    ),
    (
        "Traé a la mente, por un instante, aquello que quedó abierto. "
        "Una tarea… una decisión… algo pendiente… "
        "o algo que no salió como esperabas. "
        "Observá si tu mente intenta seguir trabajando. "
        "Quizá busque anticipar mañana… corregir el pasado… "
        "o encontrar una certeza antes de descansar. "
        "Recordale con firmeza: Esto puede esperar.",
        7.0,
    ),
    (
        "Ahora pensá en una sola cosa que hoy hayas sostenido. "
        "No tiene que ser un gran logro. "
        "Tal vez estuviste presente… cumpliste una tarea… pediste ayuda… "
        "pusiste un límite… o atravesaste un momento difícil sin abandonar lo que importa. "
        "Reconocelo sin exagerarlo… pero también sin quitarle valor.",
        7.0,
    ),
    (
        "Sentí una inhalación completa… y una exhalación. "
        "Al exhalar, dejá el día donde corresponde: en el día que terminó. "
        "Lo aprendido puede quedarse con vos. "
        "Lo pendiente puede continuar mañana. "
        "Lo que no pudiste controlar… no necesita seguir ocupando tu cuerpo ahora.",
        6.0,
    ),
    (
        "Volvé a sentir los puntos de apoyo. "
        "Permití que el peso sea sostenido. "
        "No necesitás llevar todo con vos.",
        5.0,
    ),
    (
        "Antes de terminar, elegí una intención simple para mañana. "
        "No una lista. Una dirección. "
        "Quizá estar presente… hablar con claridad… actuar con calma… "
        "o volver a intentar. "
        "Guardá esa intención… sin empezar todavía a vivir el día siguiente.",
        7.0,
    ),
    (
        "El día no necesita haber sido perfecto para poder terminar. "
        "Vos tampoco necesitás quedar completamente en calma. "
        "Solamente permitir que este momento sea suficiente.",
        6.0,
    ),
    ("Sentí una última respiración.", 5.0),
    (
        "Y cuando estés listo… dejá que el día termine.",
        7.0,
    ),
    ("La práctica terminó.", 2.0),
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
    output_dir = Path("output_cerrar_dia")
    output_dir.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="cerrar-dia-render-") as temp_dir:
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

        mp3_path = output_dir / "Cerrar_el_dia_dejar_de_responder_por_hoy.mp3"
        wav_path = output_dir / "Cerrar_el_dia_voz_limpia.wav"

        track.export(
            mp3_path,
            format="mp3",
            bitrate="192k",
            tags={
                "title": "Cerrar el día — Dejar de responder por hoy",
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
            "scripted_pause_seconds": sum(pause for _, pause in SEGMENTS),
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
