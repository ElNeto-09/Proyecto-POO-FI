"""Interfaz Runnable para separar qué hace una tarea de cómo se ejecuta."""

from abc import ABC, abstractmethod


class Runnable(ABC):
    """Una tarea que puede ejecutarse de forma secuencial o en un hilo."""

    @abstractmethod
    def run(self):
        """Ejecuta la tarea."""