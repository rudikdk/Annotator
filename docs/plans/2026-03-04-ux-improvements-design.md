# UX Improvements Design — Approach A

**Date:** 2026-03-04
**Author:** Rudi S. Kærgaard

---

## Goal

Improve user experience and simplify the application without losing any features. Four targeted changes with low regression risk.

---

## Section 1: Upload Order Fix

**Problem:** The frontend enforces strict upload ordering — Excel must be uploaded before PDF. Users who drop PDFs first get a blocking error.

**Solution:**
- Accept PDF and Excel uploads in any order (including together via drag-and-drop)
- Remove the `!hasExcelAlreadyUploaded` guard that blocks PDF uploads
- Replace with a soft readiness hint near the Process button: *"Excel file needed before processing"*
- Process button remains disabled until both PDF(s) and Excel are present — the only enforcement point

**Files:**
- `templates/index.html` — `validateAndUpload()` function

---

## Section 2: Pre-compile React/Babel

**Problem:** Page loads `@babel/standalone` from CDN and transpiles 285KB of JSX in the browser on every page load, causing a 3–5 second blank screen before the UI is interactive.

**Solution:**
- Split the monolithic `index.html` into source and compiled parts:
  - `templates/index_src.jsx` — React source (extracted from the inline `<script type="text/babel">` block)
  - `static/index_built.js` — pre-compiled output (committed to repo)
  - `templates/index.html` — HTML shell, loads `index_built.js` as a static file
- Remove CDN loads for `@babel/standalone`
- Switch from `react.development.js` to `react.production.min.js` and `react-dom.production.min.js`
- Add `package.json` with `@babel/core`, `@babel/cli`, `@babel/preset-react` as dev dependencies
- Add `build.sh` script for rebuilding the compiled output

**Development workflow:**
```bash
npm install
npx babel templates/index_src.jsx --presets @babel/preset-react -o static/index_built.js --watch
```

**Files:**
- `templates/index.html` — HTML shell only
- `templates/index_src.jsx` — new (extracted React source)
- `static/index_built.js` — new (compiled output, committed)
- `package.json` — new (dev dependencies)
- `build.sh` — new (build script)

---

## Section 3: Remove Debug Print Noise

**Problem:** Development-era `print("DEBUG: ...")` and `print("[APP DEBUG]")` statements left in production code clutter server logs and slow I/O.

**Solution:**
- `app.py`: Remove all 10 `print("DEBUG: ...")` init messages
- `processing_routes.py`: Remove `[APP DEBUG]` routine-flow prints; keep `[APP ERROR]`, `[APP WARNING]`, and Excel annotation result logs
- `preview_generator.py`: Remove per-page `[PREVIEW]` prints; keep final summary
- `pdf_indexer.py`: Keep final "indexing complete" summary; remove per-chunk progress prints

**Files:**
- `app.py`
- `pid_annotator/web/processing_routes.py`
- `pid_annotator/core/preview_generator.py`
- `pid_annotator/core/pdf_indexer.py`

---

## Section 4: Code Deduplication & Factory Method

**Problem:**
1. `try_attach_existing_files_to_session()` is duplicated in both `processing_routes.py` and `session/manager.py`
2. `AnnotationConfig.from_request()` factory method exists but is never used — `processing_routes.py` manually constructs `AnnotationConfig` with 20+ assignments

**Solution:**
- Remove the duplicate `try_attach_existing_files_to_session()` from `processing_routes.py`; import from `session/manager.py`
- Replace manual `AnnotationConfig(...)` construction with `AnnotationConfig.from_request(data, session)`

**Files:**
- `pid_annotator/web/processing_routes.py`

---

## Summary

| Section | User-visible impact | Risk |
|---------|-------------------|------|
| Upload order fix | High — removes confusing error | Low |
| Pre-compile React | High — instant page load | Medium |
| Remove debug prints | Low — cleaner logs | Low |
| Deduplication | None — maintenance only | Low |
