"""Generación del reporte mensual en archivo de texto."""

from datetime import datetime
from pathlib import Path


class GeneradorReportes:
    """Crea el reporte mensual con ingresos, asistencia y ocupación por hora."""

    @staticmethod
    def generar_reporte_mensual(gestor, anio, mes, ruta_salida):
        """Genera un archivo .txt con las estadísticas del mes solicitado."""
        ingresos = {"estudiante": 0.0, "general": 0.0, "premium": 0.0, "visitante": 0.0}
        for pago in gestor.pagos:
            fecha = datetime.fromisoformat(pago["fecha"])
            if fecha.year == anio and fecha.month == mes:
                tipo = pago["tipo"]
                if tipo in ingresos:
                    ingresos[tipo] += float(pago["monto"])

        # Conteo de personas en el gimnasio por cada hora de apertura (6:00 a 22:00)
        ocupacion = {hora: 0 for hora in range(6, 22)}
        for reg in gestor.historial_accesos:
            if reg.area != "gimnasio":
                continue
            if reg.entrada.year != anio or reg.entrada.month != mes:
                continue
            h_inicio = max(6, reg.entrada.hour)
            h_fin = min(21, reg.salida.hour if reg.salida else reg.entrada.hour)
            for h in range(h_inicio, h_fin + 1):
                ocupacion[h] += 1

        path = Path(ruta_salida)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, mode="w", encoding="utf-8") as f:
            f.write(f"REPORTE MENSUAL - CENTRO DEPORTIVO ({anio}-{mes:02d})\n")
            f.write("=" * 52 + "\n\n")

            f.write("1. INGRESOS POR TIPO DE MEMBRESÍA\n")
            total = 0.0
            for tipo, monto in ingresos.items():
                total += monto
                f.write(f"   - {tipo.capitalize():<12}: ${monto:,.2f}\n")
            f.write(f"   TOTAL DEL MES : ${total:,.2f}\n\n")

            f.write("2. ASISTENCIA A CLASES GRUPALES\n")
            clases_mes = [
                c
                for c in gestor.clases.values()
                if c.fecha_hora.year == anio and c.fecha_hora.month == mes
            ]
            if not clases_mes:
                f.write("   No hubo clases programadas en este mes.\n")
            for clase in clases_mes:
                asistentes = sum(1 for r in clase.reservas if r.estado == "asistio")
                f.write(
                    f"   - {clase.nombre} ({clase.fecha_hora:%Y-%m-%d %H:%M}): "
                    f"{asistentes}/{clase.cupo_maximo} asistentes\n"
                )

            f.write("\n3. PERSONAS EN EL GIMNASIO POR HORA\n")
            for hora, cantidad in ocupacion.items():
                f.write(f"   - {hora:02d}:00 a {hora + 1:02d}:00 -> {cantidad} personas\n")

        return path