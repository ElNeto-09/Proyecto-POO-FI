"""Simulación de hora pico con 4 torniquetes y reservas simultáneas."""

import random
import time
from datetime import datetime, timedelta
from threading import Thread

from centro_deportivo.concurrencia.runnable import Runnable
from centro_deportivo.excepciones import AccesoDenegadoError, ReservaError
from centro_deportivo.servicios.gestor_centro import GestorCentro


class Torniquete(Runnable):
    """Simula uno de los cuatro torniquetes registrando entradas y salidas."""

    def __init__(self, numero, gestor, personas, operaciones, ahora):
        self.numero = numero
        self.gestor = gestor
        self.personas = personas
        self.operaciones = operaciones
        self.ahora = ahora
        self.entradas = 0
        self.salidas = 0
        self.rechazos = 0

    def run(self):
        rng = random.Random(self.numero * 50)
        for _ in range(self.operaciones):
            persona = rng.choice(self.personas)
            if rng.random() < 0.7:
                try:
                    self.gestor.registrar_entrada(
                        persona, "gimnasio", self.ahora, es_visitante=True
                    )
                    self.entradas += 1
                except AccesoDenegadoError:
                    self.rechazos += 1
            else:
                if self.gestor.registrar_salida(persona, self.ahora):
                    self.salidas += 1
            time.sleep(0.001)


class SocioReserva(Runnable):
    """Simula a un socio intentando ganar uno de los últimos lugares de una clase."""

    def __init__(self, gestor, id_socio, id_clase, ahora):
        self.gestor = gestor
        self.id_socio = id_socio
        self.id_clase = id_clase
        self.ahora = ahora
        self.logro_lugar = False

    def run(self):
        time.sleep(random.uniform(0.001, 0.005))
        try:
            self.gestor.reservar_clase(self.id_socio, self.id_clase, self.ahora)
            self.logro_lugar = True
        except ReservaError:
            self.logro_lugar = False


class SimuladorHoraPico:
    """Lanza 4 torniquetes y varios socios reservando al mismo tiempo."""

    @staticmethod
    def ejecutar(fecha_base=None):
        """Corre la simulación y comprueba que nunca se pase el aforo ni el cupo."""
        ahora = fecha_base or datetime(2026, 11, 16, 10, 0)
        gestor = GestorCentro()

        # Preparamos una clase con solo 5 lugares y 15 socios compitiendo por ellos
        id_clase = "YOGA-PICO"
        gestor.programar_clase(
            id_clase, "Yoga Vespertino", "Prof. Laura", ahora + timedelta(hours=8), 5
        )
        socios = []
        for i in range(1, 16):
            sid = f"S-{i:02d}"
            gestor.registrar_socio(sid, f"Socio {i}", "premium", ahora)
            socios.append(sid)

        # 100 visitantes intentando entrar por 4 torniquetes (el aforo es de 60)
        visitantes = [f"VIS-{i:03d}" for i in range(1, 101)]
        torniquetes = [Torniquete(i, gestor, visitantes, 40, ahora) for i in range(1, 5)]
        tareas_reserva = [SocioReserva(gestor, sid, id_clase, ahora) for sid in socios]

        hilos = [Thread(target=t.run, name=f"Torniquete-{t.numero}") for t in torniquetes]
        hilos += [Thread(target=r.run, name=f"Reserva-{r.id_socio}") for r in tareas_reserva]

        for h in hilos:
            h.start()
        for h in hilos:
            h.join()

        clase = gestor.clases[id_clase]
        inscritos = len(clase.reservas_activas())
        return {
            "Entradas exitosas": sum(t.entradas for t in torniquetes),
            "Salidas exitosas": sum(t.salidas for t in torniquetes),
            "Accesos rechazados": sum(t.rechazos for t in torniquetes),
            "Aforo máximo alcanzado": f"{gestor.pico_aforo}/{gestor.AFORO_MAXIMO}",
            "¿Aforo respetado?": "Sí" if gestor.pico_aforo <= gestor.AFORO_MAXIMO else "No",
            "Lugares reservados en clase": f"{inscritos}/{clase.cupo_maximo}",
            "¿Cupo respetado?": "Sí" if inscritos <= clase.cupo_maximo else "No",
        }