# Centro Deportivo Universitario

Proyecto final de Programación Orientada a Objetos (Tema 4). Es un sistema de consola hecho en Python para administrar las membresías, entradas y salidas, clases grupales, reportes mensuales y la simulación de hora pico de un centro deportivo universitario.

## Integrantes
* De Anda Moctezuma Ernesto
* Miranda Rodríguez Jesús
* Peña Hernández Luis Noel
* Ramírez Arellano Felipe Emanuel

## Qué necesitas para correrlo
* **Python 3.10 o superior.**
* No hay que instalar ninguna librería extra; todo funciona con la biblioteca estándar de Python.

## Instalación
1. Clona el repositorio y entra a la carpeta del proyecto:
   ```bash
   git clone [https://github.com/TU-USUARIO/Proyecto-POO.git](https://github.com/TU-USUARIO/Proyecto-POO.git)
   cd Proyecto-POO
   ```
2. Confirma que tienes Python instalado:
   ```bash
   python --version
   ```

## Cómo ejecutar el programa
El sistema se corre desde la raíz del proyecto usando `-m`. Agregamos las opciones `--estado` (para cargar un archivo JSON específico) y `--fecha` (para fijar una fecha y hora de prueba y no tener que esperar tiempo real para probar horarios o bloqueos):

```bash
python -m centro_deportivo.main --estado datos/estado_ejemplo.json --fecha "2026-11-16 10:00"
```

Si lo corres solo con `python -m centro_deportivo.main`, usará la fecha y hora actuales de tu computadora y guardará los cambios en `estado_actual.json` al salir (incluso si cierras con `Ctrl+C`).

## Cómo probar cada función (incluyendo casos de rechazo)

Arranca el programa con el estado de ejemplo y la fecha fija de lunes 16 de noviembre de 2026 a las 10:00:
```bash
python -m centro_deportivo.main --estado datos/estado_ejemplo.json --fecha "2026-11-16 10:00"
```

El menú muestra listas de socios y clases en pantalla y genera IDs cortos (`S1`, `C1`, `V1`) para no tener que memorizar códigos largos.

1. **Cargar alumnos inscritos desde CSV (Opción 1):**
   * *Prueba normal:* Solo presiona `Enter` para cargar `datos/alumnos_inscritos.csv`.
   * *Prueba con errores:* Vuelve a entrar a la Opción 1 y escribe `datos/alumnos_con_errores.csv`. El programa te dirá qué renglones rechazó y por qué (duplicados, matrícula vacía o con caracteres raros, columnas incompletas) sin detenerse.

2. **Registrar socios, renovar y cambiar de plan (Opciones 2 y 3):**
   * *Registro válido:* En la Opción 2, registra a alguien con plan `1` (Estudiante) usando la matrícula `3201004` (que sí viene en el CSV). Se creará como `S4`.
   * *Registro rechazado:* Intenta registrar otro Estudiante con matrícula `9999999`. El sistema lo rechaza porque esa matrícula no aparece en el CSV de inscritos.
   * *Renovar o cambiar:* Entra a la Opción 3, elige `S2` y prueba renovarlo (`1`) o cambiarlo a plan Premium (`2` → `3`).

3. **Entradas, salidas y control de aforo (Opción 4):**
   * *Entrada de socio:* Opción 4 → `1`, responde `n` (no es visitante), elige `S1` (Estudiante) y área `1` (Gimnasio). Como son las 10:00 de un lunes, lo deja pasar.
   * *Entrada de visitante:* Opción 4 → `1`, responde `s` (pase diario de \$120) y área `1` (Gimnasio). Se le asigna automáticamente el folio `V1`.
   * *Rechazo por área:* Intenta meter a `S1` (Estudiante) a la `2` (Alberca). Saldrá el aviso de acceso denegado porque su plan no incluye alberca.
   * *Rechazo por horario:* Ve a la Opción 9 y cambia el reloj a `2026-11-16 18:00`. Intenta entrar con `S1` al gimnasio → lo rechaza porque el horario de estudiante termina a las 15:00. Si cambias la fecha a un domingo (`2026-11-22 10:00`), rechaza a cualquiera porque el centro abre de lunes a sábado.
   * *Salida:* Regresa el reloj a `2026-11-16 10:00` (Opción 9) y entra a Opción 4 → `2` para registrar la salida de `S1` y liberar su lugar en el aforo (máximo 60 personas).

