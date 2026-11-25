"""Clases de datos para socios, reservas y registros de acceso."""

from datetime import datetime, timedelta

from centro_deportivo.modelos.membresia import Membresia


class Reserva:
    """Guarda los datos de una reserva hecha por un socio en una clase."""

    def __init__(self, id_socio, id_clase, fecha_reserva, estado="activa"):
        self.id_socio = id_socio
        self.id_clase = id_clase
        self.fecha_reserva = fecha_reserva
        self.estado = estado  # activa, cancelada, asistio, falta

    def a_dict(self):
        """Serializa la reserva para guardarla en JSON."""
        return {
            "id_socio": self.id_socio,
            "id_clase": self.id_clase,
            "fecha_reserva": self.fecha_reserva.isoformat(),
            "estado": self.estado,
        }

    @classmethod
    def desde_dict(cls, datos):
        """Reconstruye una reserva desde un diccionario JSON."""
        return cls(
            datos["id_socio"],
            datos["id_clase"],
            datetime.fromisoformat(datos["fecha_reserva"]),
            datos["estado"],
        )


class RegistroAcceso:
    """Guarda la entrada y salida de un socio o visitante."""

    def __init__(self, id_persona, es_visitante, area, entrada, salida=None):
        self.id_persona = id_persona
        self.es_visitante = es_visitante
        self.area = area.lower()
        self.entrada = entrada
        self.salida = salida

    def a_dict(self):
        """Serializa el registro de acceso para JSON."""
        return {
            "id_persona": self.id_persona,
            "es_visitante": self.es_visitante,
            "area": self.area,
            "entrada": self.entrada.isoformat(),
            "salida": self.salida.isoformat() if self.salida else None,
        }

    @classmethod
    def desde_dict(cls, datos):
        """Reconstruye un registro de acceso desde JSON."""
        salida = datetime.fromisoformat(datos["salida"]) if datos.get("salida") else None
        return cls(
            datos["id_persona"],
            datos["es_visitante"],
            datos["area"],
            datetime.fromisoformat(datos["entrada"]),
            salida,
        )


class Socio:
    """Representa a un socio inscrito en el centro deportivo."""

    MAX_FALTAS_MES = 3
    DIAS_BLOQUEO = 7

    def __init__(
        self,
        id_socio,
        nombre,
        membresia,
        matricula=None,
        faltas=None,
        bloqueado_hasta=None,
    ):
        self._id_socio = id_socio
        self.nombre = nombre
        self.membresia = membresia
        self.matricula = matricula
        self.faltas = faltas if faltas is not None else []
        self.bloqueado_hasta = bloqueado_hasta

    @property
    def id_socio(self):
        """Identificador único del socio."""
        return self._id_socio

    def esta_bloqueado(self, ahora):
        """Devuelve True si el socio sigue sancionado sin poder reservar."""
        return self.bloqueado_hasta is not None and ahora < self.bloqueado_hasta

    def faltas_en_mes(self, anio, mes):
        """Cuenta cuántas faltas acumuló el socio en un mes y año dados."""
        return sum(1 for f in self.faltas if f.year == anio and f.month == mes)

    def registrar_falta(self, fecha_clase):
        """Agrega una falta y bloquea 7 días si junta 3 faltas en el mismo mes."""
        self.faltas.append(fecha_clase)
        if self.faltas_en_mes(fecha_clase.year, fecha_clase.month) >= self.MAX_FALTAS_MES:
            self.bloqueado_hasta = fecha_clase + timedelta(days=self.DIAS_BLOQUEO)
            return True
        return False

    def renovar_membresia(self, fecha_operacion):
        """Extiende la vigencia de la membresía actual."""
        self.membresia.extender_vigencia(fecha_operacion)

    def cambiar_membresia(self, nueva_membresia):
        """Asigna un nuevo plan de membresía al socio."""
        self.membresia = nueva_membresia

    def a_dict(self):
        """Serializa los datos del socio a diccionario."""
        bloqueo = self.bloqueado_hasta.isoformat() if self.bloqueado_hasta else None
        return {
            "id_socio": self._id_socio,
            "nombre": self.nombre,
            "matricula": self.matricula,
            "membresia": self.membresia.a_dict(),
            "faltas": [f.isoformat() for f in self.faltas],
            "bloqueado_hasta": bloqueo,
        }

    @classmethod
    def desde_dict(cls, datos):
        """Reconstruye un socio desde un diccionario JSON."""
        bloqueo = (
            datetime.fromisoformat(datos["bloqueado_hasta"])
            if datos.get("bloqueado_hasta")
            else None
        )
        return cls(
            datos["id_socio"],
            datos["nombre"],
            Membresia.desde_dict(datos["membresia"]),
            datos.get("matricula"),
            [datetime.fromisoformat(f) for f in datos.get("faltas", [])],
            bloqueo,
        )