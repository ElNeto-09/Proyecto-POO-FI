"""Interfaz de terminal amigable para el Centro Deportivo Universitario."""

import argparse
import sys
from datetime import datetime

from centro_deportivo.concurrencia.simulacion import SimuladorHoraPico
from centro_deportivo.excepciones import CentroDeportivoError, PersistenciaError
from centro_deportivo.servicios.persistencia import Persistencia
from centro_deportivo.servicios.reportes import GeneradorReportes


def leer_fecha(texto, por_defecto):
    """Convierte 'YYYY-MM-DD HH:MM' a datetime; si está vacío usa por_defecto."""
    texto = texto.strip()
    if not texto:
        return por_defecto
    try:
        return datetime.strptime(texto, "%Y-%m-%d %H:%M")
    except ValueError as e:
        raise ValueError("Formato incorrecto. Ejemplo válido: 2026-11-16 10:00") from e


def elegir_plan():
    """Permite elegir un tipo de membresía con un número."""
    print("  1. Estudiante ($300/mes - Gimnasio, lun-vie 7:00 a 15:00)")
    print("  2. General    ($700/mes - Gimnasio, todo el horario)")
    print("  3. Premium    ($1,100/mes - Gimnasio, alberca y clases)")
    planes = {"1": "estudiante", "2": "general", "3": "premium"}
    opcion = input("Elige el plan (1-3): ").strip()
    if opcion not in planes:
        raise ValueError("Debes elegir 1, 2 o 3.")
    return planes[opcion]


def elegir_area():
    """Permite elegir el área de acceso con un número."""
    print("  1. Gimnasio")
    print("  2. Alberca")
    areas = {"1": "gimnasio", "2": "alberca"}
    opcion = input("Elige el área (1-2): ").strip()
    if opcion not in areas:
        raise ValueError("Debes elegir 1 o 2.")
    return areas[opcion]


def mostrar_socios(gestor):
    """Muestra una lista rápida de socios registrados para evitar memorizar IDs."""
    if not gestor.socios:
        print("  (Todavía no hay socios registrados)")
        return False
    print("\nSocios registrados:")
    for socio in gestor.socios.values():
        print(f"  [{socio.id_socio}] {socio.nombre} — Plan {socio.membresia.tipo.capitalize()}")
    return True


def mostrar_clases(gestor):
    """Muestra una lista rápida de clases programadas y sus lugares libres."""
    if not gestor.clases:
        print("  (Todavía no hay clases programadas)")
        return False
    print("\nClases programadas:")
    for clase in gestor.clases.values():
        libres = clase.lugares_disponibles()
        print(
            f"  [{clase.id_clase}] {clase.nombre} ({clase.fecha_hora:%Y-%m-%d %H:%M}) "
            f"- Instructor: {clase.instructor} | Libres: {libres}/{clase.cupo_maximo}"
        )
    return True


