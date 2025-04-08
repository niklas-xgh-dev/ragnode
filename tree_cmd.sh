tree -I "venv|__pycache__|*.pyc"

#
#ragnode/
#├── app/
#│   ├── static/
#│   │   ├── favicon.svg
#│   │   ├── logo.svg
#│   │   ├── logo_v2.svg
#│   │   ├── gradio_force_theme.js  
#│   │   └── styles.css
#│   ├── svelte/
#│   │   ├── src/
#│   │   │   ├── App.svelte
#│   │   │   ├── BotCard.svelte
#│   │   │   └── Navigation.svelte
#│   │   ├── package.json
#│   │   ├── tailwind.config.js
#│   │   └── vite.config.js
#│   ├── config/
#│   │   └── bots/
#│   │       ├── aoe2-wizard-config.yaml
#│   │       ├── badener-config.yaml
#│   │       ├── diamond-hands-config.yaml
#│   │       └── dr-house-config.yaml
#│   ├── knowledge/
#│   │   ├── aoe2-wizard.yaml
#│   │   ├── badener.yaml
#│   │   └── diamond-hands.yaml
#│   ├── chat.py       # Combined chat functionality
#│   ├── database.py   # Database models and connection
#│   └── utils.py      # Helper functions
#├── main.py           # FastAPI application
#├── requirements.txt
#└── Dockerfile