# UX Improvements Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Improve user experience by removing upload-order friction, eliminating in-browser JSX compilation for faster page loads, cleaning up debug log noise, and deduplicating session-attachment code.

**Architecture:** Four independent changes applied in order: (1) pre-compile React so later edits target a cleaner `.jsx` source file, (2) fix upload ordering on the extracted source, (3) remove debug prints from backend, (4) deduplicate session code and use the existing factory method.

**Tech Stack:** Flask, React 18 (CDN globals), Babel CLI (`@babel/core`, `@babel/cli`, `@babel/preset-react`), PyMuPDF, pandas

---

## Task 1: Extract JSX into `index_src.jsx` and set up Babel build

**Why first:** All subsequent frontend edits will target `index_src.jsx` instead of the giant `index.html`.

**Files:**
- Create: `templates/index_src.jsx`
- Modify: `templates/index.html` (lines 88–94 CDN scripts, lines 143–5710 inline script block)
- Create: `static/index_built.js` (compiled output)
- Create: `package.json`
- Create: `build.sh`

### Step 1: Install Babel CLI tooling

```bash
cd /mnt/c/Users/Rudi/Documents/GitHub/Annotator
npm init -y
npm install --save-dev @babel/core @babel/cli @babel/preset-react
```

Expected: `package.json` updated, `node_modules/` created.

### Step 2: Extract the JSX source

Run this to pull lines 145–5709 out of `index.html` (between `{% raw %}` and `{% endraw %}`) into the new source file:

```bash
sed -n '145,5709p' templates/index.html > templates/index_src.jsx
```

Verify line count is approximately 5565 lines:
```bash
wc -l templates/index_src.jsx
```

### Step 3: Compile JSX to plain JS

```bash
npx babel templates/index_src.jsx --presets @babel/preset-react -o static/index_built.js
```

Expected: `static/index_built.js` created, no errors. Check:
```bash
wc -l static/index_built.js
head -5 static/index_built.js
```
Expected: file exists, starts with compiled JS (not JSX).

### Step 4: Update `index.html` — replace Babel CDN + inline script

In `templates/index.html`, make these changes:

**4a. Change React CDN scripts from development to production builds** (around lines 91–93):

Old:
```html
  <!-- React + ReactDOM + Babel (for JSX in-browser) -->
  <script crossorigin src="https://unpkg.com/react@18/umd/react.development.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.development.js"></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
```

New:
```html
  <!-- React + ReactDOM (production builds) -->
  <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
  <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
```

**4b. Replace the inline `<script type="text/babel">` block** (lines 143–5710) with a single line:

Old (lines 143–5710):
```html
  <script type="text/babel">
  {% raw %}
    const { useEffect, ...
    ...
    ReactDOM.createRoot(document.getElementById("root")).render(<App />);
  {% endraw %}
  </script>
```

New:
```html
  <script src="/static/index_built.js"></script>
```

Use the Edit tool to make these two changes. Because the file is too large to read into context at once, use bash for the replacement:

```bash
# Replace the babel CDN lines
python3 -c "
import re
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace dev React builds + babel with production builds
old = '''  <!-- React + ReactDOM + Babel (for JSX in-browser) -->
  <script crossorigin src=\"https://unpkg.com/react@18/umd/react.development.js\"></script>
  <script crossorigin src=\"https://unpkg.com/react-dom@18/umd/react-dom.development.js\"></script>
  <script src=\"https://unpkg.com/@babel/standalone/babel.min.js\"></script>'''
new = '''  <!-- React + ReactDOM (production builds) -->
  <script crossorigin src=\"https://unpkg.com/react@18/umd/react.production.min.js\"></script>
  <script crossorigin src=\"https://unpkg.com/react-dom@18/umd/react-dom.production.min.js\"></script>'''
content = content.replace(old, new)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(content)
print('Done: CDN lines replaced')
"
```

