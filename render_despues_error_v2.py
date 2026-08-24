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
        "Buscá una posición estable. "
        "Podés estar sentado… o acostado, con el cuerpo bien sostenido.",
        5.0,
    ),
    (
        "Dejá que los brazos descansen… "
        "Aflojá las manos… "
        "y permití que la mirada se apoye suavemente en un punto. "
        "Si te resulta cómodo… podés cerrar los ojos.",
        7.0,
    ),
    (
        "Tomate un momento para reconocer que estás acá. "
        "Sentí el peso del cuerpo… "
        "los lugares de contacto… "
        "y los sonidos que aparecen a tu alrededor.",
        8.0,
    ),
    (
        "Ahora llevá la atención a la respiración. "
        "No hace falta hacerla más profunda… "
        "ni intentar tranquilizarte. "
        "Simplemente registrá una inhalación… "
        "y una exhalación.",
        10.0,
    ),
    (
        "Esta práctica no busca borrar un error. "
        "Tampoco busca convencerte de que no fue importante… "
        "o reemplazar lo ocurrido por un pensamiento positivo.",
        6.0,
    ),
    (
        "El error ocurrió. "
        "Y puede contener información que será necesario revisar. "
        "Pero ese análisis puede llegar después.",
        7.0,
    ),
    (
        "Ahora vas a entrenar otra capacidad: "
        "evitar que una acción que ya terminó… "
        "siga ocupando la atención que necesitás para la siguiente.",
        9.0,
    ),
    (
        "Traé a la mente un error reciente. "
        "Elegí una situación concreta… "
        "y tolerable. "
        "No hace falta que busques el error más difícil de tu carrera.",
        7.0,
    ),
    (
        "Dejá que aparezca solamente el momento necesario para reconocerlo. "
        "Sin reconstruir toda la competencia… "
        "sin adelantar consecuencias… "
        "sin repetir la escena una y otra vez.",
        10.0,
    ),
    (
        "Observá brevemente qué ocurrió. "
        "Como si describieras una acción desde afuera.",
        6.0,
    ),
    (
        "Quizá fallaste una ejecución… "
        "tomaste una decisión tarde… "
        "perdiste una pelota… "
        "no pudiste sostener el plan… "
        "o reaccionaste de una manera que no querías.",
        8.0,
    ),
    (
        "Intentá describir el hecho en una sola frase… "
        "utilizando palabras simples y precisas. "
        "Sin insultarte. "
        "Sin exagerar. "
        "Sin convertir una acción en una definición sobre quién sos.",
        12.0,
    ),
    (
        "Podrías decir: "
        "Fallé esa ejecución. "
        "Tomé una decisión equivocada. "
        "No vi esa opción. "
        "No hice lo que había planificado.",
        8.0,
    ),
    (
        "Eso es lo que ocurrió. "
        "Una acción concreta… "
        "en un momento concreto.",
        8.0,
    ),
    ("Ahora observá qué agregó tu mente después del error.", 5.0),
    (
        "Quizá apareció algún pensamiento como: "
        "Otra vez lo mismo. "
        "No puedo equivocarme así. "
        "Arruiné todo. "
        "Ahora van a desconfiar de mí. "
        "Esto demuestra que no estoy preparado.",
        10.0,
    ),
    (
        "No intentes discutir con esos pensamientos. "
        "Tampoco necesitás creerles. "
        "Solamente reconocé: "
        "Esto es lo que mi mente está diciendo después del error.",
        9.0,
    ),
    (
        "El hecho es una cosa. "
        "La interpretación automática sobre el hecho… "
        "es otra.",
        9.0,
    ),
    ("Llevá ahora la atención al cuerpo.", 5.0),
    ("¿Dónde sentís actualmente el impacto del error?", 7.0),
    (
        "Tal vez aparezca presión en el pecho… "
        "un nudo en el abdomen… "
        "tensión en la mandíbula… "
        "calor en la cara… "
        "rigidez en los hombros… "
        "o inquietud en las manos y en las piernas.",
        10.0,
    ),
    (
        "Quizá no aparezca una sensación clara. "
        "También está bien. "
        "No necesitás fabricar ninguna experiencia.",
        7.0,
    ),
    (
        "Si encontrás una zona más activada… "
        "llevá la atención hacia ahí.",
        5.0,
    ),
    (
        "Observá la sensación como una experiencia corporal. "
        "¿Tiene presión? "
        "¿Temperatura? "
        "¿Movimiento? "
        "¿Pulsación? "
        "¿Límites reconocibles?",
        12.0,
    ),
    (
        "No hace falta que desaparezca. "
        "No hace falta resolverla ahora. "
        "Permití que esté presente… "
        "sin agregar una nueva lucha contra ella.",
        10.0,
    ),
    (
        "Sentí nuevamente una inhalación… "
        "y una exhalación.",
        8.0,
    ),
    (
        "La respiración no borra el error. "
        "Pero puede ofrecerte un punto estable… "
        "desde donde recuperar la atención.",
        10.0,
    ),
    (
        "El cuerpo puede seguir activado. "
        "Puede haber bronca… "
        "vergüenza… "
        "decepción… "
        "miedo… "
        "o urgencia por compensar rápidamente lo ocurrido.",
        10.0,
    ),
    (
        "No necesitás eliminar esas respuestas para volver a competir. "
        "Podés reconocerlas… "
        "y, aun así, orientar tu conducta.",
        10.0,
    ),
    (
        "Aceptar el error no significa aprobarlo. "
        "Tampoco significa resignarte. "
        "Aceptar significa dejar de discutir con el hecho de que ya ocurrió… "
        "para utilizar tus recursos en lo que todavía puede modificarse.",
        12.0,
    ),
    (
        "El error pertenece a la acción anterior. "
        "Tu atención puede volver a la acción presente.",
        10.0,
    ),
    (
        "Preguntate ahora: "
        "¿Cuál era la próxima acción relevante después de ese error?",
        10.0,
    ),
    (
        "No busques solucionar toda la competencia. "
        "No intentes recuperar todo de una vez. "
        "Elegí una acción pequeña… "
        "observable… "
        "y posible.",
        8.0,
    ),
    (
        "Tal vez recuperar tu posición… "
        "mirar nuevamente el entorno… "
        "comunicarte con un compañero… "
        "ajustar el ritmo… "
        "volver a ofrecerte… "
        "retomar tu rutina… "
        "o ejecutar de manera simple la acción siguiente.",
        12.0,
    ),
    (
        "Visualizate realizando esa acción. "
        "No necesitás imaginarla perfecta. "
        "Solamente clara.",
        10.0,
    ),
    (
        "Observá la posición de tu cuerpo… "
        "la dirección de tu mirada… "
        "y el primer movimiento que necesitás realizar.",
        10.0,
    ),
    (
        "Ahora elegí una palabra breve que pueda ayudarte a regresar. "
        "Puede ser: "
        "Acá. "
        "Siguiente. "
        "Simple. "
        "Firme.",
        8.0,
    ),
    (
        "Elegí la que mejor oriente tu conducta. "
        "No es una palabra para tapar el error. "
        "Es una señal para recordarle a tu atención… "
        "dónde necesita estar.",
        12.0,
    ),
    ("Repetila una vez, internamente.", 8.0),
    ("Y vinculala con la próxima acción relevante.", 10.0),
    ("Ahora vamos a ensayar la secuencia completa.", 5.0),
    ("El error ocurre.", 4.0),
    ("Aparece la reacción automática.", 5.0),
    (
        "Sentís un punto de contacto del cuerpo… "
        "los pies… "
        "las manos… "
        "o la respiración.",
        6.0,
    ),
    ("Reconocés: Esto ya ocurrió.", 5.0),
    ("Decís tu palabra de retorno.", 5.0),
    (
        "Orientás la mirada… "
        "acomodás el cuerpo… "
        "y realizás la próxima acción relevante.",
        12.0,
    ),
    ("Una vez más.", 4.0),
    ("Error.", 4.0),
    ("Contacto con el cuerpo.", 4.0),
    ("Palabra de retorno.", 4.0),
    ("Información relevante.", 4.0),
    ("Próxima acción.", 12.0),
    (
        "No siempre vas a poder hacerlo inmediatamente. "
        "A veces, el error volverá a tu mente. "
        "A veces, la emoción seguirá presente durante varias acciones.",
        9.0,
    ),
    (
        "Cuando lo notes… "
        "no significa que la práctica haya fallado. "
        "Ese momento en el que reconocés que tu atención quedó atrapada… "
        "es precisamente el momento en que podés volver a orientarla.",
        12.0,
    ),
    (
        "Volver no es regresar a un estado perfecto. "
        "Es recuperar suficiente claridad… "
        "para responder a lo que está ocurriendo ahora.",
        12.0,
    ),
    ("Sentí nuevamente el cuerpo completo.", 7.0),
    (
        "La postura… "
        "los puntos de apoyo… "
        "la respiración… "
        "y el espacio que te rodea.",
        10.0,
    ),
    (
        "Empezá a mover suavemente los dedos de las manos… "
        "y los dedos de los pies.",
        6.0,
    ),
    (
        "Si tenés los ojos cerrados… "
        "podés abrirlos lentamente.",
        6.0,
    ),
    (
        "Antes de terminar, recordá: "
        "El error ya forma parte de lo que ocurrió. "
        "Tu respuesta todavía se está construyendo.",
        8.0,
    ),
    (
        "No necesitás borrar el error. "
        "Necesitás evitar que decida también la acción siguiente.",
        8.0,
    ),
    (
        "Contacto. "
        "Palabra de retorno. "
        "Información relevante. "
        "Próxima acción.",
        10.0,
    ),
    ("La práctica terminó.", 3.0),
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
    output_dir = Path("output_despues_error_v2")
    output_dir.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="despues-error-v2-") as temp_dir:
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

        mp3_path = output_dir / "Despues_del_error_volver_a_la_accion_relevante_v2.mp3"
        wav_path = output_dir / "Despues_del_error_v2_voz_limpia.wav"

        track.export(
            mp3_path,
            format="mp3",
            bitrate="192k",
            tags={
                "title": "Después del error — Volver a la acción relevante",
                "artist": "SAMUKA",
                "album": "Mindfulness",
                "comment": f"Preset SAMUKA; voz {VOICE}; velocidad {RATE}; sin música",
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
