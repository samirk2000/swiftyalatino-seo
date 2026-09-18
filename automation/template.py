"""Genera el HTML final de un post de blog, con el mismo header/footer/CSS/JS
y tracking (GA4 + Meta Pixel) que el resto del sitio."""
from datetime import date
from . import config

HEAD_TRACKING = """
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-TQFGX25EHM"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-TQFGX25EHM');
</script>

<!-- Meta Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{if(f.fbq)return;n=f.fbq=function(){n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}(window, document,'script','https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '2243888319789679');
fbq('track', 'PageView');
</script>
<noscript><img height="1" width="1" style="display:none"
src="https://www.facebook.com/tr?id=2243888319789679&ev=PageView&noscript=1"
/></noscript>
<!-- End Meta Pixel Code -->
"""

HEADER = f"""<header class="site-header">
  <div class="container header-inner">
    <a href="/" class="logo">
      <img src="/assets/img/logo.png" alt="SWIFTYALATINO" width="160" height="128" class="site-logo">
    </a>
    <nav class="main-nav" aria-label="Navegacion principal">
      <a href="/#planes">Planes</a>
      <a href="/#paises">Cobertura</a>
      <a href="/#faq">Preguntas</a>
      <a href="/blog/">Blog</a>
    </nav>
    <a class="btn btn-whatsapp header-cta" target="_blank" rel="noopener"
       href="{config.WHATSAPP_LINK}?text=Hola%2C%20quiero%20informaci%C3%B3n%20de%20los%20planes%20IPTV">
      WhatsApp
    </a>
  </div>
</header>"""

FOOTER = f"""<footer class="site-footer">
  <div class="container footer-inner">
    <img src="/assets/img/logo.png" alt="SWIFTYALATINO" width="120" height="96" class="footer-logo">
    <p>&copy; <span id="year"></span> SWIFTYALATINO. Todos los derechos reservados.</p>
    <p><a href="/blog/">Blog</a></p>
  </div>
</footer>
<a class="whatsapp-float" target="_blank" rel="noopener" aria-label="Chatea por WhatsApp"
   href="{config.WHATSAPP_LINK}">
  💬
</a>
<script src="/assets/js/script.js" defer></script>"""


def build_faq_schema(faq_items: list[tuple[str, str]]) -> str:
    import json
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q,
                "acceptedAnswer": {"@type": "Answer", "text": a},
            }
            for q, a in faq_items
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def render_post(
    slug: str,
    title: str,
    meta_description: str,
    keywords: str,
    body_html: str,
    faq_items: list[tuple[str, str]],
    published_date: date | None = None,
    image_url: str | None = None,
) -> str:
    published_date = published_date or date.today()
    date_str = published_date.strftime("%Y-%m-%d")
    date_human = published_date.strftime("%d de %B de %Y")
    url = f"{config.SITE_URL}/blog/{slug}.html"
    faq_json = build_faq_schema(faq_items)
    if not image_url:
        image_url = f"{config.SITE_URL}/assets/img/og-swiftyalatino.jpg"
    image_meta = f'''<meta property="og:image" content="{image_url}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:image" content="{image_url}">'''
    hero_html = f'<img class="post-hero" src="{image_url}" alt="{title}" width="1200" height="630" loading="eager">'

    article_schema = f"""{{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": {title!r},
  "description": {meta_description!r},
  "inLanguage": "es-MX",
  "datePublished": "{date_str}",
  "dateModified": "{date_str}",
  "author": {{"@type": "Organization", "name": "SWIFTYALATINO", "url": "{config.SITE_URL}"}},
  "publisher": {{
    "@type": "Organization", "name": "SWIFTYALATINO", "url": "{config.SITE_URL}",
    "logo": {{"@type": "ImageObject", "url": "{config.SITE_URL}/assets/img/logo.png"}}
  }},
  "mainEntityOfPage": {{"@type": "WebPage", "@id": "{url}"}},
  "image": "{image_url}"
}}""".replace("'", "\"")

    return f"""<!DOCTYPE html>
<html lang="es-MX">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | SWIFTYALATINO</title>
<meta name="description" content="{meta_description}">
<meta name="keywords" content="{keywords}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{url}">
<link rel="stylesheet" href="/assets/css/style.css">
<link rel="icon" href="/assets/img/favicon.png" type="image/png">

<meta property="og:type" content="article">
<meta property="og:locale" content="es_MX">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_description}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="SWIFTYALATINO">
{image_meta}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{meta_description}">

<script type="application/ld+json">
{article_schema}
</script>

<script type="application/ld+json">
{faq_json}
</script>
{HEAD_TRACKING}
</head>
<body>
{HEADER}

<main class="section">
  <article class="container blog-post">
    {hero_html}
    <h1>{title}</h1>
    <p class="post-meta">{date_human} &middot; Guia IPTV latino</p>

{body_html}

    <div class="blog-cta">
      <p>&iquest;Listo para disfrutar SWIFTYALATINO? Escribenos y te armamos el plan segun tu pais.</p>
      <a class="btn btn-whatsapp btn-lg" target="_blank" rel="noopener"
         href="{config.WHATSAPP_LINK}?text=Hola%2C%20quiero%20mas%20informacion%20de%20IPTV">
        📲 Pedir informacion por WhatsApp
      </a>
      <p class="phone-alt">O mandanos un WhatsApp al <a href="tel:{config.PHONE_TEL}">{config.PHONE}</a></p>
    </div>
  </article>
</main>

{FOOTER}
</body>
</html>
"""
