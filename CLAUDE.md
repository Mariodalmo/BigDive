# CLAUDE.md

This file provides guidance for AI assistants (Claude and others) working in this repository.

---

## Repository Overview

**BigDive** is a personal learning and experimentation repository by Mariodalmo. It currently contains an educational Jupyter notebook demonstrating how to use Google's **MedGemma** models — Gemma 3 variants fine-tuned for medical tasks — via Hugging Face and Google Colab.

The repository is intentionally minimal and not a production application. There is no CI/CD pipeline, no test framework, and no build configuration.

---

## Repository Structure

```
BigDive/
├── CLAUDE.md                                    # This file
├── file1                                        # Placeholder text file ("ciao sono file 1")
├── file2                                        # Empty placeholder file
└── notebooks/
    └── quick_start_with_hugging_face.ipynb      # Main Jupyter notebook
```

### Key Files

| File | Description |
|------|-------------|
| `notebooks/quick_start_with_hugging_face.ipynb` | Jupyter notebook demonstrating MedGemma inference (image-text and text-only) using Hugging Face Transformers and Google Colab |
| `file1` | Legacy placeholder file with Italian text |
| `file2` | Empty legacy placeholder file |

---

## Notebook: `quick_start_with_hugging_face.ipynb`

### Purpose
Demonstrates end-to-end usage of Google's MedGemma models for medical AI tasks including:
- Radiology image analysis (X-ray interpretation)
- Medical question answering
- Thinking-mode inference (27B variant)

### Model Variants Covered
- `google/medgemma-4b-it` — 4B instruction-tuned multimodal model
- `google/medgemma-27b-it` — 27B instruction-tuned text-only model

### Key Dependencies (installed in notebook cells)
```
accelerate
bitsandbytes
transformers
```

### Environment Variables
| Variable | Purpose |
|----------|---------|
| `HF_TOKEN` | Hugging Face authentication token — **required** to download gated models |
| `HF_HOME` | Optional override for Hugging Face cache directory |
| `VERTEX_PRODUCT` | Auto-detected by notebook to identify Colab Enterprise environment |

### Notebook Conventions
- Uses `# @param` decorators for Colab form-based interactive parameters
- Detects runtime environment (Google Colab vs local) and branches accordingly
- Uses 4-bit quantization (`bitsandbytes`) for the 27B model to reduce VRAM requirements
- Role-based system prompts (e.g., radiologist, medical assistant) are passed as conversation context
- Supports both `pipeline` API and direct `model.generate()` inference

---

## Git Workflow

### Branch Convention
The active development branch follows the pattern:
```
claude/<task-identifier>
```
Current development branch: `claude/claude-md-mm4z1glacecxr4m1-8muYH`

### Commit History (as of 2026-02-27)
| Hash | Message | Date |
|------|---------|------|
| `4f33d0d` | "Creato con Colab" | 2025-08-20 |
| `267d6be` | "wow" | 2019-03-25 |
| `577cbb2` | "file modificato" | 2019-03-25 |
| `3bd63f9` | "aggiunto file1" | 2019-03-25 |

### Git Practices for AI Assistants
- Always develop on the designated `claude/` branch — never push directly to `master`
- Use `git push -u origin <branch-name>` when pushing
- Commit messages should be clear and descriptive (the existing history uses Italian; either language is acceptable)

---

## Development Workflow

Since there is no build system, test runner, or linter configured, the workflow is straightforward:

### Adding or Editing Notebooks
1. Edit `.ipynb` files directly (JSON format) or open them in JupyterLab/VS Code
2. Clear cell outputs before committing to keep diffs readable
3. Ensure any new cells that install packages use `!pip install` with pinned versions where stability matters

### Running the Notebook Locally
1. Set `HF_TOKEN` in your environment:
   ```bash
   export HF_TOKEN=your_hugging_face_token
   ```
2. Install dependencies:
   ```bash
   pip install accelerate bitsandbytes transformers
   ```
3. Launch Jupyter:
   ```bash
   jupyter notebook notebooks/quick_start_with_hugging_face.ipynb
   ```
4. For the 27B model, a GPU with sufficient VRAM is required (4-bit quantization reduces the requirement significantly)

### Running on Google Colab
The notebook is designed to run as-is on Google Colab. Open it via:
- File > Upload notebook, or
- Direct Colab link from the GitHub repository

---

## Conventions and Patterns

### Code Style (Notebook)
- Python 3 compatible code throughout
- Type hints used where appropriate (e.g., `bool`, `str` for `@param` annotations)
- Environment detection guards execution blocks (e.g., checking `IN_COLAB` before Colab-specific operations)
- Markdown cells used liberally to explain concepts

### Language
- Repository commit messages may be in Italian or English
- Notebook content and code are in English

---

## What This Repository Is Not

- Not a production application
- Not a library or installable package
- Not a tested codebase — there are no unit/integration tests
- Not a containerized application — no Dockerfile or docker-compose

---

## Future Development Areas

If this repository grows, consider adding:
- `requirements.txt` or `pyproject.toml` for dependency management
- A `README.md` with project overview and quickstart
- `.gitignore` to exclude Jupyter checkpoint files (`**/.ipynb_checkpoints/`)
- Additional notebooks for other medical AI experiments