```bash
# Replace the inline script block with a static file reference
python3 -c "
import re
with open('templates/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace the entire inline babel script block
pattern = r'  <script type=\"text/babel\">\n  {%[- ]?raw[- ]?%}.*?{%[- ]?endraw[- ]?%}\n  </script>'
replacement = '  <script src=\"/static/index_built.js\"></script>'
new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)

if new_content == content:
    print('ERROR: pattern not matched - check regex')
else:
    with open('templates/index.html', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print('Done: inline script replaced')
"
```

### Step 5: Create `build.sh` for future rebuilds

```bash
cat > build.sh << 'EOF'
#!/bin/bash
# Rebuild the compiled React bundle from source
# Run this after any changes to templates/index_src.jsx
npx babel templates/index_src.jsx --presets @babel/preset-react -o static/index_built.js
echo "Build complete: static/index_built.js"
EOF
chmod +x build.sh
```

### Step 6: Verify the app loads correctly

```bash
python app.py
```

Open `http://localhost:5001` in a browser. Expected:
- Page loads quickly (no Babel transpilation delay)
- UI renders correctly
- React DevTools show no errors in console

### Step 7: Add `node_modules/` to `.gitignore`

```bash
echo "node_modules/" >> .gitignore
```

### Step 8: Commit

```bash
git add templates/index_src.jsx static/index_built.js templates/index.html package.json build.sh .gitignore
git commit -m "perf: pre-compile React JSX, remove in-browser Babel transpilation

Switch from @babel/standalone CDN (285KB transpiled at runtime)
to pre-compiled static bundle. Page load time drops from ~3-5s to <1s.

- Extract JSX to templates/index_src.jsx
- Compile to static/index_built.js via Babel CLI
- Switch to production React/ReactDOM CDN builds
- Add build.sh for rebuilding after JSX changes"
```

---

## Task 2: Fix upload order restriction

**Why:** Users who drop PDFs before Excel get a blocking error. Only processing should require both files — upload should accept any order.

**Files:**
- Modify: `templates/index_src.jsx` (the `validateAndUpload` function, ~line 330)
- After editing, rebuild: `./build.sh`

### Step 1: Find the blocking guard in `index_src.jsx`

```bash
grep -n "Please upload at least one Excel file first" templates/index_src.jsx
```

Note the line number. It will be inside `validateAndUpload()`.

### Step 2: Remove the PDF-blocks-without-Excel guard

Find this block in `validateAndUpload()`:

```javascript
if (!hasExcelInCurrentUpload && !hasExcelAlreadyUploaded && pdfFiles.length > 0) {
  setStatusMsg("error", "Please upload at least one Excel file first");
  logToConsole(
    "Error: No Excel file uploaded, but trying to upload PDFs"
  );
  return;
}
```

Remove it entirely (delete those 7 lines). The remaining guard for "no files at all" stays.

Also find and remove this block (blocks PDFs when nothing is uploaded):
```javascript
if (!hasExcelInCurrentUpload && !hasExcelAlreadyUploaded && pdfFiles.length === 0) {
  setStatusMsg("error", "Please upload at least one Excel file");
  logToConsole("Error: No files to upload");
  return;
}
```

Keep it — this one is correct (empty upload attempt). Only remove the PDF-specific blocking guard.

### Step 3: Find the Process button area and add readiness hint

Search for where `isProcessing` or the process/test-run buttons are rendered:

```bash
grep -n "startProcessing\|isProcessing\|Process\|Test Run" templates/index_src.jsx | head -30
```

Find the process button. Add a readiness warning **above** the button, shown only when PDFs are uploaded but Excel is missing:

```javascript
{/* Readiness hint - shown only when PDFs uploaded but no Excel */}
{workspaceFiles.pdfs.length > 0 && !selectedExcel && (
  <p className="text-sm text-amber-600 dark:text-amber-400 mb-2">
    <i className="fa-solid fa-triangle-exclamation mr-1"></i>
    Excel file needed before processing
  </p>
)}
```

