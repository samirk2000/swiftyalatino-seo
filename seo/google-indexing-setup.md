# Google Indexing API — setup (5 minutos)

Para que cada post nuevo se pida a Google **directo** (además de IndexNow),
necesitas una service account de Google Cloud. Una sola vez.

## Pasos

1. Entra a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto (o usa uno existente), ej. `swiftyalatino-seo`
3. Activa la API **"Web Search Indexing API"**:
   - APIs & Services → Library → busca "Web Search Indexing API" → Enable
4. Crea una Service Account:
   - IAM & Admin → Service Accounts → Create
   - Nombre: `swifty-indexing`
   - Rol: no hace falta rol de proyecto
5. Crea una clave JSON:
   - Entra a la service account → Keys → Add key → JSON
   - Descarga el archivo (ej. `swifty-indexing.json`)
6. En **Google Search Console** (propiedad `https://swiftyalatino.com`):
   - Settings → Users and permissions → Add user
   - Pega el email de la service account (termina en `@....iam.gserviceaccount.com`)
   - Permiso: **Owner**
7. Sube el JSON al servidor (fuera de git):

```bash
scp -i ~/.ssh/swifty_blogbot swifty-indexing.json blogbot@178.105.219.215:/opt/swifty-blog-bot/secrets/google-indexing.json
```

8. En el `.env` del servidor agrega:

```
GOOGLE_SERVICE_ACCOUNT_JSON=secrets/google-indexing.json
```

9. Instala la dependencia en el venv del servidor:

```bash
cd /opt/swifty-blog-bot && venv/bin/pip install google-auth
```

10. Prueba:

```bash
venv/bin/python -c "from automation.indexing import submit_url; print(submit_url('https://swiftyalatino.com/blog/'))"
```

Si ves `google_indexing: HTTP 200` → listo. Cada post nuevo pedirá indexación a Google automático.

## Límites

- ~200 URLs/día por defecto (suficiente para 2 posts/semana).
- Solo funciona en propiedades que ya verificaste en Search Console.
