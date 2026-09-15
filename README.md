# SWIFTYALATINO – Landing IPTV SEO

Landing page ultra-rápida y optimizada para SEO local IPTV en México, USA (comunidad mexicana), España, Colombia y Perú, según lo definido en `.cursorrules`.

## Estructura del proyecto

```
swiftyalatino-seo/
├── .cursorrules              # Reglas del agente SEO (datos del negocio, objetivos)
├── planes.json                # Copys originales de los planes (fuente de verdad)
├── index.html                 # Landing principal (H1, planes, países, FAQ, CTAs WhatsApp)
├── robots.txt
├── sitemap.xml
├── .htaccess                  # Cache, gzip, https/www redirect (Hostinger/LiteSpeed)
├── assets/
│   ├── css/style.css          # Estilos (sin frameworks pesados)
│   ├── js/script.js           # JS mínimo (año dinámico, tracking WhatsApp)
│   └── img/                   # Colocar aquí: logo.png, favicon.png, og-swiftyalatino.jpg
├── blog/
│   └── index.html             # Índice del blog (el agente publica martes y viernes aquí)
├── wordpress/
│   ├── elementor-html-widget.html  # Guía para replicar la landing en WP + Elementor
│   └── functions-snippets.php      # Snippets opcionales (FAQ schema, performance)
├── seo/
│   ├── faq-schema.json        # JSON-LD FAQ reutilizable
│   └── meta-tags.md           # Checklist Rank Math + Core Web Vitals
└── scripts/
    └── deploy-hostinger.ps1   # Script de despliegue SFTP a Hostinger (PowerShell)
```

## Planes incluidos

**LATINO PREMIUM** — 3000 canales, 12000 pelis, 5000 series, 3 conexiones
- 1 Mes: $150 MXN · 3 Meses: $390 MXN · 6 Meses: $750 MXN · 12 Meses: $1,299 MXN

**MEGA TOTAL** — 8000 canales, 3 conexiones
- 1 Mes: $160 MXN · 4 Meses: $480 MXN · 8 Meses: $860 MXN · 12 Meses: $1,240 MXN · 16 Meses: $1,520 MXN

Todos los botones de compra abren WhatsApp (`https://wa.me/message/RUQZ63ESW76VB1`) con el mensaje prellenado `"Hola, quiero el plan [PLAN] de [X] meses"`. **No se incluye ningún link de pago, m3u, Xtream ni panel en la web**, conforme a las reglas del proyecto.

## Cómo previsualizar localmente

Abre `index.html` directamente en el navegador, o sirve la carpeta con cualquier servidor estático:

```powershell
cd "swiftyalatino-seo"
python -m http.server 8080
# abrir http://localhost:8080
```

## Despliegue a Hostinger

Dos rutas posibles:

1. **Sitio estático (recomendado, listo para producción ya mismo):** sube todo el contenido de esta carpeta (excepto `wordpress/`, `seo/`, `scripts/`, `.cursorrules`, `planes.json`, `README.md`) a `public_html` en Hostinger vía:
   - **hPanel > Administrador de archivos** (arrastrar y soltar), o
   - **FTP/SFTP** con `scripts/deploy-hostinger.ps1` (requiere host, usuario y contraseña SFTP de tu hPanel).

2. **WordPress + Elementor + LiteSpeed (según `.cursorrules`):** sigue la guía en `wordpress/elementor-html-widget.html` para recrear las secciones en Elementor, instala Rank Math y LiteSpeed Cache, y usa `seo/faq-schema.json` para el schema FAQ.

### Pendiente antes de publicar
- [ ] Agregar imágenes reales: `assets/img/logo.png`, `favicon.png`, `og-swiftyalatino.jpg`.
- [ ] Confirmar credenciales SFTP/hPanel de Hostinger para el despliegue automático.
- [ ] Verificar el dominio real conectado (swiftyalatino.com) en Hostinger antes de subir `.htaccess` (el redirect www/https debe coincidir con la config real del DNS).
- [ ] Dar de alta el sitio en Google Search Console y enviar `sitemap.xml`.
