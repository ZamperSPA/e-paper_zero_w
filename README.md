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
sudo apt install -y python3-pip python3-venv python3-pil python3-numpy python3-gpiozero python3-lgpio fonts-dejavu-core git
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

#### A) Pantalla de consentimiento OAuth (obligatorio)

1. [Google Cloud Console](https://console.cloud.google.com/) → **APIs y servicios** → **Pantalla de consentimiento de OAuth**.
2. Tipo de usuario: **Externo** (para cuenta Gmail personal).
3. Completa **nombre de la app** y **correo de asistencia** (campos obligatorios).
4. En **Ámbitos / Scopes**, agrega:
   - `.../auth/calendar.readonly`
   - `.../auth/gmail.readonly`
5. En **Usuarios de prueba**, agrega tu cuenta Gmail (`tu@gmail.com`).
6. Estado: **Prueba** (Testing). No pases a Producción hasta verificar la app.

> Si falta la pantalla de consentimiento o tu correo no está como usuario de prueba, Google muestra **Error 400: invalid_request**.

#### B) Habilitar APIs

En **APIs y servicios → Biblioteca**, habilita:

- **Google Calendar API**
- **Gmail API**

#### C) Credenciales OAuth

1. **APIs y servicios → Credenciales → Crear credenciales → ID de cliente de OAuth**.
2. Tipo: **Aplicación de escritorio** (no "Aplicación web").
3. Descarga el JSON → `credentials/credentials.json`.

**No edites `redirect_uris` manualmente.** En aplicación de escritorio Google usa loopback (`http://127.0.0.1:PUERTO`). El JSON puede mostrar `http://localhost`; eso es normal.

#### D) Errores frecuentes

| Error | Causa | Solución |
|-------|-------|----------|
| `400 invalid_request` | Consentimiento OAuth incompleto o sin usuario de prueba | Pasos A) arriba |
| `400 invalid_request` + `urn:ietf:wg:oauth:2.0:oob` | Flujo OOB obsoleto | Usa credencial **Escritorio** y código actualizado |
| `403 access_denied` | Tu Gmail no está en usuarios de prueba | Agrégalo en pantalla de consentimiento |
| `redirect_uri_mismatch` | Credencial tipo Web mezclada con flujo Escritorio | Crea credencial nueva tipo **Escritorio** |

### 7. Crear configuración local

```bash
cp config.example.yaml config.yaml
```

Edita `config.yaml` si necesitas cambiar rutas, calendario o intervalo de actualización.

## Primera ejecución (autenticación)

```bash
python3 main.py
```

1. La Pi mostrará una **URL** (con `127.0.0.1` y un puerto).
2. Ábrela en un navegador (teléfono o PC) e inicia sesión con el **mismo Gmail** que agregaste como usuario de prueba.
3. Acepta los permisos de Calendar y Gmail.

**Si autorizas en otro dispositivo** (no en la Pi), tras el login el navegador irá a `http://127.0.0.1:PUERTO/...` y la página no cargará. Copia esa URL completa y en la terminal SSH de la Pi ejecuta:

```bash
curl "http://127.0.0.1:PUERTO/?state=...&code=..."
```

La app recibirá el código y guardará `token.json`.

> **Importante:** `credentials/credentials.json` es OAuth de Google. No lo confundas con `config.yaml`.

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
```bash
sudo apt install fonts-dejavu-core
```
La app también busca automáticamente FreeSans, Liberation y Noto si DejaVu no está instalada.

## Licencia

Proyecto de uso personal/educativo. Las librerías de Waveshare y Google tienen sus propias licencias.
