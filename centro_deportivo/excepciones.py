"""Excepciones propias para las reglas de negocio del centro deportivo."""


class CentroDeportivoError(Exception):
    """Excepción base de todo el sistema."""


class AccesoDenegadoError(CentroDeportivoError):
    """Se lanza cuando un socio o visitante no puede entrar a un área."""

    def __init__(self, motivo, detalle=""):
        self.motivo = motivo
        mensaje = f"Acceso denegado ({motivo})"
        if detalle:
            mensaje += f": {detalle}"
        super().__init__(mensaje)


class MembresiaError(CentroDeportivoError):
    """Error al registrar, renovar o cambiar una membresía."""


class ReservaError(CentroDeportivoError):
    """Error al programar, reservar o cancelar una clase grupal."""


class PersistenciaError(CentroDeportivoError):
    """Error al leer o guardar archivos del sistema."""