Place this immediately before the process/test-run button group.

### Step 4: Rebuild the compiled bundle

```bash
./build.sh
```

Expected: `static/index_built.js` updated, no errors.

### Step 5: Verify in browser

1. Open `http://localhost:5001`
2. Drag-and-drop a PDF without an Excel file — should upload successfully (no blocking error)
3. Confirm the "Excel file needed before processing" hint appears near the Process button
4. Upload an Excel file — hint should disappear, Process button should become enabled
5. Verify existing flow (Excel then PDF) still works normally

### Step 6: Commit

```bash
git add templates/index_src.jsx static/index_built.js
git commit -m "ux: allow PDF upload before Excel file

Remove strict Excel-first ordering. Users can now upload files in
any order. A soft hint near the Process button replaces the hard
error block when Excel is missing."
```

---

## Task 3: Remove debug print noise from backend

**Files:**
- Modify: `app.py`
- Modify: `pid_annotator/web/processing_routes.py`
- Modify: `pid_annotator/core/preview_generator.py`
- Modify: `pid_annotator/core/pdf_indexer.py`

### Step 1: Remove all DEBUG prints from `app.py`

Current `app.py` has 10 `print("DEBUG: ...")` statements (lines 31, 33, 40, 44, 55, 61, 64, 66, 69, 71, 72).

Remove every line matching `print("DEBUG:` in `app.py`:

```bash
grep -n "DEBUG" app.py
```