def main():
    """Inicia el menú del sistema y garantiza el guardado de datos al salir."""
    parser = argparse.ArgumentParser(description="Centro Deportivo Universitario")
    parser.add_argument("--estado", default="estado_actual.json", help="Archivo JSON de estado.")
    parser.add_argument("--fecha", default=None, help="Fecha inicial (YYYY-MM-DD HH:MM).")
    args = parser.parse_args()

    try:
        ahora = leer_fecha(args.fecha, datetime.now()) if args.fecha else datetime.now()
        gestor = Persistencia.cargar_estado(args.estado)
    except (ValueError, PersistenciaError) as e:
        print(f"Error al iniciar el programa: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        while True:
            print(f"\n====================================================")
            print(f"  CENTRO DEPORTIVO | Reloj: {ahora:%Y-%m-%d %H:%M}")
            print(f"  Aforo gimnasio: {len(gestor.dentro_gimnasio)}/{gestor.AFORO_MAXIMO} | Socios: {len(gestor.socios)}")
            print(f"====================================================")
            print("1. Cargar lista de alumnos inscritos (CSV)")
            print("2. Registrar un nuevo socio")
            print("3. Renovar o cambiar membresía")
            print("4. Registrar entrada o salida")
            print("5. Clases grupales (crear, reservar, cancelar, lista)")
            print("6. Ver estado de un socio")
            print("7. Generar reporte mensual")
            print("8. Simular hora pico (4 torniquetes + reservas)")
            print("9. Cambiar fecha/hora de prueba")
            print("0. Guardar y salir")

            opcion = input("\nElige una opción: ").strip()
            try:
                if opcion == "1":
                    ruta = input("Ruta del CSV [Enter = datos/alumnos_inscritos.csv]: ").strip()
                    ruta = ruta or "datos/alumnos_inscritos.csv"
                    ok, mal = Persistencia.cargar_alumnos_csv(gestor, ruta)
                    print(f"Carga terminada -> Alumnos válidos: {ok} | Rechazados: {mal}")

                elif opcion == "2":
                    nombre = input("Nombre completo del socio: ").strip()
                    if not nombre:
                        raise ValueError("El nombre no puede quedar vacío.")
                    tipo = elegir_plan()
                    mat = None
                    if tipo == "estudiante":
                        mat = input("Matrícula universitaria: ").strip()
                    sid = gestor.generar_id_socio()
                    socio = gestor.registrar_socio(sid, nombre, tipo, ahora, matricula=mat)
                    print(f"\n¡Listo! Socio registrado con ID [{socio.id_socio}]:")
                    print(f"  {socio.nombre} | {socio.membresia}")

                elif opcion == "3":
                    if not mostrar_socios(gestor):
                        continue
                    sid = input("Escribe el ID del socio (ej. S1): ").strip().upper()
                    print("  1. Renovar membresía actual")
                    print("  2. Cambiar a otro plan")
                    accion = input("Elige (1-2): ").strip()
                    if accion == "1":
                        socio = gestor.renovar_membresia(sid, ahora)
                    elif accion == "2":
                        nuevo = elegir_plan()
                        mat = input("Matrícula (solo si pasa a estudiante): ").strip() if nuevo == "estudiante" else None
                        socio = gestor.cambiar_membresia(sid, nuevo, ahora, matricula=mat)
                    else:
                        print("Opción no válida.")
                        continue
                    print(f"Membresía actualizada: {socio.membresia}")

                elif opcion == "4":
                    print("  1. Registrar ENTRADA")
                    print("  2. Registrar SALIDA")
                    mov = input("Elige (1-2): ").strip()

                    if mov == "1":
                        es_vis = input("¿Es visitante con pase diario ($120)? (s/n): ").strip().lower() == "s"
                        if es_vis:
                            pid = gestor.generar_id_visitante()
                            print(f"  Se asignó el folio de visitante: [{pid}]")
                        else:
                            if not mostrar_socios(gestor):
                                continue
                            pid = input("Escribe el ID del socio (ej. S1): ").strip().upper()
                        area = elegir_area()
                        gestor.registrar_entrada(pid, area, ahora, es_visitante=es_vis)
                        print(f"Entrada permitida para [{pid}]. Aforo gimnasio: {len(gestor.dentro_gimnasio)}/{gestor.AFORO_MAXIMO}")

                    elif mov == "2":
                        if not gestor.dentro_gimnasio:
                            print("No hay nadie registrado dentro del gimnasio en este momento.")
                            continue
                        print(f"Personas dentro ahora: {', '.join(sorted(gestor.dentro_gimnasio))}")
                        pid = input("Escribe el ID de quien sale: ").strip().upper()
                        if gestor.registrar_salida(pid, ahora):
                            print(f"Salida registrada. Aforo gimnasio: {len(gestor.dentro_gimnasio)}/{gestor.AFORO_MAXIMO}")
                        else:
                            print("Ese ID no estaba registrado dentro del gimnasio.")
                    else:
                        print("Opción no válida.")

                elif opcion == "5":
                    print("  1. Programar nueva clase")
                    print("  2. Reservar lugar en una clase")
                    print("  3. Cancelar reserva")
                    print("  4. Pasar lista")
                    sub = input("Elige (1-4): ").strip()

                    if sub == "1":
                        cid = gestor.generar_id_clase()
                        nom = input("Nombre de la clase (ej. Yoga, Spinning): ").strip()
                        inst = input("Nombre del instructor: ").strip()
                        fh = leer_fecha(input("Fecha y hora (YYYY-MM-DD HH:MM): "), ahora)
                        cupo = int(input("Cupo máximo de personas: ").strip())
                        gestor.programar_clase(cid, nom, inst, fh, cupo)
                        print(f"Clase '{nom}' programada con ID [{cid}].")

                    elif sub == "2":
                        if not mostrar_socios(gestor) or not mostrar_clases(gestor):
                            continue
                        sid = input("ID del socio (ej. S1): ").strip().upper()
                        cid = input("ID de la clase (ej. C1): ").strip().upper()
                        gestor.reservar_clase(sid, cid, ahora)
                        print("¡Lugar reservado correctamente!")

                    elif sub == "3":
                        if not mostrar_clases(gestor):
                            continue
                        sid = input("ID del socio (ej. S1): ").strip().upper()
                        cid = input("ID de la clase (ej. C1): ").strip().upper()
                        gestor.cancelar_reserva(sid, cid, ahora)
                        print("Reserva cancelada.")

                    elif sub == "4":
                        if not mostrar_clases(gestor):
                            continue
                        cid = input("ID de la clase (ej. C1): ").strip().upper()
                        raw = input("IDs de quienes SÍ asistieron (separados por coma, ej. S1, S2): ").strip()
                        asistentes = {x.strip().upper() for x in raw.split(",") if x.strip()}
                        res = gestor.pasar_lista(cid, asistentes)
                        print(f"  Asistieron: {res['asistieron'] or 'Ninguno'}")
                        print(f"  Faltaron:   {res['faltaron'] or 'Ninguno'}")
                        if res["bloqueados"]:
                            print(f"  ¡Bloqueados 7 días por 3 faltas!: {res['bloqueados']}")
                    else:
                        print("Opción no válida.")

                elif opcion == "6":
                    if not mostrar_socios(gestor):
                        continue
                    sid = input("ID del socio (ej. S1): ").strip().upper()
                    estado = gestor.consultar_estado_socio(sid, ahora)
                    print("\n--- Estado del socio ---")
                    for clave, valor in estado.items():
                        print(f"  {clave}: {valor}")

                elif opcion == "7":
                    anio_str = input(f"Año [Enter = {ahora.year}]: ").strip()
                    mes_str = input(f"Mes 1-12 [Enter = {ahora.month}]: ").strip()
                    anio = int(anio_str) if anio_str else ahora.year
                    mes = int(mes_str) if mes_str else ahora.month
                    ruta = f"reporte_{anio}_{mes:02d}.txt"
                    GeneradorReportes.generar_reporte_mensual(gestor, anio, mes, ruta)
                    print(f"Reporte mensual guardado en: '{ruta}'")

                elif opcion == "8":
                    print("\nEjecutando simulación de hora pico con 4 torniquetes...")
                    res = SimuladorHoraPico.ejecutar(ahora)
                    for clave, valor in res.items():
                        print(f"  {clave}: {valor}")

                elif opcion == "9":
                    ahora = leer_fecha(input("Nueva fecha/hora (YYYY-MM-DD HH:MM): "), ahora)
                    print(f"Reloj actualizado a: {ahora:%Y-%m-%d %H:%M}")

                elif opcion == "0":
                    break
                else:
                    print("Opción no válida, elige un número del 0 al 9.")

            except (CentroDeportivoError, ValueError) as e:
                print(f"\n[Aviso] {e}")

    except (KeyboardInterrupt, EOFError):
        print("\nCerrando el sistema de forma ordenada...")
    finally:
        try:
            Persistencia.guardar_estado(gestor, args.estado)
            print(f"Datos guardados en '{args.estado}'.")
        except PersistenciaError as e:
            print(f"No se pudo guardar el estado: {e}", file=sys.stderr)


if __name__ == "__main__":
    main()