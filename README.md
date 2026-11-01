1| # CotizacionDolar
2| 
3| Sitio estático para mostrar el precio de venta del dólar estadounidense (USD) en guaraníes (PYG), preparado para GitHub Pages y Visual Studio Code.
4| 
5| ## Abrir en VS Code
6| 
7| 1. Abrí esta carpeta en VS Code.
8| 2. Ejecutá `python3 -m http.server 8000` desde la carpeta y entrá a `http://localhost:8000`.
9| 3. Las cotizaciones se muestran desde `data/cotizaciones.json`.
10| 
11| ## Actualización automática y fuentes
12| 
13| El proyecto incluye un flujo de GitHub Actions para consultar las páginas oficiales de las entidades y actualizar los datos de lunes a sábado a las 09:00 de Paraguay. También se puede ejecutar manualmente con `python3 scripts/update_quotes.py`.
14| 
15| Fuentes oficiales activas:
16| 
17| - [Banco Atlas](https://www.bancoatlas.com.py/web)
18| - [Ueno](https://www.ueno.com.py/cambio-de-moneda/)
19| 
20| Se mantienen solo las fuentes que publican una estructura estable y scrapeable. Fuentes que cambian a iframes, contenido dinámico o no exponen la cotización en un formato público confiable quedan fuera de la automatización.
21| 
22| ## Publicar en GitHub Pages
23| 
24| El flujo `.github/workflows/pages.yml` publica el sitio al hacer push a `main`. En GitHub, abrí **Settings → Pages** y elegí **GitHub Actions** como fuente.
25| 
26| Para crear el repositorio en GitHub con la CLI: `gh repo create CotizacionDolar --public --source . --remote origin --push`.
27| 
