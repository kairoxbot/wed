# forum-monitor

Corre en GitHub Actions cada 15 minutos — sin computador encendido, gratis.

## Setup (5 pasos)

### 1. Crear el Gist (memoria entre runs)
- ir a https://gist.github.com
- crear un Gist nuevo, archivo: `seen_posts.json`, contenido: `[]`
- copiar el ID del Gist (está en la URL: gist.github.com/user/**ID_AQUI**)

### 2. Crear GitHub Personal Access Token
- https://github.com/settings/tokens → Generate new token (classic)
- scope: marcar solo **gist**
- copiar el token

### 3. Añadir Secrets al repo
- en tu repo → Settings → Secrets and variables → Actions → New repository secret

| Secret | Valor |
|--------|-------|
| `WEBHOOK_URL` | tu webhook de Discord |
| `GIST_TOKEN` | el token del paso 2 |
| `GIST_ID` | el ID del Gist del paso 1 |

### 4. Push al repo
```bash
git add .
git commit -m "add monitor"
git push
```

### 5. Activar Actions
- repo → pestaña Actions → enable workflows

Listo. Corre solo cada 15 minutos, manda hits al webhook, no necesita nada local.

---

## Foros monitoreados

| Fuente | Secciones |
|--------|-----------|
| BreachForums | Databases, Leaks, Combolists |
| Nulled | Databases, Leaks, Tools |
| Cracked | Databases, Leaks, Configs |
| XSS.is | Leaks |
| Hackforums | Databases |
| GitHub API | repos con combo/stealer/dump/infostealer |
| LeakIX | databases expuestas en internet |

## Lanzar manual

repo → Actions → Forum Monitor → Run workflow
