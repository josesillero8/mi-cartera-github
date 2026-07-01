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

### 1. Crea una cuenta gratuita en Financial Modeling Prep
Ve a https://financialmodelingprep.com/, regístrate en el plan gratuito y copia
tu API key (la encontrarás en tu panel/dashboard).

### 2. Crea el repositorio en GitHub
- Entra en https://github.com/new
- Ponle un nombre, por ejemplo `mi-cartera`
- Que sea **público** (necesario para que GitHub Pages sea gratis)
- Crea el repositorio vacío

### 3. Sube estos archivos
Puedes hacerlo desde la web de GitHub (botón "Add file" → "Upload files",
arrastrando toda esta carpeta), o por terminal:

```bash
git init
git add .
git commit -m "Primera versión de mi cartera"
git branch -M main
git remote add origin https://github.com/TU-USUARIO/mi-cartera.git
git push -u origin main
```

### 4. Añade tu API key como secreto
En tu repositorio: `Settings` → `Secrets and variables` → `Actions` →
`New repository secret`.
- Name: `FMP_API_KEY`
- Value: la clave que copiaste en el paso 1

### 5. Edita `tickers.json` con tus acciones
Sustituye los ejemplos por los ISIN reales de tus acciones (los encuentras en
la ficha de cada valor dentro de Trade Republic). No hace falta que busques
el ticker: el script resuelve el símbolo bursátil automáticamente a partir
del ISIN la primera vez, y lo guarda en caché (`data/isin_map.json`) para no
repetir la búsqueda.

### 6. Activa GitHub Pages
`Settings` → `Pages` → en "Source" elige la rama `main` y la carpeta `/ (root)`
→ Guardar. En un par de minutos tendrás tu URL, algo como:
`https://TU-USUARIO.github.io/mi-cartera/`

### 7. Lanza la primera actualización manualmente
No hace falta esperar 15 minutos la primera vez: ve a la pestaña `Actions` de
tu repositorio, entra en "Actualizar precios" → `Run workflow` → `Run workflow`.
En menos de un minuto tendrás `data/prices.json` relleno y tu web mostrará los
precios automáticamente.

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