Delete each of those lines using the Edit tool. The resulting file should have no print statements — the server init is silent (errors will still surface via Flask's logger).

### Step 2: Remove `[APP DEBUG]` routine prints from `processing_routes.py`

Keep: lines with `[APP ERROR]`, `[APP WARNING]`, `[APP INFO]`, `[APP SUCCESS]`, and the Excel annotation block prints.

Remove: all `[APP DEBUG]` prints that describe normal flow (file selections, validation steps, per-file progress).

```bash
grep -n "\[APP DEBUG\]" pid_annotator/web/processing_routes.py
```

Use the Edit tool to delete each `[APP DEBUG]` print line. Leave all `[APP ERROR]` / `[APP WARNING]` / `[APP SUCCESS]` lines intact.

### Step 3: Trim `preview_generator.py` prints

```bash
grep -n "print(" pid_annotator/core/preview_generator.py
```

Keep only the final summary line:
```python
print(f"[PREVIEW] Preview complete: {color_stats['colored_tags']} colored, {comments_added} comments, {watermarks_added} watermarks")
```

Remove all other `print(` lines in that file (start/progress/phase prints).

### Step 4: Trim `pdf_indexer.py` prints

```bash
grep -n "print(" pid_annotator/core/pdf_indexer.py
```

Keep the two final summary lines:
```python
print(f"Sequential indexing complete. Found {total_tags} tag instances across {len(tag_index)} unique tags.")
print(f"Parallel indexing complete. Found {total_tags} tag instances across {len(tag_index)} unique tags.")
```

Remove all other `print(` calls (e.g. `"Building comprehensive tag index..."`, `"Using tag matching pattern..."`, `"Using parallel indexing..."`, per-bookmark map prints).

### Step 5: Smoke test — start the server, check logs are clean

```bash
python app.py
```

Expected: server starts with **no** `DEBUG:` output. Only Flask's own startup lines appear:
```
 * Running on http://0.0.0.0:5001
```

### Step 6: Commit

```bash
git add app.py pid_annotator/web/processing_routes.py pid_annotator/core/preview_generator.py pid_annotator/core/pdf_indexer.py
git commit -m "chore: remove debug print statements from production code

Remove development-era print() calls that cluttered server logs.
Keep only ERROR, WARNING, SUCCESS, and final-summary prints."
```

---

## Task 4: Deduplicate session code and use `AnnotationConfig.from_request()`

**Files:**
- Modify: `pid_annotator/web/processing_routes.py`

### Step 1: Remove the local duplicate of `try_attach_existing_files_to_session`

```bash
grep -n "def try_attach_existing_files_to_session\|try_attach_existing_files_to_session" pid_annotator/web/processing_routes.py | head -20
```

The function definition is at lines 28–60 of `processing_routes.py`. Delete that entire function definition.

Then update the import at the top of `processing_routes.py` to import it from `session/manager`:

Add to the imports section:
```python
from pid_annotator.session.manager import try_attach_existing_files_to_session
```

However, note that the signature differs slightly. The one in `session/manager.py` takes `(upload_folder, reload_excel_columns_func)` as arguments. The one in `processing_routes.py` used `current_app` directly.

Update each call site in `process_files()` to pass the required arguments:

Old call (used in processing_routes.py):
```python
try_attach_existing_files_to_session()
```

New call:
```python
from pid_annotator.analysis import reload_excel_columns
try_attach_existing_files_to_session(
    current_app.config['UPLOAD_FOLDER'],
    reload_excel_columns
)
```

There are 2 call sites — update both.

### Step 2: Use `AnnotationConfig.from_request()` factory

```bash
grep -n "config = AnnotationConfig(" pid_annotator/web/processing_routes.py
```

Find the `AnnotationConfig(...)` construction block (around lines 380–401). Replace it with:

```python
# Create annotation configuration from request data
config = AnnotationConfig.from_request(data, dict(session))
# Override fields that need computed values from earlier in this function
config.pdf_paths = [pdf_path]
config.excel_path = excel_path
config.output_path = output_path
config.max_tags = max_tags
config.task_id = task_id
config.progress_callback = per_file_progress_cb
```

Note: `AnnotationConfig.from_request()` handles watermark, tag_matching, color_rules, filters, and all other fields from `data`. The overrides above set the file paths and callbacks that are computed at runtime.

### Step 3: Verify `from_request()` covers all needed fields

Check `pid_annotator/config/annotation_config.py` `from_request()` method to confirm it reads:
- `selected_excel` → `excel_path` (we override this anyway)
- `tag_column`, `header_row`, `comment_columns`
- `default_highlight_color`, `enable_default_color`
- `watermark_enabled` + all watermark fields
- `tag_matching_config`
- `tag_filters`, `filter_logic`
- `color_rules`, `column_color_pairs`
- `excel_constraint_mode`, `excel_constraint_logic`
- `annotate_excel`, `annotation_type`

If any field is missing from `from_request()`, add it there (not in the processing route).

### Step 4: Run a full processing test

Start the server and run a complete annotation through the UI (upload Excel + PDF, click Process). Verify:
- Processing completes without errors
- Output PDF is downloadable
- Report is generated

```bash
python app.py
# Open http://localhost:5001, upload files, run processing
```

### Step 5: Commit

```bash
git add pid_annotator/web/processing_routes.py pid_annotator/config/annotation_config.py
git commit -m "refactor: deduplicate session attachment, use AnnotationConfig.from_request()

Remove duplicate try_attach_existing_files_to_session() from processing_routes,
import from session/manager instead. Replace 20+ manual AnnotationConfig field
assignments with AnnotationConfig.from_request() factory method."
```

---

## Final verification

After all 4 tasks:

```bash
python app.py
```

1. Page loads in < 1 second (no Babel spinner)
2. Can upload PDF before Excel without error
3. Server logs are clean — no `DEBUG:` lines
4. Full annotation run completes successfully

---

## Notes for implementer

- `static/index_built.js` **must be committed** — it is the served file, not generated at deploy time
- After any change to `templates/index_src.jsx`, run `./build.sh` and commit the updated `static/index_built.js`
- The `node_modules/` directory is in `.gitignore` and should not be committed
- `AnnotationConfig.from_request()` reads `session_data` as a plain dict — pass `dict(session)` not the Flask session proxy
