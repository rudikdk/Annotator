# PID Annotator

> Automatically find and highlight components from Excel spreadsheets in your PDF documents

A web-based tool that matches tags and component identifiers from Excel spreadsheets against PDF documents, automatically highlighting matches and adding annotations. Perfect for P&ID (Piping & Instrumentation Diagram) documents, technical drawings, and component tracking.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker)](https://www.docker.com/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org/)

---

## 📋 Overview

PID Annotator bridges the gap between Excel component lists and PDF technical documents. Instead of manually searching through hundreds of pages to find specific components, simply upload your files and let the tool do the work.

**What it does:**
1. You provide a PDF document and an Excel spreadsheet with component tags
2. The tool automatically finds every tag mentioned in the Excel file within the PDF
3. It highlights the found tags and adds annotations with your notes
4. You download the annotated PDF (and optionally an updated Excel file)

**Perfect for:**
- Engineering teams managing P&ID documents
- Project managers tracking component lists
- Quality assurance teams verifying documentation
- Anyone working with technical drawings and component databases

---

## ✨ Features

### Core Functionality
- **🎯 Automatic Tag Matching** - Finds component tags in PDFs using your Excel data
- **🖍️ Smart Highlighting** - Visually highlights matched tags with colored boxes
- **📝 Annotation Notes** - Adds popup notes with information from your Excel file
- **📊 Excel Feedback** - Marks which tags were found in the Excel file (optional)
- **🏷️ Custom Watermarks** - Add watermarks to annotated pages (optional)

### User Experience
- **🌐 Web-Based Interface** - No software installation needed, use from any browser
- **📱 Drag-and-Drop Upload** - Easy file uploads with progress tracking
- **⚡ Real-Time Progress** - Watch as your documents are processed
- **🎨 Dark Mode** - Easy on the eyes with automatic theme switching
- **📦 Multi-File Support** - Process multiple PDFs with one Excel file

### Performance
- **🚀 Fast Processing** - Handles documents of any size efficiently
- **💾 Smart Memory Management** - Optimized for both small and large files
- **🔄 Parallel Processing** - Multi-core support for faster results
- **📈 Progress Tracking** - Real-time updates on processing status

---
Demo site : https://rudisk.com

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# 1. Download the application
git clone https://github.com/rudikdk/pid-annotator.git
cd pid-annotator

# 2. Start the application
docker-compose up -d

# 3. Open your browser
# Go to: http://localhost:5001
```

That's it! The application is now running and ready to use.

---

## 📥 Installation

### Prerequisites

**Option 1: Docker (Easiest)**
- [Docker Desktop](https://www.docker.com/products/docker-desktop) installed
- 2GB of free disk space

**Option 2: Local Installation**
- Python 3.11 or higher
- 1GB of free disk space

### Docker Installation (Recommended)

1. **Install Docker Desktop**
   - Download from [docker.com](https://www.docker.com/products/docker-desktop)
   - Follow the installation instructions for your operating system
   - Verify installation: Open terminal/command prompt and type `docker --version`

2. **Download PID Annotator**
   ```bash
   git clone https://github.com/rudikdk/pid-annotator.git
   cd pid-annotator
   ```

3. **Start the Application**
   ```bash
   docker-compose up -d
   ```

4. **Access the Application**
   - Open your web browser
   - Go to: `http://localhost:5001`

5. **Stop the Application** (when done)
   ```bash
   docker-compose down
   ```

### Local Installation (Advanced)

```bash
# 1. Download the application
git clone https://github.com/rudikdk/pid-annotator.git
cd pid-annotator

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start the application
python app.py

# 4. Open browser to http://localhost:5001
```

### Raspberry Pi 5 Installation

See [RASPBERRY_PI_QUICKSTART.md](RASPBERRY_PI_QUICKSTART.md) for detailed Raspberry Pi setup instructions.

---

## 📖 How to Use

### Step-by-Step Guide

#### 1. Prepare Your Files

**Excel File Requirements:**
- Must contain a column with component tags (e.g., "TAG-001-A", "PUMP-123")
- Can include additional columns with descriptions, notes, or metadata
- Typical format:

  | Tag ID    | Description           | Location | Notes           |
  |-----------|-----------------------|----------|-----------------|
  | TAG-001-A | Main Pump            | Room 1   | Check quarterly |
  | VALVE-123 | Safety Relief Valve  | Room 2   | Annual test     |
  | PUMP-456  | Backup Water Pump    | Room 3   | Monthly check   |

**PDF File:**
- Any PDF document containing the tags you want to find
- Can be technical drawings, P&IDs, schematics, or any document with text

#### 2. Upload Your Files

1. Open the application in your browser (`http://localhost:5001`)
2. **Upload PDF(s):**
   - Click "Select PDF files" or drag-and-drop your PDF(s)
   - You can upload one or multiple PDF files at once
3. **Upload Excel File:**
   - Click "Select Excel file" or drag-and-drop your Excel file
   - Only one Excel file per session

#### 3. Configure Settings

**Basic Settings:**
- **Header Row:** Which row contains your column names (default: 6)
- **Tag Column:** Which column contains the component tags
- **Comment Columns:** Additional columns to include in annotations (optional)

**Advanced Options:**
- **Add Watermarks:** Include watermark on annotated pages
- **Annotate Excel:** Mark found tags in the Excel file with green highlighting

#### 4. Process Documents

1. Click the **"Process Files"** button
2. Watch the real-time progress bar
3. Processing time varies based on:
   - Number of pages in PDF(s)
   - Number of tags in Excel
   - Your computer's performance
   - Typical: 10-page PDF = ~5-10 seconds

#### 5. Download Results

Once processing completes:
- **Annotated PDF(s)** - Click to download highlighted PDF(s)
- **Annotated Excel** - Click to download (if Excel annotation was enabled)
- **Processing Report** - Detailed summary of what was found

### Example Workflow

```
Excel File (components.xlsx)
┌─────────────┬────────────────┬──────────┐
│ Tag ID      │ Description    │ Notes    │
├─────────────┼────────────────┼──────────┤
│ PUMP-001-A  │ Main Pump     │ Annual   │
│ VALVE-123   │ Safety Valve  │ Monthly  │
└─────────────┴────────────────┴──────────┘
                     ↓
              Upload to PID Annotator
                     ↓
         ┌───────────────────────┐
         │   Processing...       │
         │   Finding tags...     │
         │   Adding highlights...│
         │   Creating notes...   │
         └───────────────────────┘
                     ↓
    Annotated PDF (drawing_annotated.pdf)
    ┌─────────────────────────────────┐
    │ [PUMP-001-A] ← Highlighted box  │
    │              ← Popup note       │
    │ [VALVE-123]  ← Highlighted box  │
    │              ← Popup note       │
    └─────────────────────────────────┘
                     ↓
                Download!
```

---

## 💡 Tips & Best Practices

### For Best Results

1. **Excel Preparation:**
   - Keep tag IDs consistent (e.g., all uppercase or lowercase)
   - Avoid special characters in tag columns
   - Remove empty rows between data

2. **PDF Quality:**
   - Use PDFs with searchable text (not scanned images)
   - Ensure text is not password-protected
   - Higher resolution PDFs work better

3. **Tag Formats:**
   - Supported formats: `A-B-C`, `A.B.C`, `TAG-001`, `PUMP_123`
   - Tags should be 3-5 parts separated by `-`, `.`, or `_`
   - Example valid tags: `PUMP-001-A`, `V.123.B`, `TAG_1_2_3`

4. **Performance:**
   - Smaller PDFs (< 50 pages) process fastest
   - Larger PDFs automatically use optimized processing mode
   - Close unnecessary browser tabs to free up memory

### Common Questions

**Q: What file formats are supported?**
- PDF: Any standard PDF with searchable text
- Excel: .xlsx, .xls

**Q: How large can my files be?**
- PDF: Up to 100MB per file
- Excel: Up to 10MB
- Contact support for larger files

**Q: Will my files be stored?**
- Files are automatically deleted after 24 hours
- Your files never leave your local machine when using Docker

**Q: Can I process multiple PDFs at once?**
- Yes! Upload multiple PDFs and process them all with one Excel file

**Q: What if tags aren't found?**
- Check that tags match exactly (case-insensitive)
- Verify the PDF has searchable text (not just images)
- Review the processing report for details

**Q: Can I run this on my own machine?**
- Yes! The source code is available on GitHub for free: [github.com/rudikdk/Annotator](https://github.com/rudikdk/Annotator)
- You can clone the repository and run it locally with Docker or Python
- Perfect for local deployments, private use, or customization
- Full setup instructions available in the [Local Installation](#local-installation) section

---

## 🔧 Requirements

### System Requirements

**Minimum:**
- 2GB RAM
- 1GB free disk space
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection (for initial Docker download)

**Recommended:**
- 4GB RAM or more
- 2GB free disk space
- Multi-core processor for faster processing

### Software Requirements

**Using Docker:**
- Docker Desktop 20.10+ or Docker Engine + Docker Compose
- No other software needed

**Local Installation:**
- Python 3.11 or higher
- pip (Python package manager)
- Web browser

### Supported Platforms

- ✅ macOS 11+
- ✅ Linux (Ubuntu 20.04+, Debian 11+)
- ✅ Raspberry Pi 5 (4GB or 8GB model) - Primary deployment target

---

## 🏗️ Technical Architecture

### How It Works

```
┌─────────────┐
│   Upload    │ → User uploads PDF(s) and Excel file
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Extract   │ → Extract all tags from Excel file
│    Tags     │ → Build searchable tag index
└──────┬──────┘
       │
       ↓
┌─────────────┐
│   Search    │ → Search PDF for each tag
│     PDF     │ → Record positions and page numbers
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Annotate   │ → Add highlighting boxes to PDF
│     PDF     │ → Create popup annotations with notes
└──────┬──────┘
       │
       ↓
┌─────────────┐
│  Download   │ → User downloads annotated files
└─────────────┘
```

### Built With

- **Backend:** Flask (Python web framework)
- **Frontend:** React 18 with TailwindCSS
- **PDF Processing:** PyMuPDF (fitz), ReportLab, PyPDF2
- **Excel Processing:** openpyxl
- **Real-Time Updates:** Flask-SocketIO
- **Deployment:** Docker, Gunicorn

### Modular Architecture

The application has been refactored into a clean, modular structure:

**Before:** 3 monolithic files (5,339+ lines)
- `pid_annotator_core.py` - 2,211 lines
- `report_template.py` - 3,037 lines
- `app.py` - massive routes file

**After:** 8 focused packages with 25+ specialized modules
- `pid_annotator/core/` - PDF and Excel processing
- `pid_annotator/config/` - Centralized configuration with AnnotationConfig
- `pid_annotator/tag_engine/` - Tag parsing and filtering
- `pid_annotator/reports/` - Report generation
- `pid_annotator/web/` - Flask blueprints for routes
- `pid_annotator/analysis/` - Excel analysis tools
- `pid_annotator/session/` - Session and file management
- `pid_annotator/utils/` - Shared utilities

**Key Benefits:**
- 96% reduction in app.py (91 lines vs thousands)
- Single-responsibility modules for easier maintenance
- AnnotationConfig dataclass eliminates parameter passing chaos
- Backward-compatible wrappers maintain existing functionality

See [REFACTORING.md](REFACTORING.md) for complete refactoring details.

---

## 🐳 Docker Details

### Default Configuration

```yaml
Container: pid-annotator-web
Port: 5001
Memory: 2GB (adjustable)
CPU: 2 cores (adjustable)
Storage: Persistent volumes for uploads/output
```

### Custom Port Configuration

Change the external port while keeping internal port at 5001:

```yaml
# In docker-compose.yml
ports:
  - "9000:5001"  # Use external port 9000
```

Then access at: `http://localhost:9000`

### Volume Management

Files are stored in persistent volumes:
- `./persistent_uploads` - Uploaded files (auto-cleaned after 24h)
- `./persistent_output` - Generated annotated files (auto-cleaned after 24h)
- `./data` - Configuration profiles (persistent)

### Useful Docker Commands

```bash
# View logs
docker-compose logs -f pid-annotator

# Restart container
docker-compose restart

# Stop and remove
docker-compose down

# Rebuild after code changes
docker-compose up -d --build

# Check container status
docker ps

# View resource usage
docker stats pid-annotator-web
```

---

## 🤝 Contributing

Contributions are welcome! Whether it's:
- 🐛 Bug reports
- 💡 Feature requests
- 📝 Documentation improvements
- 🔧 Code contributions

Please open an issue or pull request on GitHub.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**You are free to:**
- ✅ Use commercially
- ✅ Modify
- ✅ Distribute
- ✅ Use privately

**Under the condition that:**
- 📋 License and copyright notice are included

---

## 👤 Author

**Rudi S. Kærgaard**
- Email: rudikdk@gmail.com
- GitHub: [@rudikdk](https://github.com/rudikdk)

---

## 🙏 Acknowledgments

- Built with Python and Flask
- PDF processing powered by PyMuPDF
- UI components from TailwindCSS
- Icons from Heroicons

---

## 📚 Additional Documentation

- [Raspberry Pi Quick Start](RASPBERRY_PI_QUICKSTART.md) - Raspberry Pi 5 deployment guide
- [Developer Guide](CLAUDE.md) - Technical documentation for developers
- [Refactoring Details](REFACTORING.md) - Architecture transformation documentation

---

## 🆘 Getting Help

**Having issues?**

1. Check the [Common Questions](#common-questions) section above
2. Review the logs: `docker-compose logs pid-annotator`
3. Open an issue on GitHub with:
   - Description of the problem
   - Steps to reproduce
   - Screenshots if applicable
   - Your system information (OS, Docker version)

**Found a bug?**
Please report it on GitHub Issues with as much detail as possible.

---

## 🗺️ Roadmap

**Upcoming Features:**
- [ ] Support for scanned PDFs (OCR)
- [ ] Batch processing API
- [ ] Custom tag matching rules
- [ ] Export to different formats
- [ ] Integration with cloud storage
- [ ] Mobile-responsive UI improvements

**Have a feature request?** Open an issue on GitHub!

---

<div align="center">

**Made with ❤️ for engineers and technical teams**

[⭐ Star on GitHub](https://github.com/rudikdk/pid-annotator) | [📖 Documentation](CLAUDE.md) | [🐛 Report Bug](https://github.com/rudikdk/pid-annotator/issues)

</div>


