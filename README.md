# AI Act Risk Assessment Toolkit

A minimal toolkit to assess AI systems per EU AI Act and generate a Markdown report.

## Quick start

```bash
python -m ai_act_risk.cli \
  --input examples/recruitment.json \
  --output examples/recruitment_report.md \
  --dump-json
```

---

# Generatore configurazioni Color Grading per DaVinci Resolve

Questo repository include anche un assistente per i colorist che:

- offre preset curati (Cinema orientale, Wes Anderson, B&W analogico, Kubrick, Fellini);
- descrive le condizioni di partenza del girato (LogC, S-Log3, Rec.709, ecc.);
- crea una configurazione completa dei nodi di DaVinci Resolve;
- può generare una LUT `.cube` coerente con i parametri calcolati.

## Elenca i preset

```bash
python -m resolve_grading.cli list-presets
python -m resolve_grading.cli list-presets --format json
```

## Genera configurazione + LUT

```bash
python -m resolve_grading.cli generate \
  --preset wes_anderson \
  --footage-json examples/footage_slog3.json \
  --timeline-gamma "DaVinci Intermediate" \
  --timeline-gamut "DaVinci Wide Gamut" \
  --output-transform "Rec.709 Gamma 2.4" \
  --output-json /tmp/wes_anderson_config.json \
  --lut-path /tmp/wes_anderson.cube
```

Il JSON contiene:

- profilo del girato (gamma, gamut, camera, WB, ISO, condizioni di luce);
- nodi suggeriti (CST input, Primaries, Contrasto, Palette, Texture, Output, Note creative) con parametri dettagliati;
- note operative e raccomandazioni sui formati di partenza;
- metadati della LUT (dimensione, regolazioni incluse, percorso). Se non si fornisce `--lut-path`, la LUT viene restituita inline nel JSON.

## Override veloci

Si possono sovrascrivere parametri dei preset con `--custom`, anche in chiavi annidate:

```bash
python -m resolve_grading.cli generate \
  --preset fellini \
  --capture-gamma "Rec.709" \
  --capture-gamut "Rec.709" \
  --custom contrast=1.05 \
  --custom split_tone_highlights.hue=32
```

## Esempi

- `examples/footage_slog3.json`: profilo pronto per girato Sony S-Log3, utilizzabile con `--footage-json`.

## UI interattiva (Streamlit)

Per utilizzare un'interfaccia visuale:

```bash
pip install streamlit
streamlit run streamlit_app.py
```

La UI consente di:

- scegliere rapidamente il preset e consultare note/look raccomandati;
- impostare profilo del girato e parametri timeline tramite form;
- inserire override JSON per modificare qualsiasi parametro del preset;
- scaricare il JSON della configurazione e la LUT `.cube` con un click.
