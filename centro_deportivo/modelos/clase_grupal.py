"""Modelo de clase grupal con manejo de cupo, reservas y pase de lista."""

from datetime import datetime, timedelta
from threading import Lock

from centro_deportivo.excepciones import ReservaError
from centro_deportivo.modelos.socio import Reserva


class ClaseGrupal:
    """Representa una clase grupal (yoga, spinning, natación, etc.)."""

    HORAS_MAX_RESERVA = 48
    HORAS_MIN_CANCELACION = 2

    def __init__(self, id_clase, nombre, instructor, fecha_hora, cupo_maximo, reservas=None):
        if cupo_maximo <= 0:
            raise ValueError("El cupo máximo debe ser un número positivo.")
        self._id_clase = id_clase
        self.nombre = nombre
        self.instructor = instructor
        self.fecha_hora = fecha_hora
        self.cupo_maximo = cupo_maximo
        self._reservas = reservas if reservas is not None else []
        self._candado = Lock()

    @property
    def id_clase(self):
        """Identificador único de la clase."""
        return self._id_clase

    @property
    def reservas(self):
        """Lista completa de reservas de la clase."""
        return self._reservas

    def reservas_activas(self):
        """Devuelve solo las reservas que siguen activas."""
        return [r for r in self._reservas if r.estado == "activa"]

    def lugares_disponibles(self):
        """Calcula cuántos lugares quedan libres."""
        return self.cupo_maximo - len(self.reservas_activas())

    def reservar(self, socio, ahora):
        """Reserva un lugar validando membresía, bloqueo, ventana de 48h y cupo."""
        if not socio.membresia.esta_vigente(ahora):
            raise ReservaError("Tu membresía está vencida.")
        if not socio.membresia.incluye_area("clases_grupales"):
            raise ReservaError("Tu membresía no incluye clases grupales.")
        if socio.esta_bloqueado(ahora):
            hasta = socio.bloqueado_hasta.strftime("%Y-%m-%d %H:%M")
            raise ReservaError(f"Estás bloqueado por faltas hasta el {hasta}.")
        if ahora >= self.fecha_hora:
            raise ReservaError("No puedes reservar una clase que ya empezó.")
        if self.fecha_hora - ahora > timedelta(hours=self.HORAS_MAX_RESERVA):
            raise ReservaError("Solo puedes reservar con hasta 48 horas de anticipación.")

        # Sección crítica protegida para evitar sobreventa con hilos
        with self._candado:
            for r in self._reservas:
                if r.id_socio == socio.id_socio and r.estado == "activa":
                    raise ReservaError("Ya tienes un lugar reservado en esta clase.")
            if self.lugares_disponibles() <= 0:
                raise ReservaError(f"Ya no hay cupo en la clase '{self.nombre}'.")
            nueva = Reserva(socio.id_socio, self._id_clase, ahora, estado="activa")
            self._reservas.append(nueva)
            return nueva

    def cancelar(self, id_socio, ahora):
        """Cancela una reserva activa si faltan al menos 2 horas para la clase."""
        if self.fecha_hora - ahora < timedelta(hours=self.HORAS_MIN_CANCELACION):
            raise ReservaError("Solo se puede cancelar hasta 2 horas antes de la clase.")

        with self._candado:
            for r in self._reservas:
                if r.id_socio == id_socio and r.estado == "activa":
                    r.estado = "cancelada"
                    return
            raise ReservaError("No tienes una reserva activa en esta clase.")

    def pasar_lista(self, ids_asistentes, socios_por_id):
        """Marca asistencias y faltas; devuelve un resumen con los resultados."""
        asistieron = []
        faltaron = []
        bloqueados = []

        with self._candado:
            for r in self._reservas:
                if r.estado != "activa":
                    continue
                if r.id_socio in ids_asistentes:
                    r.estado = "asistio"
                    asistieron.append(r.id_socio)
                else:
                    r.estado = "falta"
                    faltaron.append(r.id_socio)
                    socio = socios_por_id.get(r.id_socio)
                    if socio and socio.registrar_falta(self.fecha_hora):
                        bloqueados.append(r.id_socio)

        return {
            "asistieron": asistieron,
            "faltaron": faltaron,
            "bloqueados": bloqueados,
        }

    def a_dict(self):
        """Serializa la clase y sus reservas para JSON."""
        return {
            "id_clase": self._id_clase,
            "nombre": self.nombre,
            "instructor": self.instructor,
            "fecha_hora": self.fecha_hora.isoformat(),
            "cupo_maximo": self.cupo_maximo,
            "reservas": [r.a_dict() for r in self._reservas],
        }

    @classmethod
    def desde_dict(cls, datos):
        """Reconstruye una clase grupal desde JSON."""
        reservas = [Reserva.desde_dict(r) for r in datos.get("reservas", [])]
        return cls(
            datos["id_clase"],
            datos["nombre"],
            datos["instructor"],
            datetime.fromisoformat(datos["fecha_hora"]),
            int(datos["cupo_maximo"]),
            reservas,
        )