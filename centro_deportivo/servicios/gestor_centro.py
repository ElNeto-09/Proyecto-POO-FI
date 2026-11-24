"""Lógica principal del centro deportivo: socios, accesos, clases y aforo."""

from threading import Lock

from centro_deportivo.excepciones import (
    AccesoDenegadoError,
    MembresiaError,
    ReservaError,
)
from centro_deportivo.modelos.clase_grupal import ClaseGrupal
from centro_deportivo.modelos.membresia import Membresia, PaseVisitante
from centro_deportivo.modelos.socio import RegistroAcceso, Socio


class GestorCentro:
    """Coordina todas las operaciones del centro deportivo universitario."""

    AFORO_MAXIMO = 60

    def __init__(self):
        self.socios = {}
        self.clases = {}
        self.alumnos_inscritos = {}  # matricula -> nombre
        self.dentro_gimnasio = set()
        self.pases_visitantes = {}
        self.historial_accesos = []
        self.pagos = []
        self._candado = Lock()
        self.pico_aforo = 0

    def generar_id_socio(self):
        """Genera un ID corto y automático para un nuevo socio (S1, S2, ...)."""
        numero = len(self.socios) + 1
        while f"S{numero}" in self.socios:
            numero += 1
        return f"S{numero}"

    def generar_id_clase(self):
        """Genera un ID corto y automático para una nueva clase (C1, C2, ...)."""
        numero = len(self.clases) + 1
        while f"C{numero}" in self.clases:
            numero += 1
        return f"C{numero}"

    def generar_id_visitante(self):
        """Genera un folio corto para un visitante (V1, V2, ...)."""
        numero = len(self.pases_visitantes) + 1
        while f"V{numero}" in self.pases_visitantes:
            numero += 1
        return f"V{numero}"

    def _registrar_pago(self, tipo_membresia, monto, fecha):
        """Agrega un pago al historial para el reporte mensual."""
        self.pagos.append(
            {
                "tipo": tipo_membresia,
                "monto": float(monto),
                "fecha": fecha.isoformat(),
            }
        )

    def _buscar_socio(self, id_socio):
        if id_socio not in self.socios:
            raise MembresiaError(f"No existe ningún socio con el ID '{id_socio}'.")
        return self.socios[id_socio]

    def _buscar_clase(self, id_clase):
        if id_clase not in self.clases:
            raise ReservaError(f"No existe ninguna clase con el ID '{id_clase}'.")
        return self.clases[id_clase]

    # --- Función 1: Gestión de socios y membresías ---

    def registrar_socio(self, id_socio, nombre, tipo_membresia, ahora, matricula=None):
        """Da de alta a un socio y registra el pago de su membresía inicial."""
        if id_socio in self.socios:
            raise MembresiaError(f"El ID '{id_socio}' ya está registrado.")

        tipo = tipo_membresia.strip().lower()
        if tipo == "visitante":
            raise MembresiaError("Los visitantes entran con pase diario, no como socios.")

        if tipo == "estudiante":
            if not matricula or matricula not in self.alumnos_inscritos:
                raise MembresiaError(
                    f"La matrícula '{matricula}' no aparece en la lista de alumnos inscritos."
                )

        membresia = Membresia.crear(tipo, ahora)
        socio = Socio(id_socio, nombre, membresia, matricula=matricula)
        self.socios[id_socio] = socio
        self._registrar_pago(membresia.tipo, membresia.costo, ahora)
        return socio

    def renovar_membresia(self, id_socio, ahora):
        """Renueva la membresía actual de un socio."""
        socio = self._buscar_socio(id_socio)
        if socio.membresia.tipo == "estudiante":
            if not socio.matricula or socio.matricula not in self.alumnos_inscritos:
                raise MembresiaError("El alumno ya no aparece en el CSV de inscritos.")

        socio.renovar_membresia(ahora)
        self._registrar_pago(socio.membresia.tipo, socio.membresia.costo, ahora)
        return socio

    def cambiar_membresia(self, id_socio, nuevo_tipo, ahora, matricula=None):
        """Cambia el tipo de membresía de un socio y cobra el nuevo plan."""
        socio = self._buscar_socio(id_socio)
        tipo = nuevo_tipo.strip().lower()
        if tipo == "visitante":
            raise MembresiaError("Un socio no puede cambiar a pase de visitante.")

        if tipo == "estudiante":
            mat = matricula or socio.matricula
            if not mat or mat not in self.alumnos_inscritos:
                raise MembresiaError(
                    f"La matrícula '{mat}' no aparece en el CSV de alumnos inscritos."
                )
            socio.matricula = mat

        nueva = Membresia.crear(tipo, ahora)
        socio.cambiar_membresia(nueva)
        self._registrar_pago(nueva.tipo, nueva.costo, ahora)
        return socio

    # --- Función 2: Control de entradas y salidas ---

    def registrar_entrada(self, id_persona, area, ahora, es_visitante=False):
        """Valida vigencia, área, horario y aforo antes de permitir la entrada."""
        area_limpia = area.strip().lower()

        with self._candado:
            if es_visitante:
                pase = self.pases_visitantes.get(id_persona)
                if pase is None or not pase.esta_vigente(ahora):
                    pase = PaseVisitante(ahora)
                    self.pases_visitantes[id_persona] = pase
                    self._registrar_pago(pase.tipo, pase.costo, ahora)
                membresia = pase
            else:
                if id_persona not in self.socios:
                    raise AccesoDenegadoError("socio no registrado", id_persona)
                membresia = self.socios[id_persona].membresia

            if not membresia.esta_vigente(ahora):
                raise AccesoDenegadoError("membresía vencida")
            if not membresia.incluye_area(area_limpia):
                raise AccesoDenegadoError("área no incluida", area_limpia)
            if not membresia.puede_acceder_horario(ahora):
                raise AccesoDenegadoError("fuera del horario permitido")

            if area_limpia == "gimnasio":
                if id_persona in self.dentro_gimnasio:
                    raise AccesoDenegadoError("ya está dentro", id_persona)
                if len(self.dentro_gimnasio) >= self.AFORO_MAXIMO:
                    raise AccesoDenegadoError(
                        "aforo completo", f"límite de {self.AFORO_MAXIMO} personas"
                    )
                self.dentro_gimnasio.add(id_persona)
                if len(self.dentro_gimnasio) > self.pico_aforo:
                    self.pico_aforo = len(self.dentro_gimnasio)

            registro = RegistroAcceso(id_persona, es_visitante, area_limpia, ahora)
            self.historial_accesos.append(registro)
            return registro

    def registrar_salida(self, id_persona, ahora):
        """Registra la salida del gimnasio y libera un lugar del aforo."""
        with self._candado:
            if id_persona not in self.dentro_gimnasio:
                return False
            self.dentro_gimnasio.remove(id_persona)
            for reg in reversed(self.historial_accesos):
                if reg.id_persona == id_persona and reg.salida is None:
                    reg.salida = ahora
                    break
            return True

    # --- Función 3: Clases grupales ---

    def programar_clase(self, id_clase, nombre, instructor, fecha_hora, cupo_maximo):
        """Da de alta una nueva clase grupal dentro del horario del centro."""
        if id_clase in self.clases:
            raise ReservaError(f"Ya existe una clase con el ID '{id_clase}'.")
        if not Membresia.en_horario_general(fecha_hora):
            raise ReservaError("La clase debe programarse dentro del horario de apertura.")

        clase = ClaseGrupal(id_clase, nombre, instructor, fecha_hora, cupo_maximo)
        self.clases[id_clase] = clase
        return clase

    def reservar_clase(self, id_socio, id_clase, ahora):
        """Reserva un lugar para un socio en la clase indicada."""
        socio = self._buscar_socio(id_socio)
        clase = self._buscar_clase(id_clase)
        return clase.reservar(socio, ahora)

    def cancelar_reserva(self, id_socio, id_clase, ahora):
        """Cancela una reserva existente."""
        clase = self._buscar_clase(id_clase)
        clase.cancelar(id_socio, ahora)

    def pasar_lista(self, id_clase, ids_asistentes):
        """Registra asistencias y faltas en una clase."""
        clase = self._buscar_clase(id_clase)
        return clase.pasar_lista(ids_asistentes, self.socios)

    # --- Función 4: Consulta del socio ---

    def consultar_estado_socio(self, id_socio, ahora):
        """Devuelve un diccionario con la información actual del socio."""
        socio = self._buscar_socio(id_socio)
        reservas = []
        for clase in self.clases.values():
            for r in clase.reservas:
                if r.id_socio == id_socio:
                    reservas.append(
                        f"{clase.nombre} ({clase.fecha_hora:%Y-%m-%d %H:%M}) -> {r.estado}"
                    )

        bloqueo = (
            socio.bloqueado_hasta.strftime("%Y-%m-%d %H:%M")
            if socio.esta_bloqueado(ahora)
            else "Ninguno"
        )
        return {
            "ID": socio.id_socio,
            "Nombre": socio.nombre,
            "Membresía": str(socio.membresia),
            "Vigente": "Sí" if socio.membresia.esta_vigente(ahora) else "No",
            "Faltas acumuladas": len(socio.faltas),
            "Bloqueo activo": bloqueo,
            "Reservas": reservas if reservas else ["Sin reservas"],
        }