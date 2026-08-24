from __future__ import annotations

import asyncio
import json
import tempfile
from pathlib import Path

import edge_tts
from pydub import AudioSegment, effects, silence

VOICE = "es-AR-ElenaNeural"
RATE = "-10%"
PITCH = "-1Hz"
VOLUME = "+0%"

SEGMENTS: list[tuple[str, float]] = [
    (
        "Buscá una posición estable. "
        "Podés estar sentado… "
        "o acostado, con el cuerpo bien sostenido.",
        5.0,
    ),
    (
        "Dejá que las manos descansen… "
        "aflojá los brazos… "
        "y permití que la mirada se apoye suavemente en un punto. "
        "Si te resulta cómodo… "
        "podés cerrar los ojos.",
        7.0,
    ),
    (
        "Comenzá reconociendo los puntos de contacto del cuerpo. "
        "Los pies… "
        "las piernas… "
        "la pelvis… "
        "la espalda… "
        "y las manos.",
        8.0,
    ),
    (
        "Sentí el peso del cuerpo. "
        "No necesitás cambiar la postura. "
        "Solamente reconocé cómo estás en este momento.",
        8.0,
    ),
    (
        "Ahora llevá la atención a la respiración. "
        "No hace falta respirar más lento… "
        "ni más profundo. "
        "La respiración no va a ser utilizada para eliminar la presión. "
        "Va a funcionar solamente como un punto de referencia… "
        "al que podés volver cuando la atención queda atrapada.",
        10.0,
    ),
    (
        "Registrá una inhalación… "
        "y una exhalación.",
        8.0,
    ),
    (
        "En esta práctica no vas a intentar sentirte completamente tranquilo. "
        "Tampoco vas a imaginar que la presión no existe.",
        7.0,
    ),
    (
        "Vas a entrenar algo diferente: "
        "la capacidad de hacerle lugar a una experiencia incómoda… "
        "sin permitir que esa experiencia decida por vos.",
        10.0,
    ),
    (
        "Traé a la mente una situación deportiva en la que habitualmente sientas presión.",
        6.0,
    ),
    (
        "Puede ser una competencia importante… "
        "un momento decisivo… "
        "una evaluación… "
        "una convocatoria… "
        "el regreso después de una lesión… "
        "o una situación en la que sentís que necesitás demostrar algo.",
        10.0,
    ),
    (
        "Elegí una escena concreta. "
        "No hace falta que sea la situación más difícil que hayas vivido. "
        "Buscá una que puedas observar sin quedar completamente absorbido por ella.",
        8.0,
    ),
    (
        "Dejá que la escena aparezca lentamente. "
        "El lugar… "
        "las personas… "
        "los sonidos… "
        "el momento previo a comenzar.",
        12.0,
    ),
    (
        "Sin analizar todavía cómo deberías responder… "
        "observá qué hace tu mente frente a esa situación.",
        7.0,
    ),
    (
        "Quizá aparezcan pensamientos como: "
        "Tengo que hacerlo bien. "
        "No puedo fallar. "
        "Esta oportunidad es demasiado importante. "
        "Todos están esperando algo de mí. "
        "Necesito demostrar que estoy preparado.",
        10.0,
    ),
    (
        "Tal vez aparezcan imágenes de algo que podría salir mal… "
        "recuerdos de errores anteriores… "
        "comparaciones… "
        "dudas… "
        "o intentos de anticipar cada detalle.",
        10.0,
    ),
    (
        "No necesitás detener esos pensamientos. "
        "Tampoco necesitás responderles. "
        "Simplemente reconocé: "
        "Mi mente está intentando anticipar lo que puede ocurrir.",
        9.0,
    ),
    (
        "Los pensamientos pueden estar presentes… "
        "sin transformarse automáticamente en instrucciones.",
        9.0,
    ),
    (
        "Llevá ahora la atención al cuerpo.",
        5.0,
    ),
    (
        "Observá dónde se manifiesta la presión.",
        8.0,
    ),
    (
        "Tal vez aparezca tensión en el pecho… "
        "un nudo en el abdomen… "
        "rigidez en los hombros… "
        "calor en la cara… "
        "inquietud en las piernas… "
        "o una respiración más rápida.",
        10.0,
    ),
    (
        "Quizá sientas energía… "
        "urgencia… "
        "pesadez… "
        "o dificultad para permanecer quieto.",
        8.0,
    ),
    (
        "No hace falta decidir si esas sensaciones son buenas o malas. "
        "Por unos instantes… "
        "observá solamente sus características.",
        8.0,
    ),
    (
        "¿Dónde comienzan? "
        "¿Dónde terminan? "
        "¿Permanecen estables… "
        "o cambian de intensidad?",
        12.0,
    ),
    (
        "Notá si aparece el impulso de hacerlas desaparecer. "
        "Quizá quieras tranquilizarte… "
        "controlar la respiración… "
        "distraerte… "
        "o convencerte de que no pasa nada.",
        10.0,
    ),
    (
        "Reconocé también ese impulso.",
        5.0,
    ),
    (
        "La lucha contra la presión suele agregar una segunda exigencia: "
        "además de competir… "
        "sentir que primero deberías encontrarte de una manera determinada.",
        10.0,
    ),
    (
        "Por unos instantes… "
        "soltá esa exigencia.",
        7.0,
    ),
    (
        "No necesitás sentirte perfecto para actuar con claridad. "
        "No necesitás eliminar la activación para responder bien.",
        10.0,
    ),
    (
        "Permití que las sensaciones ocupen exactamente el espacio que ocupan. "
        "Ni más… "
        "ni menos.",
        8.0,
    ),
    (
        "Podés decir internamente: "
        "Hay presión.",
        6.0,
    ),
    (
        "No: Soy débil. "
        "No: No estoy preparado. "
        "Solamente: En este momento, hay presión.",
        10.0,
    ),
    (
        "Observá si podés permanecer junto a esa experiencia durante una respiración completa.",
        10.0,
    ),
    (
        "Y después, durante una respiración más.",
        10.0,
    ),
    (
        "No para esperar que desaparezca… "
        "sino para comprobar que podés permanecer presente mientras está.",
        10.0,
    ),
    (
        "Ahora ampliá la atención. "
        "Además de las sensaciones relacionadas con la presión… "
        "percibí los pies.",
        5.0,
    ),
    (
        "Las manos.",
        5.0,
    ),
    (
        "Los puntos de apoyo.",
        5.0,
    ),
    (
        "Los sonidos que aparecen a tu alrededor.",
        7.0,
    ),
    (
        "La presión continúa formando parte de la experiencia… "
        "pero ya no es necesariamente toda la experiencia.",
        10.0,
    ),
    (
        "Hay sensaciones internas… "
        "y también existe un entorno. "
        "Hay pensamientos… "
        "y también hay información disponible. "
        "Hay activación… "
        "y también existe la posibilidad de elegir una respuesta.",
        12.0,
    ),
    (
        "Preguntate ahora: "
        "¿Qué hace que esta situación sea importante para mí?",
        10.0,
    ),
    (
        "Quizá aparezca tu compromiso… "
        "el trabajo realizado… "
        "el deseo de competir… "
        "la responsabilidad con un equipo… "
        "o la oportunidad de poner en juego algo que valorás.",
        10.0,
    ),
    (
        "No necesitás romantizar la presión. "
        "Puede ser incómoda… "
        "intensa… "
        "y difícil de sostener.",
        8.0,
    ),
    (
        "Pero su presencia suele indicar que hay algo en juego que te importa.",
        10.0,
    ),
    (
        "Ahora preguntate: "
        "¿Cómo quiero actuar cuando la presión está presente?",
        10.0,
    ),
    (
        "No cómo querés sentirte. "
        "Cómo querés actuar.",
        8.0,
    ),
    (
        "Tal vez quieras actuar con decisión… "
        "con valentía… "
        "con paciencia… "
        "con claridad… "
        "con intensidad… "
        "o con compromiso.",
        10.0,
    ),
    (
        "Elegí una cualidad. "
        "Una forma de estar en la competencia… "
        "que dependa de tu conducta y no de la desaparición de la presión.",
        12.0,
    ),
    (
        "Repetí esa palabra internamente.",
        8.0,
    ),
    (
        "Y preguntate: "
        "¿Cuál es la primera conducta concreta que representa esa cualidad?",
        10.0,
    ),
    (
        "Puede ser orientar la mirada hacia el entorno… "
        "comunicarte… "
        "mantener una postura disponible… "
        "respetar tu rutina… "
        "buscar información… "
        "o ejecutar de manera simple la primera acción.",
        12.0,
    ),
    (
        "Visualizate nuevamente en la situación de presión.",
        6.0,
    ),
    (
        "La competencia está por comenzar. "
        "La activación aparece. "
        "Los pensamientos también.",
        8.0,
    ),
    (
        "Esta vez… "
        "no intentás expulsarlos.",
        6.0,
    ),
    (
        "Reconocés: "
        "Hay presión.",
        5.0,
    ),
    (
        "Sentís un punto de contacto del cuerpo.",
        5.0,
    ),
    (
        "Recordás la cualidad que elegiste.",
        5.0,
    ),
    (
        "Orientás la mirada hacia la información relevante… "
        "y realizás la primera acción.",
        12.0,
    ),
    (
        "Una vez más.",
        4.0,
    ),
    (
        "Presión.",
        4.0,
    ),
    (
        "Contacto con el cuerpo.",
        4.0,
    ),
    (
        "Hacer lugar.",
        4.0,
    ),
    (
        "Mirar hacia afuera.",
        4.0,
    ),
    (
        "Actuar de acuerdo con lo que importa.",
        12.0,
    ),
    (
        "La presión puede seguir presente. "
        "No necesitás comprobar constantemente si disminuyó.",
        8.0,
    ),
    (
        "Cada vez que revisás si ya te sentís bien… "
        "la atención vuelve a quedar atrapada en tu estado interno.",
        9.0,
    ),
    (
        "En cambio, podés preguntarte: "
        "¿Qué información necesito ahora?",
        8.0,
    ),
    (
        "¿Qué pide esta situación?",
        8.0,
    ),
    (
        "¿Cuál es la próxima acción relevante?",
        10.0,
    ),
    (
        "Sentir presión y actuar con claridad… "
        "no son experiencias incompatibles.",
        9.0,
    ),
    (
        "Podés tener dudas… "
        "y buscar información.",
        6.0,
    ),
    (
        "Podés sentir activación… "
        "y ejecutar con precisión.",
        6.0,
    ),
    (
        "Podés sentir miedo… "
        "y avanzar hacia aquello que elegiste hacer.",
        10.0,
    ),
    (
        "La presión puede estar presente… "
        "sin ocupar el lugar de la decisión.",
        12.0,
    ),
    (
        "Volvé ahora a sentir el cuerpo completo.",
        7.0,
    ),
    (
        "La respiración… "
        "los puntos de contacto… "
        "los sonidos… "
        "y el espacio que te rodea.",
        10.0,
    ),
    (
        "Mové lentamente los dedos de las manos… "
        "y los dedos de los pies.",
        6.0,
    ),
    (
        "Si tenés los ojos cerrados… "
        "podés abrirlos suavemente.",
        7.0,
    ),
    (
        "Antes de terminar, recordá: "
        "No necesitás esperar a que la presión desaparezca.",
        6.0,
    ),
    (
        "Podés reconocerla… "
        "hacerle lugar… "
        "orientar la atención… "
        "y actuar.",
        8.0,
    ),
    (
        "Tranquilo para percibir. "
        "Intenso para buscar. "
        "Disponible para responder.",
        10.0,
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
    output_dir = Path("output_hacer_lugar_presion")
    output_dir.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="hacer-lugar-presion-") as temp_dir:
        temp_path = Path(temp_dir)
        speech_segments: list[AudioSegment] = []

        for index, (text, _) in enumerate(SEGMENTS, start=1):
            mp3_path = temp_path / f"segment_{index:03d}.mp3"
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

        mp3_path = output_dir / "Hacer_lugar_a_la_presion_actuar_sin_esperar_que_desaparezca.mp3"
        wav_path = output_dir / "Hacer_lugar_a_la_presion_voz_limpia.wav"

        track.export(
            mp3_path,
            format="mp3",
            bitrate="192k",
            tags={
                "title": "Hacer lugar a la presión",
                "artist": "SAMUKA",
                "album": "Mindfulness",
                "comment": f"Actuar sin esperar que desaparezca; voz {VOICE}; velocidad {RATE}; sin música",
            },
        )
        track.export(wav_path, format="wav")

        metadata = {
            "title": "Hacer lugar a la presión",
            "subtitle": "Actuar sin esperar que desaparezca",
            "voice": VOICE,
            "rate": RATE,
            "pitch": PITCH,
            "duration_seconds": round(len(track) / 1000, 2),
            "segments": len(SEGMENTS),
            "scripted_pause_seconds": round(sum(pause for _, pause in SEGMENTS), 1),
            "mp3": mp3_path.name,
            "wav": wav_path.name,
        }
        (output_dir / "render_metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(json.dumps(metadata, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
