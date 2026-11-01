# CotizacionDolar

Sitio estático para mostrar el precio de venta del dólar estadounidense (USD) en guaraníes (PYG), preparado para GitHub Pages y Visual Studio Code.

## Abrir en VS Code

1. Abrí esta carpeta en VS Code.
2. Ejecutá `python3 -m http.server 8000` desde la carpeta y entrá a `http://localhost:8000`.
3. Las cotizaciones se muestran desde `data/cotizaciones.json`.

## Actualización automática y fuentes

El proyecto incluye un flujo de GitHub Actions para consultar las páginas oficiales de las entidades y actualizar los datos de lunes a sábado a las 09:00 de Paraguay. También se puede ejecutar manualmente desde **Actions**. Si una página deja de responder o cambia su formato, el flujo mantiene el valor anterior y la página lo identifica como dato previo.

Fuentes oficiales:

- [Banco Atlas](https://www.bancoatlas.com.py/web)
- [Ueno](https://www.ueno.com.py/cambio-de-moneda/)

No se cargaron valores de ejemplo: el archivo inicial marca las cotizaciones como no disponibles hasta poder obtenerlas y validarlas. Revisá **Actions** luego de publicar; los sitios pueden variar y no se pudo comprobar una ejecución en vivo desde este entorno.

## Publicar en GitHub Pages

El flujo `.github/workflows/pages.yml` publica el sitio al hacer push a `main`. En GitHub, abrí **Settings → Pages** y elegí **GitHub Actions** como fuente.

Para crear el repositorio en GitHub con la CLI: `gh repo create CotizacionDolar --public --source . --remote origin --push`.
