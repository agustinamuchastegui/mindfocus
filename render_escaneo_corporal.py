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
        "Buscá una posición cómoda… "
        "Podés hacer esta práctica acostado… "
        "o sentado, con el cuerpo bien sostenido.",
        5.0,
    ),
    (
        "Dejá que los brazos descansen… "
        "y permití que las manos encuentren una posición natural. "
        "Si te resulta cómodo, cerrá los ojos. "
        "Y si preferís mantenerlos abiertos… "
        "dejá la mirada apoyada suavemente en un punto.",
        6.0,
    ),
    (
        "Antes de comenzar, recordá algo importante: "
        "No necesitás relajarte. "
        "No necesitás sentirte de una manera determinada. "
        "El objetivo de esta práctica es reconocer, con la mayor precisión posible… "
        "cómo se encuentra tu cuerpo ahora.",
        7.0,
    ),
    (
        "Si en algún momento aparece una molestia intensa… "
        "podés cambiar de posición, abrir los ojos o detener la práctica. "
        "Ajustar el cuerpo también es parte de escucharlo.",
        5.0,
    ),
    (
        "Empezá llevando la atención a los lugares donde el cuerpo está siendo sostenido. "
        "El contacto de los pies… "
        "las piernas… "
        "la pelvis… "
        "la espalda.",
        7.0,
    ),
    (
        "Sentí el peso del cuerpo. "
        "Notá dónde hay más presión… "
        "dónde hay menos… "
        "y qué zonas apenas podés percibir.",
        8.0,
    ),
    (
        "Ahora reconocé la respiración. "
        "No hace falta hacerla más profunda… "
        "ni más lenta. "
        "Simplemente registrá que el cuerpo está respirando.",
        7.0,
    ),
    (
        "Tal vez percibas el movimiento en el abdomen… "
        "en el pecho… "
        "o en las fosas nasales. "
        "Elegí el lugar donde la respiración se sienta con mayor claridad… "
        "y permanecé ahí durante unos instantes.",
        12.0,
    ),
    (
        "Ahora comenzaremos a recorrer el cuerpo. "
        "Llevá la atención al pie izquierdo.",
        4.0,
    ),
    (
        "Percibí los dedos… "
        "la planta… "
        "el empeine… "
        "el talón… "
        "y el tobillo.",
        8.0,
    ),
    (
        "Observá si aparece calor… "
        "frío… "
        "presión… "
        "hormigueo… "
        "pulsación… "
        "tensión… "
        "o quizá ninguna sensación claramente reconocible. "
        "No sentir algo específico también es información.",
        9.0,
    ),
    (
        "Subí lentamente por la pierna izquierda. "
        "La pantorrilla… "
        "la parte anterior de la pierna… "
        "y la rodilla.",
        7.0,
    ),
    (
        "Notá la superficie de la rodilla… "
        "su interior… "
        "y la zona posterior. "
        "Sin evaluarla. "
        "Sin decidir si debería sentirse diferente.",
        7.0,
    ),
    (
        "Continuá hacia el muslo izquierdo… "
        "su parte anterior… "
        "posterior… "
        "interna… "
        "y externa.",
        8.0,
    ),
    (
        "Percibí la conexión entre la pierna y la cadera. "
        "Reconocé la pierna izquierda como un conjunto… "
        "desde la cadera hasta los dedos del pie.",
        10.0,
    ),
    (
        "Ahora desplazá la atención al pie derecho. "
        "Los dedos… "
        "la planta… "
        "el empeine… "
        "el talón… "
        "y el tobillo.",
        8.0,
    ),
    (
        "Registrá las sensaciones presentes. "
        "Quizá este pie se sienta distinto del izquierdo. "
        "No necesitás que ambos lados sean iguales. "
        "Solamente reconocé la diferencia.",
        8.0,
    ),
    (
        "Subí por la pierna derecha… "
        "la pantorrilla… "
        "la parte anterior… "
        "y la rodilla.",
        7.0,
    ),
    (
        "Continuá hacia el muslo… "
        "recorriendo su parte anterior… "
        "posterior… "
        "interna… "
        "y externa.",
        8.0,
    ),
    (
        "Percibí la cadera derecha… "
        "y después, la pierna completa. "
        "Desde la cadera… "
        "hasta los dedos del pie.",
        10.0,
    ),
    (
        "Ampliá ahora la atención para incluir las dos piernas al mismo tiempo.",
        5.0,
    ),
    (
        "Notá su peso… "
        "su temperatura… "
        "los puntos de contacto… "
        "y cualquier diferencia entre un lado y el otro.",
        10.0,
    ),
    (
        "Llevá la atención a la pelvis. "
        "Percibí los glúteos… "
        "las caderas… "
        "y los puntos donde esta zona está siendo sostenida.",
        8.0,
    ),
    (
        "Observá si hay tensión… "
        "presión… "
        "movimiento… "
        "o zonas que se sienten más neutras.",
        7.0,
    ),
    (
        "Desplazá la atención hacia la parte baja del abdomen. "
        "Sin modificar la respiración… "
        "sentí cómo el abdomen cambia con cada ciclo. "
        "Tal vez se expanda al inhalar… "
        "y descienda al exhalar.",
        12.0,
    ),
    (
        "Ahora incluí la zona lumbar… "
        "la parte baja de la espalda.",
        5.0,
    ),
    (
        "Notá si algún músculo permanece activo… "
        "si aparece rigidez… "
        "calor… "
        "cansancio… "
        "o simplemente el contacto con la superficie que sostiene el cuerpo.",
        9.0,
    ),
    (
        "No intentes eliminar la tensión. "
        "Primero reconocela. "
        "Observá su ubicación… "
        "su intensidad… "
        "y sus límites.",
        9.0,
    ),
    (
        "Subí hacia la parte media de la espalda… "
        "y después hacia la parte alta.",
        7.0,
    ),
    (
        "Percibí los omóplatos… "
        "el espacio entre ellos… "
        "y el contacto de la espalda con la ropa o la superficie.",
        9.0,
    ),
    (
        "Llevá ahora la atención al pecho. "
        "Observá el movimiento de la respiración… "
        "la expansión… "
        "y el regreso.",
        10.0,
    ),
    (
        "Quizá también puedas percibir el latido del corazón. "
        "Y si no lo percibís… "
        "no es necesario buscarlo. "
        "Continuá con lo que sí está disponible.",
        8.0,
    ),
    (
        "Dirigí la atención hacia los hombros.",
        4.0,
    ),
    (
        "Notá su posición. "
        "Observá si están elevados… "
        "hacia adelante… "
        "hacia atrás… "
        "o si existe alguna diferencia entre ambos.",
        8.0,
    ),
    (
        "Desde el hombro izquierdo, recorré lentamente el brazo. "
        "La parte superior… "
        "el codo… "
        "el antebrazo… "
        "la muñeca… "
        "la palma… "
        "el dorso de la mano… "
        "y cada uno de los dedos.",
        12.0,
    ),
    (
        "Percibí la mano izquierda completa. "
        "Su temperatura… "
        "su peso… "
        "y cualquier pequeño movimiento o pulsación.",
        7.0,
    ),
    (
        "Ahora recorré el brazo derecho. "
        "La parte superior… "
        "el codo… "
        "el antebrazo… "
        "la muñeca… "
        "la palma… "
        "el dorso… "
        "y los dedos.",
        12.0,
    ),
    (
        "Registrá el brazo y la mano derecha como un conjunto.",
        7.0,
    ),
    (
        "Después, incluí los dos brazos y las dos manos en un mismo campo de atención.",
        10.0,
    ),
    (
        "Llevá la atención hacia el cuello… "
        "la nuca… "
        "y la garganta.",
        7.0,
    ),
    (
        "Observá si existe tensión o esfuerzo. "
        "No hace falta corregirlo. "
        "Si el cuerpo se acomoda por sí mismo… "
        "simplemente notá ese cambio.",
        8.0,
    ),
    (
        "Subí hacia la mandíbula. "
        "Percibí los músculos a cada lado de la cara… "
        "el contacto entre los dientes… "
        "los labios… "
        "y la lengua dentro de la boca.",
        9.0,
    ),
    (
        "Continuá hacia las mejillas… "
        "la nariz… "
        "y la zona alrededor de los ojos.",
        7.0,
    ),
    (
        "Notá los párpados… "
        "las cejas… "
        "y el espacio entre ellas.",
        8.0,
    ),
    (
        "Recorré la frente… "
        "las sienes… "
        "el cuero cabelludo… "
        "y la parte posterior de la cabeza.",
        10.0,
    ),
    (
        "Ahora ampliá lentamente la atención. "
        "Incluí la cabeza… "
        "el cuello… "
        "los hombros… "
        "los brazos… "
        "el torso… "
        "la pelvis… "
        "las piernas… "
        "y los pies.",
        12.0,
    ),
    (
        "Percibí el cuerpo completo… "
        "como un solo campo de sensaciones.",
        12.0,
    ),
    (
        "Algunas zonas se sienten con claridad. "
        "Otras pueden parecer distantes… "
        "neutras… "
        "o difíciles de reconocer. "
        "No necesitás completar ninguna imagen perfecta del cuerpo. "
        "Permanecé disponible para aquello que aparece.",
        15.0,
    ),
    (
        "Notá también que las sensaciones cambian. "
        "Una presión puede disminuir… "
        "una tensión puede desplazarse… "
        "una zona puede hacerse más presente… "
        "y otra, desaparecer de la atención.",
        10.0,
    ),
    (
        "El entrenamiento no consiste en controlar cada sensación. "
        "Consiste en reconocerla antes de reaccionar automáticamente.",
        10.0,
    ),
    (
        "Volvé a sentir la respiración dentro del cuerpo completo.",
        8.0,
    ),
    (
        "Cada vez que inhalás… "
        "el cuerpo cambia ligeramente. "
        "Cada vez que exhalás… "
        "vuelve a reorganizarse.",
        12.0,
    ),
    (
        "El objetivo no es alcanzar un estado perfecto. "
        "Es reconocer con mayor claridad el estado que ya está presente… "
        "para poder responder mejor a lo que viene.",
        10.0,
    ),
    (
        "Empezá a percibir nuevamente el espacio que te rodea. "
        "Los sonidos… "
        "la temperatura del ambiente… "
        "y la superficie que sostiene tu cuerpo.",
        7.0,
    ),
    (
        "Mové suavemente los dedos de las manos… "
        "y los dedos de los pies.",
        5.0,
    ),
    (
        "Si estás acostado, podés flexionar las piernas… "
        "o girar lentamente hacia un costado antes de incorporarte.",
        6.0,
    ),
    (
        "Cuando estés listo… "
        "abrí los ojos.",
        5.0,
    ),
    (
        "Antes de continuar con tu día o con tu entrenamiento… "
        "registrá una última vez cómo está tu cuerpo. "
        "Sin juzgarlo. "
        "Sin exigirle que sea diferente. "
        "Solamente reconociendo la información que está disponible.",
        7.0,
    ),
    (
        "La práctica terminó.",
        3.0,
    ),
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
    for attempt in range(6):
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
        await asyncio.sleep(2.5 + attempt * 2.5)
    raise RuntimeError(f"No se pudo sintetizar el segmento: {last_error}")


async def main() -> None:
    output_dir = Path("output_escaneo_corporal")
    output_dir.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="escaneo-corporal-") as temp_dir:
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

        track = AudioSegment.silent(duration=1_000, frame_rate=44_100)
        for clip, (_, pause_seconds) in zip(speech_segments, SEGMENTS):
            track += clip
            track += AudioSegment.silent(
                duration=round(pause_seconds * 1_000),
                frame_rate=44_100,
            )

        track = effects.normalize(track, headroom=3.0)
        track = track.fade_in(350).fade_out(1_200)
        track = track.set_sample_width(2)

        mp3_path = output_dir / "Escaneo_corporal_reconocer_las_senales_del_cuerpo.mp3"
        wav_path = output_dir / "Escaneo_corporal_voz_limpia.wav"

        track.export(
            mp3_path,
            format="mp3",
            bitrate="192k",
            tags={
                "title": "Escaneo corporal — Reconocer las señales del cuerpo",
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
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
