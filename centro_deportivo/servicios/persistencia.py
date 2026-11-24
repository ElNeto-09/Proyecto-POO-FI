"""Lectura de CSV de alumnos y guardado/carga de datos en JSON."""

import csv
import json
import sys
from pathlib import Path

from centro_deportivo.excepciones import PersistenciaError
from centro_deportivo.modelos.clase_grupal import ClaseGrupal
from centro_deportivo.modelos.socio import RegistroAcceso, Socio
from centro_deportivo.servicios.gestor_centro import GestorCentro


class Persistencia:
    """Maneja los archivos de entrada (CSV) y el estado persistente (JSON)."""

    @staticmethod
    def cargar_alumnos_csv(gestor, ruta):
        """Lee el CSV de alumnos inscritos e informa renglones inválidos en stderr."""
        path = Path(ruta)
        if not path.exists():
            raise PersistenciaError(f"No se encontró el archivo '{path}'.")

        cargados = 0
        rechazados = 0

        try:
            with open(path, mode="r", encoding="utf-8", newline="") as archivo:
                lector = csv.reader(archivo)
                for num_linea, fila in enumerate(lector, start=1):
                    # Ignoramos líneas completamente vacías
                    if not fila or all(not campo.strip() for campo in fila):
                        continue
                    # Saltamos el encabezado si existe
                    if num_linea == 1 and fila[0].strip().lower() == "matricula":
                        continue

                    if len(fila) != 2:
                        print(
                            f"Línea {num_linea} rechazada: se esperaban 2 columnas.",
                            file=sys.stderr,
                        )
                        rechazados += 1
                        continue

                    matricula = fila[0].strip()
                    nombre = fila[1].strip()

                    if not matricula or not matricula.isalnum():
                        print(
                            f"Línea {num_linea} rechazada: matrícula inválida '{matricula}'.",
                            file=sys.stderr,
                        )
                        rechazados += 1
                        continue
                    if not nombre:
                        print(
                            f"Línea {num_linea} rechazada: falta el nombre del alumno.",
                            file=sys.stderr,
                        )
                        rechazados += 1
                        continue
                    if matricula in gestor.alumnos_inscritos:
                        print(
                            f"Línea {num_linea} rechazada: matrícula duplicada '{matricula}'.",
                            file=sys.stderr,
                        )
                        rechazados += 1
                        continue

                    gestor.alumnos_inscritos[matricula] = nombre
                    cargados += 1
        except OSError as e:
            raise PersistenciaError(f"No se pudo leer el CSV '{path}'.") from e

        return cargados, rechazados

    @staticmethod
    def guardar_estado(gestor, ruta):
        """Guarda toda la información del centro deportivo en un archivo JSON."""
        path = Path(ruta)
        path.parent.mkdir(parents=True, exist_ok=True)
        datos = {
            "alumnos_inscritos": gestor.alumnos_inscritos,
            "socios": [s.a_dict() for s in gestor.socios.values()],
            "clases": [c.a_dict() for c in gestor.clases.values()],
            "dentro_gimnasio": sorted(gestor.dentro_gimnasio),
            "historial_accesos": [r.a_dict() for r in gestor.historial_accesos],
            "pagos": gestor.pagos,
        }
        try:
            with open(path, mode="w", encoding="utf-8") as archivo:
                json.dump(datos, archivo, indent=2, ensure_ascii=False)
        except OSError as e:
            raise PersistenciaError(f"No se pudo guardar en '{path}'.") from e

    @staticmethod
    def cargar_estado(ruta):
        """Recupera el estado desde JSON; si el archivo no existe, inicia vacío."""
        gestor = GestorCentro()
        path = Path(ruta)
        if not path.exists():
            return gestor

        try:
            with open(path, mode="r", encoding="utf-8") as archivo:
                datos = json.load(archivo)

            gestor.alumnos_inscritos = dict(datos.get("alumnos_inscritos", {}))
            for item in datos.get("socios", []):
                socio = Socio.desde_dict(item)
                gestor.socios[socio.id_socio] = socio
            for item in datos.get("clases", []):
                clase = ClaseGrupal.desde_dict(item)
                gestor.clases[clase.id_clase] = clase
            gestor.dentro_gimnasio = set(datos.get("dentro_gimnasio", []))
            gestor.historial_accesos = [
                RegistroAcceso.desde_dict(r) for r in datos.get("historial_accesos", [])
            ]
            gestor.pagos = list(datos.get("pagos", []))
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as e:
            raise PersistenciaError(
                f"El archivo de datos '{path}' está dañado o tiene un formato inválido."
            ) from e

        return gestor