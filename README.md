# Consola de envíos ARINC 429

Aplicación Flask para configurar instrumentos, crear y administrar envíos, calcular una palabra lógica ARINC429 de 32 bits y guardar cada registro en MySQL. La interfaz queda en modo simulación por defecto: guardar un envío **no** transmite bytes a hardware.

## Requisitos y puesta en marcha

- Python 3.10 o posterior.
- MySQL 8+ (o compatible) para el uso normal. La aplicación crea las tablas al arrancar; configure una base de datos existente y un usuario con permisos de lectura/escritura/creación de tablas.
- En Linux, cree un entorno virtual e instale los paquetes declarados en `requirements.txt`.
- Copie `.env.example` a `.env`, cambie `SECRET_KEY` y configure `DATABASE_URL` con una URL SQLAlchemy `mysql+pymysql://usuario:contraseña@host:3306/base`. Codifique caracteres especiales de la contraseña como URL.
- Cargue las variables del archivo `.env` con su entorno de desarrollo o exportándolas en la terminal. La aplicación no lee `.env` automáticamente.
- Ejecute `flask --app app run` desde la carpeta del proyecto y abra la dirección local indicada por Flask.

Para pruebas no hace falta servidor MySQL: los tests usan SQLite en memoria. Ejecútelos con `python -m unittest discover -s tests`.

## Uso

1. Cree un instrumento con etiqueta en octal, codificación BNR con signo o UINT, unidades, límites, resolución, SDI y SSM.
2. Cree un envío seleccionando el instrumento e ingresando un valor. Se valida rango y múltiplo de resolución; se calcula y guarda la palabra de 32 bits.
3. Consulte, edite o elimine envíos desde el historial. El botón **Enviar serial** requiere habilitación explícita.

## Perfil lógico ARINC429

La palabra construida es: etiqueta de 8 bits con inversión de bits, SDI de 2 bits, campo de datos de 19 bits, SSM de 2 bits y paridad impar en el bit 32. BNR usa complemento a dos de 19 bits; UINT ocupa los 19 bits sin signo. Es un perfil simplificado; la interpretación y asignación del SSM, resolución, orden de los bits y codificación deben verificarse con el estándar aplicable y la documentación del equipo.

## Límites importantes de hardware

- Una palabra lógica o bytes por UART **no** implementan la capa eléctrica ARINC429. El adaptador serial, su protocolo, orden de bytes, velocidad, temporización, aislamiento y transmisor de línea deben estar documentados y verificados para el modelo real.
- La transmisión está apagada salvo que `HW_SERIAL_ENABLED=1` **y** `HW_SERIAL_RAW_WORDS=1`. `HW_SERIAL_RAW_WORDS` solo es apropiado si el fabricante documenta que el adaptador acepta exactamente cuatro bytes crudos por UART. La convención big-endian de este ejemplo es un marcador de integración, no una recomendación universal. No habilite la salida física sin validar el adaptador en un banco de prueba seguro.
- No se genera tensión por la salida de auriculares. El audio analógico no es una salida de tensión calibrada ni sustituye un DAC/generador aislado con etapa y carga especificadas. La aplicación muestra ese canal únicamente como simulado.
- No se han dado modelos de instrumentos, interfaz o especificación eléctrica, así que los instrumentos y perfiles deben ser ingresados por el operador. No usar como equipo de vuelo ni para control de sistemas reales.

## Variables de entorno

`DATABASE_URL`, `SECRET_KEY`, `HW_SERIAL_ENABLED`, `HW_SERIAL_PORT`, `HW_SERIAL_BAUDRATE` y `HW_SERIAL_RAW_WORDS`. No almacene secretos en el repositorio.
