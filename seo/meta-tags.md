# SEO – Focus keywords y metadatos

## Keyword principal (Rank Math Focus Keyword)
`mejor iptv mexico`

## Keywords secundarias
- iptv mexicanos en usa
- mejor iptv españa
- iptv colombia
- iptv peru
- comprar iptv

## Home (`/`)
- **Title:** Mejor IPTV México, USA, España, Colombia y Perú | SWIFTYALATINO
- **Meta description:** El mejor IPTV latino para México, iptv mexicanos en USA, España, Colombia y Perú. +3000 canales, +12000 películas, +5000 series. Comprar IPTV fácil por WhatsApp, OXXO, PayPal o Stripe.
- **H1:** El Mejor IPTV Latino para México, USA, España, Colombia y Perú
- **H2s:** Beneficios / Planes / Cobertura por país / Cómo comprar / FAQ

## Checklist Rank Math (objetivo 90+)
- [x] Focus keyword en title, meta description, H1, primer párrafo y URL.
- [x] Densidad de keywords secundarias en secciones de "Cobertura por país".
- [x] Imágenes con atributo `alt` descriptivo (agregar al subir imágenes reales).
- [x] Enlaces internos: Home -> /blog/, /blog/ -> Home.
- [x] Schema: Organization, Service/Offer, FAQPage.
- [x] Contenido > 1000 palabras entre home + FAQ.
- [ ] Enlaces externos de autoridad (opcional).
- [ ] Imagen Open Graph 1200x630 subida a `/assets/img/og-swiftyalatino.jpg`.

## Internacionalización (hreflang)
- `/` → español (predeterminado, `x-default`).
- `/en/` → inglés (USA/Canadá).
- Cada página enlaza a la otra con `<link rel="alternate" hreflang="...">` y en el `sitemap.xml`.
- El selector "ES / EN" está en el header y footer de ambas versiones.

## Conversión de moneda
- Selector de moneda en `#planes` (MXN, USD, COP, PEN, EUR, CAD), implementado en `assets/js/script.js`.
- Detecta automáticamente el idioma/país del navegador (`navigator.language`) para preseleccionar la moneda (ej. `es-PE` → PEN, `es-CO` → COP).
- Los precios de MEGA TOTAL en USD son los oficiales de Stripe; el resto son conversión referencial (tasa aproximada, actualizar cada cierto tiempo en `RATE_FROM_MXN` dentro de `script.js`).
- **Importante:** nunca se publican URLs de pago (Stripe/PayPal) en la web; el cobro se coordina siempre por WhatsApp, conforme a `.cursorrules`.

## Core Web Vitals 95+
- CSS crítico inline en `<head>`, resto en `style.css` con `preload`.
- JS único, sin dependencias, cargado con `defer`.
- Sin frameworks pesados (no jQuery, no Bootstrap).
- Fuentes con `font-display: swap` (si se agregan Google Fonts, usar `preconnect`).
- Imágenes: usar WebP + `loading="lazy"` + `width`/`height` explícitos para evitar CLS.
- En Hostinger: activar LiteSpeed Cache (o hPanel > Optimización de sitio web) y CDN.