4. **Clases grupales, reservas, cancelaciones y bloqueo por faltas (Opción 5):**
   * *Programar clase:* Opción 5 → `1`, crea por ejemplo una clase de `Yoga` para `2026-11-17 12:00` con cupo de `5`.
   * *Rechazo por tipo de plan:* Intenta reservar (Opción 5 → `2`) con `S1` o `S2`. Los rechaza porque solo la membresía Premium tiene acceso a clases.
   * *Rechazo por más de 48 horas:* Crea una clase para `2026-11-25 10:00` e intenta reservar con `S3` (Premium) estando en `2026-11-16 10:00`. Lo rechaza porque pasa de las 48 horas de anticipación.
   * *Rechazo al cancelar tarde:* Cambia el reloj (Opción 9) a `2026-11-17 09:00` e intenta cancelar la reserva de `S3` en `C1` (que empieza a las 10:00). Lo rechaza porque faltan menos de 2 horas.
   * *Pase de lista y bloqueo de 7 días:* Regresa el reloj a `2026-11-16 10:00`, entra a Opción 5 → `4`, elige `C1` y presiona `Enter` sin escribir asistentes. Como `S3` ya traía 2 faltas en noviembre en `estado_ejemplo.json`, con esta junta 3 y queda bloqueado 7 días para volver a reservar.

5. **Consultar estado de un socio (Opción 6):**
   * Elige `S3` para ver su plan, hasta cuándo está vigente, sus reservas, cuántas faltas lleva y si tiene bloqueo activo.

6. **Generar reporte mensual (Opción 7):**
   * Solo presiona `Enter` en año (`2026`) y mes (`11`). Se creará el archivo `reporte_2026_11.txt` con el dinero recaudado por tipo de membresía, la asistencia a cada clase y cuántas personas hubo en el gimnasio por cada hora del día.

7. **Simulación de hora pico (Opción 8):**
   * Corre 4 torniquetes en paralelo metiendo y sacando gente al azar mientras 15 socios intentan ganar los 5 lugares de una clase. Al final muestra el resumen confirmando que nunca se pasó del aforo de 60 ni del cupo de la clase.

8. **Prueba con archivo dañado (manejo de errores sin *traceback*):**
   * Corre el programa pasándole el JSON roto de prueba:
     ```bash
     python -m centro_deportivo.main --estado datos/estado_danado.json
     ```
   * Verás un mensaje claro avisando que el archivo está dañado y el programa se cerrará de forma ordenada, sin aventar un *traceback*.

## Estructura del proyecto
```text
Proyecto-POO/
├── README.md                       # Instrucciones de instalación, pruebas y estructura
├── .gitignore                      # Ignora __pycache__/, .venv/ y archivos temporales
├── datos/                          # Archivos de ejemplo para probar el sistema
│   ├── alumnos_inscritos.csv       # Lista de alumnos válidos
│   ├── alumnos_con_errores.csv     # Lista con errores a propósito para probar rechazos
│   ├── estado_ejemplo.json         # Datos precargados (socios, clases, accesos y pagos)
│   └── estado_danado.json          # Archivo corrupto para probar que no truene el programa
├── docs/
│   ├── diseno.md                   # Explicación del diseño, decisiones y trabajo en equipo
│   └── uml/
│       └── diagrama_clases.png     # Diagrama UML de clases
└── centro_deportivo/
    ├── __init__.py
    ├── main.py                     # Menú en consola y lectura de argumentos (argparse)
    ├── excepciones.py              # Excepciones propias para los errores de negocio
    ├── modelos/                    # Clases principales del dominio
    │   ├── __init__.py
    │   ├── membresia.py            # Clase abstracta Membresia y sus 4 planes
    │   ├── socio.py                # Clases Socio, Reserva y RegistroAcceso
    │   └── clase_grupal.py         # ClaseGrupal con control de cupo, horarios y Lock
    ├── servicios/                  # Lógica general, archivos y reportes
    │   ├── __init__.py
    │   ├── gestor_centro.py        # Coordina socios, clases, accesos y aforo máximo (60)
    │   ├── persistencia.py         # Carga de CSV y guardado/lectura del estado en JSON
    │   └── reportes.py             # Genera el reporte mensual en archivo .txt
    └── concurrencia/               # Hilos para la simulación de hora pico
        ├── __init__.py
        ├── runnable.py             # Interfaz Runnable para tareas ejecutables
        └── simulacion.py           # Torniquetes, reservas simultáneas y simulador
```

## Rúbrica de evaluación
| Criterio | Qué se revisa | % |
| :--- | :--- | :---: |
| **Ejecución** | Se clona, se instala y se ejecuta en otra computadora siguiendo solo el `README.md`, y los datos de ejemplo permiten probar todas las funciones. | 15% |
| **Funcionalidad** | Las funciones del tema están completas y son correctas, incluidas sus reglas y sus casos de rechazo. | 25% |
| **Diseño** | Las responsabilidades están bien repartidas entre las clases, y el uso de cada concepto del curso resuelve un problema del sistema. | 25% |
| **Robustez** | Los datos inválidos, los archivos faltantes o dañados y las operaciones simultáneas no detienen el programa ni dejan datos inconsistentes. | 10% |
| **Documentación** | `README.md`, diagramas UML coherentes con el código, documento de diseño y docstrings. | 15% |
| **Trabajo en equipo** | Historial de commits de todos los integrantes a lo largo del desarrollo. | 10% |