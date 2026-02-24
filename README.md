# Solver simbólico (SymPy + Flask + Vercel)

Aplicación web en Python para resolver ecuaciones individuales o sistemas de ecuaciones de forma simbólica usando SymPy.

## Características

- Entrada de ecuaciones en una caja de texto (una por línea).
- Soporte para ecuaciones con `=` y expresiones sin `=` (se interpretan como `expresión = 0`).
- Incógnitas opcionales (`x, y, z`); si no se especifican, se deducen automáticamente.
- Resultados renderizados en LaTeX con MathJax.
- Lista para despliegue en Vercel.

## Ejecutar localmente

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 api/index.py
```

Abre `http://localhost:8000`.

## Desplegar en Vercel

1. Instala/actualiza CLI de Vercel y autentícate:
   ```bash
   npm i -g vercel
   vercel login
   ```
2. Desde la raíz del proyecto:
   ```bash
   vercel
   ```
3. Para producción:
   ```bash
   vercel --prod
   ```

## Formato de entrada recomendado

```text
x + y = 5
2*x - y = 1
```

Variables opcionales:

```text
x, y
```
