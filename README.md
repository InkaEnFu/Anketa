# Anketa – Jakou máš značku telefonu?

Jednoduchá webová anketa vytvořená jako školní projekt (WA, 2026).

---

## Obsah
1. [Otázka a možnosti](#otázka-a-možnosti)
2. [Wireframe](#wireframe)
3. [Deployment diagram](#deployment-diagram)
4. [Struktura souborů](#struktura-souborů)
5. [Endpointy](#endpointy)
6. [Instalace a lokální spuštění](#instalace-a-lokální-spuštění)
7. [Nasazení na PythonAnywhere](#nasazení-na-pythonanywhere)
8. [Postup nasazení změn (krok za krokem)](#postup-nasazení-změn-krok-za-krokem)
9. [Reset token](#reset-token)
10. [Monitoring a uptime](#monitoring-a-uptime)

---

## Otázka a možnosti

**Jakou máš značku telefonu?**

| Možnost | Label     |
|---------|-----------|
| a)      | iPhone    |
| b)      | Samsung   |
| c)      | Huawei    |
| d)      | Xiaomi    |
| e)      | Jiné      |

---

## Wireframe

```
wireframe.png v /diagrams
```

---

## Deployment diagram

deployment.png v /diagrams

---

## Struktura souborů

```
Anketa/
├── app.py              # Flask aplikace, routy
├── config.py           # Otázka, možnosti, reset token
├── database.py         # Práce s SQLite databází
├── requirements.txt    # Python závislosti
├── anketa.db           # SQLite databáze (vytvoří se automaticky)
├── README.md           # Tato dokumentace
├── templates/
│   ├── base.html       # Základní šablona (nav, flash zprávy, footer)
│   ├── index.html      # Stránka s hlasovacím formulářem
│   ├── results.html    # Stránka s výsledky
│   ├── reset.html      # Formulář pro reset hlasování
│   └── about.html      # Stránka O anketě
└── static/
    └── style.css       # CSS styly
```

---

## Endpointy

| Metoda | URL        | Popis                                              |
|--------|------------|----------------------------------------------------|
| GET    | `/`        | Zobrazí hlasovací formulář                         |
| POST   | `/`        | Uloží hlas a přesměruje na výsledky                |
| GET    | `/results` | Zobrazí aktuální výsledky hlasování                |
| GET    | `/reset`   | Zobrazí formulář pro zadání reset tokenu           |
| POST   | `/reset`   | Ověří token; pokud OK, vynuluje hlasy              |
| GET    | `/about`   | Stránka O anketě                                   |

---

## Instalace a lokální spuštění

```bash
# 1. Klonuj repozitář
git clone https://github.com/Inkaenfu/Anketa.git
cd Anketa

# 2. Vytvoř a aktivuj virtualenv
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# 3. Nainstaluj závislosti
pip install -r requirements.txt

# 4. Spusť vývojový server
python app.py
```

Aplikace poběží na `http://127.0.0.1:5000`.

---

## Nasazení na PythonAnywhere

### Předpoklady
- Účet na [pythonanywhere.com](https://www.pythonanywhere.com/) (FREE tier stačí)
- Repozitář na GitHubu

### Kroky (první nasazení)

1. **Přihlaš se** na PythonAnywhere → otevři **Bash console**.

2. **Klonuj repozitář:**
   ```bash
   git clone https://github.com/<vaše_jméno>/Anketa.git ~/anketa
   ```

3. **Vytvoř virtualenv:**
   ```bash
   mkvirtualenv --python=python3.11 anketa-venv
   pip install -r ~/anketa/requirements.txt
   ```

4. **Nastav Web App:**
   - Záložka **Web** → **Add a new web app**
   - Vyber **Manual configuration** → **Python 3.11**
   - Source code: `/home/<vaše_jméno>/anketa`
   - Working directory: `/home/<vaše_jméno>/anketa`
   - Virtualenv: `/home/<vaše_jméno>/.virtualenvs/anketa-venv`

5. **Nastav WSGI soubor** (`/var/www/<vaše_jméno>_pythonanywhere_com_wsgi.py`):
   ```python
   import sys
   sys.path.insert(0, '/home/<vaše_jméno>/anketa')
   from app import app as application
   ```

6. Klikni **Reload** – aplikace je živá na `<vaše_jméno>.pythonanywhere.com`.

---

## Postup nasazení změn (krok za krokem)

Tento postup použij pokaždé, když chceš nahrát aktualizaci na produkci.

### Na lokálním počítači

```bash
# 1. Ulož změny do Gitu
git add .
git commit -m "Popis změny, např. Přidána stránka O anketě"

# 2. Nahraj na GitHub
git push origin main
```

### Na PythonAnywhere

```bash
# 3. Otevři Bash console na PythonAnywhere

# 4. Přejdi do složky projektu
cd ~/anketa

# 5. Stáhni novou verzi z GitHubu
git pull origin main

# 6. Pokud přibyly nové závislosti, doinstaluj je
workon anketa-venv
pip install -r requirements.txt

# 7. Reloadni web app
# BUĎTO klikni tlačítko Reload v záložce Web
# NEBO spusť API příkaz:
touch /var/www/<vaše_jméno>_pythonanywhere_com_wsgi.py
```

> **Tip:** Změna `touch` na WSGI soubor způsobí restart aplikace bez nutnosti klikat v prohlížeči.

### Ověření

8. Otevři `<vaše_jméno>.pythonanywhere.com` v prohlížeči a ověř, že změna je vidět.
9. Zkontroluj **Error log** v záložce Web, pokud aplikace nefunguje.

---

## Reset token

Token je uložen v `config.py`:

```python
RESET_TOKEN = "tajny-token-2026"
```

**Před nasazením na produkci změň token na vlastní tajnou hodnotu.**  
Token zadáš na stránce `/reset`. Bez správného tokenu se hlasy nevynulují.

---

## Monitoring a uptime

Aplikace využívá [UptimeRobot](https://uptimerobot.com/) pro nepřetržité sledování dostupnosti.

### Nastavení UptimeRobot

1. Zaregistruj se zdarma na [uptimerobot.com](https://uptimerobot.com/).
2. Klikni **Add New Monitor**:
   - Type: **HTTP(s)**
   - Friendly Name: `Anketa Telefony`
   - URL: `https://<vaše_jméno>.pythonanywhere.com/`
   - Monitoring Interval: **5 minutes**
3. Nastav **Alert Contact**:
   - E-mail nebo SMS upozornění, když web přestane odpovídat.
4. Uložit → monitor je aktivní.

### Co se stane při výpadku

- UptimeRobot detekuje, že `/` nevrátilo HTTP 200.
- Do 5 minut odešle upozornění na e-mail / SMS.
- Proveď kontrolu chyb v záložce **Error log** na PythonAnywhere.
- Případně restartuj web app kliknutím na **Reload**.

### Diagram monitoringu (součást deployment diagramu výše)

```
UptimeRobot → ping každých 5 min → <vaše_jméno>.pythonanywhere.com
     │
     └─ výpadek → e-mail / SMS → správce → Reload na PythonAnywhere
```

---

## 🌐 Živá aplikace

Aplikace je veřejně přístupná na:

**https://InkaEnFu.pythonanywhere.com**

Stačí otevřít odkaz v prohlížeči – žádná instalace není potřeba.
