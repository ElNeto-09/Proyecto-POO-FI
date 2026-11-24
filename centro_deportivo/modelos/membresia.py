"""Jerarquía de membresías y pases del centro deportivo."""

from abc import ABC, abstractmethod
from datetime import datetime, time, timedelta


class Membresia(ABC):
    """Clase base abstracta para todos los tipos de membresía y pase."""

    HORA_APERTURA = time(6, 0)
    HORA_CIERRE = time(22, 0)

    def __init__(self, tipo, costo, areas, fecha_inicio, fecha_fin=None):
        """Inicializa la membresía y calcula su vigencia si no se proporciona."""
        self._tipo = tipo
        self._costo = float(costo)
        self._areas = frozenset(a.lower() for a in areas)
        self._fecha_inicio = fecha_inicio
        if fecha_fin is None:
            self._fecha_fin = fecha_inicio + timedelta(days=self.duracion_dias())
        else:
            self._fecha_fin = fecha_fin

    @property
    def tipo(self):
        """Tipo de membresía."""
        return self._tipo

    @property
    def costo(self):
        """Costo de la membresía."""
        return self._costo

    @property
    def areas(self):
        """Áreas a las que da acceso esta membresía."""
        return self._areas

    @property
    def fecha_inicio(self):
        """Fecha de inicio de vigencia."""
        return self._fecha_inicio

    @property
    def fecha_fin(self):
        """Fecha de vencimiento."""
        return self._fecha_fin

    @staticmethod
    def en_horario_general(fecha_hora):
        """Revisa si la fecha y hora caen de lunes a sábado entre 6:00 y 22:00."""
        if fecha_hora.weekday() == 6:  # Domingo está cerrado
            return False
        hora = fecha_hora.time()
        return Membresia.HORA_APERTURA <= hora < Membresia.HORA_CIERRE

    def esta_vigente(self, fecha_hora):
        """Indica si la membresía está activa en la fecha y hora dadas."""
        return self._fecha_inicio <= fecha_hora <= self._fecha_fin

    def incluye_area(self, area):
        """Indica si el área solicitada está incluida en este plan."""
        return area.strip().lower() in self._areas

    def extender_vigencia(self, fecha_operacion):
        """Renueva la membresía sumando los días de su plan."""
        # Si todavía no vence, sumamos desde la fecha de vencimiento actual
        base = max(self._fecha_fin, fecha_operacion)
        self._fecha_fin = base + timedelta(days=self.duracion_dias())

    @abstractmethod
    def duracion_dias(self):
        """Devuelve cuántos días dura la membresía."""

    @abstractmethod
    def puede_acceder_horario(self, fecha_hora):
        """Indica si este plan permite entrar en el día y hora indicados."""

    def a_dict(self):
        """Convierte la membresía a diccionario para guardarla en JSON."""
        return {
            "tipo": self._tipo,
            "fecha_inicio": self._fecha_inicio.isoformat(),
            "fecha_fin": self._fecha_fin.isoformat(),
        }

    @classmethod
    def crear(cls, tipo, fecha_inicio, fecha_fin=None):
        """Crea la subclase de membresía correspondiente según el nombre."""
        tipos = {
            "estudiante": MembresiaEstudiante,
            "general": MembresiaGeneral,
            "premium": MembresiaPremium,
            "visitante": PaseVisitante,
        }
        clave = tipo.strip().lower()
        if clave not in tipos:
            raise ValueError(f"Tipo de membresía no válido: '{tipo}'")
        return tipos[clave](fecha_inicio, fecha_fin)

    @classmethod
    def desde_dict(cls, datos):
        """Reconstruye una membresía a partir de un diccionario guardado en JSON."""
        return cls.crear(
            datos["tipo"],
            datetime.fromisoformat(datos["fecha_inicio"]),
            datetime.fromisoformat(datos["fecha_fin"]),
        )

    def __str__(self):
        vence = self._fecha_fin.strftime("%Y-%m-%d %H:%M")
        return f"{self._tipo.capitalize()} (${self._costo:,.2f}) - Vigente hasta: {vence}"


class MembresiaEstudiante(Membresia):
    """Plan estudiante: $300/mes, solo gimnasio, lunes a viernes de 7:00 a 15:00."""

    HORA_INICIO = time(7, 0)
    HORA_FIN = time(15, 0)

    def __init__(self, fecha_inicio, fecha_fin=None):
        super().__init__("estudiante", 300.0, {"gimnasio"}, fecha_inicio, fecha_fin)

    def duracion_dias(self):
        return 30

    def puede_acceder_horario(self, fecha_hora):
        if fecha_hora.weekday() > 4:  # Sábado o domingo no entra
            return False
        hora = fecha_hora.time()
        return self.HORA_INICIO <= hora < self.HORA_FIN


class MembresiaGeneral(Membresia):
    """Plan general: $700/mes, gimnasio en todo el horario del centro."""

    def __init__(self, fecha_inicio, fecha_fin=None):
        super().__init__("general", 700.0, {"gimnasio"}, fecha_inicio, fecha_fin)

    def duracion_dias(self):
        return 30

    def puede_acceder_horario(self, fecha_hora):
        return self.en_horario_general(fecha_hora)


class MembresiaPremium(Membresia):
    """Plan premium: $1,100/mes, gimnasio, alberca y clases grupales."""

    def __init__(self, fecha_inicio, fecha_fin=None):
        areas = {"gimnasio", "alberca", "clases_grupales"}
        super().__init__("premium", 1100.0, areas, fecha_inicio, fecha_fin)

    def duracion_dias(self):
        return 30

    def puede_acceder_horario(self, fecha_hora):
        return self.en_horario_general(fecha_hora)


class PaseVisitante(Membresia):
    """Pase por día: $120/día, solo gimnasio en el horario del centro."""

    def __init__(self, fecha_inicio, fecha_fin=None):
        if fecha_fin is None:
            fecha_fin = fecha_inicio.replace(hour=23, minute=59, second=59)
        super().__init__("visitante", 120.0, {"gimnasio"}, fecha_inicio, fecha_fin)

    def duracion_dias(self):
        return 1

    def puede_acceder_horario(self, fecha_hora):
        return self.en_horario_general(fecha_hora)