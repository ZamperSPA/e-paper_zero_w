# e-paper Zero W — Calendario y notificaciones Gmail

Aplicación para **Raspberry Pi** con el [Waveshare 2.7" e-Paper HAT monocromo](https://www.waveshare.com/2.7inch-e-paper-hat.htm). Muestra eventos de Google Calendar y correos sin leer de Gmail, controlados con los 4 botones del HAT.

## Características

- Vista de **calendario por día** con eventos
- Vista de **agenda** con próximos eventos
- Vista de **notificaciones** (eventos + Gmail sin leer)
- Sincronización manual y automática con Google
- Modo simulación (`--mock`) para probar sin hardware

## Requisitos

### Hardware

- Raspberry Pi con header de 40 pines (Zero W, 3, 4, 5, etc.)
- Waveshare **2.7" e-Paper HAT monocromo** (176×264 px, blanco/negro)
- Conexión a internet (Wi‑Fi o Ethernet)

### Software

- Raspberry Pi OS (o distribución compatible con `gpiozero` y SPI)
- Python 3.9 o superior
- SPI habilitado en la Pi

## Instalación

### 1. Habilitar SPI

```bash
sudo raspi-config
```

Ve a **Interface Options → SPI → Enable** y reinicia si es necesario.

### 2. Clonar el repositorio

```bash
git clone <url-del-repositorio> e-paper_zero_w
cd e-paper_zero_w
```

### 3. Instalar dependencias del sistema

```bash
sudo apt update
sudo apt install -y python3-pip python3-venv python3-pil python3-numpy python3-gpiozero python3-lgpio git
```

### 4. Instalar drivers de Waveshare

Instálalos **dentro del mismo entorno virtual** que usará la app:

```bash
cd e-paper_zero_w
python3 -m venv .venv
source .venv/bin/activate

git clone https://github.com/waveshare/e-Paper.git ~/e-Paper
cd ~/e-Paper/RaspberryPi_JetsonNano/python
pip install .
```

### 5. Instalar dependencias Python del proyecto

```bash
cd ~/e-paper_zero_w
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` incluye `spidev` (SPI), `lgpio` y `gpiozero` (GPIO del HAT y botones), necesarios en Raspberry Pi OS Bookworm o posterior.

### 6. Configurar Google Cloud (Gmail + Calendar)

1. Entra a [Google Cloud Console](https://console.cloud.google.com/).
2. Crea un proyecto (o usa uno existente).
3. Habilita estas APIs:
   - **Google Calendar API**
   - **Gmail API**
4. Ve a **APIs y servicios → Credenciales → Crear credenciales → ID de cliente de OAuth**.
5. Tipo de aplicación: **Aplicación de escritorio**.
6. Descarga el JSON y guárdalo como:

   ```
   credentials/credentials.json
   ```

7. En **Pantalla de consentimiento de OAuth**, agrega tu cuenta Gmail como usuario de prueba (si el proyecto está en modo de prueba).

### 7. Crear configuración local

```bash
cp config.example.yaml config.yaml
```

Edita `config.yaml` si necesitas cambiar rutas, calendario o intervalo de actualización.

## Primera ejecución (autenticación)

La primera vez debes autorizar la cuenta Gmail. El programa mostrará una URL en la consola:

```bash
python3 main.py
```

1. Abre la URL en un navegador (puede ser en otro dispositivo).
2. Inicia sesión con tu cuenta Gmail y acepta los permisos.
3. Copia el código de autorización y pégalo en la terminal.

El token queda guardado en `token.json` para ejecuciones futuras.

## Uso básico

### Ejecutar en la Raspberry Pi

```bash
source .venv/bin/activate   # si usas entorno virtual
python3 main.py
```

Para detener la aplicación: `Ctrl + C`.

### Probar sin hardware (PC o desarrollo)

Genera una imagen `preview.png` en lugar de usar el e-paper:

```bash
python3 main.py --mock
```

### Logs detallados

```bash
python3 main.py --debug
```

## Botones del HAT

Los botones están mapeados de **arriba hacia abajo** (KEY1 → KEY4):

| Botón | GPIO | Acción principal |
|-------|------|------------------|
| KEY1  | 5    | Día anterior / volver al calendario |
| KEY2  | 6    | Día siguiente / cambiar pantalla |
| KEY3  | 13   | Sincronizar con Google |
| KEY4  | 19   | Cambiar entre Agenda y Notificaciones |

### Pantallas

1. **Calendario del día** — eventos del día seleccionado
2. **Agenda** — próximos eventos de varios días
3. **Notificaciones** — próximos eventos + correos Gmail sin leer

## Configuración (`config.yaml`)

Opciones más útiles:

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `google.calendar_id` | ID del calendario (`primary` = principal de Gmail) | `primary` |
| `google.days_ahead` | Días de eventos a cargar | `14` |
| `google.max_unread_emails` | Correos sin leer a mostrar | `5` |
| `refresh.auto_interval_seconds` | Actualización automática (0 = desactivada) | `900` (15 min) |
| `display.mock` | Simular pantalla sin hardware | `false` |

## Estructura del proyecto

```
e-paper_zero_w/
├── main.py              # Punto de entrada
├── config.example.yaml  # Plantilla de configuración
├── config.yaml          # Tu configuración (no se sube a git)
├── requirements.txt
├── credentials/         # credentials.json (no se sube a git)
├── token.json           # Token OAuth (no se sube a git)
└── app/
    ├── app.py           # Lógica principal y botones
    ├── config.py
    ├── display.py       # Driver e-paper monocromo
    ├── screens.py       # Renderizado de pantallas
    ├── google_services.py
    ├── buttons.py
    └── models.py
```

## Solución de problemas

**No se encuentra `config.yaml`**
```bash
cp config.example.yaml config.yaml
```

**`ModuleNotFoundError: No module named 'spidev'`**
```bash
source .venv/bin/activate
pip install spidev
# o
pip install -r requirements.txt
```

**Avisos de `PinFactoryFallback` o error `/sys/class/gpio/gpio24/value`**

En Raspberry Pi OS reciente el GPIO por sysfs está deshabilitado. Instala `lgpio` en el venv:

```bash
source .venv/bin/activate
pip install lgpio
pip install -r requirements.txt
```

Si persiste, agrega tu usuario al grupo `gpio`, cierra sesión y vuelve a entrar:

```bash
sudo usermod -aG gpio $USER
```

**Error al importar `waveshare_epd`**
- Verifica que instalaste los drivers de Waveshare (paso 4).
- Confirma que SPI está habilitado.

**Pantalla en blanco o sin actualizar**
- Revisa que el HAT esté bien conectado al header de 40 pines.
- Ejecuta con `--debug` para ver errores en consola.

**Error de autenticación Google**
- Confirma que `credentials/credentials.json` existe.
- Borra `token.json` y vuelve a autenticarte si cambiaste de cuenta o permisos.
- Verifica que Calendar API y Gmail API estén habilitadas.

**Fuentes no encontradas**
- En Raspberry Pi OS las fuentes DejaVu suelen estar en `/usr/share/fonts/truetype/dejavu/`.
- Ajusta las rutas en `config.yaml` si usas otra distribución.

## Licencia

Proyecto de uso personal/educativo. Las librerías de Waveshare y Google tienen sus propias licencias.
