# Mi Cartera — control de inversiones con precios automáticos

Esta carpeta contiene todo lo necesario para tener tu propia app de control de
cartera, gratis, alojada en GitHub, con los precios actualizándose solos cada
15 minutos (en horario de mercado, de lunes a viernes).

## Qué hace cada archivo

- `index.html` — la herramienta en sí (lo que abres en el navegador).
- `tickers.json` — la lista de acciones cuyo precio quieres que se consulte automáticamente.
- `data/prices.json` — último precio conocido de cada acción (lo escribe el robot, no lo toques a mano).
- `data/history.json` — histórico de precios, usado para el gráfico de evolución (tampoco lo toques a mano).
- `scripts/fetch_prices.py` — script que consulta los precios en Financial Modeling Prep.
- `.github/workflows/update-prices.yml` — la tarea automática que ejecuta ese script cada 15 minutos.

## Puesta en marcha (una sola vez)

- `index.html` — la herramienta en sí (lo que abres en el navegador).
- `tickers.json` — la lista de acciones cuyo precio quieres que se consulte automáticamente (ISIN + símbolo bursátil).
- `data/prices.json` — último precio conocido de cada acción (lo escribe el robot, no lo toques a mano).
- `data/history.json` — histórico de precios, usado para el gráfico de evolución (tampoco lo toques a mano).
- `scripts/fetch_prices.py` — script que consulta los precios en Yahoo Finance (gratis, sin necesidad de cuenta ni clave).
- `.github/workflows/update-prices.yml` — la tarea automática que ejecuta ese script cada 15 minutos.

## Puesta en marcha (una sola vez)

### 1. Crea el repositorio en GitHub
- Entra en https://github.com/new
- Ponle un nombre, por ejemplo `mi-cartera`
- Que sea **público** (necesario para que GitHub Pages sea gratis)
- Crea el repositorio vacío

### 2. Sube estos archivos
Puedes hacerlo desde la web de GitHub (botón "Add file" → "Upload files",
arrastrando toda esta carpeta), con GitHub Desktop, o por terminal:

```bash
git init
git add .
git commit -m "Primera versión de mi cartera"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/mi-cartera.git
git push -u origin main
```

### 3. Revisa `tickers.json`
Ya viene con tus acciones (ISIN + símbolo de bolsa). Si añades una nueva más
adelante, necesitas su ISIN y el símbolo bursátil exacto tal y como lo usa
Yahoo Finance (búscalo en https://finance.yahoo.com/lookup, o pídemelo en el
chat y te lo confirmo).

### 4. Activa GitHub Pages
`Settings` → `Pages` → en "Source" elige la rama `main` y la carpeta `/ (root)`
→ Guardar. En un par de minutos tendrás tu URL, algo como:
`https://TU-USUARIO.github.io/mi-cartera/`

### 5. Lanza la primera actualización manualmente
No hace falta esperar 15 minutos la primera vez: ve a la pestaña `Actions` de
tu repositorio, entra en "Actualizar precios" → `Run workflow` → `Run workflow`.
En menos de un minuto tendrás `data/prices.json` relleno y tu web mostrará los
precios automáticamente.

## Sobre la fuente de precios

Este proyecto usa un endpoint no oficial de Yahoo Finance: no requiere cuenta
ni clave, y cubre tanto EEUU como bolsas internacionales, pero no es una API
publicada ni garantizada por Yahoo — en teoría podría cambiar sin aviso. Si un
día algún precio deja de actualizarse, entra en `Actions` → la ejecución más
reciente → "Consultar precios" para ver el log: te dirá símbolo por símbolo
cuál falló. El resto de acciones no se ve afectado, y la que falle vuelve a
mostrarse en modo manual en la herramienta hasta que se resuelva.

## A partir de aquí

- Abre tu URL de GitHub Pages para usar la herramienta. Tus compras se guardan
  en tu navegador (igual que antes).
- Al añadir una operación tienes dos modos: **"Acción nueva"** (metes nombre,
  ISIN y los datos de la compra) y **"Ya tengo esta acción"** (eliges el ISIN
  de un desplegable y solo rellenas fecha, nº de acciones, precio y comisión —
  no vuelves a escribir el ISIN).
- El emparejamiento con los precios automáticos se hace por **ISIN**, no por
  nombre, así que no hay riesgo de que "Inditex" e "ITX" se traten como cosas
  distintas.
- Cada acción cuyo ISIN esté en `tickers.json` mostrará el precio con el icono
  ⚡ auto y no se podrá editar a mano (viene del robot). Las que no añadas a
  `tickers.json` seguirán funcionando con precio manual, como hasta ahora.
- Si añades una acción nueva a tu cartera, recuerda añadir también su ISIN a
  `tickers.json` y volver a subirlo (o editarlo directamente desde la web de
  GitHub) para que empiece a recibir precio automático.
