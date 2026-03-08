const {
  useEffect,
  useMemo,
  useRef,
  useState
} = React;

// UI helpers
function cx(...classes) {
  return classes.filter(Boolean).join(" ");
}

// Help content for all features
const HELP_CONTENT = {
  headerRow: "Specify which row in your Excel file contains the column headers. The application will read column names from this row. Default is row 6, but adjust to match your file structure.",
  tagColumn: "Select the Excel column containing your component identifiers (tags). These tags will be searched for in your PDF files. Examples: TAG-001-A, SYS.PUMP.01, A.B.C",
  commentColumns: "Choose which Excel columns to include as annotations in the PDF. Selected columns will appear as notes attached to each found tag. Useful for adding descriptions, specifications, or notes.",
  excelAnnotation: "When enabled, the application highlights Excel rows (with green fill) where tags were successfully found in the PDF. Only works with .xlsx files. Helps you identify which components were located.",
  watermark: "Add text labels near tags in the PDF using values from your Excel file. Choose which attribute columns to display, customize text color, and optionally add a white background for better readability.",
  conditionalHighlighting: "Highlight only tags where a specific Excel column has a value. For example, select 'Critical' column to highlight only critical components. Combine with color rules for advanced filtering.",
  configurationProfiles: "Save and reuse all your settings across sessions, including color rules and tag filters. Export profiles as JSON files to share or back up, and import them on any device. Your settings auto-save to your browser.",
  tagFilters: "Control which tags get processed by creating include/exclude rules based on tag structure or Excel column values. Combine multiple filters with AND/OR logic to precisely target the tags you need.",
  customTagMatching: "Customize how tags are identified in PDFs. Choose from presets (Default for standard tags, Match All for any text) or create custom patterns with configurable separators, part counts, and lengths.",
  colorRules: "Apply different highlight colors based on tag structure or Excel column values. Create rules to match specific tag parts or column criteria, set priority order, and use default colors for unmatched tags.",
  testRun: "Process only the first 100 tags from your Excel file to quickly verify your configuration before running the full job. Perfect for testing color rules, filters, and settings without processing thousands of tags.",
  startProcessing: "Begin full processing of all selected PDFs with all tags from your Excel file. The application will search for tags, apply highlights, add annotations, and generate watermarks if enabled.",
  fileWorkspace: "Manage all your files in one place. Upload PDFs and Excel/CSV files, select which files to process, and reuse annotated outputs as inputs. Files persist across sessions until you clear the workspace."
};

/**
 * HelpIcon Component
 *
 * A reusable help icon that displays a tooltip on hover (desktop) or click (mobile)
 * with keyboard accessibility support. Uses fixed positioning to avoid clipping by parent containers.
 */
function HelpIcon({
  content,
  position = 'top'
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const [tooltipPos, setTooltipPos] = useState({
    top: 0,
    left: 0
  });
  const buttonRef = useRef(null);
  const tooltipRef = useRef(null);

  // Detect mobile devices
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.matchMedia('(max-width: 768px)').matches || 'ontouchstart' in window);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Calculate tooltip position for fixed positioning
  const calculatePosition = () => {
    if (!buttonRef.current || !tooltipRef.current) return;
    const buttonRect = buttonRef.current.getBoundingClientRect();
    const tooltipRect = tooltipRef.current.getBoundingClientRect();
    const gap = 12;
    let top = 0,
      left = 0;
    if (position === 'top') {
      top = buttonRect.top - tooltipRect.height - gap;
      left = buttonRect.left + buttonRect.width / 2 - tooltipRect.width / 2;
    } else if (position === 'bottom') {
      top = buttonRect.bottom + gap;
      left = buttonRect.left + buttonRect.width / 2 - tooltipRect.width / 2;
    } else if (position === 'left') {
      top = buttonRect.top + buttonRect.height / 2 - tooltipRect.height / 2;
      left = buttonRect.left - tooltipRect.width - gap;
    } else if (position === 'right') {
      top = buttonRect.top + buttonRect.height / 2 - tooltipRect.height / 2;
      left = buttonRect.right + gap;
    }

    // Adjust for viewport boundaries
    const padding = 8;
    if (left < padding) left = padding;
    if (left + tooltipRect.width > window.innerWidth - padding) {
      left = window.innerWidth - tooltipRect.width - padding;
    }
    if (top < padding) top = padding;
    if (top + tooltipRect.height > window.innerHeight - padding) {
      top = window.innerHeight - tooltipRect.height - padding;
    }
    setTooltipPos({
      top,
      left
    });
  };

  // Update position when tooltip opens
  useEffect(() => {
    if (isOpen) {
      calculatePosition();
      window.addEventListener('scroll', calculatePosition);
      window.addEventListener('resize', calculatePosition);
      return () => {
        window.removeEventListener('scroll', calculatePosition);
        window.removeEventListener('resize', calculatePosition);
      };
    }
  }, [isOpen, position]);

  // Close tooltip when clicking outside
  useEffect(() => {
    if (!isMobile || !isOpen) return;
    function handleClickOutside(event) {
      if (buttonRef.current && !buttonRef.current.contains(event.target) && tooltipRef.current && !tooltipRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('touchstart', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('touchstart', handleClickOutside);
    };
  }, [isOpen, isMobile]);
  const handleToggle = e => {
    e.stopPropagation();
    if (isMobile) {
      setIsOpen(!isOpen);
    }
  };
  const handleKeyDown = e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      e.stopPropagation();
      setIsOpen(!isOpen);
    } else if (e.key === 'Escape' && isOpen) {
      setIsOpen(false);
    }
  };
  return /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    ref: buttonRef,
    type: "button",
    onClick: handleToggle,
    onKeyDown: handleKeyDown,
    className: cx("inline-flex items-center justify-center", "h-5 w-5 rounded-full", "border border-brand/30 text-brand/50 dark:border-brand/20 dark:text-brand/40 hover:border-brand hover:text-brand dark:hover:border-brand dark:hover:text-brand", "transition-all duration-200", "focus:outline-none focus:ring-2 focus:ring-brand/50 focus:ring-offset-2", "dark:focus:ring-offset-zinc-900", "cursor-help", "ml-1.5", "flex-shrink-0", "text-xs font-medium leading-none"),
    "aria-label": "Help information",
    "aria-expanded": isOpen,
    tabIndex: 0,
    onMouseEnter: () => !isMobile && setIsOpen(true),
    onMouseLeave: () => !isMobile && setIsOpen(false)
  }, "?"), isOpen && /*#__PURE__*/React.createElement("div", {
    ref: tooltipRef,
    className: "fixed z-50 w-64 sm:w-72 pointer-events-auto",
    style: {
      top: `${tooltipPos.top}px`,
      left: `${tooltipPos.left}px`,
      animation: 'fadeIn 0.15s ease-in'
    },
    role: "tooltip"
  }, /*#__PURE__*/React.createElement("div", {
    className: "relative"
  }, /*#__PURE__*/React.createElement("div", {
    className: cx("rounded-lg px-3 py-2.5", "bg-zinc-800 dark:bg-zinc-200", "text-zinc-100 dark:text-zinc-900", "text-xs leading-relaxed", "shadow-lg border border-zinc-700 dark:border-zinc-300")
  }, content))));
}
function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  useEffect(() => {
    if (dark) {
      document.documentElement.classList.add("dark");
      localStorage.setItem("theme", "dark");
    } else {
      document.documentElement.classList.remove("dark");
      localStorage.setItem("theme", "light");
    }
  }, [dark]);
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => setDark(d => !d),
    className: "inline-flex items-center gap-2 rounded-full bg-zinc-200/60 dark:bg-zinc-800 px-3 py-1.5 text-sm font-medium hover:scale-105 active:scale-95 transition-transform duration-200",
    "aria-label": "Toggle theme"
  }, /*#__PURE__*/React.createElement("i", {
    className: cx("fa-solid", dark ? "fa-moon" : "fa-sun")
  }), /*#__PURE__*/React.createElement("span", null, dark ? "Dark" : "Light"));
}
function DeleteBrowserDataButton() {
  const handleDeleteData = () => {
    const confirmed = window.confirm("This will delete all saved browser data for this app (settings, preferences, cache). This action cannot be undone. Are you sure?");
    if (!confirmed) {
      return;
    }
    try {
      // Clear localStorage
      localStorage.clear();

      // Clear sessionStorage
      sessionStorage.clear();

      // Show success message
      alert("Browser data deleted successfully. The page will now reload.");

      // Reload the page
      window.location.reload();
    } catch (error) {
      console.error("Error deleting browser data:", error);
      alert("Error deleting browser data. Please try again.");
    }
  };
  return /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: handleDeleteData,
    className: "inline-flex items-center gap-2 rounded-full bg-zinc-200/60 dark:bg-zinc-800 px-3 py-1.5 text-sm font-medium hover:scale-105 active:scale-95 transition-transform duration-200",
    "aria-label": "Delete browser data",
    title: "Delete all saved browser data"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-trash"
  }), /*#__PURE__*/React.createElement("span", null, "Clear Data"));
}
function Header() {
  return /*#__PURE__*/React.createElement("header", {
    className: "sticky top-0 z-30 backdrop-blur bg-white/70 dark:bg-zinc-900/70 border-b border-zinc-200/60 dark:border-zinc-800"
  }, /*#__PURE__*/React.createElement("div", {
    className: "mx-auto max-w-6xl px-4 sm:px-6"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex h-16 items-center justify-between"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex h-10 w-10 items-center justify-center rounded-xl bg-brand/10 text-brand"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-file-pdf text-lg"
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "text-lg sm:text-xl font-semibold tracking-tight"
  }, "PID Annotator"), /*#__PURE__*/React.createElement("div", {
    className: "text-xs sm:text-sm text-zinc-500 dark:text-zinc-400"
  }, "Annotate PDF files using Excel data"))), /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2"
  }, /*#__PURE__*/React.createElement(DeleteBrowserDataButton, null), /*#__PURE__*/React.createElement(ThemeToggle, null)))));
}
function SectionCard({
  title,
  children,
  right
}) {
  const [open, setOpen] = useState(true);
  return /*#__PURE__*/React.createElement("section", {
    className: "rounded-xl bg-white dark:bg-zinc-950/60 border border-zinc-200/60 dark:border-zinc-800 shadow-soft"
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => setOpen(o => !o),
    className: "w-full flex items-center justify-between gap-3 px-4 sm:px-6 py-3 border-b border-zinc-200/60 dark:border-zinc-800",
    "aria-expanded": open
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-3"
  }, /*#__PURE__*/React.createElement("i", {
    className: cx("fa-solid text-brand", open ? "fa-chevron-down rotate-0" : "fa-chevron-right rotate-0", "transition-transform duration-200")
  }), /*#__PURE__*/React.createElement("h2", {
    className: "text-base sm:text-lg font-semibold"
  }, title)), /*#__PURE__*/React.createElement("div", {
    onClick: e => e.stopPropagation()
  }, right)), /*#__PURE__*/React.createElement("div", {
    className: cx("grid transition-all duration-300", open ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0")
  }, /*#__PURE__*/React.createElement("div", {
    className: "overflow-hidden"
  }, /*#__PURE__*/React.createElement("div", {
    className: "px-4 sm:px-6 py-4"
  }, children))));
}
function UploadArea({
  onFilesUploaded,
  onColumnsLoaded,
  uploadedFiles,
  setUploadedFiles,
  setToast
}) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [status, setStatus] = useState(null); // {type: 'processing'|'success'|'error'|'warning', text: string}

  function logToConsole(message) {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[${timestamp}] ${message}`);
  }
  function setStatusMsg(type, text) {
    setStatus({
      type,
      text
    });
  }
  function validateAndUpload(files) {
    if (!files || files.length === 0) return;
    setStatusMsg("processing", `Processing ${files.length} file(s)...`);
    logToConsole(`Processing ${files.length} files...`);
    const pdfFiles = files.filter(f => f.name.toLowerCase().endsWith(".pdf"));
    const excelFiles = files.filter(f => f.name.toLowerCase().endsWith(".xlsx") || f.name.toLowerCase().endsWith(".xls"));
    const invalidFiles = files.filter(f => !f.name.toLowerCase().endsWith(".pdf") && !f.name.toLowerCase().endsWith(".xlsx") && !f.name.toLowerCase().endsWith(".xls"));
    if (invalidFiles.length > 0) {
      setStatusMsg("error", `Invalid file types: ${invalidFiles.map(f => f.name).join(", ")}`);
      logToConsole(`Invalid file types: ${invalidFiles.map(f => f.name).join(", ")}`);
      return;
    }
    const hasExcelInCurrentUpload = excelFiles.length > 0;
    const hasExcelAlreadyUploaded = uploadedFiles.excel.length > 0;
    logToConsole(`Debug: hasExcelInCurrentUpload=${hasExcelInCurrentUpload}, hasExcelAlreadyUploaded=${hasExcelAlreadyUploaded}, uploadedFiles.excel.length=${uploadedFiles.excel.length}`);
    if (excelFiles.length > 1) {
      setStatusMsg("error", "Please upload only one Excel file");
      logToConsole("Error: Multiple Excel files uploaded");
      return;
    }
    if (hasExcelInCurrentUpload && hasExcelAlreadyUploaded) {
      setStatusMsg("error", "Excel file already uploaded. Please upload only PDF files now.");
      logToConsole("Error: Excel file already uploaded");
      return;
    }
    if (!hasExcelInCurrentUpload && !hasExcelAlreadyUploaded && pdfFiles.length === 0) {
      setStatusMsg("error", "Please upload at least one Excel file");
      logToConsole("Error: No files to upload");
      return;
    }

    // If uploading a new Excel, clear previous lists
    if (hasExcelInCurrentUpload) {
      setUploadedFiles({
        excel: [],
        pdf: []
      });
    }
    const uploadPromises = [];
    if (hasExcelInCurrentUpload) {
      uploadPromises.push(uploadFile(excelFiles[0], "excel"));
    }
    pdfFiles.forEach(pdf => uploadPromises.push(uploadFile(pdf, "pdf")));
    Promise.all(uploadPromises).then(results => {
      const successful = results.filter(r => r.success).length;
      const total = results.length;
      if (successful === total) {
        setStatusMsg("success", `${successful} file(s) uploaded successfully`);
        logToConsole(`Successfully uploaded ${successful} files`);
      } else {
        setStatusMsg("warning", `${successful}/${total} files uploaded`);
        logToConsole(`Partial upload: ${successful}/${total} files uploaded`);
      }
      if (typeof onFilesUploaded === "function") onFilesUploaded();
    });
  }
  function uploadFile(file, type) {
    return new Promise(resolve => {
      const formData = new FormData();
      formData.append(type === "pdf" ? "pdf_file" : "excel_file", file);
      logToConsole(`Uploading ${type.toUpperCase()}: ${file.name}`);
      fetch(type === "pdf" ? "/upload_pdf" : "/upload_excel", {
        method: "POST",
        body: formData
      }).then(res => res.json()).then(data => {
        if (data.success) {
          logToConsole(`${type.toUpperCase()} uploaded: ${data.filename}`);
          setUploadedFiles(prev => {
            const next = {
              ...prev
            };
            next[type] = [...prev[type], {
              name: file.name,
              filename: data.filename
            }];
            return next;
          });
          if (type === "excel" && data.columns && onColumnsLoaded) {
            onColumnsLoaded(data.columns, data.default_tag_column);
          }
          resolve({
            success: true,
            data
          });
        } else {
          logToConsole(`Error uploading ${type.toUpperCase()}: ${data.message}`);
          setToast({
            type: "error",
            text: data.message
          });
          resolve({
            success: false,
            data
          });
        }
      }).catch(error => {
        logToConsole(`Error uploading ${type.toUpperCase()}: ${error.message}`);
        setToast({
          type: "error",
          text: error.message
        });
        resolve({
          success: false,
          error
        });
      });
    });
  }
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    onClick: () => inputRef.current?.click(),
    onDragOver: e => {
      e.preventDefault();
      setDragOver(true);
    },
    onDragLeave: () => setDragOver(false),
    onDrop: e => {
      e.preventDefault();
      setDragOver(false);
      const files = Array.from(e.dataTransfer.files || []);
      validateAndUpload(files);
    },
    className: cx("group cursor-pointer rounded-2xl border-2 border-dashed p-8 sm:p-10 text-center transition-colors duration-300", "bg-white dark:bg-zinc-950/40 border-zinc-300/60 dark:border-zinc-700", "hover:border-brand/60 hover:bg-brand/5", dragOver && "border-brand bg-brand/10")
  }, /*#__PURE__*/React.createElement("div", {
    className: "mx-auto flex h-16 w-16 items-center justify-center rounded-xl bg-brand/10 text-brand mb-3"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-file-arrow-up text-2xl"
  })), /*#__PURE__*/React.createElement("div", {
    className: "text-lg font-semibold"
  }, "Click or drag files here."), /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-zinc-500 dark:text-zinc-400"
  }, "Upload one Excel first, then one or more PDF files"), /*#__PURE__*/React.createElement("div", {
    className: "mt-2 text-xs text-zinc-400"
  }, "Supported: PDF, Excel (.xlsx / .xls)"), /*#__PURE__*/React.createElement("input", {
    ref: inputRef,
    type: "file",
    accept: ".pdf,.xlsx,.xls",
    multiple: true,
    className: "hidden",
    onChange: e => {
      const files = Array.from(e.target.files || []);
      validateAndUpload(files);
      e.target.value = "";
    }
  })), status && /*#__PURE__*/React.createElement("div", {
    className: cx("mt-3 inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-medium", status.type === "processing" && "bg-zinc-200/70 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300", status.type === "success" && "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300", status.type === "warning" && "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300", status.type === "error" && "bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300")
  }, status.type === "processing" && /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-spinner animate-spin"
  }), status.type === "success" && /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-check"
  }), status.type === "warning" && /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-triangle-exclamation"
  }), status.type === "error" && /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-xmark"
  }), /*#__PURE__*/React.createElement("span", null, status.text)));
}
function FilesList({
  uploadedFiles
}) {
  const hasFiles = uploadedFiles.excel.length > 0 || uploadedFiles.pdf.length > 0;
  if (!hasFiles) return null;
  return /*#__PURE__*/React.createElement("div", {
    className: "mt-6"
  }, /*#__PURE__*/React.createElement("h3", {
    className: "text-sm font-semibold text-zinc-500 dark:text-zinc-400 mb-3"
  }, "Uploaded Files"), /*#__PURE__*/React.createElement("div", {
    className: "grid gap-3 sm:grid-cols-2"
  }, uploadedFiles.excel.map((f, idx) => /*#__PURE__*/React.createElement("div", {
    key: `excel-${idx}`,
    className: "flex items-center gap-3 rounded-xl border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-950/60 p-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-file-excel"
  })), /*#__PURE__*/React.createElement("div", {
    className: "flex-1"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-medium"
  }, f.name), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-zinc-500 dark:text-zinc-400"
  }, "Uploaded")), /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-check text-emerald-500"
  }))), uploadedFiles.pdf.map((f, idx) => /*#__PURE__*/React.createElement("div", {
    key: `pdf-${idx}`,
    className: "flex items-center gap-3 rounded-xl border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-950/60 p-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex h-10 w-10 items-center justify-center rounded-lg bg-rose-500/10 text-rose-500"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-file-pdf"
  })), /*#__PURE__*/React.createElement("div", {
    className: "flex-1"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-medium"
  }, f.name), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-zinc-500 dark:text-zinc-400"
  }, "Uploaded")), /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-check text-emerald-500"
  })))));
}

// New FileWorkspace component
function FileWorkspace({
  workspaceFiles,
  selectedPdfs,
  selectedExcel,
  onSelectionChange,
  onExcelSelectionChange,
  onDeleteFile,
  onUploadFiles,
  onColumnsLoaded,
  setToast,
  onRefresh,
  loadingColumns,
  setLoadingColumns
}) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  }
  function handleFileUpload(files) {
    if (!files || files.length === 0) return;
    const pdfFiles = files.filter(f => f.name.toLowerCase().endsWith(".pdf"));
    const excelFiles = files.filter(f => f.name.toLowerCase().endsWith(".xlsx") || f.name.toLowerCase().endsWith(".xls") || f.name.toLowerCase().endsWith(".csv"));

    // Multiple Excel files are now allowed - users can select which one to use

    // Upload files
    const uploadPromises = [];
    excelFiles.forEach(file => uploadPromises.push(uploadFile(file, "excel")));
    pdfFiles.forEach(file => uploadPromises.push(uploadFile(file, "pdf")));
    Promise.all(uploadPromises).then(results => {
      // Refresh the workspace file list
      // Note: refreshWorkspace() will automatically handle Excel file selection
      // and column loading, so we don't need to do it here
      onRefresh();
    });
  }
  function uploadFile(file, type) {
    return new Promise(resolve => {
      const formData = new FormData();
      formData.append(type === "pdf" ? "pdf_file" : "excel_file", file);

      // Show loading indicator for Excel uploads (header detection takes time)
      if (type === "excel") {
        setLoadingColumns(true);
      }
      fetch(type === "pdf" ? "/upload_pdf" : "/upload_excel", {
        method: "POST",
        body: formData
      }).then(res => res.json()).then(data => {
        if (data.success) {
          // Note: Don't call onColumnsLoaded here - we'll do it when selecting the file
          // This prevents double-loading columns
          setToast({
            type: "success",
            text: `${file.name} uploaded successfully`
          });
          resolve({
            success: true,
            filename: data.filename,
            type: type
          });
        } else {
          setToast({
            type: "error",
            text: data.message
          });
          resolve({
            success: false
          });
        }
      }).catch(error => {
        setToast({
          type: "error",
          text: error.message
        });
        resolve({
          success: false
        });
      }).finally(() => {
        // Stop loading indicator for Excel uploads
        // Note: This will be set to true again when we select the file in handleFileUpload
        if (type === "excel") {
          setLoadingColumns(false);
        }
      });
    });
  }
  function handleDeleteFile(filename) {
    if (!confirm(`Delete ${filename}?`)) return;
    fetch("/delete_file", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        filename
      })
    }).then(res => res.json()).then(data => {
      if (data.success) {
        setToast({
          type: "success",
          text: "File deleted"
        });

        // Clear selectedExcel if the deleted file was selected
        if (selectedExcel === filename) {
          onExcelSelectionChange(null);
        }
        onRefresh();
      } else {
        setToast({
          type: "error",
          text: data.message
        });
      }
    }).catch(err => {
      setToast({
        type: "error",
        text: `Error: ${err.message}`
      });
    });
  }
  function togglePdfSelection(filename) {
    const newSelection = selectedPdfs.includes(filename) ? selectedPdfs.filter(f => f !== filename) : [...selectedPdfs, filename];
    onSelectionChange(newSelection);
  }
  function selectAllPdfs() {
    onSelectionChange(workspaceFiles.pdfs.map(f => f.filename));
  }
  function deselectAllPdfs() {
    onSelectionChange([]);
  }
  function toggleExcelSelection(filename) {
    // Single selection: if clicking on already selected, do nothing
    // if clicking on different file, switch to that one
    if (selectedExcel === filename) {
      // Already selected, keep it selected (don't allow deselection)
      return;
    }
    onExcelSelectionChange(filename);

    // Show loading indicator while loading columns
    setLoadingColumns(true);

    // Update session and reload columns for the newly selected Excel file
    fetch("/select_excel", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        excel_file: filename,
        header_row: 6
      })
    }).then(r => r.json()).then(data => {
      if (data.success && onColumnsLoaded) {
        onColumnsLoaded(data.columns, data.default_tag_column);
        setToast({
          type: "success",
          text: `Switched to ${filename.split('_').slice(1).join('_')}`
        });
      } else {
        setToast({
          type: "error",
          text: data.message || "Failed to load columns"
        });
      }
    }).catch(err => {
      console.error("Error reloading columns:", err);
      setToast({
        type: "error",
        text: "Failed to switch Excel file"
      });
    }).finally(() => {
      setLoadingColumns(false);
    });
  }
  const totalFiles = workspaceFiles.excel.length + workspaceFiles.pdfs.length;
  const selectedCount = selectedPdfs.length;
  return /*#__PURE__*/React.createElement("div", {
    className: "space-y-4"
  }, /*#__PURE__*/React.createElement("div", {
    onClick: () => inputRef.current?.click(),
    onDragOver: e => {
      e.preventDefault();
      setDragOver(true);
    },
    onDragLeave: () => setDragOver(false),
    onDrop: e => {
      e.preventDefault();
      setDragOver(false);
      const files = Array.from(e.dataTransfer.files || []);
      handleFileUpload(files);
    },
    className: cx("cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition-colors duration-300", "bg-white dark:bg-zinc-950/40 border-zinc-300/60 dark:border-zinc-700", "hover:border-brand/60 hover:bg-brand/5", dragOver && "border-brand bg-brand/10")
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-center gap-3"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-cloud-arrow-up text-2xl text-brand"
  }), /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-medium"
  }, "Drop files here or click to upload"), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-zinc-500 dark:text-zinc-400"
  }, "(PDF, Excel, CSV)")), /*#__PURE__*/React.createElement("input", {
    ref: inputRef,
    type: "file",
    accept: ".pdf,.xlsx,.xls,.csv",
    multiple: true,
    className: "hidden",
    onChange: e => {
      const files = Array.from(e.target.files || []);
      handleFileUpload(files);
      e.target.value = "";
    }
  })), totalFiles > 0 && /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between gap-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-sm font-semibold text-zinc-700 dark:text-zinc-300"
  }, "Workspace (", totalFiles, " file", totalFiles !== 1 ? 's' : '', ")", selectedCount > 0 && /*#__PURE__*/React.createElement("span", {
    className: "ml-2 text-brand"
  }, selectedCount, " PDF", selectedCount !== 1 ? 's' : '', " selected")), /*#__PURE__*/React.createElement("div", {
    className: "flex gap-2"
  }, workspaceFiles.pdfs.length > 0 && /*#__PURE__*/React.createElement(React.Fragment, null, selectedPdfs.length === workspaceFiles.pdfs.length ? /*#__PURE__*/React.createElement("button", {
    onClick: deselectAllPdfs,
    className: "text-xs px-3 py-1.5 rounded-lg bg-zinc-200/60 dark:bg-zinc-800 hover:bg-zinc-300/60 dark:hover:bg-zinc-700 transition-colors"
  }, "Deselect All") : /*#__PURE__*/React.createElement("button", {
    onClick: selectAllPdfs,
    className: "text-xs px-3 py-1.5 rounded-lg bg-brand/10 text-brand hover:bg-brand/20 transition-colors"
  }, "Select All PDFs")), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      if (confirm('Clear all files from workspace?')) {
        fetch('/clear_session', {
          method: 'POST'
        }).then(r => r.json()).then(data => {
          if (data.success) {
            setToast({
              type: 'success',
              text: 'Workspace cleared'
            });
            onRefresh();
          }
        });
      }
    },
    className: "text-xs px-3 py-1.5 rounded-lg bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
  }, "Clear All"))), totalFiles > 0 && /*#__PURE__*/React.createElement("div", {
    className: "grid gap-3 sm:grid-cols-2"
  }, workspaceFiles.excel.map((file, idx) => {
    const isSelected = selectedExcel === file.filename;
    return /*#__PURE__*/React.createElement("div", {
      key: `excel-${idx}`,
      className: cx("flex items-center gap-3 rounded-xl border p-3 transition-colors", isSelected ? "border-emerald-500 bg-emerald-500/5 dark:bg-emerald-500/10" : "border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-950/60")
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      checked: isSelected,
      onChange: () => toggleExcelSelection(file.filename),
      className: "h-5 w-5 rounded border-zinc-300 dark:border-zinc-700 text-emerald-500 focus:ring-emerald-500/50"
    }), /*#__PURE__*/React.createElement("div", {
      className: "flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-500"
    }, /*#__PURE__*/React.createElement("i", {
      className: cx("fa-solid", file.type === 'csv' ? 'fa-file-csv' : 'fa-file-excel')
    })), /*#__PURE__*/React.createElement("div", {
      className: "flex-1 min-w-0"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-sm font-medium truncate"
    }, file.name), /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 flex items-center gap-2"
    }, /*#__PURE__*/React.createElement("span", null, formatFileSize(file.size)), /*#__PURE__*/React.createElement("span", {
      className: "px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium"
    }, "TAG SOURCE"), isSelected && /*#__PURE__*/React.createElement("span", {
      className: "px-2 py-0.5 rounded bg-brand/10 text-brand font-medium"
    }, "SELECTED"))), /*#__PURE__*/React.createElement("button", {
      onClick: () => handleDeleteFile(file.filename),
      className: "flex h-8 w-8 items-center justify-center rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 transition-colors",
      title: "Delete file"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-xmark"
    })));
  }), workspaceFiles.pdfs.map((file, idx) => {
    const isSelected = selectedPdfs.includes(file.filename);
    return /*#__PURE__*/React.createElement("div", {
      key: `pdf-${idx}`,
      className: cx("flex items-center gap-3 rounded-xl border p-3 transition-colors", isSelected ? "border-brand bg-brand/5 dark:bg-brand/10" : "border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-950/60")
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      checked: isSelected,
      onChange: () => togglePdfSelection(file.filename),
      className: "h-5 w-5 rounded border-zinc-300 dark:border-zinc-700 text-brand focus:ring-brand/50"
    }), /*#__PURE__*/React.createElement("div", {
      className: "flex h-10 w-10 items-center justify-center rounded-lg bg-rose-500/10 text-rose-500"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-file-pdf"
    })), /*#__PURE__*/React.createElement("div", {
      className: "flex-1 min-w-0"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-sm font-medium truncate"
    }, file.name), /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 flex items-center gap-2"
    }, /*#__PURE__*/React.createElement("span", null, formatFileSize(file.size)), file.isAnnotated && /*#__PURE__*/React.createElement("span", {
      className: "px-2 py-0.5 rounded bg-brand/10 text-brand font-medium"
    }, "ANNOTATED"), file.isTest && /*#__PURE__*/React.createElement("span", {
      className: "px-2 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 font-medium"
    }, "TEST"))), /*#__PURE__*/React.createElement("button", {
      onClick: () => handleDeleteFile(file.filename),
      className: "flex h-8 w-8 items-center justify-center rounded-lg hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 dark:text-red-400 transition-colors",
      title: "Delete file"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-xmark"
    })));
  })), totalFiles === 0 && /*#__PURE__*/React.createElement("div", {
    className: "text-center py-8 text-zinc-500 dark:text-zinc-400"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-folder-open text-4xl mb-2 opacity-50"
  }), /*#__PURE__*/React.createElement("div", {
    className: "text-sm"
  }, "No files in workspace. Upload files to get started.")));
}
function Tabs({
  tabs,
  current,
  onChange
}) {
  return /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
    className: "flex flex-wrap gap-2"
  }, tabs.map(t => /*#__PURE__*/React.createElement("button", {
    key: t.key,
    onClick: () => onChange(t.key),
    className: cx("px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200", current === t.key ? "bg-brand text-white shadow-soft" : "bg-zinc-200/60 dark:bg-zinc-800 text-zinc-700 dark:text-zinc-300 hover:bg-zinc-300/60 dark:hover:bg-zinc-700"),
    role: "tab",
    "aria-selected": current === t.key
  }, t.icon && /*#__PURE__*/React.createElement("i", {
    className: cx("mr-2", t.icon)
  }), t.label))));
}
function ProgressModal({
  open,
  modeTitle,
  progress,
  status,
  onClose,
  onDownload,
  fileCount,
  error,
  reportFilename,
  annotateExcelEnabled,
  isTestRun,
  onStartFullRun
}) {
  if (!open) return null;
  const complete = progress === 100 && !error;
  return /*#__PURE__*/React.createElement("div", {
    className: "fixed inset-0 z-50 flex items-center justify-center p-4",
    role: "dialog",
    "aria-modal": "true"
  }, /*#__PURE__*/React.createElement("div", {
    className: "absolute inset-0 bg-black/50 backdrop-blur-sm",
    onClick: () => {}
  }), /*#__PURE__*/React.createElement("div", {
    className: "relative w-full max-w-md rounded-2xl border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-950/90 shadow-soft"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between px-5 py-4 border-b border-zinc-200/60 dark:border-zinc-800"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2"
  }, /*#__PURE__*/React.createElement("i", {
    className: cx("fa-solid text-brand", isTestRun ? "fa-bolt" : "fa-cogs")
  }), /*#__PURE__*/React.createElement("h3", {
    className: "font-semibold"
  }, modeTitle)), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    className: "rounded-lg p-2 hover:bg-zinc-200/60 dark:hover:bg-zinc-800",
    "aria-label": "Close"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-xmark"
  }))), !error && /*#__PURE__*/React.createElement("div", {
    className: "px-5 py-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "h-3 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800 mb-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "h-3 rounded-full bg-brand transition-all duration-300",
    style: {
      width: `${Math.max(0, Math.min(100, progress))}%`
    }
  })), /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between text-sm"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-zinc-600 dark:text-zinc-400"
  }, status || "Initializing..."), /*#__PURE__*/React.createElement("div", {
    className: "font-semibold"
  }, progress, "%")), !!fileCount && /*#__PURE__*/React.createElement("div", {
    className: "mt-2 text-xs text-zinc-500 dark:text-zinc-400"
  }, "Processing ", fileCount, " PDF file(s)"), complete && /*#__PURE__*/React.createElement("div", {
    className: "mt-5 space-y-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2 text-emerald-500"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-circle-check text-2xl"
  }), /*#__PURE__*/React.createElement("div", {
    className: "font-semibold"
  }, isTestRun ? "Test run complete!" : annotateExcelEnabled ? fileCount > 1 ? `Your ${fileCount} annotated PDF and Excel files are ready.` : "Your annotated PDF and Excel files are ready." : fileCount > 1 ? `Your ${fileCount} annotated PDF files are ready.` : "Your annotated PDF is ready.")), isTestRun && /*#__PURE__*/React.createElement("div", {
    className: "rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200/60 dark:border-blue-800 px-3 py-2"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-start gap-2"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-info-circle text-blue-600 dark:text-blue-400 mt-0.5"
  }), /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-blue-800 dark:text-blue-200"
  }, "Upload data has been preserved. You can now review the test output and run the full processing when ready."))), /*#__PURE__*/React.createElement("div", {
    className: "grid gap-2"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => onDownload('pdf'),
    className: "inline-flex w-full items-center justify-center gap-2 rounded-lg bg-success text-white px-4 py-2.5 font-semibold hover:bg-success-hover transition-colors"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-file-pdf"
  }), isTestRun ? "Download Test PDF(s)" : fileCount > 1 ? `Download ${fileCount} PDF(s)` : "Download PDF"), annotateExcelEnabled && /*#__PURE__*/React.createElement("button", {
    onClick: () => onDownload('excel'),
    className: "inline-flex w-full items-center justify-center gap-2 rounded-lg bg-emerald-600 text-white px-4 py-2.5 font-semibold hover:bg-emerald-700 transition-colors"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-file-excel"
  }), "Download Annotated Excel"), reportFilename && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("button", {
    onClick: () => window.open(`/view_report/${reportFilename}`, '_blank'),
    className: "inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand text-white px-4 py-2.5 font-semibold hover:bg-brand-hover transition-colors"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-chart-bar"
  }), "View Processing Report"), /*#__PURE__*/React.createElement("button", {
    onClick: () => onDownload('report'),
    className: "inline-flex w-full items-center justify-center gap-2 rounded-lg bg-purple-600 text-white px-4 py-2.5 font-semibold hover:bg-purple-700 transition-colors"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-download"
  }), "Download Report (HTML)")), isTestRun && /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      onClose();
      onStartFullRun();
    },
    className: "inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand text-white px-4 py-2.5 font-semibold hover:bg-brand-hover transition-colors"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-play"
  }), "Run Full Processing"), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    className: "inline-flex w-full items-center justify-center gap-2 rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-4 py-2.5 font-semibold hover:bg-zinc-300/70 dark:hover:bg-zinc-700 transition-colors"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-times"
  }), "Close")))), error && /*#__PURE__*/React.createElement("div", {
    className: "px-5 py-6"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex flex-col items-center text-center"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-triangle-exclamation text-danger text-4xl mb-3"
  }), /*#__PURE__*/React.createElement("div", {
    className: "text-xl font-semibold text-danger mb-2"
  }, "Processing Failed"), /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-zinc-600 dark:text-zinc-400 mb-4"
  }, error), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    className: "inline-flex items-center justify-center gap-2 rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-4 py-2.5 font-semibold hover:bg-zinc-300/70 dark:hover:bg-zinc-700 transition-colors"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-times"
  }), "Close")))));
}
function SaveProfileModal({
  open,
  onClose,
  onSave
}) {
  const [profileName, setProfileName] = useState("");
  const [profileDescription, setProfileDescription] = useState("");
  if (!open) return null;
  function handleSave() {
    if (!profileName.trim()) {
      alert("Profile name is required");
      return;
    }
    onSave(profileName.trim(), profileDescription.trim());
    setProfileName("");
    setProfileDescription("");
  }
  return /*#__PURE__*/React.createElement("div", {
    className: "fixed inset-0 z-50 flex items-center justify-center p-4",
    role: "dialog",
    "aria-modal": "true"
  }, /*#__PURE__*/React.createElement("div", {
    className: "absolute inset-0 bg-black/50 backdrop-blur-sm",
    onClick: onClose
  }), /*#__PURE__*/React.createElement("div", {
    className: "relative w-full max-w-md rounded-2xl border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-950/90 shadow-soft"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between px-5 py-4 border-b border-zinc-200/60 dark:border-zinc-800"
  }, /*#__PURE__*/React.createElement("h3", {
    className: "font-semibold"
  }, "Save Configuration Profile"), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    className: "rounded-lg p-2 hover:bg-zinc-200/60 dark:hover:bg-zinc-800",
    "aria-label": "Close"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-xmark"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "px-5 py-4 space-y-4"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    htmlFor: "profile-name",
    className: "block text-sm font-medium mb-1"
  }, "Profile Name ", /*#__PURE__*/React.createElement("span", {
    className: "text-danger"
  }, "*")), /*#__PURE__*/React.createElement("input", {
    id: "profile-name",
    type: "text",
    value: profileName,
    onChange: e => setProfileName(e.target.value),
    placeholder: "e.g., My Custom Setup",
    className: "w-full rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/60"
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    htmlFor: "profile-description",
    className: "block text-sm font-medium mb-1"
  }, "Description (Optional)"), /*#__PURE__*/React.createElement("textarea", {
    id: "profile-description",
    value: profileDescription,
    onChange: e => setProfileDescription(e.target.value),
    placeholder: "Describe this configuration...",
    rows: 3,
    className: "w-full rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/60"
  })), /*#__PURE__*/React.createElement("div", {
    className: "flex gap-2"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: handleSave,
    className: "flex-1 rounded-lg bg-brand text-white px-4 py-2 font-semibold hover:bg-brand-hover transition-colors"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-save mr-1"
  }), "Save Profile"), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    className: "flex-1 rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-4 py-2 font-semibold hover:bg-zinc-300/70 dark:hover:bg-zinc-700 transition-colors"
  }, "Cancel")))));
}
function ImportProfileModal({
  open,
  onClose,
  onImport
}) {
  const fileInputRef = useRef(null);
  if (!open) return null;
  function handleFileSelect(e) {
    const file = e.target.files?.[0];
    if (file) {
      if (!file.name.endsWith('.json')) {
        alert("Please select a JSON file");
        return;
      }
      onImport(file);
    }
  }
  return /*#__PURE__*/React.createElement("div", {
    className: "fixed inset-0 z-50 flex items-center justify-center p-4",
    role: "dialog",
    "aria-modal": "true"
  }, /*#__PURE__*/React.createElement("div", {
    className: "absolute inset-0 bg-black/50 backdrop-blur-sm",
    onClick: onClose
  }), /*#__PURE__*/React.createElement("div", {
    className: "relative w-full max-w-md rounded-2xl border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-950/90 shadow-soft"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between px-5 py-4 border-b border-zinc-200/60 dark:border-zinc-800"
  }, /*#__PURE__*/React.createElement("h3", {
    className: "font-semibold"
  }, "Import Configuration Profile"), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    className: "rounded-lg p-2 hover:bg-zinc-200/60 dark:hover:bg-zinc-800",
    "aria-label": "Close"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-xmark"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "px-5 py-4 space-y-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-zinc-600 dark:text-zinc-400"
  }, "Select a JSON profile file to import. The profile must match the expected format."), /*#__PURE__*/React.createElement("div", {
    onClick: () => fileInputRef.current?.click(),
    className: "cursor-pointer rounded-xl border-2 border-dashed border-zinc-300/60 dark:border-zinc-700 bg-white dark:bg-zinc-950/40 p-8 text-center hover:border-brand/60 hover:bg-brand/5 transition-colors"
  }, /*#__PURE__*/React.createElement("div", {
    className: "mx-auto flex h-16 w-16 items-center justify-center rounded-xl bg-brand/10 text-brand mb-3"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-file-import text-2xl"
  })), /*#__PURE__*/React.createElement("div", {
    className: "text-lg font-semibold"
  }, "Click to select JSON file"), /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-zinc-500 dark:text-zinc-400 mt-1"
  }, "Supported: .json files only"), /*#__PURE__*/React.createElement("input", {
    ref: fileInputRef,
    type: "file",
    accept: ".json",
    className: "hidden",
    onChange: handleFileSelect
  })), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    className: "w-full rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-4 py-2 font-semibold hover:bg-zinc-300/70 dark:hover:bg-zinc-700 transition-colors"
  }, "Cancel"))));
}
function FAQModal({
  open,
  onClose
}) {
  const [activeCategory, setActiveCategory] = React.useState('getting-started');
  const [searchQuery, setSearchQuery] = React.useState('');
  console.log('FAQModal render, open:', open);

  // Define FAQ categories outside of conditional to avoid recreation
  const faqCategories = React.useMemo(() => ({
    'getting-started': {
      title: 'Getting Started',
      icon: 'fa-rocket',
      questions: [{
        q: 'How do I get started with PID Annotator?',
        a: 'Follow these steps: 1) Upload your Excel file with component tags, 2) Upload one or more PDF files, 3) Configure settings or load a template, 4) Click "Start" to process.'
      }, {
        q: 'Which row is used as headers in Excel?',
        a: 'You can configure which row contains the headers using the "Header Row" field. The default is row 6, but you can adjust this to match your Excel file structure.'
      }, {
        q: 'Which column should I use for tags?',
        a: 'Select any column from your Excel file using the "Tag Column" dropdown. This column should contain your component identifiers (e.g., TAG-001-A, SYS.PUMP.01).'
      }, {
        q: 'Can I run this on my own machine?',
        a: /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
          className: "mb-2"
        }, "Yes! The source code is available on GitHub for free and you can run it locally:"), /*#__PURE__*/React.createElement("p", {
          className: "mb-2"
        }, /*#__PURE__*/React.createElement("a", {
          href: "https://github.com/rudikdk/Annotator",
          target: "_blank",
          rel: "noopener noreferrer",
          className: "text-brand hover:text-brand-hover font-semibold flex items-center gap-1"
        }, /*#__PURE__*/React.createElement("i", {
          className: "fa-brands fa-github"
        }), "github.com/rudikdk/Annotator")), /*#__PURE__*/React.createElement("p", {
          className: "text-sm"
        }, "You can clone the repository and run it locally with Docker or Python. Perfect for local deployments, private use, or customization. Full setup instructions are available in the repository README."))
      }]
    },
    'features': {
      title: 'Features & Configuration',
      icon: 'fa-sliders',
      questions: [{
        q: 'What are Configuration Profiles?',
        a: 'Profiles save all your settings including color rules and tag filters. Your settings auto-save to your browser. You can export them as JSON files to back up or share with team members, and import profiles on any device. For local setups, profiles can also be stored as JSON files in the server profiles folder.'
      }, {
        q: 'What is the difference between "Start" and "Test Run"?',
        a: '"Start" processes all tags in your Excel file, while "Test Run" processes only the first 100 tags. Use Test Run to quickly verify your configuration before running a full batch.'
      }, {
        q: 'How does Excel Annotation work?',
        a: 'When enabled, the application highlights rows in your Excel file (with green fill) where tags were successfully found in the PDF. This helps you quickly identify which components were annotated.'
      }, {
        q: 'What is the Watermark feature?',
        a: 'Watermarks add text labels directly next to tags in the PDF using values from your Excel columns. You can select multiple attributes — all selected values are shown joined by " / " (e.g. "Pump / Gate / 150mm"). Use drag-and-drop to reorder attributes, adjust font size (5–24pt), pick text color, and optionally add a white background for readability. A live preview updates as you configure.'
      }, {
        q: 'How do Color Rules work?',
        a: 'Color Rules let you highlight tags with different colors based on matching criteria. There are two rule types: Tag Part (match by a part of the tag string, e.g. Part B = "HV") and Excel Column (match by a column value in your Excel file). Rules are evaluated in order — the last matching rule wins and decides the color. Use the up/down arrows to set priority.'
      }, {
        q: 'What match types are available in Color Rules?',
        a: 'For Tag Part rules: Exact and Contains. For Excel Column rules: Exact, Contains, Has value (colorizes if the column has any non-empty value), Greater than, and Less than. Greater/less than compares numerically when possible, falling back to alphabetical comparison for text.'
      }, {
        q: 'How do I know which rules might overlap?',
        a: 'When two Excel Column rules target the same column, the later rule shows an amber info badge: "Overrides rule #N on same column — last wins". This is just for awareness — the behavior is intentional and correct.'
      }, {
        q: 'What are the Live Examples in the rule builder?',
        a: 'When building an Excel Column rule, a live panel shows up to 3 rows from your Excel that would match the rule (green ✓) and 2 rows that would not match (red ✗), including the tag name and column value. This updates as you change the column, match type, or value — so you can verify the rule before adding it.'
      }, {
        q: 'Can I process multiple PDFs at once?',
        a: 'Yes! Upload multiple PDF files and they will all be processed with the same Excel file. Each PDF gets its own annotated output. Use the checkboxes to select which PDFs to process.'
      }]
    },
    'troubleshooting': {
      title: 'Troubleshooting',
      icon: 'fa-wrench',
      questions: [{
        q: 'What if a tag is not found in the PDF?',
        a: 'Tags not found are skipped. Common causes: 1) Formatting differences (check delimiters: hyphens vs periods), 2) OCR quality in scanned PDFs, 3) Case sensitivity issues, 4) Extra spaces in tags. Verify tags match between Excel and PDF exactly.'
      }, {
        q: 'Why is processing slow for large files?',
        a: 'The application automatically uses optimized modes for large files: Standard mode (<50MB), Streaming mode (≥50MB), and Parallel indexing (>20 pages). Performance depends on file size, page count, and tag density. Expected times: 10 pages ~7s, 100 pages ~18s, 500 pages ~2.5 min.'
      }, {
        q: 'What are the file size limits?',
        a: 'Maximum upload size is 100MB per file. The application can handle very large PDFs (1000+ pages, 200MB+) using streaming mode. Files are automatically cleaned up after 24 hours.'
      }, {
        q: 'How long are my files stored?',
        a: 'Uploaded and generated files are automatically deleted after 24 hours. Each user session is isolated with a unique ID to prevent conflicts. You can manually clear files using the "Clear All" button.'
      }, {
        q: 'What if my Excel file has a different structure?',
        a: 'Adjust the "Header Row" setting to match your file. The application is flexible and works with most Excel structures as long as you specify the correct header row and tag column.'
      }]
    },
    'technical': {
      title: 'Technical Details',
      icon: 'fa-code',
      questions: [{
        q: 'What tag formats are supported?',
        a: 'Both hyphen-delimited (e.g., 230-HV-NON-501) and period-delimited (e.g., 230.HV.NON.501) formats are supported. Tags should have 3-5 hierarchical parts. Matching is case-insensitive with automatic variant lookup.'
      }, {
        q: 'What is included in the PDF annotations?',
        a: 'Annotations include: 1) Highlights on the tag text, colored by your Color Rules (or a default color if no rule matches), 2) Popup comment notes containing all selected Excel columns for that tag, 3) Optional watermark text labels placed next to each tag showing selected attribute values. All three are optional and configurable.'
      }, {
        q: 'Where is the output saved?',
        a: 'Output files are generated on the server and available for download via the processing modal. Click the download button when processing completes. Files are stored in session-isolated folders.'
      }, {
        q: 'How does the parallel processing work?',
        a: 'For PDFs with >20 pages, the application uses multi-threaded page processing to build the tag index faster. It utilizes CPU cores efficiently (configurable) while managing memory with periodic cleanup cycles.'
      }, {
        q: 'What happens during "Streaming Mode"?',
        a: 'For files ≥50MB, streaming mode activates: 1) Document is closed/reopened between processing phases, 2) Memory cleanup runs every 100 pages, 3) Chunk-based processing reduces memory footprint. This prevents memory issues with very large files.'
      }]
    },
    'about': {
      title: 'About & Licenses',
      icon: 'fa-info-circle',
      questions: [{
        q: 'Python Libraries and Licenses',
        a: /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("p", {
          className: "mb-2"
        }, "This application uses the following open-source Python libraries:"), /*#__PURE__*/React.createElement("ul", {
          className: "list-disc list-inside space-y-1 text-xs"
        }, /*#__PURE__*/React.createElement("li", null, "Flask (BSD-3-Clause) - Web framework"), /*#__PURE__*/React.createElement("li", null, "Flask-SocketIO (MIT) - Real-time communication"), /*#__PURE__*/React.createElement("li", null, "pandas (BSD-3-Clause) - Data processing"), /*#__PURE__*/React.createElement("li", null, "PyMuPDF (AGPL-3.0) - PDF manipulation"), /*#__PURE__*/React.createElement("li", null, "openpyxl (MIT) - Excel file handling"), /*#__PURE__*/React.createElement("li", null, "Werkzeug (BSD-3-Clause) - WSGI utilities"), /*#__PURE__*/React.createElement("li", null, "python-socketio (MIT) - WebSocket support"), /*#__PURE__*/React.createElement("li", null, "eventlet (MIT) - Concurrent networking"), /*#__PURE__*/React.createElement("li", null, "gunicorn (MIT) - Production server"), /*#__PURE__*/React.createElement("li", null, "reportlab (BSD) - PDF generation"), /*#__PURE__*/React.createElement("li", null, "PyPDF2 (BSD-3-Clause) - PDF merging")))
      }, {
        q: 'Who created this application?',
        a: 'PID Annotator was created by Rudi S. Kærgaard (rudikdk@gmail.com). The application is optimized for Docker deployment on Raspberry Pi 5 with CasaOS, but works on any system with Docker support.'
      }]
    }
  }), []); // Empty dependency array since this never changes

  const filteredCategories = React.useMemo(() => {
    if (!searchQuery.trim()) return faqCategories;
    const query = searchQuery.toLowerCase();
    const filtered = {};
    Object.entries(faqCategories).forEach(([key, category]) => {
      const matchingQuestions = category.questions.filter(item => item.q.toLowerCase().includes(query) || typeof item.a === 'string' && item.a.toLowerCase().includes(query));
      if (matchingQuestions.length > 0) {
        filtered[key] = {
          ...category,
          questions: matchingQuestions
        };
      }
    });
    return filtered;
  }, [searchQuery, faqCategories]);
  if (!open) return null;
  return /*#__PURE__*/React.createElement("div", {
    className: "fixed inset-0 z-50 flex items-center justify-center p-4",
    role: "dialog",
    "aria-modal": "true"
  }, /*#__PURE__*/React.createElement("div", {
    className: "absolute inset-0 bg-black/50 backdrop-blur-sm",
    onClick: onClose
  }), /*#__PURE__*/React.createElement("div", {
    className: "relative w-full max-w-4xl rounded-2xl border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-950/90 shadow-soft flex flex-col max-h-[85vh]"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between px-5 py-4 border-b border-zinc-200/60 dark:border-zinc-800"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    className: "font-semibold text-lg"
  }, "FAQ \u2013 PID Annotator"), /*#__PURE__*/React.createElement("p", {
    className: "text-xs text-zinc-500 dark:text-zinc-400 mt-1"
  }, "Frequently Asked Questions & Help")), /*#__PURE__*/React.createElement("button", {
    onClick: onClose,
    className: "rounded-lg p-2 hover:bg-zinc-200/60 dark:hover:bg-zinc-800",
    "aria-label": "Close FAQ"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-xmark"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "px-5 py-3 border-b border-zinc-200/60 dark:border-zinc-800"
  }, /*#__PURE__*/React.createElement("div", {
    className: "relative"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-search absolute left-3 top-1/2 -translate-y-1/2 text-zinc-400"
  }), /*#__PURE__*/React.createElement("input", {
    type: "text",
    placeholder: "Search FAQ...",
    value: searchQuery,
    onChange: e => setSearchQuery(e.target.value),
    className: "w-full pl-10 pr-4 py-2 rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-900 text-sm focus:ring-2 focus:ring-brand focus:border-brand"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "flex flex-1 overflow-hidden"
  }, /*#__PURE__*/React.createElement("div", {
    className: "w-56 border-r border-zinc-200/60 dark:border-zinc-800 overflow-y-auto"
  }, /*#__PURE__*/React.createElement("div", {
    className: "p-2 space-y-1"
  }, Object.entries(filteredCategories).map(([key, category]) => /*#__PURE__*/React.createElement("button", {
    key: key,
    onClick: () => setActiveCategory(key),
    className: cx('w-full text-left px-3 py-2 rounded-lg text-sm transition-colors flex items-center gap-2', activeCategory === key ? 'bg-brand/10 text-brand font-medium' : 'hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300')
  }, /*#__PURE__*/React.createElement("i", {
    className: cx('fa-solid', category.icon, 'w-4')
  }), /*#__PURE__*/React.createElement("span", {
    className: "flex-1"
  }, category.title), /*#__PURE__*/React.createElement("span", {
    className: "text-xs bg-zinc-200 dark:bg-zinc-700 px-1.5 py-0.5 rounded"
  }, category.questions.length))))), /*#__PURE__*/React.createElement("div", {
    className: "flex-1 overflow-y-auto px-5 py-4"
  }, Object.keys(filteredCategories).length === 0 ? /*#__PURE__*/React.createElement("div", {
    className: "text-center py-8 text-zinc-500 dark:text-zinc-400"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-search text-3xl mb-2"
  }), /*#__PURE__*/React.createElement("p", null, "No results found for \"", searchQuery, "\"")) : /*#__PURE__*/React.createElement("div", {
    className: "space-y-6"
  }, filteredCategories[activeCategory]?.questions.map((item, idx) => /*#__PURE__*/React.createElement("div", {
    key: idx,
    className: "space-y-2"
  }, /*#__PURE__*/React.createElement("h4", {
    className: "font-semibold text-brand flex items-start gap-2"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-circle-question text-sm mt-0.5"
  }), item.q), /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-zinc-700 dark:text-zinc-300 pl-6"
  }, typeof item.a === 'string' ? /*#__PURE__*/React.createElement("p", null, item.a) : item.a)))))), /*#__PURE__*/React.createElement("div", {
    className: "px-5 py-3 border-t border-zinc-200/60 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/50"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-xs text-zinc-500 dark:text-zinc-400"
  }, /*#__PURE__*/React.createElement("p", null, /*#__PURE__*/React.createElement("strong", null, "Created by:"), " Rudi S. K\xE6rgaard \u2014 ", /*#__PURE__*/React.createElement("strong", null, "Email:"), " rudikdk@gmail.com")))));
}
function App() {
  // Backend-bound state
  const [excelColumns, setExcelColumns] = useState([]);
  const [uploadedFiles, setUploadedFiles] = useState({
    excel: [],
    pdf: []
  });

  // Workspace state
  const [workspaceFiles, setWorkspaceFiles] = useState({
    excel: [],
    pdfs: []
  });
  const [selectedPdfs, setSelectedPdfs] = useState([]);
  const [selectedExcel, setSelectedExcel] = useState(null); // Track selected Excel file
  const [loadingColumns, setLoadingColumns] = useState(false); // Track column loading state

  // Configuration state
  const [headerRow, setHeaderRow] = useState(6);
  const [tagColumn, setTagColumn] = useState("");
  const [commentColumns, setCommentColumns] = useState([]);
  const [highlightColor, setHighlightColor] = useState("#FFFF00");
  const [highlightColumn, setHighlightColumn] = useState("");

  // Color rules state (new advanced color system)
  const [colorRules, setColorRules] = useState([]); // Array of {id, rule_type, part, column_name, value, match_type, color}
  const [defaultHighlightColor, setDefaultHighlightColor] = useState("#FFFF00");
  const [enableDefaultColor, setEnableDefaultColor] = useState(true);
  const [excelConstraintMode, setExcelConstraintMode] = useState(true); // Default to ON - only color tags from Excel
  const [excelConstraintLogic, setExcelConstraintLogic] = useState("AND");
  const [colorRulePanelOpen, setColorRulePanelOpen] = useState(false);
  const [colorRuleBuilderOpen, setColorRuleBuilderOpen] = useState(false);
  const [newRuleType, setNewRuleType] = useState('tag_part'); // 'tag_part' or 'header_column'
  const [newRulePart, setNewRulePart] = useState(1);
  const [newRuleColumn, setNewRuleColumn] = useState(''); // For header_column rule type
  const [newRuleValue, setNewRuleValue] = useState('');
  const [newRuleMatchType, setNewRuleMatchType] = useState('contains');
  const [newRuleColor, setNewRuleColor] = useState('#FFFF00');
  const [ruleAvailableHeaderValues, setRuleAvailableHeaderValues] = useState([]); // For header column unique values
  const [ruleLoadingHeaderValues, setRuleLoadingHeaderValues] = useState(false);
  const [showAllRuleValues, setShowAllRuleValues] = useState(false); // Toggle for showing all available values

  // Floating Preview Modal state
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [previewModalPage, setPreviewModalPage] = useState(1);
  const [previewModalZoom, setPreviewModalZoom] = useState(1.0);
  const [previewModalData, setPreviewModalData] = useState(null);
  const [previewModalLoading, setPreviewModalLoading] = useState(false);
  const [isModalDragging, setIsModalDragging] = useState(false);
  const [modalDragStart, setModalDragStart] = useState({
    x: 0,
    y: 0
  });
  const [modalPanOffset, setModalPanOffset] = useState({
    x: 0,
    y: 0
  });
  const previewModalContainerRef = useRef(null);
  const previewCanvasRef = useRef(null);
  const [pdfDocument, setPdfDocument] = useState(null);
  const [annotateExcel, setAnnotateExcel] = useState(true);
  const [ruleExamples, setRuleExamples] = useState({
    matches: [],
    non_matches: []
  });
  const [ruleLoadingExamples, setRuleLoadingExamples] = useState(false);
  const [watermarkEnabled, setWatermarkEnabled] = useState(false);
  const [watermarkAttributes, setWatermarkAttributes] = useState([]);
  const [watermarkTextColor, setWatermarkTextColor] = useState("#000000");
  const [watermarkBackgroundEnabled, setWatermarkBackgroundEnabled] = useState(false);
  const [watermarkFontSize, setWatermarkFontSize] = useState(9);
  const [watermarkDragIndex, setWatermarkDragIndex] = useState(null);

  // Tag matching configuration state
  const [tagMatchingPreset, setTagMatchingPreset] = useState('default'); // 'default', 'match_all', 'custom'
  const [tagMatchingMinParts, setTagMatchingMinParts] = useState(3);
  const [tagMatchingMaxParts, setTagMatchingMaxParts] = useState(5);
  const [tagMatchingSeparators, setTagMatchingSeparators] = useState(['-', '.']);
  const [tagMatchingMinPartLength, setTagMatchingMinPartLength] = useState(1);
  const [tagMatchingMaxPartLength, setTagMatchingMaxPartLength] = useState(5);
  const [tagMatchingAllowPartial, setTagMatchingAllowPartial] = useState(false);
  const [tagMatchingCustomRegex, setTagMatchingCustomRegex] = useState('');
  const [tagMatchingPanelOpen, setTagMatchingPanelOpen] = useState(false);
  const [tagMatchingPreviewOpen, setTagMatchingPreviewOpen] = useState(false);
  const [tagMatchingPreviewTags, setTagMatchingPreviewTags] = useState([]);
  const [tagMatchingPreviewExpanded, setTagMatchingPreviewExpanded] = useState(false);
  const [tagMatchingPreviewLoading, setTagMatchingPreviewLoading] = useState(false);

  // Tag filtering state
  const [tagFilters, setTagFilters] = useState([]); // Array of {filter_type, part, value, match_type, action, column_name}
  const [filterLogic, setFilterLogic] = useState('AND'); // 'AND' or 'OR'
  const [tagFilterPanelOpen, setTagFilterPanelOpen] = useState(false);
  const [availableTagParts, setAvailableTagParts] = useState({}); // {part1: [{value, count}], part2: [...]}
  const [filterBuilderOpen, setFilterBuilderOpen] = useState(false);
  const [newFilterType, setNewFilterType] = useState('tag_part'); // 'tag_part' or 'header_column'
  const [newFilterPart, setNewFilterPart] = useState(1);
  const [newFilterColumn, setNewFilterColumn] = useState(''); // For header_column filter type
  const [newFilterValue, setNewFilterValue] = useState('');
  const [newFilterMatchType, setNewFilterMatchType] = useState('exact');
  const [newFilterAction, setNewFilterAction] = useState('include');
  const [availableHeaderValues, setAvailableHeaderValues] = useState([]); // For header column unique values
  const [loadingHeaderValues, setLoadingHeaderValues] = useState(false);
  const [showAllFilterValues, setShowAllFilterValues] = useState(false); // Toggle for showing all filter values
  const [filterMatchingCount, setFilterMatchingCount] = useState(null);
  const [filterPreviewOpen, setFilterPreviewOpen] = useState(false);
  const [filterPreviewTags, setFilterPreviewTags] = useState([]);
  const [filterPreviewExpanded, setFilterPreviewExpanded] = useState(false);
  const [filterPreviewLoading, setFilterPreviewLoading] = useState(false);

  // Profile management state
  // Hybrid profile system: localStorage for user profiles, server templates read-only
  const [serverProfiles, setServerProfiles] = useState([]); // Read-only templates from server
  const [selectedProfile, setSelectedProfile] = useState("");
  const [profilePreview, setProfilePreview] = useState(null);
  const [currentSettingsPreview, setCurrentSettingsPreview] = useState(null);
  const [activeProfileName, setActiveProfileName] = useState("");
  const [showImportProfileModal, setShowImportProfileModal] = useState(false);

  // UI state
  const [showFAQ, setShowFAQ] = useState(false);
  const [toast, setToast] = useState(null); // {type, text}

  // Processing modal state
  const [processingOpen, setProcessingOpen] = useState(false);
  const [processingTitle, setProcessingTitle] = useState("Processing Files");
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("Initializing...");
  const [fileCount, setFileCount] = useState(0);
  const [errorText, setErrorText] = useState(null);
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [annotateExcelEnabled, setAnnotateExcelEnabled] = useState(false);
  const [isCurrentTestRun, setIsCurrentTestRun] = useState(false);
  const [reportFilename, setReportFilename] = useState(null);

  // Socket
  const socket = useMemo(() => io(), []);
  const pollRef = useRef(null);
  function logToConsole(message) {
    const timestamp = new Date().toLocaleTimeString();
    console.log(`[${timestamp}] ${message}`);
  }
  function onColumnsLoaded(columns, defaultTag) {
    setExcelColumns(columns || []);
    setTagColumn(defaultTag || "");
    // Reset dependent fields
    setWatermarkAttributes([]);
    setHighlightColumn("");
    // Default: no columns selected for comments
    setCommentColumns([]);
    logToConsole(`Loaded ${columns?.length ?? 0} columns from Excel file`);

    // Always trigger visual effect for Header Row and Tag Column to guide user
    const headerRowElement = document.getElementById('header-row');
    const tagColumnElement = document.getElementById('tag-column');
    if (headerRowElement) {
      headerRowElement.classList.add('animate-bounce-attention');
      setTimeout(() => {
        headerRowElement.classList.remove('animate-bounce-attention');
      }, 5000);
    }
    if (tagColumnElement) {
      tagColumnElement.classList.add('animate-bounce-attention');
      logToConsole('Please verify the Header Row and Tag Column selections');
      setTimeout(() => {
        tagColumnElement.classList.remove('animate-bounce-attention');
      }, 5000);
    }
  }
  function reloadColumnsForHeaderRow(nextHeaderRow) {
    setLoadingColumns(true);
    fetch("/reload_columns", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        header_row: nextHeaderRow
      })
    }).then(r => r.json()).then(data => {
      if (data.success) {
        onColumnsLoaded(data.columns, data.default_tag_column);
        logToConsole(data.message || "Columns reloaded");
      } else {
        setToast({
          type: "error",
          text: data.message || "Failed to reload columns"
        });
        logToConsole(`Error reloading columns: ${data.message}`);
      }
    }).catch(err => {
      setToast({
        type: "error",
        text: err.message
      });
      logToConsole(`Error reloading columns: ${err.message}`);
    }).finally(() => {
      setLoadingColumns(false);
    });
  }

  // Handle tag matching preset changes
  function handleTagMatchingPresetChange(preset) {
    setTagMatchingPreset(preset);
    if (preset === 'default') {
      setTagMatchingMinParts(3);
      setTagMatchingMaxParts(5);
      setTagMatchingSeparators(['-', '.']);
      setTagMatchingMinPartLength(1);
      setTagMatchingMaxPartLength(5);
      setTagMatchingAllowPartial(false);
      setTagMatchingCustomRegex('');
    } else if (preset === 'match_all') {
      setTagMatchingMinParts(1);
      setTagMatchingMaxParts(10);
      setTagMatchingSeparators(['-', '.', '_', '/', ':']);
      setTagMatchingMinPartLength(1);
      setTagMatchingMaxPartLength(20);
      setTagMatchingAllowPartial(false);
      setTagMatchingCustomRegex('');
    }
    // For 'custom', keep current settings
  }

  // Tag filter handlers
  function handleAddFilter() {
    if (!newFilterValue.trim()) {
      setToast({
        type: "error",
        text: "Please enter a filter value"
      });
      return;
    }

    // Validate header_column filter has column selected
    if (newFilterType === 'header_column' && !newFilterColumn) {
      setToast({
        type: "error",
        text: "Please select a column for header-based filtering"
      });
      return;
    }

    // Build filter object based on filter type
    const newFilter = {
      filter_type: newFilterType,
      value: newFilterValue.trim(),
      match_type: newFilterMatchType,
      action: newFilterAction
    };

    // Add type-specific fields
    if (newFilterType === 'tag_part') {
      newFilter.part = newFilterPart;
    } else if (newFilterType === 'header_column') {
      newFilter.column_name = newFilterColumn;
    }
    setTagFilters([...tagFilters, newFilter]);
    setFilterBuilderOpen(false);
    // Reset builder fields
    setNewFilterType('tag_part');
    setNewFilterPart(1);
    setNewFilterColumn('');
    setNewFilterValue('');
    setNewFilterMatchType('exact');
    setNewFilterAction('include');
    setAvailableHeaderValues([]);
    setToast({
      type: "success",
      text: "Filter added successfully"
    });
  }
  function handleRemoveFilter(index) {
    const updated = tagFilters.filter((_, i) => i !== index);
    setTagFilters(updated);
  }
  function handleClearAllFilters() {
    setTagFilters([]);
    setFilterMatchingCount(null);
    setFilterPreviewTags([]);
    setFilterPreviewOpen(false);
    setToast({
      type: "success",
      text: "All filters cleared"
    });
  }
  function handlePreviewFilters() {
    if (!selectedExcel || !tagColumn) {
      setToast({
        type: "error",
        text: "Please select an Excel file and tag column first"
      });
      return;
    }
    if (tagFilters.length === 0) {
      setToast({
        type: "info",
        text: "No filters to preview. All tags will be processed."
      });
      return;
    }
    setFilterPreviewLoading(true);
    setFilterPreviewOpen(true);
    fetch("/preview_filtered_tags", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        selected_excel: selectedExcel,
        tag_column: tagColumn,
        header_row: headerRow,
        tag_filters: tagFilters,
        filter_logic: filterLogic
      })
    }).then(r => r.json()).then(data => {
      setFilterPreviewLoading(false);
      if (data.success) {
        setFilterPreviewTags(data.matching_tags);
        setFilterMatchingCount(data.matching_tags.length);
        logToConsole(`Filter preview: ${data.matching_tags.length}/${data.total_tags} tags match`);
      } else {
        setToast({
          type: "error",
          text: data.message || "Failed to preview filters"
        });
        logToConsole(`Error previewing filters: ${data.message}`);
      }
    }).catch(err => {
      setFilterPreviewLoading(false);
      setToast({
        type: "error",
        text: "Error fetching filter preview"
      });
      logToConsole(`Error previewing filters: ${err.message}`);
    });
  }

  // Function to fetch unique values from a header column for filter building
  function handleFetchHeaderValuesForFilter(columnName) {
    if (!columnName) {
      setAvailableHeaderValues([]);
      return;
    }
    setLoadingHeaderValues(true);
    fetch("/get_header_unique_values", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        selected_excel: selectedExcel,
        column_name: columnName,
        header_row: headerRow
      })
    }).then(r => r.json()).then(data => {
      setLoadingHeaderValues(false);
      if (data.error) {
        setToast({
          type: "error",
          text: data.error
        });
        setAvailableHeaderValues([]);
      } else {
        setAvailableHeaderValues(data.values || []);
        logToConsole(`Loaded ${data.values?.length || 0} unique values for column '${columnName}'`);
      }
    }).catch(err => {
      setLoadingHeaderValues(false);
      setToast({
        type: "error",
        text: "Error fetching column values"
      });
      setAvailableHeaderValues([]);
      logToConsole(`Error fetching header values: ${err.message}`);
    });
  }
  function handlePreviewTagMatching() {
    if (!selectedPdfs || selectedPdfs.length === 0) {
      setToast({
        type: "error",
        text: "Please select a PDF file first"
      });
      return;
    }
    setTagMatchingPreviewLoading(true);
    setTagMatchingPreviewOpen(true);

    // Build tag matching config object
    const tagMatchingConfig = {
      preset: tagMatchingPreset,
      min_parts: tagMatchingMinParts,
      max_parts: tagMatchingMaxParts,
      separators: tagMatchingSeparators,
      min_part_length: tagMatchingMinPartLength,
      max_part_length: tagMatchingMaxPartLength,
      allow_partial_match: tagMatchingAllowPartial,
      custom_regex: tagMatchingCustomRegex || null
    };
    fetch("/preview_tag_matching", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        selected_pdfs: selectedPdfs,
        tag_matching_config: tagMatchingConfig
      })
    }).then(r => r.json()).then(data => {
      setTagMatchingPreviewLoading(false);
      if (data.success) {
        setTagMatchingPreviewTags(data.matched_tags);
        logToConsole(`Tag matching preview: Found ${data.total_matched} unique tags from ${data.sample_pages} sample pages`);
        if (data.total_matched === 0) {
          setToast({
            type: "warning",
            text: "No tags matched the current configuration"
          });
        }
      } else {
        setToast({
          type: "error",
          text: data.message || "Failed to preview tag matching"
        });
        logToConsole(`Error previewing tag matching: ${data.message}`);
      }
    }).catch(err => {
      setTagMatchingPreviewLoading(false);
      setToast({
        type: "error",
        text: "Error fetching tag matching preview"
      });
      logToConsole(`Error previewing tag matching: ${err.message}`);
    });
  }

  // Color rules handlers
  function handleAddColorRule() {
    // has_value doesn't need a value to match against
    if (newRuleMatchType !== 'has_value' && !newRuleValue.trim()) {
      setToast({
        type: "error",
        text: "Please enter a value to match"
      });
      return;
    }

    // Validate header_column rule has column selected
    if (newRuleType === 'header_column' && !newRuleColumn) {
      setToast({
        type: "error",
        text: "Please select a column for header-based coloring"
      });
      return;
    }

    // Build rule object based on rule type
    const newRule = {
      id: `rule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      rule_type: newRuleType,
      value: newRuleValue.trim(),
      match_type: newRuleMatchType,
      color: newRuleColor
    };

    // Add type-specific fields
    if (newRuleType === 'tag_part') {
      newRule.part = newRulePart;
    } else if (newRuleType === 'header_column') {
      newRule.column_name = newRuleColumn;
    }
    setColorRules([...colorRules, newRule]);
    setColorRuleBuilderOpen(false);
    // Reset builder fields
    setNewRuleType('tag_part');
    setNewRulePart(1);
    setNewRuleColumn('');
    setNewRuleValue('');
    setNewRuleMatchType('contains');
    setNewRuleColor('#FFFF00');
    setRuleAvailableHeaderValues([]);
    setRuleExamples({
      matches: [],
      non_matches: []
    });
    setToast({
      type: "success",
      text: "Color rule added successfully"
    });
  }

  // Function to fetch unique values from a header column for color rule building
  function handleFetchHeaderValuesForRule(columnName) {
    if (!columnName) {
      setRuleAvailableHeaderValues([]);
      return;
    }
    setRuleLoadingHeaderValues(true);
    fetch("/get_header_unique_values", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        selected_excel: selectedExcel,
        column_name: columnName,
        header_row: headerRow
      })
    }).then(r => r.json()).then(data => {
      setRuleLoadingHeaderValues(false);
      if (data.error) {
        setToast({
          type: "error",
          text: data.error
        });
        setRuleAvailableHeaderValues([]);
      } else {
        setRuleAvailableHeaderValues(data.values || []);
        logToConsole(`Loaded ${data.values?.length || 0} unique values for column '${columnName}'`);
      }
    }).catch(err => {
      setRuleLoadingHeaderValues(false);
      setToast({
        type: "error",
        text: "Error fetching column values"
      });
      setRuleAvailableHeaderValues([]);
      logToConsole(`Error fetching header values: ${err.message}`);
    });
  }
  function handleFetchRuleExamples(columnName, matchType, value) {
    if (!columnName || !selectedExcel) {
      setRuleExamples({
        matches: [],
        non_matches: []
      });
      return;
    }
    // For match types that need a value, skip if value is empty
    if (['exact', 'contains', 'greater_than', 'less_than'].includes(matchType) && !value.trim()) {
      setRuleExamples({
        matches: [],
        non_matches: []
      });
      return;
    }
    setRuleLoadingExamples(true);
    fetch("/get_color_rule_examples", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        selected_excel: selectedExcel,
        column_name: columnName,
        match_type: matchType,
        value: value,
        tag_column: tagColumn,
        header_row: headerRow
      })
    }).then(r => r.json()).then(data => {
      setRuleLoadingExamples(false);
      setRuleExamples({
        matches: data.matches || [],
        non_matches: data.non_matches || []
      });
    }).catch(() => {
      setRuleLoadingExamples(false);
      setRuleExamples({
        matches: [],
        non_matches: []
      });
    });
  }
  function handleFetchHeaderValuesForFilter(columnName) {
    if (!columnName) {
      setAvailableHeaderValues([]);
      return;
    }
    setLoadingHeaderValues(true);
    fetch("/get_header_unique_values", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        selected_excel: selectedExcel,
        column_name: columnName,
        header_row: headerRow
      })
    }).then(r => r.json()).then(data => {
      setLoadingHeaderValues(false);
      if (data.error) {
        setToast({
          type: "error",
          text: data.error
        });
        setAvailableHeaderValues([]);
      } else {
        setAvailableHeaderValues(data.values || []);
        logToConsole(`Loaded ${data.values?.length || 0} unique values for column '${columnName}'`);
      }
    }).catch(err => {
      setLoadingHeaderValues(false);
      setToast({
        type: "error",
        text: "Error fetching column values"
      });
      setAvailableHeaderValues([]);
      logToConsole(`Error fetching header values: ${err.message}`);
    });
  }
  function handleRemoveColorRule(ruleId) {
    const updated = colorRules.filter(r => r.id !== ruleId);
    setColorRules(updated);
    setToast({
      type: "success",
      text: "Color rule removed"
    });
  }
  function handleClearAllColorRules() {
    setColorRules([]);
    setToast({
      type: "success",
      text: "All color rules cleared"
    });
  }
  function handleMoveColorRule(ruleId, direction) {
    const index = colorRules.findIndex(r => r.id === ruleId);
    if (index === -1) return;
    const newRules = [...colorRules];
    if (direction === 'up' && index > 0) {
      [newRules[index], newRules[index - 1]] = [newRules[index - 1], newRules[index]];
    } else if (direction === 'down' && index < newRules.length - 1) {
      [newRules[index], newRules[index + 1]] = [newRules[index + 1], newRules[index]];
    }
    setColorRules(newRules);
  }

  // Floating Preview Modal functions
  function openPreviewModal() {
    if (selectedPdfs.length === 0 || !selectedExcel) {
      setToast({
        type: "warning",
        text: "Please upload PDF and Excel files first"
      });
      return;
    }
    setPreviewModalOpen(true);
    // Load preview without specifying page - backend will choose smart default (total_pages / 3)
    setPreviewModalPage(null);
    loadPreviewModalPage(null);
  }
  function closePreviewModal() {
    setPreviewModalOpen(false);
    setPreviewModalData(null);
    setPdfDocument(null);
    setPreviewModalZoom(1.0);
    setModalPanOffset({
      x: 0,
      y: 0
    });
  }
  function loadPreviewModalPage(pageNum) {
    setPreviewModalLoading(true);
    const requestBody = {
      selected_pdfs: selectedPdfs,
      selected_excel: selectedExcel,
      tag_column: tagColumn,
      header_row: headerRow,
      page_number: pageNum,
      color_rules: colorRules,
      default_highlight_color: defaultHighlightColor,
      enable_default_color: enableDefaultColor,
      excel_constraint_mode: excelConstraintMode,
      excel_constraint_logic: excelConstraintLogic,
      tag_filters: tagFilters,
      filter_logic: filterLogic,
      tag_matching_config: {
        preset: tagMatchingPreset,
        min_parts: tagMatchingMinParts,
        max_parts: tagMatchingMaxParts,
        separators: tagMatchingSeparators,
        min_part_length: tagMatchingMinPartLength,
        max_part_length: tagMatchingMaxPartLength,
        allow_partial: tagMatchingAllowPartial,
        custom_regex: tagMatchingCustomRegex
      },
      // Include ALL settings for complete preview
      comment_columns: commentColumns,
      watermark_enabled: watermarkEnabled,
      watermark_attributes: watermarkAttributes,
      watermark_text_color: watermarkTextColor,
      watermark_font_size: watermarkFontSize,
      watermark_background_enabled: watermarkBackgroundEnabled
    };

    // Use the new comprehensive preview endpoint that generates actual PDF
    fetch('/generate_full_preview', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestBody)
    }).then(r => r.json()).then(data => {
      setPreviewModalLoading(false);
      if (data.success) {
        setPreviewModalData(data);
        // Update page number to match the actual page that was processed
        setPreviewModalPage(data.page_number);
        const statsMsg = `Page ${data.page_number} of ${data.total_pages}, ${data.stats.colored_tags}/${data.stats.total_tags} tags colored`;
        logToConsole(`Preview generated: ${statsMsg}`);
        setToast({
          type: "success",
          text: `Preview ready! Page ${data.page_number} processed successfully.`
        });
      } else {
        setToast({
          type: "error",
          text: data.message || 'Failed to load preview'
        });
      }
    }).catch(err => {
      setPreviewModalLoading(false);
      setToast({
        type: "error",
        text: `Error: ${err.message}`
      });
    });
  }
  function handleModalPageChange(direction) {
    if (!previewModalData) return;
    const newPage = direction === 'next' ? Math.min(previewModalPage + 1, previewModalData.total_pages) : Math.max(previewModalPage - 1, 1);
    if (newPage !== previewModalPage) {
      setPreviewModalPage(newPage);
      setTimeout(() => loadPreviewModalPage(newPage), 100);
    }
  }
  function handleModalGoToPage(pageNum) {
    if (!previewModalData || pageNum < 1 || pageNum > previewModalData.total_pages) return;
    setPreviewModalPage(pageNum);
    setTimeout(() => loadPreviewModalPage(pageNum), 100);
  }
  function handleModalZoom(action, value = null) {
    if (action === 'in') {
      setPreviewModalZoom(prev => Math.min(4.0, prev + 0.25));
    } else if (action === 'out') {
      setPreviewModalZoom(prev => Math.max(0.25, prev - 0.25));
    } else if (action === 'reset') {
      setPreviewModalZoom(1.0);
      setModalPanOffset({
        x: 0,
        y: 0
      });
    } else if (action === 'fitWidth') {
      setPreviewModalZoom(1.0);
      setModalPanOffset({
        x: 0,
        y: 0
      });
    } else if (action === 'fitHeight') {
      setPreviewModalZoom(1.0);
      setModalPanOffset({
        x: 0,
        y: 0
      });
    } else if (action === 'set' && value !== null) {
      setPreviewModalZoom(parseFloat(value));
    }
  }
  function handleModalWheel(e) {
    // Allow zoom with or without Ctrl key, prevent browser scroll
    e.preventDefault();
    e.stopPropagation();
    const container = previewModalContainerRef.current;
    const canvas = previewCanvasRef.current;
    if (!container || !canvas) return;

    // Get mouse position relative to container
    const rect = container.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    // Calculate zoom delta
    const delta = e.deltaY > 0 ? -0.1 : 0.1;
    const oldZoom = previewModalZoom;
    const newZoom = Math.max(0.25, Math.min(4.0, oldZoom + delta));

    // Calculate the point under the mouse in the canvas coordinate system
    // Account for current pan offset
    const canvasRect = canvas.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();

    // Mouse position relative to canvas
    const canvasMouseX = e.clientX - canvasRect.left;
    const canvasMouseY = e.clientY - canvasRect.top;

    // Update zoom
    setPreviewModalZoom(newZoom);

    // Adjust pan offset to keep the point under the mouse stable
    const zoomRatio = newZoom / oldZoom;
    setModalPanOffset(prev => ({
      x: prev.x - canvasMouseX * (zoomRatio - 1),
      y: prev.y - canvasMouseY * (zoomRatio - 1)
    }));
  }
  function handleModalMouseDown(e) {
    if (e.button !== 0) return;
    setIsModalDragging(true);
    setModalDragStart({
      x: e.clientX - modalPanOffset.x,
      y: e.clientY - modalPanOffset.y
    });
  }
  function handleModalMouseMove(e) {
    if (isModalDragging) {
      e.preventDefault();
      setModalPanOffset({
        x: e.clientX - modalDragStart.x,
        y: e.clientY - modalDragStart.y
      });
    }
  }
  function handleModalMouseUp(e) {
    setIsModalDragging(false);
  }

  // Keyboard shortcuts for modal
  useEffect(() => {
    function handleModalKeyPress(e) {
      if (!previewModalOpen) return;
      if (e.key === 'Escape') {
        closePreviewModal();
      } else if (e.key === 'ArrowLeft') {
        handleModalPageChange('prev');
      } else if (e.key === 'ArrowRight') {
        handleModalPageChange('next');
      }
    }
    window.addEventListener('keydown', handleModalKeyPress);
    return () => window.removeEventListener('keydown', handleModalKeyPress);
  }, [previewModalOpen, previewModalPage, previewModalData]);

  // Disable main window scrolling when preview window is active
  useEffect(() => {
    if (previewModalOpen) {
      // Disable body scrolling when preview is open
      document.body.style.overflow = 'hidden';
    } else {
      // Restore body scrolling when preview is closed
      document.body.style.overflow = '';
    }

    // Cleanup: restore scrolling on unmount
    return () => {
      document.body.style.overflow = '';
    };
  }, [previewModalOpen]);

  // PDF.js loading effect - load PDF document once when data changes
  useEffect(() => {
    if (!previewModalData || !previewModalData.pdf_url) return;
    let isMounted = true;
    const loadingTask = pdfjsLib.getDocument(previewModalData.pdf_url);
    loadingTask.promise.then(pdf => {
      if (isMounted) {
        setPdfDocument(pdf);
      }
    }).catch(err => {
      if (isMounted) {
        console.error('Error loading PDF:', err);
        setToast({
          type: 'error',
          text: 'Failed to load PDF preview'
        });
      }
    });
    return () => {
      isMounted = false;
      if (pdfDocument) {
        pdfDocument.destroy();
      }
    };
  }, [previewModalData?.pdf_url]);

  // PDF.js rendering effect - re-render when zoom changes
  useEffect(() => {
    if (!pdfDocument || !previewCanvasRef.current) return;
    const canvas = previewCanvasRef.current;
    const context = canvas.getContext('2d');
    let renderTask = null;
    pdfDocument.getPage(1).then(page => {
      const viewport = page.getViewport({
        scale: previewModalZoom
      });

      // Set canvas dimensions
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      const renderContext = {
        canvasContext: context,
        viewport: viewport
      };

      // Cancel previous render if still running
      if (renderTask) {
        renderTask.cancel();
      }
      renderTask = page.render(renderContext);
      return renderTask.promise;
    }).catch(err => {
      if (err.name !== 'RenderingCancelledException') {
        console.error('Error rendering PDF:', err);
      }
    });
    return () => {
      if (renderTask) {
        renderTask.cancel();
      }
    };
  }, [pdfDocument, previewModalZoom]);
  function startProcessing(isTest) {
    // Validate that files are selected
    if (selectedPdfs.length === 0) {
      setToast({
        type: "error",
        text: "Please select at least one PDF file to process"
      });
      return;
    }
    if (!selectedExcel) {
      setToast({
        type: "error",
        text: "Please select an Excel/CSV file from the workspace"
      });
      return;
    }
    setProcessingOpen(true);
    setProcessingTitle(isTest ? "Test Run (100 tags)" : "Processing Files");
    setProgress(0);
    setStatusText("Initializing...");
    setErrorText(null);
    setFileCount(0);
    setReportFilename(null);
    setIsCurrentTestRun(isTest);
    const data = {
      header_row: Number(headerRow) || 1,
      tag_column: tagColumn || "",
      comment_columns: commentColumns.length > 0 ? commentColumns : null,
      highlight_color: highlightColor,
      highlight_column: highlightColumn,
      annotate_excel: annotateExcel,
      watermark_enabled: watermarkEnabled,
      watermark_attributes: watermarkAttributes,
      watermark_text_color: watermarkTextColor,
      watermark_font_size: watermarkFontSize,
      watermark_background_enabled: watermarkBackgroundEnabled,
      max_tags: isTest ? 100 : null,
      is_test: isTest,
      selected_pdfs: selectedPdfs,
      // Send selected PDF filenames
      selected_excel: selectedExcel,
      // Send selected Excel filename
      tag_matching_config: {
        preset: tagMatchingPreset,
        min_parts: tagMatchingMinParts,
        max_parts: tagMatchingMaxParts,
        separators: tagMatchingSeparators,
        min_part_length: tagMatchingMinPartLength,
        max_part_length: tagMatchingMaxPartLength,
        allow_partial_match: tagMatchingAllowPartial,
        custom_regex: tagMatchingCustomRegex || null
      },
      tag_filters: tagFilters,
      // Send tag filters
      filter_logic: filterLogic,
      // Send filter logic (AND/OR)
      color_rules: colorRules,
      // Send color rules
      default_highlight_color: defaultHighlightColor,
      // Send default highlight color
      enable_default_color: enableDefaultColor,
      // Send enable default color flag
      excel_constraint_mode: excelConstraintMode,
      // Send excel constraint mode
      excel_constraint_logic: excelConstraintLogic // Send excel constraint logic (AND/OR)
    };
    logToConsole(isTest ? `Starting test run (100 tags) with ${selectedPdfs.length} PDF(s)...` : `Starting full processing with ${selectedPdfs.length} PDF(s)...`);
    fetch("/process", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    }).then(r => r.json()).then(data => {
      if (data.success) {
        setCurrentTaskId(data.task_id);
        setFileCount(data.file_count || 0);
        logToConsole(`Processing started with task ID: ${data.task_id}`);
        startProgressPolling(data.task_id);
      } else {
        setErrorText(data.message || "Failed to start processing");
        setStatusText("Error starting processing");
        logToConsole(`Error starting processing: ${data.message}`);
      }
    }).catch(err => {
      setErrorText(err.message);
      setStatusText("Error starting processing");
      logToConsole(`Error starting processing: ${err.message}`);
    });
  }
  function startProgressPolling(taskId) {
    if (pollRef.current) {
      clearInterval(pollRef.current);
    }
    pollRef.current = setInterval(() => {
      fetch(`/progress/${taskId}`).then(r => r.json()).then(data => {
        if (typeof data.progress === "number" && data.progress >= 0) {
          setProgress(data.progress);
          setStatusText(data.status || "");
        }
        if (data.progress === 100) {
          // Extract file count from status if present
          const statusMessage = data.status || "";
          const fileCountMatch = statusMessage.match(/(\d+)\s+PDF\(s\)/);
          const count = fileCountMatch ? parseInt(fileCountMatch[1], 10) : fileCount || 1;
          setFileCount(count);
          clearInterval(pollRef.current);
          pollRef.current = null;
          logToConsole("Processing complete! (detected via polling)");
        } else if (data.progress === -1) {
          setErrorText(data.status || "Processing failed");
          clearInterval(pollRef.current);
          pollRef.current = null;
          logToConsole(`Error detected via polling: ${data.status}`);
        }
      }).catch(err => {
        logToConsole(`Error polling progress: ${err.message}`);
      });
    }, 2000);
  }

  // Profile Management Functions
  // Load server profiles (read-only)
  function loadProfilesAndTemplates() {
    // Load server template profiles (read-only)
    fetch("/api/profiles").then(r => r.json()).then(data => {
      if (data.success) {
        setServerProfiles(data.profiles || []);
        logToConsole(`Loaded ${data.count || 0} server template profiles`);
      }
    }).catch(err => {
      logToConsole(`Error loading server profiles: ${err.message}`);
    });
  }

  // Generate profile preview (client-side)
  function generateProfilePreview(profile) {
    if (!profile) {
      setProfilePreview(null);
      return;
    }
    const settings = profile.settings || {};
    const complexity = calculateProfileComplexity(settings);
    setProfilePreview({
      name: profile.name || 'Unknown',
      description: profile.description || '',
      complexity: complexity,
      settings: {
        tagColumn: settings.tag_column !== null && settings.tag_column !== undefined ? `Column ${settings.tag_column}` : 'Not configured',
        highlightColor: settings.highlight_color || '#FFFF00',
        highlightColumn: settings.highlight_column !== null && settings.highlight_column !== undefined ? `Column ${settings.highlight_column}` : 'Not configured',
        commentColumns: settings.comment_columns && settings.comment_columns.length > 0 ? `${settings.comment_columns.length} column(s)` : 'None',
        annotateExcel: settings.annotate_excel ? 'Enabled' : 'Disabled',
        watermark: settings.watermark_enabled ? 'Enabled' : 'Disabled',
        tagMatchingPreset: settings.tag_matching_preset || 'Standard',
        headerRow: settings.header_row || 6,
        colorRules: settings.color_rules && settings.color_rules.length > 0 ? `${settings.color_rules.length} rule(s)` : 'None',
        tagFilters: settings.tag_filters && settings.tag_filters.length > 0 ? `${settings.tag_filters.length} filter(s)` : 'None'
      }
    });
  }
  function calculateProfileComplexity(settings) {
    let score = 0;
    if (settings.annotate_excel) score += 2;
    if (settings.watermark_enabled) score += 3;
    if (settings.comment_columns && settings.comment_columns.length > 0) score += 1;
    if (settings.color_rules && settings.color_rules.length > 0) score += 2;
    if (settings.tag_filters && settings.tag_filters.length > 0) score += 1;
    if (score >= 5) return 'Comprehensive';
    if (score >= 2) return 'Moderate';
    return 'Minimal';
  }

  // Generate preview of current settings loaded from browser
  function generateCurrentSettingsPreview() {
    const settings = getCurrentSettings();
    const complexity = calculateProfileComplexity(settings);
    setCurrentSettingsPreview({
      name: 'Current Settings (Browser)',
      description: 'Settings loaded from your browser cache',
      complexity: complexity,
      settings: {
        tagColumn: settings.tag_column !== null && settings.tag_column !== undefined ? `Column ${settings.tag_column}` : 'Not configured',
        highlightColor: settings.highlight_color || '#FFFF00',
        highlightColumn: settings.highlight_column !== null && settings.highlight_column !== undefined ? `Column ${settings.highlight_column}` : 'Not configured',
        commentColumns: settings.comment_columns && settings.comment_columns.length > 0 ? `${settings.comment_columns.length} column(s)` : 'None',
        annotateExcel: settings.annotate_excel ? 'Enabled' : 'Disabled',
        watermark: settings.watermark_enabled ? 'Enabled' : 'Disabled',
        tagMatchingPreset: settings.tag_matching_preset || 'Standard',
        headerRow: settings.header_row || 6,
        colorRules: settings.color_rules && settings.color_rules.length > 0 ? `${settings.color_rules.length} rule(s)` : 'None',
        tagFilters: settings.tag_filters && settings.tag_filters.length > 0 ? `${settings.tag_filters.length} filter(s)` : 'None'
      }
    });
  }

  // Apply settings from profile to state
  function applyProfileSettings(settings) {
    if (settings.header_row !== undefined) setHeaderRow(settings.header_row);
    if (settings.tag_column !== undefined && settings.tag_column !== null) setTagColumn(settings.tag_column);
    if (settings.comment_columns !== undefined) setCommentColumns(settings.comment_columns);
    if (settings.highlight_column !== undefined) setHighlightColumn(settings.highlight_column);
    if (settings.highlight_color !== undefined) setHighlightColor(settings.highlight_color);
    if (settings.annotate_excel !== undefined) setAnnotateExcel(settings.annotate_excel);
    if (settings.watermark_enabled !== undefined) setWatermarkEnabled(settings.watermark_enabled);
    if (settings.watermark_attributes !== undefined) setWatermarkAttributes(settings.watermark_attributes);
    if (settings.watermark_text_color !== undefined) setWatermarkTextColor(settings.watermark_text_color);
    if (settings.watermark_background_enabled !== undefined) setWatermarkBackgroundEnabled(settings.watermark_background_enabled);
    if (settings.watermark_font_size !== undefined) setWatermarkFontSize(settings.watermark_font_size);

    // Apply tag matching settings
    if (settings.tag_matching_preset !== undefined) setTagMatchingPreset(settings.tag_matching_preset);
    if (settings.tag_matching_min_parts !== undefined) setTagMatchingMinParts(settings.tag_matching_min_parts);
    if (settings.tag_matching_max_parts !== undefined) setTagMatchingMaxParts(settings.tag_matching_max_parts);
    if (settings.tag_matching_separators !== undefined) setTagMatchingSeparators(settings.tag_matching_separators);
    if (settings.tag_matching_min_part_length !== undefined) setTagMatchingMinPartLength(settings.tag_matching_min_part_length);
    if (settings.tag_matching_max_part_length !== undefined) setTagMatchingMaxPartLength(settings.tag_matching_max_part_length);
    if (settings.tag_matching_allow_partial !== undefined) setTagMatchingAllowPartial(settings.tag_matching_allow_partial);
    if (settings.tag_matching_custom_regex !== undefined) setTagMatchingCustomRegex(settings.tag_matching_custom_regex);

    // Apply color rules
    if (settings.color_rules !== undefined) setColorRules(settings.color_rules);
    if (settings.default_highlight_color !== undefined) setDefaultHighlightColor(settings.default_highlight_color);
    if (settings.enable_default_color !== undefined) setEnableDefaultColor(settings.enable_default_color);
    if (settings.excel_constraint_mode !== undefined) setExcelConstraintMode(settings.excel_constraint_mode);
    if (settings.excel_constraint_logic !== undefined) setExcelConstraintLogic(settings.excel_constraint_logic);

    // Apply tag filters
    if (settings.tag_filters !== undefined) setTagFilters(settings.tag_filters);
    if (settings.filter_logic !== undefined) setFilterLogic(settings.filter_logic);
  }

  // Get current settings as object
  function getCurrentSettings() {
    return {
      header_row: headerRow,
      tag_column: tagColumn,
      comment_columns: commentColumns,
      highlight_column: highlightColumn,
      highlight_color: highlightColor,
      annotate_excel: annotateExcel,
      watermark_enabled: watermarkEnabled,
      watermark_attributes: watermarkAttributes,
      watermark_text_color: watermarkTextColor,
      watermark_font_size: watermarkFontSize,
      watermark_background_enabled: watermarkBackgroundEnabled,
      tag_matching_preset: tagMatchingPreset,
      tag_matching_min_parts: tagMatchingMinParts,
      tag_matching_max_parts: tagMatchingMaxParts,
      tag_matching_separators: tagMatchingSeparators,
      tag_matching_min_part_length: tagMatchingMinPartLength,
      tag_matching_max_part_length: tagMatchingMaxPartLength,
      tag_matching_allow_partial: tagMatchingAllowPartial,
      tag_matching_custom_regex: tagMatchingCustomRegex,
      // Color rules
      color_rules: colorRules,
      default_highlight_color: defaultHighlightColor,
      enable_default_color: enableDefaultColor,
      excel_constraint_mode: excelConstraintMode,
      excel_constraint_logic: excelConstraintLogic,
      // Tag filters
      tag_filters: tagFilters,
      filter_logic: filterLogic
    };
  }

  // Save settings to localStorage (auto-save)
  function saveToLocalStorage() {
    try {
      const settings = getCurrentSettings();
      localStorage.setItem('annotator_profile', JSON.stringify(settings));
      logToConsole('Settings auto-saved to browser');
    } catch (err) {
      logToConsole(`Error saving to localStorage: ${err.message}`);
    }
  }

  // Load settings from localStorage
  function loadFromLocalStorage() {
    try {
      const saved = localStorage.getItem('annotator_profile');
      if (saved) {
        const settings = JSON.parse(saved);
        applyProfileSettings(settings);
        logToConsole('Settings loaded from browser');
        setToast({
          type: "success",
          text: "Settings restored from browser"
        });
        return true;
      }
    } catch (err) {
      logToConsole(`Error loading from localStorage: ${err.message}`);
    }
    return false;
  }

  // Load selected profile (built-in template or server template)
  function loadSelectedProfile() {
    if (!selectedProfile) {
      setToast({
        type: "warning",
        text: "No profile selected"
      });
      return;
    }
    if (selectedProfile.startsWith('server:')) {
      // Load server template profile
      const filename = selectedProfile.replace('server:', '');
      fetch(`/api/profiles/${filename}`).then(r => r.json()).then(data => {
        if (data.success) {
          applyProfileSettings(data.profile.settings);
          saveToLocalStorage(); // Auto-save to localStorage
          setActiveProfileName(data.profile.name);
          setToast({
            type: "success",
            text: `Server profile "${data.profile.name}" loaded`
          });
          logToConsole(`Loaded server profile: ${data.profile.name}`);
        } else {
          setToast({
            type: "error",
            text: data.message
          });
        }
      }).catch(err => {
        setToast({
          type: "error",
          text: err.message
        });
      });
    }
  }

  // Export current settings as JSON file (download to user's computer)
  function exportCurrentProfile() {
    const profileData = {
      name: activeProfileName || 'exported_profile',
      description: 'Exported profile from PID Annotator',
      version: '1.1',
      exported_at: new Date().toISOString(),
      settings: getCurrentSettings()
    };
    const blob = new Blob([JSON.stringify(profileData, null, 2)], {
      type: 'application/json'
    });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `annotator_profile_${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
    setToast({
      type: "success",
      text: "Profile exported successfully"
    });
    logToConsole('Current settings exported as JSON file');
  }

  // Import profile from JSON file (load from user's computer)
  function importProfileFile(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = e => {
      try {
        const profileData = JSON.parse(e.target.result);

        // Validate profile structure
        if (!profileData.settings) {
          setToast({
            type: "error",
            text: "Invalid profile file: missing settings"
          });
          return;
        }

        // Apply the settings
        applyProfileSettings(profileData.settings);
        saveToLocalStorage(); // Save to localStorage
        setActiveProfileName(profileData.name || 'Imported Profile');
        setToast({
          type: "success",
          text: `Profile "${profileData.name || 'Imported'}" loaded`
        });
        logToConsole(`Imported profile: ${profileData.name || 'unknown'}`);
        setShowImportProfileModal(false);
      } catch (err) {
        setToast({
          type: "error",
          text: `Error parsing profile: ${err.message}`
        });
        logToConsole(`Error importing profile: ${err.message}`);
      }
    };
    reader.onerror = () => {
      setToast({
        type: "error",
        text: "Error reading file"
      });
    };
    reader.readAsText(file);
  }

  // Workspace functions
  function refreshWorkspace() {
    fetch("/list_workspace_files").then(r => r.json()).then(data => {
      if (data.success) {
        setWorkspaceFiles(data.files);
        logToConsole(`Workspace refreshed: ${data.total} files`);

        // Auto-select all PDFs if none are selected yet
        if (selectedPdfs.length === 0 && data.files.pdfs.length > 0) {
          setSelectedPdfs(data.files.pdfs.map(f => f.filename));
        }

        // Excel file selection logic:
        // 1. If no Excel file is selected AND Excel files exist -> select first one
        // 2. If an Excel file is selected BUT it no longer exists in workspace -> select first available one
        // 3. Always ensure one Excel file is selected when Excel files are available

        const hasExcelFiles = data.files.excel.length > 0;
        const selectedExcelStillExists = selectedExcel && data.files.excel.some(f => f.filename === selectedExcel);
        if (hasExcelFiles && (!selectedExcel || !selectedExcelStillExists)) {
          const firstExcel = data.files.excel[0].filename;
          setSelectedExcel(firstExcel);
          logToConsole(`Auto-selected Excel file: ${data.files.excel[0].name}`);

          // Load columns for the auto-selected Excel file
          setLoadingColumns(true);
          fetch("/select_excel", {
            method: "POST",
            headers: {
              "Content-Type": "application/json"
            },
            body: JSON.stringify({
              excel_file: firstExcel,
              header_row: 6
            })
          }).then(r => r.json()).then(colData => {
            if (colData.success) {
              onColumnsLoaded(colData.columns, colData.default_tag_column);
            }
          }).catch(err => {
            console.error("Error loading columns for auto-selected Excel:", err);
          }).finally(() => {
            setLoadingColumns(false);
          });
        } else if (!hasExcelFiles && selectedExcel) {
          // No Excel files in workspace but one is selected -> clear selection
          setSelectedExcel(null);
          setExcelColumns([]);
          setTagColumn("");
          logToConsole("No Excel files in workspace - cleared selection");
        }
      } else {
        logToConsole(`Error refreshing workspace: ${data.message}`);
      }
    }).catch(err => {
      logToConsole(`Error refreshing workspace: ${err.message}`);
    });
  }
  function addOutputsToWorkspace(outputFiles) {
    if (!outputFiles || outputFiles.length === 0) return;
    fetch("/add_outputs_to_workspace", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        output_files: outputFiles
      })
    }).then(r => r.json()).then(data => {
      if (data.success) {
        logToConsole(`Added ${data.moved_files.length} PDFs to workspace`);
        refreshWorkspace();
      } else {
        logToConsole(`Error adding outputs to workspace: ${data.message}`);
      }
    }).catch(err => {
      logToConsole(`Error adding outputs to workspace: ${err.message}`);
    });
  }

  // Load workspace files on mount
  useEffect(() => {
    refreshWorkspace();
  }, []);

  // Load profiles, templates, and restore settings from localStorage on mount
  useEffect(() => {
    loadProfilesAndTemplates();
    // Try to restore settings from localStorage
    const restored = loadFromLocalStorage();
    if (!restored) {
      logToConsole('No saved settings found in browser, using defaults');
    }
  }, []);

  // Auto-save settings to localStorage whenever they change
  useEffect(() => {
    saveToLocalStorage();
    // Also update the current settings preview
    generateCurrentSettingsPreview();
  }, [headerRow, tagColumn, commentColumns, highlightColumn, highlightColor, annotateExcel, watermarkEnabled, watermarkAttributes, watermarkTextColor, watermarkBackgroundEnabled, tagMatchingPreset, tagMatchingMinParts, tagMatchingMaxParts, tagMatchingSeparators, tagMatchingMinPartLength, tagMatchingMaxPartLength, tagMatchingAllowPartial, tagMatchingCustomRegex, colorRules, defaultHighlightColor, enableDefaultColor, excelConstraintMode, excelConstraintLogic, tagFilters, filterLogic]);

  // Monitor selected Excel file and disable annotation for .xls files
  useEffect(() => {
    if (!selectedExcel) {
      setAnnotateExcelEnabled(false);
      return;
    }

    // Find the selected Excel file in workspaceFiles
    const excelFile = workspaceFiles.excel?.find(f => f.filename === selectedExcel);
    if (excelFile) {
      // Enable annotation only for .xlsx files
      const supportsAnnotation = excelFile.supportsAnnotation !== false;
      setAnnotateExcelEnabled(supportsAnnotation);

      // Auto-disable annotateExcel if file doesn't support annotation (silently, no warning)
      if (!supportsAnnotation && annotateExcel) {
        setAnnotateExcel(false);
      }
    } else {
      setAnnotateExcelEnabled(false);
    }
  }, [selectedExcel, workspaceFiles.excel]);

  // Socket listeners
  useEffect(() => {
    function onConnect() {
      logToConsole("Connected to server");
    }
    function onDisconnect() {
      logToConsole("Disconnected from server");
    }
    function onConnectError(error) {
      logToConsole("Connection error: " + error);
    }
    function onProgress(data) {
      logToConsole(`[DEBUG] Received progress update: task_id=${data.task_id}, progress=${data.progress}, status=${data.status}`);
      if (data.task_id === currentTaskId) {
        if (typeof data.progress === "number" && data.progress >= 0) {
          setProgress(data.progress);
          setStatusText(data.status || "");
          if (data.progress === 100) {
            const statusMessage = data.status || "";
            const fileCountMatch = statusMessage.match(/(\d+)\s+PDF\(s\)/);
            const count = fileCountMatch ? parseInt(fileCountMatch[1], 10) : fileCount || 1;
            setFileCount(count);
            logToConsole("Processing complete! Download is now available!");

            // Get output files from server (for report tracking only, outputs stay separate)
            fetch("/download").then(r => r.json()).then(data => {
              if (data && data.success) {
                // Extract output files info
                const outputFiles = data.output_files || [];
                logToConsole(`Processing completed with ${outputFiles.length} output files`);

                // Find report file (starts with session ID and contains "report_")
                const reportFile = outputFiles.find(f => f.includes('_report_') && f.endsWith('.html'));
                if (reportFile) {
                  setReportFilename(reportFile);
                  logToConsole(`Report available: ${reportFile}`);
                }

                // Output files stay in OUTPUT_FOLDER and are only accessible via download popup
                // They will NOT be added to the workspace/upload area
              }
            }).catch(err => {
              logToConsole(`Error fetching output files: ${err.message}`);
            });
          }
        } else {
          setErrorText(data.status || "Processing failed");
          logToConsole(`Error: ${data.status}`);
        }
      }
    }
    socket.on("connect", onConnect);
    socket.on("disconnect", onDisconnect);
    socket.on("connect_error", onConnectError);
    socket.on("progress_update", onProgress);
    return () => {
      socket.off("connect", onConnect);
      socket.off("disconnect", onDisconnect);
      socket.off("connect_error", onConnectError);
      socket.off("progress_update", onProgress);
    };
  }, [socket, currentTaskId, fileCount]);

  // Fetch available tag parts when Excel file or tag column changes
  useEffect(() => {
    if (selectedExcel && tagColumn) {
      fetch("/get_tag_parts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          selected_excel: selectedExcel,
          tag_column: tagColumn,
          header_row: headerRow
        })
      }).then(r => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      }).then(data => {
        if (data.success) {
          setAvailableTagParts(data.parts || {});
          logToConsole(`Loaded tag parts: ${Object.keys(data.parts || {}).length} parts available`);
        } else {
          logToConsole(`Warning: ${data.message || 'Failed to load tag parts'}`);
        }
      }).catch(err => {
        logToConsole(`Error fetching tag parts: ${err.message}`);
        // Clear available parts on error to prevent stale data
        setAvailableTagParts({});
      });
    }
  }, [selectedExcel, tagColumn, headerRow]);
  function closeProcessing() {
    setProcessingOpen(false);
    setErrorText(null);
    setProgress(0);
    setStatusText("Initializing...");
    setReportFilename(null);
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }
  function downloadFromModal(fileType = 'pdf') {
    logToConsole(`Starting download from modal... (type: ${fileType})`);
    fetch(`/download?type=${fileType}`).then(r => r.json()).then(data => {
      logToConsole(`[DEBUG] Download JSON response: ${JSON.stringify(data)}`);
      if (data.success && Array.isArray(data.files)) {
        logToConsole(`Starting download of ${data.file_count || data.files.length} files...`);
        logToConsole(`[DEBUG] File URLs: ${JSON.stringify(data.files)}`);
        sequentialDownloads(data.files, fileType);
      } else {
        logToConsole(`Download error: ${data.message}`);
        setToast({
          type: "error",
          text: data.message || "Download error"
        });
      }
    }).catch(err => {
      logToConsole(`Download error: ${err.message}`);
      setToast({
        type: "error",
        text: `Download failed: ${err.message}`
      });
    });
  }
  function sequentialDownloads(urls, fileType = 'pdf') {
    let i = 0;
    function next() {
      if (i < urls.length) {
        const a = document.createElement("a");
        a.href = urls[i];
        a.download = "";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        i += 1;
        setTimeout(next, 1000);
      } else {
        logToConsole("All files downloaded successfully!");
        // Only trigger cleanup for PDF/Excel downloads, not for report downloads
        if (fileType !== 'report') {
          cleanupAfterDownload();
        } else {
          logToConsole("Report downloaded - no cleanup needed");
          setToast({
            type: "success",
            text: "Report downloaded successfully!"
          });
        }
      }
    }
    next();
  }
  function cleanupAfterDownload() {
    logToConsole("Starting post-download cleanup...");

    // Determine cleanup type based on whether this was a test run
    const isTestCleanup = isCurrentTestRun;
    fetch("/cleanup_after_download", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      }
    }).then(r => r.json()).then(data => {
      if (data.success) {
        const deletedCount = (data.deleted_uploads || 0) + (data.deleted_outputs || 0);
        if (isTestCleanup) {
          logToConsole(`Test cleanup successful: deleted ${data.deleted_outputs} test output(s). Uploads preserved.`);
          setToast({
            type: "success",
            text: `Test files downloaded! Upload data preserved. Ready for full run.`
          });
          // Modal stays open for additional downloads
        } else {
          logToConsole(`Full cleanup successful: deleted ${data.deleted_outputs} Excel output(s). PDFs remain in workspace.`);
          setToast({
            type: "success",
            text: `Files downloaded! Annotated PDFs added to workspace for reprocessing.`
          });
          // Modal stays open for additional downloads
        }
      } else {
        logToConsole(`Cleanup error: ${data.message}`);
        setToast({
          type: "error",
          text: `Cleanup failed: ${data.message}`
        });
      }
    }).catch(err => {
      logToConsole(`Cleanup error: ${err.message}`);
      setToast({
        type: "error",
        text: `Cleanup failed: ${err.message}`
      });
    });
  }
  function handleClearSession() {
    // Show confirmation dialog
    const confirmed = window.confirm("This will delete all uploaded files and reset the session. Are you sure you want to continue?");
    if (!confirmed) {
      return;
    }
    logToConsole("Clearing session...");
    fetch("/clear_session", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      }
    }).then(r => r.json()).then(data => {
      if (data.success) {
        logToConsole(data.message || "Session cleared successfully");

        // Reset all UI state
        setUploadedFiles({
          excel: [],
          pdf: []
        });
        setExcelColumns([]);
        setTagColumn("");
        setCommentColumns([]);
        setHeaderRow(6);
        setHighlightColumn("");
        setHighlightColor("#FFFF00");
        setAnnotateExcel(false);
        setWatermarkEnabled(false);
        setWatermarkAttributes([]);
        setWatermarkTextColor("#000000");
        setWatermarkBackgroundEnabled(false);

        // Show success toast
        setToast({
          type: "success",
          text: data.message || "Session cleared successfully"
        });
      } else {
        logToConsole(`Error clearing session: ${data.message}`);
        setToast({
          type: "error",
          text: data.message || "Failed to clear session"
        });
      }
    }).catch(err => {
      logToConsole(`Error clearing session: ${err.message}`);
      setToast({
        type: "error",
        text: `Error clearing session: ${err.message}`
      });
    });
  }
  return /*#__PURE__*/React.createElement("div", {
    className: "flex min-h-screen flex-col"
  }, /*#__PURE__*/React.createElement(Header, null), /*#__PURE__*/React.createElement("main", {
    className: "mx-auto w-full max-w-6xl flex-1 px-4 sm:px-6 py-6 sm:py-8 space-y-6"
  }, /*#__PURE__*/React.createElement(SectionCard, {
    title: /*#__PURE__*/React.createElement("span", {
      className: "flex items-center"
    }, "File Workspace", /*#__PURE__*/React.createElement(HelpIcon, {
      content: HELP_CONTENT.fileWorkspace
    }))
  }, /*#__PURE__*/React.createElement(FileWorkspace, {
    workspaceFiles: workspaceFiles,
    selectedPdfs: selectedPdfs,
    selectedExcel: selectedExcel,
    onSelectionChange: setSelectedPdfs,
    onExcelSelectionChange: setSelectedExcel,
    onDeleteFile: () => {},
    onUploadFiles: () => {},
    onColumnsLoaded: onColumnsLoaded,
    setToast: setToast,
    onRefresh: refreshWorkspace,
    loadingColumns: loadingColumns,
    setLoadingColumns: setLoadingColumns
  })), /*#__PURE__*/React.createElement(SectionCard, {
    title: "Options & Configurations"
  }, /*#__PURE__*/React.createElement("div", {
    className: "space-y-6"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    className: "text-sm font-semibold text-zinc-500 dark:text-zinc-400 mb-3"
  }, "Configuration"), /*#__PURE__*/React.createElement("div", {
    className: "grid gap-4 sm:grid-cols-2"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    htmlFor: "header-row",
    className: "block text-sm font-medium mb-1 flex items-center"
  }, /*#__PURE__*/React.createElement("span", {
    className: "flex items-center"
  }, "Header Row", /*#__PURE__*/React.createElement(HelpIcon, {
    content: HELP_CONTENT.headerRow
  })), loadingColumns && /*#__PURE__*/React.createElement("span", {
    className: "ml-2 text-xs text-brand"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-spinner fa-spin"
  }), " Loading...")), /*#__PURE__*/React.createElement("select", {
    id: "header-row",
    value: headerRow,
    onChange: e => {
      const v = Number(e.target.value);
      setHeaderRow(v);
      reloadColumnsForHeaderRow(v);
    },
    disabled: loadingColumns,
    className: "w-full rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/60 disabled:opacity-50 disabled:cursor-not-allowed"
  }, [...Array(20)].map((_, i) => {
    const rowNum = i + 1;
    return /*#__PURE__*/React.createElement("option", {
      key: rowNum,
      value: rowNum
    }, "Row ", rowNum);
  })), /*#__PURE__*/React.createElement("div", {
    className: "mt-1 text-xs text-zinc-500 dark:text-zinc-400"
  }, "Default: 6")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    htmlFor: "tag-column",
    className: "block text-sm font-medium mb-1 flex items-center"
  }, /*#__PURE__*/React.createElement("span", {
    className: "flex items-center"
  }, "Tag Column", /*#__PURE__*/React.createElement(HelpIcon, {
    content: HELP_CONTENT.tagColumn
  }))), /*#__PURE__*/React.createElement("select", {
    id: "tag-column",
    value: tagColumn,
    onChange: e => {
      const val = e.target.value;
      setTagColumn(val);
      // keep all comments except tag
      setCommentColumns(excelColumns.filter(c => c !== val));
    },
    className: "w-full rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-brand/60"
  }, excelColumns.length === 0 && /*#__PURE__*/React.createElement("option", {
    value: ""
  }, "Select Excel file first"), excelColumns.map(c => /*#__PURE__*/React.createElement("option", {
    key: c,
    value: c
  }, c)))))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    className: "text-sm font-semibold text-zinc-500 dark:text-zinc-400 mb-3 flex items-center"
  }, /*#__PURE__*/React.createElement("span", {
    className: "flex items-center"
  }, "Comment Columns", /*#__PURE__*/React.createElement(HelpIcon, {
    content: HELP_CONTENT.commentColumns
  }))), /*#__PURE__*/React.createElement("div", {
    className: "mb-3 flex flex-wrap gap-2"
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => setCommentColumns(excelColumns.filter(c => c !== tagColumn)),
    className: "rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-3 py-1.5 text-sm font-medium hover:bg-zinc-300/70 dark:hover:bg-zinc-700"
  }, "Select All"), /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => setCommentColumns([]),
    className: "rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-3 py-1.5 text-sm font-medium hover:bg-zinc-300/70 dark:hover:bg-zinc-700"
  }, "Select None")), /*#__PURE__*/React.createElement("div", {
    className: "grid gap-2",
    style: {
      gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))"
    }
  }, excelColumns.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-zinc-500 dark:text-zinc-400"
  }, "Load Excel file to see available columns"), excelColumns.filter(c => c !== tagColumn).map(c => {
    const checked = commentColumns.includes(c);
    return /*#__PURE__*/React.createElement("label", {
      key: c,
      className: cx("flex items-center gap-2 rounded-lg border px-3 py-2 text-sm cursor-pointer transition-colors", checked ? "border-brand/50 bg-brand/5" : "border-zinc-200/60 dark:border-zinc-800 bg-transparent hover:bg-zinc-200/40 dark:hover:bg-zinc-800/60")
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      className: "accent-brand",
      checked: checked,
      onChange: e => {
        if (e.target.checked) {
          setCommentColumns([...commentColumns, c]);
        } else {
          setCommentColumns(commentColumns.filter(x => x !== c));
        }
      }
    }), /*#__PURE__*/React.createElement("span", null, c));
  }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    className: "text-sm font-semibold text-zinc-500 dark:text-zinc-400 mb-3 flex items-center"
  }, /*#__PURE__*/React.createElement("span", {
    className: "flex items-center"
  }, "Excel Annotation", /*#__PURE__*/React.createElement(HelpIcon, {
    content: HELP_CONTENT.excelAnnotation
  }))), /*#__PURE__*/React.createElement("div", {
    className: "grid gap-4 sm:grid-cols-2"
  }, /*#__PURE__*/React.createElement("div", {
    className: "sm:col-span-2"
  }, /*#__PURE__*/React.createElement("label", {
    className: cx("flex items-center gap-3", !annotateExcelEnabled && "opacity-50 cursor-not-allowed")
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    role: "switch",
    "aria-checked": annotateExcel,
    onClick: () => annotateExcelEnabled && setAnnotateExcel(v => !v),
    disabled: !annotateExcelEnabled,
    className: cx("h-6 w-11 rounded-full transition-colors", annotateExcel && annotateExcelEnabled ? "bg-brand" : "bg-zinc-400/60 dark:bg-zinc-700", !annotateExcelEnabled && "cursor-not-allowed opacity-50")
  }, /*#__PURE__*/React.createElement("span", {
    className: cx("block h-5 w-5 rounded-full bg-white dark:bg-zinc-200 translate-x-0.5 transition-transform", annotateExcel && "translate-x-[22px]")
  })), /*#__PURE__*/React.createElement("span", {
    className: "text-sm font-medium"
  }, "Annotate Excel file")), /*#__PURE__*/React.createElement("div", {
    className: "mt-1 text-xs text-zinc-500 dark:text-zinc-400"
  }, annotateExcelEnabled ? "Highlight rows in light green where tags are found in the PDF" : /*#__PURE__*/React.createElement("span", {
    className: "text-orange-500 dark:text-orange-400"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-exclamation-triangle mr-1"
  }), "Only .xlsx files support Excel annotation. Convert your .xls file to .xlsx format."))))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("h3", {
    className: "text-sm font-semibold text-zinc-500 dark:text-zinc-400 mb-3 flex items-center"
  }, /*#__PURE__*/React.createElement("span", {
    className: "flex items-center"
  }, "Watermark", /*#__PURE__*/React.createElement(HelpIcon, {
    content: HELP_CONTENT.watermark
  }))), /*#__PURE__*/React.createElement("div", {
    className: "space-y-4"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    className: "flex items-center gap-3"
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    role: "switch",
    "aria-checked": watermarkEnabled,
    onClick: () => setWatermarkEnabled(v => !v),
    className: cx("h-6 w-11 rounded-full transition-colors", watermarkEnabled ? "bg-brand" : "bg-zinc-400/60 dark:bg-zinc-700")
  }, /*#__PURE__*/React.createElement("span", {
    className: cx("block h-5 w-5 rounded-full bg-white dark:bg-zinc-200 translate-x-0.5 transition-transform", watermarkEnabled && "translate-x-[22px]")
  })), /*#__PURE__*/React.createElement("span", {
    className: "text-sm font-medium"
  }, "Enable Watermark"))), watermarkEnabled && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
    className: "flex flex-wrap gap-4 items-end"
  }, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    htmlFor: "watermark-text-color",
    className: "block text-sm font-medium mb-1"
  }, "Text Color"), /*#__PURE__*/React.createElement("input", {
    id: "watermark-text-color",
    type: "color",
    value: watermarkTextColor,
    onChange: e => setWatermarkTextColor(e.target.value),
    className: "h-10 w-14 rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-1"
  })), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    htmlFor: "watermark-font-size",
    className: "block text-sm font-medium mb-1"
  }, "Font Size (pt)"), /*#__PURE__*/React.createElement("input", {
    id: "watermark-font-size",
    type: "number",
    min: "5",
    max: "24",
    value: watermarkFontSize,
    onChange: e => setWatermarkFontSize(Math.max(5, Math.min(24, parseInt(e.target.value) || 9))),
    className: "h-10 w-20 rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900 px-3 text-sm"
  }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    className: "flex items-center gap-2 cursor-pointer"
  }, /*#__PURE__*/React.createElement("input", {
    type: "checkbox",
    className: "accent-brand h-4 w-4 rounded",
    checked: watermarkBackgroundEnabled,
    onChange: e => setWatermarkBackgroundEnabled(e.target.checked)
  }), /*#__PURE__*/React.createElement("span", {
    className: "text-sm font-medium"
  }, "White background behind watermark")), /*#__PURE__*/React.createElement("p", {
    className: "text-xs text-zinc-500 dark:text-zinc-400 mt-1 ml-6"
  }, "Improves readability when watermark overlaps graphics")), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
    className: "block text-sm font-medium mb-2"
  }, "Watermark Attributes"), /*#__PURE__*/React.createElement("div", {
    className: "mb-3 rounded-lg border border-zinc-200/60 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-800/50 px-3 py-2"
  }, /*#__PURE__*/React.createElement("p", {
    className: "text-xs text-zinc-500 dark:text-zinc-400 mb-1"
  }, "Preview"), /*#__PURE__*/React.createElement("p", {
    className: "text-sm font-mono",
    style: {
      color: watermarkTextColor,
      fontSize: `${Math.max(10, watermarkFontSize)}px`
    }
  }, watermarkAttributes.length === 0 ? /*#__PURE__*/React.createElement("span", {
    className: "text-zinc-400 italic"
  }, "No attributes selected") : watermarkAttributes.map(a => a.split(' ')[0]).join(' / '))), watermarkAttributes.length > 1 && /*#__PURE__*/React.createElement("div", {
    className: "mb-3"
  }, /*#__PURE__*/React.createElement("p", {
    className: "text-xs text-zinc-500 dark:text-zinc-400 mb-1"
  }, "Drag to reorder"), /*#__PURE__*/React.createElement("div", {
    className: "flex flex-col gap-1"
  }, watermarkAttributes.map((attr, idx) => /*#__PURE__*/React.createElement("div", {
    key: attr,
    draggable: true,
    onDragStart: () => setWatermarkDragIndex(idx),
    onDragOver: e => e.preventDefault(),
    onDrop: () => {
      if (watermarkDragIndex === null || watermarkDragIndex === idx) return;
      const reordered = [...watermarkAttributes];
      const [moved] = reordered.splice(watermarkDragIndex, 1);
      reordered.splice(idx, 0, moved);
      setWatermarkAttributes(reordered);
      setWatermarkDragIndex(null);
    },
    onDragEnd: () => setWatermarkDragIndex(null),
    className: cx("flex items-center gap-2 rounded-lg border px-3 py-2 text-sm cursor-grab active:cursor-grabbing transition-colors select-none", watermarkDragIndex === idx ? "border-brand/50 bg-brand/10 opacity-60" : "border-zinc-200/60 dark:border-zinc-700 bg-white dark:bg-zinc-800")
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-zinc-400"
  }, "\u283F"), /*#__PURE__*/React.createElement("span", {
    className: "text-xs text-zinc-400 w-4"
  }, idx + 1, "."), /*#__PURE__*/React.createElement("span", null, attr))))), /*#__PURE__*/React.createElement("div", {
    className: "mb-2 flex flex-wrap gap-2"
  }, /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => setWatermarkAttributes(excelColumns.filter(c => c !== tagColumn)),
    className: "rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-3 py-1.5 text-sm font-medium hover:bg-zinc-300/70 dark:hover:bg-zinc-700"
  }, "Select All"), /*#__PURE__*/React.createElement("button", {
    type: "button",
    onClick: () => setWatermarkAttributes([]),
    className: "rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-3 py-1.5 text-sm font-medium hover:bg-zinc-300/70 dark:hover:bg-zinc-700"
  }, "Select None")), /*#__PURE__*/React.createElement("div", {
    className: "grid gap-2",
    style: {
      gridTemplateColumns: "repeat(auto-fit,minmax(220px,1fr))"
    }
  }, excelColumns.length === 0 && /*#__PURE__*/React.createElement("div", {
    className: "text-sm text-zinc-500 dark:text-zinc-400"
  }, "Load Excel file to see available columns"), excelColumns.map(c => {
    const checked = watermarkAttributes.includes(c);
    return /*#__PURE__*/React.createElement("label", {
      key: c,
      className: cx("flex items-center gap-2 rounded-lg border px-3 py-2 text-sm cursor-pointer transition-colors", checked ? "border-brand/50 bg-brand/5" : "border-zinc-200/60 dark:border-zinc-800 bg-transparent hover:bg-zinc-200/40 dark:hover:bg-zinc-800/60")
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      className: "accent-brand",
      checked: checked,
      onChange: e => {
        if (e.target.checked) {
          setWatermarkAttributes([...watermarkAttributes, c]);
        } else {
          setWatermarkAttributes(watermarkAttributes.filter(x => x !== c));
        }
      }
    }), /*#__PURE__*/React.createElement("span", null, c));
  })))))))), /*#__PURE__*/React.createElement(SectionCard, {
    title: "Advanced Options"
  }, /*#__PURE__*/React.createElement("div", {
    className: "space-y-4"
  }, (() => {
    const [profilesExpanded, setProfilesExpanded] = useState(true);
    return /*#__PURE__*/React.createElement("div", {
      className: "rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30 ml-2"
    }, /*#__PURE__*/React.createElement("button", {
      type: "button",
      onClick: () => setProfilesExpanded(!profilesExpanded),
      className: "w-full flex items-center justify-between gap-3 px-4 py-2.5 text-left",
      "aria-expanded": profilesExpanded
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center gap-2.5"
    }, /*#__PURE__*/React.createElement("i", {
      className: cx("fa-solid text-sm text-brand", profilesExpanded ? "fa-chevron-down" : "fa-chevron-right", "transition-transform duration-200")
    }), /*#__PURE__*/React.createElement("h3", {
      className: "text-sm font-semibold flex items-center"
    }, /*#__PURE__*/React.createElement("span", {
      className: "flex items-center"
    }, "Configuration Profiles", /*#__PURE__*/React.createElement(HelpIcon, {
      content: HELP_CONTENT.configurationProfiles
    })))), activeProfileName && /*#__PURE__*/React.createElement("span", {
      className: "text-xs px-2 py-1 rounded bg-brand/10 text-brand font-medium"
    }, "Active: ", activeProfileName)), /*#__PURE__*/React.createElement("div", {
      className: cx("grid transition-all duration-300", profilesExpanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0")
    }, /*#__PURE__*/React.createElement("div", {
      className: "overflow-hidden"
    }, /*#__PURE__*/React.createElement("div", {
      className: "px-4 pb-3 space-y-3"
    }, serverProfiles.length > 0 && /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium mb-1.5"
    }, "Load Profile from Server"), /*#__PURE__*/React.createElement("div", {
      className: "flex gap-2"
    }, /*#__PURE__*/React.createElement("select", {
      value: selectedProfile,
      onChange: e => {
        setSelectedProfile(e.target.value);
        if (e.target.value) {
          if (e.target.value.startsWith('server:')) {
            const profileData = serverProfiles.find(p => `server:${p.filename}` === e.target.value);
            if (profileData) generateProfilePreview(profileData);
          }
        } else {
          setProfilePreview(null);
        }
      },
      className: "flex-1 rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
    }, /*#__PURE__*/React.createElement("option", {
      value: ""
    }, "-- Choose a profile --"), serverProfiles.map(p => /*#__PURE__*/React.createElement("option", {
      key: `server:${p.filename}`,
      value: `server:${p.filename}`
    }, p.name))), /*#__PURE__*/React.createElement("button", {
      onClick: loadSelectedProfile,
      disabled: !selectedProfile,
      className: "inline-flex items-center justify-center gap-2 rounded-lg bg-brand text-white px-3 py-2 text-sm font-medium shadow-soft hover:bg-brand-hover transition-all disabled:opacity-50 disabled:cursor-not-allowed"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-arrow-down-to-bracket"
    }), "Load"))), /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-2 gap-2"
    }, /*#__PURE__*/React.createElement("button", {
      onClick: exportCurrentProfile,
      className: "inline-flex items-center justify-center gap-2 rounded-lg bg-success/10 text-success hover:bg-success/20 px-3 py-2 text-sm font-medium transition-all",
      title: "Download current settings as JSON file"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-download"
    }), "Export Profile"), /*#__PURE__*/React.createElement("button", {
      onClick: () => setShowImportProfileModal(true),
      className: "inline-flex items-center justify-center gap-2 rounded-lg bg-warning/10 text-warning hover:bg-warning/20 px-3 py-2 text-sm font-medium transition-all",
      title: "Import settings from JSON file"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-upload"
    }), "Import Profile")), /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-100/50 dark:bg-zinc-900/50 rounded px-3 py-2 border border-zinc-200/40 dark:border-zinc-800/60"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-circle-info mr-1.5"
    }), "All settings auto-save to your browser, including color rules and tag filters. Export profiles as JSON to share or back up your configuration."), currentSettingsPreview && /*#__PURE__*/React.createElement("div", {
      className: "mt-3 rounded-lg border border-success/30 bg-success/5 p-3 space-y-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-start justify-between pb-2 border-b border-success/20"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex-1"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, currentSettingsPreview.name), currentSettingsPreview.description && /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-zinc-600 dark:text-zinc-400 mt-1"
    }, currentSettingsPreview.description)), /*#__PURE__*/React.createElement("span", {
      className: cx("inline-block text-xs font-medium px-2 py-1 rounded ml-2 whitespace-nowrap", currentSettingsPreview.complexity === 'Comprehensive' && 'bg-danger/20 text-danger', currentSettingsPreview.complexity === 'Moderate' && 'bg-warning/20 text-warning', currentSettingsPreview.complexity === 'Minimal' && 'bg-success/20 text-success')
    }, currentSettingsPreview.complexity)), currentSettingsPreview.settings && /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-2 gap-2 text-xs"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Header Row:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, currentSettingsPreview.settings.headerRow)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Tag Column:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, currentSettingsPreview.settings.tagColumn)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Highlight:"), /*#__PURE__*/React.createElement("span", {
      className: "flex items-center gap-1"
    }, /*#__PURE__*/React.createElement("span", {
      className: "w-4 h-4 rounded border border-zinc-300 dark:border-zinc-600",
      style: {
        backgroundColor: currentSettingsPreview.settings.highlightColor
      }
    }), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, currentSettingsPreview.settings.highlightColumn))), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Comments:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, currentSettingsPreview.settings.commentColumns)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Watermark:"), /*#__PURE__*/React.createElement("span", {
      className: cx("font-medium px-1.5 py-0.5 rounded text-xs", currentSettingsPreview.settings.watermark === 'Enabled' ? 'bg-success/20 text-success' : 'bg-zinc-200/50 dark:bg-zinc-800/50 text-zinc-600 dark:text-zinc-400')
    }, currentSettingsPreview.settings.watermark)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Excel:"), /*#__PURE__*/React.createElement("span", {
      className: cx("font-medium px-1.5 py-0.5 rounded text-xs", currentSettingsPreview.settings.annotateExcel === 'Enabled' ? 'bg-success/20 text-success' : 'bg-zinc-200/50 dark:bg-zinc-800/50 text-zinc-600 dark:text-zinc-400')
    }, currentSettingsPreview.settings.annotateExcel)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Tag Matching:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, currentSettingsPreview.settings.tagMatchingPreset)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Color Rules:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, currentSettingsPreview.settings.colorRules)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Tag Filters:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, currentSettingsPreview.settings.tagFilters)))), profilePreview && /*#__PURE__*/React.createElement("div", {
      className: "mt-3 rounded-lg border border-brand/30 bg-brand/5 p-3 space-y-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-start justify-between pb-2 border-b border-brand/20"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex-1"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, profilePreview.name), profilePreview.description && /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-zinc-600 dark:text-zinc-400 mt-1"
    }, profilePreview.description)), /*#__PURE__*/React.createElement("span", {
      className: cx("inline-block text-xs font-medium px-2 py-1 rounded ml-2 whitespace-nowrap", profilePreview.complexity === 'Comprehensive' && 'bg-danger/20 text-danger', profilePreview.complexity === 'Moderate' && 'bg-warning/20 text-warning', profilePreview.complexity === 'Minimal' && 'bg-success/20 text-success')
    }, profilePreview.complexity)), profilePreview.settings && /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-2 gap-2 text-xs"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Header Row:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, profilePreview.settings.headerRow)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Tag Column:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, profilePreview.settings.tagColumn)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Highlight:"), /*#__PURE__*/React.createElement("span", {
      className: "flex items-center gap-1"
    }, /*#__PURE__*/React.createElement("span", {
      className: "w-4 h-4 rounded border border-zinc-300 dark:border-zinc-600",
      style: {
        backgroundColor: profilePreview.settings.highlightColor
      }
    }), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, profilePreview.settings.highlightColumn))), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Comments:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, profilePreview.settings.commentColumns)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Watermark:"), /*#__PURE__*/React.createElement("span", {
      className: cx("font-medium px-1.5 py-0.5 rounded text-xs", profilePreview.settings.watermark === 'Enabled' ? 'bg-success/20 text-success' : 'bg-zinc-200/50 dark:bg-zinc-800/50 text-zinc-600 dark:text-zinc-400')
    }, profilePreview.settings.watermark)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Excel:"), /*#__PURE__*/React.createElement("span", {
      className: cx("font-medium px-1.5 py-0.5 rounded text-xs", profilePreview.settings.annotateExcel === 'Enabled' ? 'bg-success/20 text-success' : 'bg-zinc-200/50 dark:bg-zinc-800/50 text-zinc-600 dark:text-zinc-400')
    }, profilePreview.settings.annotateExcel)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Tag Matching:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, profilePreview.settings.tagMatchingPreset)), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Color Rules:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, profilePreview.settings.colorRules || 'None')), /*#__PURE__*/React.createElement("div", {
      className: "flex items-start gap-2"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-600 dark:text-zinc-400 min-w-fit"
    }, "Tag Filters:"), /*#__PURE__*/React.createElement("span", {
      className: "font-medium"
    }, profilePreview.settings.tagFilters || 'None'))))))));
  })(), (() => {
    const [tagFiltersExpanded, setTagFiltersExpanded] = useState(false);

    // Helper to get part label
    const getPartLabel = partNum => {
      const labels = ['A', 'B', 'C', 'D', 'E'];
      return labels[partNum - 1] || partNum.toString();
    };

    // Helper to format filter display
    const formatFilterDisplay = filter => {
      const actionLabel = filter.action === 'include' ? 'INCLUDE' : 'EXCLUDE';
      const actionClass = filter.action === 'include' ? 'text-success bg-success/10' : 'text-danger bg-danger/10';
      if (filter.filter_type === 'tag_part') {
        const partLabel = getPartLabel(filter.part);
        const matchLabel = filter.match_type === 'exact' ? '=' : '≈';
        return {
          action: actionLabel,
          actionClass: actionClass,
          description: `Part ${partLabel} ${matchLabel} "${filter.value}"`
        };
      } else if (filter.filter_type === 'header_column') {
        const matchLabel = filter.match_type === 'exact' ? '=' : '≈';
        return {
          action: actionLabel,
          actionClass: actionClass,
          description: `${filter.column_name} ${matchLabel} "${filter.value}"`
        };
      } else if (filter.filter_type === 'value') {
        const matchLabel = filter.match_type === 'exact' ? '=' : '≈';
        return {
          action: actionLabel,
          actionClass: actionClass,
          description: `Value ${matchLabel} "${filter.value}"`
        };
      }
      return {
        action: actionLabel,
        actionClass: actionClass,
        description: 'Unknown filter'
      };
    };
    return /*#__PURE__*/React.createElement("div", {
      className: "rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30 ml-2"
    }, /*#__PURE__*/React.createElement("button", {
      type: "button",
      onClick: () => setTagFiltersExpanded(!tagFiltersExpanded),
      className: "w-full flex items-center justify-between gap-3 px-4 py-2.5 text-left",
      "aria-expanded": tagFiltersExpanded
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center gap-2.5"
    }, /*#__PURE__*/React.createElement("i", {
      className: cx("fa-solid text-sm text-brand", tagFiltersExpanded ? "fa-chevron-down" : "fa-chevron-right", "transition-transform duration-200")
    }), /*#__PURE__*/React.createElement("h3", {
      className: "text-sm font-semibold flex items-center"
    }, /*#__PURE__*/React.createElement("span", {
      className: "flex items-center"
    }, "Tag Filters", /*#__PURE__*/React.createElement(HelpIcon, {
      content: HELP_CONTENT.tagFilters
    })))), tagFilters.length > 0 && /*#__PURE__*/React.createElement("span", {
      className: "text-xs px-2 py-1 rounded bg-brand/10 text-brand font-medium"
    }, tagFilters.length, " ", tagFilters.length === 1 ? 'filter' : 'filters')), /*#__PURE__*/React.createElement("div", {
      className: cx("grid transition-all duration-300", tagFiltersExpanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0")
    }, /*#__PURE__*/React.createElement("div", {
      className: "overflow-hidden"
    }, /*#__PURE__*/React.createElement("div", {
      className: "px-4 pb-3 space-y-3"
    }, /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Filter Logic"), /*#__PURE__*/React.createElement("div", {
      className: "flex gap-3"
    }, /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "filter-logic",
      value: "AND",
      checked: filterLogic === 'AND',
      onChange: e => setFilterLogic(e.target.value),
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "AND (all must match)")), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "filter-logic",
      value: "OR",
      checked: filterLogic === 'OR',
      onChange: e => setFilterLogic(e.target.value),
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "OR (any can match)"))), /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-100/50 dark:bg-zinc-900/50 rounded px-3 py-2 border border-zinc-200/40 dark:border-zinc-800/60"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-circle-info mr-1.5"
    }), filterLogic === 'AND' ? 'Tags must match ALL filters to be processed' : 'Tags matching ANY filter will be processed')), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2 pt-2 border-t border-zinc-200/60 dark:border-zinc-800"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center justify-between"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Active Filters"), tagFilters.length > 0 && /*#__PURE__*/React.createElement("button", {
      onClick: handleClearAllFilters,
      className: "text-xs px-2 py-1 rounded bg-danger/10 text-danger hover:bg-danger/20 font-medium transition-colors"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-trash-can mr-1"
    }), "Clear All")), tagFilters.length === 0 ? /*#__PURE__*/React.createElement("div", {
      className: "text-sm text-zinc-500 dark:text-zinc-400 italic text-center py-4"
    }, "No filters defined. Click \"Add Filter\" to create one.") : /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, tagFilters.map((filter, index) => {
      const {
        action,
        actionClass,
        description
      } = formatFilterDisplay(filter);
      return /*#__PURE__*/React.createElement("div", {
        key: index,
        className: "flex items-center gap-2 p-2 rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900/50"
      }, /*#__PURE__*/React.createElement("div", {
        className: cx("px-2 py-1 rounded text-xs font-bold flex-shrink-0", actionClass)
      }, action), /*#__PURE__*/React.createElement("div", {
        className: "flex-1 text-sm"
      }, description), /*#__PURE__*/React.createElement("button", {
        onClick: () => handleRemoveFilter(index),
        className: "p-1.5 rounded hover:bg-danger/10 text-danger",
        title: "Delete filter"
      }, /*#__PURE__*/React.createElement("i", {
        className: "fa-solid fa-trash-can text-xs"
      })));
    })), /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-2 gap-2"
    }, /*#__PURE__*/React.createElement("button", {
      onClick: () => setFilterBuilderOpen(!filterBuilderOpen),
      className: "inline-flex items-center justify-center gap-2 rounded-lg bg-brand/10 text-brand hover:bg-brand/20 px-3 py-2 text-sm font-medium transition-colors"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-plus"
    }), "Add Filter"), /*#__PURE__*/React.createElement("button", {
      onClick: handlePreviewFilters,
      disabled: !selectedExcel || !tagColumn,
      className: "inline-flex items-center justify-center gap-2 rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-3 py-2 text-sm font-medium hover:bg-zinc-300/70 dark:hover:bg-zinc-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-eye"
    }), "Preview Tags"))), filterBuilderOpen && /*#__PURE__*/React.createElement("div", {
      className: "space-y-3 pt-2 border-t border-zinc-200/60 dark:border-zinc-800"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center justify-between"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Filter Builder"), /*#__PURE__*/React.createElement("button", {
      onClick: () => setFilterBuilderOpen(false),
      className: "text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-xmark"
    }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium mb-2"
    }, "Action"), /*#__PURE__*/React.createElement("div", {
      className: "flex gap-3"
    }, /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-filter-action",
      value: "include",
      checked: newFilterAction === 'include',
      onChange: e => setNewFilterAction(e.target.value),
      className: "accent-success"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm text-success font-medium"
    }, "INCLUDE")), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-filter-action",
      value: "exclude",
      checked: newFilterAction === 'exclude',
      onChange: e => setNewFilterAction(e.target.value),
      className: "accent-danger"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm text-danger font-medium"
    }, "EXCLUDE")))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium mb-2"
    }, "Filter Type"), /*#__PURE__*/React.createElement("div", {
      className: "flex gap-3"
    }, /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-filter-type",
      value: "tag_part",
      checked: newFilterType === 'tag_part',
      onChange: e => {
        setNewFilterType(e.target.value);
        setAvailableHeaderValues([]);
      },
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Tag Part")), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-filter-type",
      value: "header_column",
      checked: newFilterType === 'header_column',
      onChange: e => setNewFilterType(e.target.value),
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Excel Column")), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-filter-type",
      value: "value",
      checked: newFilterType === 'value',
      onChange: e => {
        setNewFilterType(e.target.value);
        setAvailableHeaderValues([]);
      },
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Value")))), newFilterType === 'tag_part' && /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium"
    }, "Tag Part"), /*#__PURE__*/React.createElement("select", {
      value: newFilterPart,
      onChange: e => setNewFilterPart(parseInt(e.target.value)),
      className: "w-full rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
    }, /*#__PURE__*/React.createElement("option", {
      value: 1
    }, "Part A (1st part)"), /*#__PURE__*/React.createElement("option", {
      value: 2
    }, "Part B (2nd part)"), /*#__PURE__*/React.createElement("option", {
      value: 3
    }, "Part C (3rd part)"), /*#__PURE__*/React.createElement("option", {
      value: 4
    }, "Part D (4th part)"), /*#__PURE__*/React.createElement("option", {
      value: 5
    }, "Part E (5th part)")), newFilterPart && availableTagParts[`part${newFilterPart}`] && availableTagParts[`part${newFilterPart}`].length > 0 && /*#__PURE__*/React.createElement("div", {
      className: "mt-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-xs"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-zinc-500 dark:text-zinc-400 mb-1"
    }, "Available values (click to use):"), /*#__PURE__*/React.createElement("div", {
      className: "flex flex-wrap gap-1 max-h-20 overflow-y-auto"
    }, availableTagParts[`part${newFilterPart}`].slice(0, showAllFilterValues ? undefined : 20).map((val, idx) => /*#__PURE__*/React.createElement("button", {
      key: val.value || idx,
      onClick: () => setNewFilterValue(val.value),
      className: "px-2 py-0.5 rounded bg-zinc-200/70 dark:bg-zinc-800 hover:bg-brand/10 hover:text-brand text-xs",
      title: `Click to use "${val.value}" (found ${val.count} times)`
    }, val.value, " ", /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-400"
    }, "(", val.count, ")"))), availableTagParts[`part${newFilterPart}`].length > 20 && /*#__PURE__*/React.createElement("button", {
      onClick: () => setShowAllFilterValues(!showAllFilterValues),
      className: "text-zinc-400 hover:text-brand text-xs px-2 py-0.5 rounded hover:bg-zinc-200/50 dark:hover:bg-zinc-800"
    }, showAllFilterValues ? '- Show less' : `+ ${availableTagParts[`part${newFilterPart}`].length - 20} more`))))), newFilterType === 'header_column' && /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium"
    }, "Excel Column"), /*#__PURE__*/React.createElement("select", {
      value: newFilterColumn,
      onChange: e => {
        setNewFilterColumn(e.target.value);
        handleFetchHeaderValuesForFilter(e.target.value);
      },
      className: "w-full rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
    }, /*#__PURE__*/React.createElement("option", {
      value: ""
    }, "-- Select column --"), excelColumns.map(col => /*#__PURE__*/React.createElement("option", {
      key: col,
      value: col
    }, col))), newFilterColumn && /*#__PURE__*/React.createElement("div", {
      className: "mt-2"
    }, loadingHeaderValues ? /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-spinner fa-spin mr-1"
    }), "Loading values...") : availableHeaderValues.length > 0 ? /*#__PURE__*/React.createElement("div", {
      className: "text-xs"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-zinc-500 dark:text-zinc-400 mb-1"
    }, "Available values (click to use):"), /*#__PURE__*/React.createElement("div", {
      className: "flex flex-wrap gap-1 max-h-20 overflow-y-auto"
    }, availableHeaderValues.slice(0, showAllFilterValues ? undefined : 20).map((val, idx) => {
      // Handle both formats: {value, count} object and plain string
      const displayValue = typeof val === 'object' ? val.value : val;
      const displayCount = typeof val === 'object' ? val.count : 1;
      return /*#__PURE__*/React.createElement("button", {
        key: displayValue || idx,
        onClick: () => setNewFilterValue(displayValue),
        className: "px-2 py-0.5 rounded bg-zinc-200/70 dark:bg-zinc-800 hover:bg-brand/10 hover:text-brand text-xs",
        title: `Click to use "${displayValue}" (found ${displayCount} times)`
      }, displayValue, " ", /*#__PURE__*/React.createElement("span", {
        className: "text-zinc-400"
      }, "(", displayCount, ")"));
    }), availableHeaderValues.length > 20 && /*#__PURE__*/React.createElement("button", {
      onClick: () => setShowAllFilterValues(!showAllFilterValues),
      className: "text-zinc-400 hover:text-brand text-xs px-2 py-0.5 rounded hover:bg-zinc-200/50 dark:hover:bg-zinc-800"
    }, showAllFilterValues ? '- Show less' : `+ ${availableHeaderValues.length - 20} more`))) : null)), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium"
    }, newFilterType === 'value' ? 'Match Value (tag text)' : 'Match Value'), /*#__PURE__*/React.createElement("input", {
      type: "text",
      value: newFilterValue,
      onChange: e => setNewFilterValue(e.target.value),
      placeholder: newFilterType === 'value' ? 'Enter tag value to match...' : 'Enter value to match...',
      className: "w-full rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
    })), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium"
    }, "Match Type"), /*#__PURE__*/React.createElement("div", {
      className: "flex gap-3"
    }, /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-filter-match-type",
      value: "exact",
      checked: newFilterMatchType === 'exact',
      onChange: e => setNewFilterMatchType(e.target.value),
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Exact")), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-filter-match-type",
      value: "contains",
      checked: newFilterMatchType === 'contains',
      onChange: e => setNewFilterMatchType(e.target.value),
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Contains")))), /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-2 gap-2 pt-2"
    }, /*#__PURE__*/React.createElement("button", {
      onClick: handleAddFilter,
      className: cx("inline-flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-medium shadow-soft transition-all", newFilterAction === 'include' ? "bg-success text-white hover:bg-success/90" : "bg-danger text-white hover:bg-danger/90")
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-plus"
    }), "Add Filter"), /*#__PURE__*/React.createElement("button", {
      onClick: () => {
        setFilterBuilderOpen(false);
        // Reset builder fields
        setNewFilterType('tag_part');
        setNewFilterPart(1);
        setNewFilterColumn('');
        setNewFilterValue('');
        setNewFilterMatchType('exact');
        setNewFilterAction('include');
        setAvailableHeaderValues([]);
        setShowAllFilterValues(false);
      },
      className: "inline-flex items-center justify-center gap-2 rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-3 py-2 text-sm font-medium hover:bg-zinc-300/70 dark:hover:bg-zinc-700 transition-all"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-xmark"
    }), "Cancel"))), /*#__PURE__*/React.createElement("div", {
      className: "pt-2 border-t border-zinc-200/60 dark:border-zinc-800"
    }, /*#__PURE__*/React.createElement("button", {
      type: "button",
      onClick: () => setFilterPreviewOpen(!filterPreviewOpen),
      className: "w-full flex items-center gap-2 text-left mb-2"
    }, /*#__PURE__*/React.createElement("i", {
      className: cx("fa-solid text-xs text-zinc-500", filterPreviewOpen ? "fa-chevron-down" : "fa-chevron-right", "transition-transform duration-200")
    }), /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Filter Preview"), filterPreviewTags.length > 0 && /*#__PURE__*/React.createElement("span", {
      className: "text-xs px-2 py-0.5 rounded bg-brand/10 text-brand font-medium ml-auto"
    }, filterPreviewTags.length, " tags")), /*#__PURE__*/React.createElement("div", {
      className: cx("grid transition-all duration-300", filterPreviewOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0")
    }, /*#__PURE__*/React.createElement("div", {
      className: "overflow-hidden"
    }, /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, filterPreviewLoading ? /*#__PURE__*/React.createElement("div", {
      className: "text-sm text-center py-4 text-zinc-500 dark:text-zinc-400"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-spinner fa-spin mr-2"
    }), "Loading preview...") : filterPreviewTags.length === 0 ? /*#__PURE__*/React.createElement("div", {
      className: "text-sm text-zinc-500 dark:text-zinc-400 italic text-center py-4"
    }, "Click \"Preview Tags\" to see matching tags") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-100/50 dark:bg-zinc-900/50 rounded px-3 py-2 border border-zinc-200/40 dark:border-zinc-800/60"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-circle-info mr-1.5"
    }), "Showing ", filterPreviewTags.length, " tag", filterPreviewTags.length !== 1 ? 's' : '', " matching current filters"), /*#__PURE__*/React.createElement("div", {
      className: cx("flex flex-wrap gap-1.5 p-2 rounded-lg bg-white dark:bg-zinc-900/50 border border-zinc-200/60 dark:border-zinc-800", !filterPreviewExpanded && "max-h-32 overflow-hidden")
    }, filterPreviewTags.map((tag, idx) => /*#__PURE__*/React.createElement("span", {
      key: idx,
      className: "px-2 py-1 rounded text-xs bg-zinc-200/70 dark:bg-zinc-800 font-mono"
    }, tag))), filterPreviewTags.length > 10 && /*#__PURE__*/React.createElement("button", {
      onClick: () => setFilterPreviewExpanded(!filterPreviewExpanded),
      className: "w-full text-xs text-brand hover:underline"
    }, filterPreviewExpanded ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-chevron-up mr-1"
    }), "Show Less") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-chevron-down mr-1"
    }), "Show All (", filterPreviewTags.length, " tags)")))))))))));
  })(), (() => {
    const availableSeparators = [{
      value: '-',
      label: 'Dash (-)'
    }, {
      value: '.',
      label: 'Dot (.)'
    }, {
      value: '_',
      label: 'Underscore (_)'
    }, {
      value: '/',
      label: 'Slash (/)'
    }, {
      value: ':',
      label: 'Colon (:)'
    }];
    const handleSeparatorToggle = separator => {
      if (tagMatchingSeparators.includes(separator)) {
        setTagMatchingSeparators(tagMatchingSeparators.filter(s => s !== separator));
      } else {
        setTagMatchingSeparators([...tagMatchingSeparators, separator]);
      }
    };
    return /*#__PURE__*/React.createElement("div", {
      className: "rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30 ml-2"
    }, /*#__PURE__*/React.createElement("button", {
      type: "button",
      onClick: () => setTagMatchingPanelOpen(!tagMatchingPanelOpen),
      className: "w-full flex items-center justify-between gap-3 px-4 py-2.5 text-left",
      "aria-expanded": tagMatchingPanelOpen
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center gap-2.5"
    }, /*#__PURE__*/React.createElement("i", {
      className: cx("fa-solid text-sm text-brand", tagMatchingPanelOpen ? "fa-chevron-down" : "fa-chevron-right", "transition-transform duration-200")
    }), /*#__PURE__*/React.createElement("h3", {
      className: "text-sm font-semibold flex items-center"
    }, /*#__PURE__*/React.createElement("span", {
      className: "flex items-center"
    }, "Custom Tag Matching", /*#__PURE__*/React.createElement(HelpIcon, {
      content: HELP_CONTENT.customTagMatching
    }))))), /*#__PURE__*/React.createElement("div", {
      className: cx("grid transition-all duration-300", tagMatchingPanelOpen ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0")
    }, /*#__PURE__*/React.createElement("div", {
      className: "overflow-hidden"
    }, /*#__PURE__*/React.createElement("div", {
      className: "px-4 pb-3 space-y-3"
    }, /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Tag Matching Preset"), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "flex items-start gap-2 cursor-pointer group"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "tag-matching-preset",
      value: "default",
      checked: tagMatchingPreset === 'default',
      onChange: e => setTagMatchingPreset(e.target.value),
      className: "accent-brand mt-0.5"
    }), /*#__PURE__*/React.createElement("div", {
      className: "flex-1"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-sm font-medium block"
    }, "Default"), /*#__PURE__*/React.createElement("span", {
      className: "text-xs text-zinc-500 dark:text-zinc-400"
    }, "Standard 3-5 part hierarchical tags (e.g., A-B-C, SYS.PUMP.01, TAG-001-A)"))), /*#__PURE__*/React.createElement("label", {
      className: "flex items-start gap-2 cursor-pointer group"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "tag-matching-preset",
      value: "match_all",
      checked: tagMatchingPreset === 'match_all',
      onChange: e => setTagMatchingPreset(e.target.value),
      className: "accent-brand mt-0.5"
    }), /*#__PURE__*/React.createElement("div", {
      className: "flex-1"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-sm font-medium block"
    }, "Match Everything"), /*#__PURE__*/React.createElement("span", {
      className: "text-xs text-zinc-500 dark:text-zinc-400"
    }, "Accept any text as valid tags (match all alphanumeric sequences)"))), /*#__PURE__*/React.createElement("label", {
      className: "flex items-start gap-2 cursor-pointer group"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "tag-matching-preset",
      value: "custom",
      checked: tagMatchingPreset === 'custom',
      onChange: e => setTagMatchingPreset(e.target.value),
      className: "accent-brand mt-0.5"
    }), /*#__PURE__*/React.createElement("div", {
      className: "flex-1"
    }, /*#__PURE__*/React.createElement("span", {
      className: "text-sm font-medium block"
    }, "Custom"), /*#__PURE__*/React.createElement("span", {
      className: "text-xs text-zinc-500 dark:text-zinc-400"
    }, "Define your own tag matching pattern with custom configuration or regex")))), /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-100/50 dark:bg-zinc-900/50 rounded px-3 py-2 border border-zinc-200/40 dark:border-zinc-800/60"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-circle-info mr-1.5"
    }), "The preset determines which patterns are recognized as tags in your PDF")), tagMatchingPreset === 'custom' && /*#__PURE__*/React.createElement("div", {
      className: "space-y-3 pt-2 border-t border-zinc-200/60 dark:border-zinc-800"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Custom Configuration"), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium"
    }, "Allowed Separators"), /*#__PURE__*/React.createElement("div", {
      className: "flex flex-wrap gap-2"
    }, availableSeparators.map(sep => /*#__PURE__*/React.createElement("label", {
      key: sep.value,
      className: "flex items-center gap-2 px-3 py-1.5 rounded border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900/50 cursor-pointer hover:bg-zinc-50 dark:hover:bg-zinc-800/50 transition-colors"
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      className: "accent-brand h-3.5 w-3.5 rounded",
      checked: tagMatchingSeparators.includes(sep.value),
      onChange: () => handleSeparatorToggle(sep.value)
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-xs font-medium"
    }, sep.label)))), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-zinc-500 dark:text-zinc-400"
    }, "Select which characters can separate tag parts")), /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-2 gap-3"
    }, /*#__PURE__*/React.createElement("div", {
      className: "space-y-1"
    }, /*#__PURE__*/React.createElement("label", {
      htmlFor: "min-parts",
      className: "block text-sm font-medium"
    }, "Minimum Parts"), /*#__PURE__*/React.createElement("input", {
      id: "min-parts",
      type: "number",
      min: "1",
      max: "10",
      value: tagMatchingMinParts,
      onChange: e => {
        const val = parseInt(e.target.value) || 1;
        setTagMatchingMinParts(Math.max(1, Math.min(val, tagMatchingMaxParts)));
      },
      className: "w-full px-3 py-1.5 text-sm rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900"
    })), /*#__PURE__*/React.createElement("div", {
      className: "space-y-1"
    }, /*#__PURE__*/React.createElement("label", {
      htmlFor: "max-parts",
      className: "block text-sm font-medium"
    }, "Maximum Parts"), /*#__PURE__*/React.createElement("input", {
      id: "max-parts",
      type: "number",
      min: "1",
      max: "10",
      value: tagMatchingMaxParts,
      onChange: e => {
        const val = parseInt(e.target.value) || 1;
        setTagMatchingMaxParts(Math.max(tagMatchingMinParts, Math.min(val, 10)));
      },
      className: "w-full px-3 py-1.5 text-sm rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900"
    }))), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-zinc-500 dark:text-zinc-400"
    }, "Number of parts in a valid tag (e.g., A-B-C has 3 parts)"), /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-2 gap-3"
    }, /*#__PURE__*/React.createElement("div", {
      className: "space-y-1"
    }, /*#__PURE__*/React.createElement("label", {
      htmlFor: "min-part-length",
      className: "block text-sm font-medium"
    }, "Min Part Length"), /*#__PURE__*/React.createElement("input", {
      id: "min-part-length",
      type: "number",
      min: "1",
      max: "10",
      value: tagMatchingMinPartLength,
      onChange: e => {
        const val = parseInt(e.target.value) || 1;
        setTagMatchingMinPartLength(Math.max(1, Math.min(val, tagMatchingMaxPartLength)));
      },
      className: "w-full px-3 py-1.5 text-sm rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900"
    })), /*#__PURE__*/React.createElement("div", {
      className: "space-y-1"
    }, /*#__PURE__*/React.createElement("label", {
      htmlFor: "max-part-length",
      className: "block text-sm font-medium"
    }, "Max Part Length"), /*#__PURE__*/React.createElement("input", {
      id: "max-part-length",
      type: "number",
      min: "1",
      max: "10",
      value: tagMatchingMaxPartLength,
      onChange: e => {
        const val = parseInt(e.target.value) || 1;
        setTagMatchingMaxPartLength(Math.max(tagMatchingMinPartLength, Math.min(val, 10)));
      },
      className: "w-full px-3 py-1.5 text-sm rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900"
    }))), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-zinc-500 dark:text-zinc-400"
    }, "Character length of each part in a tag (e.g., \"ABC\" has length 3)"), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      className: "accent-brand h-4 w-4 rounded",
      checked: tagMatchingAllowPartial,
      onChange: e => setTagMatchingAllowPartial(e.target.checked)
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm font-medium"
    }, "Allow partial tag matching")), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 ml-6"
    }, "Tags can be matched even if they don't start at word boundaries"))), tagMatchingPreset === 'custom' && /*#__PURE__*/React.createElement("div", {
      className: "space-y-2 pt-2 border-t border-zinc-200/60 dark:border-zinc-800"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center justify-between"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Advanced: Custom Regex Pattern"), /*#__PURE__*/React.createElement("a", {
      href: "https://regex101.com/",
      target: "_blank",
      rel: "noopener noreferrer",
      className: "text-xs text-brand hover:underline"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-external-link mr-1"
    }), "Regex Help")), /*#__PURE__*/React.createElement("textarea", {
      value: tagMatchingCustomRegex,
      onChange: e => setTagMatchingCustomRegex(e.target.value),
      placeholder: String.raw`\b[A-Za-z0-9]{1,5}[-\.][A-Za-z0-9]{1,5}[-\.][A-Za-z0-9]{1,5}\b`,
      rows: "3",
      className: "w-full px-3 py-2 text-xs font-mono rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900 resize-y"
    }), /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 bg-amber-50/50 dark:bg-amber-900/10 rounded px-3 py-2 border border-amber-200/40 dark:border-amber-800/60"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-triangle-exclamation mr-1.5 text-amber-600 dark:text-amber-500"
    }), "If provided, this regex will override the configuration above. Leave empty to use the configuration-based pattern.")), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2 pt-2 border-t border-zinc-200/60 dark:border-zinc-800"
    }, /*#__PURE__*/React.createElement("button", {
      onClick: handlePreviewTagMatching,
      disabled: tagMatchingPreviewLoading || !selectedPdfs || selectedPdfs.length === 0,
      className: "w-full inline-flex items-center justify-center gap-2 rounded-lg bg-brand/10 text-brand hover:bg-brand/20 px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
    }, tagMatchingPreviewLoading ? /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-spinner fa-spin"
    }), "Loading Preview...") : /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-eye"
    }), "Preview Tag Matching")), !selectedPdfs || selectedPdfs.length === 0 ? /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 text-center"
    }, "Upload a PDF file to preview tag matching") : null, tagMatchingPreviewOpen && !tagMatchingPreviewLoading && /*#__PURE__*/React.createElement("div", {
      className: "space-y-2 pt-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center justify-between p-3 rounded-lg bg-zinc-100/50 dark:bg-zinc-900/50 border border-zinc-200/60 dark:border-zinc-800"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center gap-2"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-tags text-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm font-semibold"
    }, tagMatchingPreviewTags.length, " ", tagMatchingPreviewTags.length === 1 ? 'tag' : 'tags', " matched")), tagMatchingPreviewTags.length > 0 && /*#__PURE__*/React.createElement("button", {
      onClick: () => setTagMatchingPreviewExpanded(!tagMatchingPreviewExpanded),
      className: "text-xs text-brand hover:underline"
    }, tagMatchingPreviewExpanded ? 'Hide' : 'Show', " Tags")), tagMatchingPreviewExpanded && tagMatchingPreviewTags.length > 0 && /*#__PURE__*/React.createElement("div", {
      className: "max-h-48 overflow-y-auto rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900/50"
    }, /*#__PURE__*/React.createElement("div", {
      className: "p-3 space-y-1"
    }, tagMatchingPreviewTags.slice(0, 50).map((tag, index) => /*#__PURE__*/React.createElement("div", {
      key: index,
      className: "text-xs font-mono px-2 py-1 rounded bg-zinc-100/50 dark:bg-zinc-800/50"
    }, tag)), tagMatchingPreviewTags.length > 50 && /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 italic text-center pt-2"
    }, "...and ", tagMatchingPreviewTags.length - 50, " more tags"))), tagMatchingPreviewTags.length === 0 && /*#__PURE__*/React.createElement("div", {
      className: "text-sm text-zinc-500 dark:text-zinc-400 text-center py-4 italic"
    }, "No tags matched the current configuration")))))));
  })(), (() => {
    const [colorRulesExpanded, setColorRulesExpanded] = useState(false);

    // Helper to get part label
    const getPartLabel = partNum => {
      const labels = ['A', 'B', 'C', 'D', 'E'];
      return labels[partNum - 1] || partNum.toString();
    };

    // Helper to format rule display
    const formatRuleDisplay = rule => {
      if (rule.rule_type === 'tag_part') {
        const partLabel = getPartLabel(rule.part);
        const matchLabel = rule.match_type === 'exact' ? '=' : '≈';
        return `Part ${partLabel} ${matchLabel} "${rule.value}"`;
      } else if (rule.rule_type === 'header_column') {
        const matchLabel = rule.match_type === 'exact' ? '=' : '≈';
        return `${rule.column_name} ${matchLabel} "${rule.value}"`;
      }
      return 'Unknown rule';
    };
    return /*#__PURE__*/React.createElement("div", {
      className: "rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-900/30 ml-2"
    }, /*#__PURE__*/React.createElement("button", {
      type: "button",
      onClick: () => setColorRulesExpanded(!colorRulesExpanded),
      className: "w-full flex items-center justify-between gap-3 px-4 py-2.5 text-left",
      "aria-expanded": colorRulesExpanded
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center gap-2.5"
    }, /*#__PURE__*/React.createElement("i", {
      className: cx("fa-solid text-sm text-brand", colorRulesExpanded ? "fa-chevron-down" : "fa-chevron-right", "transition-transform duration-200")
    }), /*#__PURE__*/React.createElement("h3", {
      className: "text-sm font-semibold flex items-center"
    }, /*#__PURE__*/React.createElement("span", {
      className: "flex items-center"
    }, "Color Rules", /*#__PURE__*/React.createElement(HelpIcon, {
      content: HELP_CONTENT.colorRules
    })))), colorRules.length > 0 && /*#__PURE__*/React.createElement("span", {
      className: "text-xs px-2 py-1 rounded bg-brand/10 text-brand font-medium"
    }, colorRules.length, " ", colorRules.length === 1 ? 'rule' : 'rules')), /*#__PURE__*/React.createElement("div", {
      className: cx("grid transition-all duration-300", colorRulesExpanded ? "grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0")
    }, /*#__PURE__*/React.createElement("div", {
      className: "overflow-hidden"
    }, /*#__PURE__*/React.createElement("div", {
      className: "px-4 pb-3 space-y-3"
    }, /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Default Highlight Color"), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      className: "accent-brand h-4 w-4 rounded",
      checked: enableDefaultColor,
      onChange: e => setEnableDefaultColor(e.target.checked)
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm font-medium"
    }, "Enable default highlight color")), enableDefaultColor && /*#__PURE__*/React.createElement("div", {
      className: "ml-6"
    }, /*#__PURE__*/React.createElement("label", {
      htmlFor: "default-color-picker",
      className: "block text-sm font-medium mb-1"
    }, "Default Color"), /*#__PURE__*/React.createElement("input", {
      id: "default-color-picker",
      type: "color",
      value: defaultHighlightColor,
      onChange: e => setDefaultHighlightColor(e.target.value),
      className: "h-10 w-20 rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-1 cursor-pointer"
    }), /*#__PURE__*/React.createElement("p", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 mt-1"
    }, "Used for tags that don't match any color rules"))), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2 pt-2 border-t border-zinc-200/60 dark:border-zinc-800"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Excel Constraint Mode"), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "checkbox",
      className: "accent-brand h-4 w-4 rounded",
      checked: excelConstraintMode,
      onChange: e => setExcelConstraintMode(e.target.checked)
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm font-medium"
    }, "Restrict to Excel column values")), /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-100/50 dark:bg-zinc-900/50 rounded px-3 py-2 border border-zinc-200/40 dark:border-zinc-800/60"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-circle-info mr-1.5"
    }), "When enabled, only tags found in the Excel file will be highlighted"), excelConstraintMode && /*#__PURE__*/React.createElement("div", {
      className: "ml-6 space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium"
    }, "Logic Mode"), /*#__PURE__*/React.createElement("div", {
      className: "flex gap-3"
    }, /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "constraint-logic",
      value: "AND",
      checked: excelConstraintLogic === 'AND',
      onChange: e => setExcelConstraintLogic(e.target.value),
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "AND (all rules must match)")), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "constraint-logic",
      value: "OR",
      checked: excelConstraintLogic === 'OR',
      onChange: e => setExcelConstraintLogic(e.target.value),
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "OR (any rule can match)"))))), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2 pt-2 border-t border-zinc-200/60 dark:border-zinc-800"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center justify-between"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Active Color Rules"), colorRules.length > 0 && /*#__PURE__*/React.createElement("button", {
      onClick: handleClearAllColorRules,
      className: "text-xs px-2 py-1 rounded bg-danger/10 text-danger hover:bg-danger/20 font-medium transition-colors"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-trash-can mr-1"
    }), "Clear All")), colorRules.length === 0 ? /*#__PURE__*/React.createElement("div", {
      className: "text-sm text-zinc-500 dark:text-zinc-400 italic text-center py-4"
    }, "No color rules defined. Click \"Add Rule\" to create one.") : /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, colorRules.map((rule, index) => {
      // Find earlier rules that share the same column (potential overlap)
      const overlappingIndices = rule.rule_type === 'header_column' ? colorRules.slice(0, index).map((r, i) => ({
        r,
        i
      })).filter(({
        r
      }) => r.rule_type === 'header_column' && r.column_name === rule.column_name).map(({
        i
      }) => i + 1) // 1-based display index
      : [];
      return /*#__PURE__*/React.createElement("div", {
        key: rule.id,
        className: "flex items-center gap-2 p-2 rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900/50"
      }, /*#__PURE__*/React.createElement("div", {
        className: "w-6 h-6 rounded border border-zinc-300 dark:border-zinc-700 flex-shrink-0",
        style: {
          backgroundColor: rule.color
        },
        title: rule.color
      }), /*#__PURE__*/React.createElement("div", {
        className: "flex-1 text-sm min-w-0"
      }, /*#__PURE__*/React.createElement("div", null, formatRuleDisplay(rule)), overlappingIndices.length > 0 && /*#__PURE__*/React.createElement("div", {
        className: "flex items-center gap-1 mt-0.5",
        title: "Both rules can match the same rows \u2014 this rule applies last and wins"
      }, /*#__PURE__*/React.createElement("i", {
        className: "fa-solid fa-circle-info text-amber-400 text-xs"
      }), /*#__PURE__*/React.createElement("span", {
        className: "text-xs text-amber-500 dark:text-amber-400"
      }, "Overrides rule ", overlappingIndices.join(', '), " on same column \u2014 last wins"))), /*#__PURE__*/React.createElement("div", {
        className: "flex items-center gap-1"
      }, /*#__PURE__*/React.createElement("button", {
        onClick: () => handleMoveColorRule(rule.id, 'up'),
        disabled: index === 0,
        className: "p-1.5 rounded hover:bg-zinc-200/60 dark:hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed",
        title: "Move up"
      }, /*#__PURE__*/React.createElement("i", {
        className: "fa-solid fa-arrow-up text-xs"
      })), /*#__PURE__*/React.createElement("button", {
        onClick: () => handleMoveColorRule(rule.id, 'down'),
        disabled: index === colorRules.length - 1,
        className: "p-1.5 rounded hover:bg-zinc-200/60 dark:hover:bg-zinc-800 disabled:opacity-30 disabled:cursor-not-allowed",
        title: "Move down"
      }, /*#__PURE__*/React.createElement("i", {
        className: "fa-solid fa-arrow-down text-xs"
      })), /*#__PURE__*/React.createElement("button", {
        onClick: () => handleRemoveColorRule(rule.id),
        className: "p-1.5 rounded hover:bg-danger/10 text-danger",
        title: "Delete rule"
      }, /*#__PURE__*/React.createElement("i", {
        className: "fa-solid fa-trash-can text-xs"
      }))));
    })), /*#__PURE__*/React.createElement("button", {
      onClick: () => setColorRuleBuilderOpen(!colorRuleBuilderOpen),
      className: "w-full inline-flex items-center justify-center gap-2 rounded-lg bg-brand/10 text-brand hover:bg-brand/20 px-3 py-2 text-sm font-medium transition-colors"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-plus"
    }), "Add Rule")), colorRuleBuilderOpen && /*#__PURE__*/React.createElement("div", {
      className: "space-y-3 pt-2 border-t border-zinc-200/60 dark:border-zinc-800"
    }, /*#__PURE__*/React.createElement("div", {
      className: "flex items-center justify-between"
    }, /*#__PURE__*/React.createElement("h4", {
      className: "text-sm font-semibold"
    }, "Rule Builder"), /*#__PURE__*/React.createElement("button", {
      onClick: () => setColorRuleBuilderOpen(false),
      className: "text-xs text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-xmark"
    }))), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium mb-2"
    }, "Rule Type"), /*#__PURE__*/React.createElement("div", {
      className: "flex gap-3"
    }, /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-rule-type",
      value: "tag_part",
      checked: newRuleType === 'tag_part',
      onChange: e => {
        setNewRuleType(e.target.value);
        setRuleAvailableHeaderValues([]);
      },
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Tag Part")), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-rule-type",
      value: "header_column",
      checked: newRuleType === 'header_column',
      onChange: e => setNewRuleType(e.target.value),
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Excel Column")))), newRuleType === 'tag_part' && /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium"
    }, "Tag Part"), /*#__PURE__*/React.createElement("select", {
      value: newRulePart,
      onChange: e => setNewRulePart(parseInt(e.target.value)),
      className: "w-full rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
    }, /*#__PURE__*/React.createElement("option", {
      value: 1
    }, "Part A (1st part)"), /*#__PURE__*/React.createElement("option", {
      value: 2
    }, "Part B (2nd part)"), /*#__PURE__*/React.createElement("option", {
      value: 3
    }, "Part C (3rd part)"), /*#__PURE__*/React.createElement("option", {
      value: 4
    }, "Part D (4th part)"), /*#__PURE__*/React.createElement("option", {
      value: 5
    }, "Part E (5th part)")), newRulePart && availableTagParts[`part${newRulePart}`] && availableTagParts[`part${newRulePart}`].length > 0 && /*#__PURE__*/React.createElement("div", {
      className: "mt-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-xs"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-zinc-500 dark:text-zinc-400 mb-1"
    }, "Available values (click to use):"), /*#__PURE__*/React.createElement("div", {
      className: "flex flex-wrap gap-1 max-h-20 overflow-y-auto"
    }, availableTagParts[`part${newRulePart}`].slice(0, showAllRuleValues ? undefined : 20).map((val, idx) => /*#__PURE__*/React.createElement("button", {
      key: val.value || idx,
      onClick: () => setNewRuleValue(val.value),
      className: "px-2 py-0.5 rounded bg-zinc-200/70 dark:bg-zinc-800 hover:bg-brand/10 hover:text-brand text-xs",
      title: `Click to use "${val.value}" (found ${val.count} times)`
    }, val.value, " ", /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-400"
    }, "(", val.count, ")"))), availableTagParts[`part${newRulePart}`].length > 20 && /*#__PURE__*/React.createElement("button", {
      onClick: () => setShowAllRuleValues(!showAllRuleValues),
      className: "text-zinc-400 hover:text-brand text-xs px-2 py-0.5 rounded hover:bg-zinc-200/50 dark:hover:bg-zinc-800"
    }, showAllRuleValues ? '- Show less' : `+ ${availableTagParts[`part${newRulePart}`].length - 20} more`))))), newRuleType === 'header_column' && /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium"
    }, "Excel Column"), /*#__PURE__*/React.createElement("select", {
      value: newRuleColumn,
      onChange: e => {
        setNewRuleColumn(e.target.value);
        handleFetchHeaderValuesForRule(e.target.value);
        handleFetchRuleExamples(e.target.value, newRuleMatchType, newRuleValue);
      },
      className: "w-full rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
    }, /*#__PURE__*/React.createElement("option", {
      value: ""
    }, "-- Select column --"), excelColumns.map(col => /*#__PURE__*/React.createElement("option", {
      key: col,
      value: col
    }, col))), newRuleColumn && /*#__PURE__*/React.createElement("div", {
      className: "mt-2"
    }, ruleLoadingHeaderValues ? /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-spinner fa-spin mr-1"
    }), "Loading values...") : ruleAvailableHeaderValues.length > 0 ? /*#__PURE__*/React.createElement("div", {
      className: "text-xs"
    }, /*#__PURE__*/React.createElement("div", {
      className: "text-zinc-500 dark:text-zinc-400 mb-1"
    }, "Available values (click to use):"), /*#__PURE__*/React.createElement("div", {
      className: "flex flex-wrap gap-1 max-h-20 overflow-y-auto"
    }, ruleAvailableHeaderValues.slice(0, showAllRuleValues ? undefined : 20).map((val, idx) => /*#__PURE__*/React.createElement("button", {
      key: val.value || idx,
      onClick: () => {
        setNewRuleValue(val.value);
        handleFetchRuleExamples(newRuleColumn, newRuleMatchType, val.value);
      },
      className: "px-2 py-0.5 rounded bg-zinc-200/70 dark:bg-zinc-800 hover:bg-brand/10 hover:text-brand text-xs",
      title: `Click to use "${val.value}" (found ${val.count} times)`
    }, val.value, " ", /*#__PURE__*/React.createElement("span", {
      className: "text-zinc-400"
    }, "(", val.count, ")"))), ruleAvailableHeaderValues.length > 20 && /*#__PURE__*/React.createElement("button", {
      onClick: () => setShowAllRuleValues(!showAllRuleValues),
      className: "text-zinc-400 hover:text-brand text-xs px-2 py-0.5 rounded hover:bg-zinc-200/50 dark:hover:bg-zinc-800"
    }, showAllRuleValues ? '- Show less' : `+ ${ruleAvailableHeaderValues.length - 20} more`))) : /*#__PURE__*/React.createElement("div", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 italic"
    }, "No values found in this column"))), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium"
    }, "Match Type"), /*#__PURE__*/React.createElement("div", {
      className: "flex flex-wrap gap-3"
    }, /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-match-type",
      value: "exact",
      checked: newRuleMatchType === 'exact',
      onChange: e => {
        setNewRuleMatchType(e.target.value);
        handleFetchRuleExamples(newRuleColumn, e.target.value, newRuleValue);
      },
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Exact")), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-match-type",
      value: "contains",
      checked: newRuleMatchType === 'contains',
      onChange: e => {
        setNewRuleMatchType(e.target.value);
        handleFetchRuleExamples(newRuleColumn, e.target.value, newRuleValue);
      },
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Contains")), newRuleType === 'header_column' && /*#__PURE__*/React.createElement(React.Fragment, null, /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-match-type",
      value: "has_value",
      checked: newRuleMatchType === 'has_value',
      onChange: e => {
        setNewRuleMatchType(e.target.value);
        handleFetchRuleExamples(newRuleColumn, e.target.value, newRuleValue);
      },
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Has value")), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-match-type",
      value: "greater_than",
      checked: newRuleMatchType === 'greater_than',
      onChange: e => {
        setNewRuleMatchType(e.target.value);
        handleFetchRuleExamples(newRuleColumn, e.target.value, newRuleValue);
      },
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Greater than")), /*#__PURE__*/React.createElement("label", {
      className: "flex items-center gap-2 cursor-pointer"
    }, /*#__PURE__*/React.createElement("input", {
      type: "radio",
      name: "new-match-type",
      value: "less_than",
      checked: newRuleMatchType === 'less_than',
      onChange: e => {
        setNewRuleMatchType(e.target.value);
        handleFetchRuleExamples(newRuleColumn, e.target.value, newRuleValue);
      },
      className: "accent-brand"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm"
    }, "Less than"))))), newRuleMatchType !== 'has_value' && /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      className: "block text-sm font-medium"
    }, newRuleType === 'header_column' && newRuleColumn ? 'Or enter custom value:' : 'Match Value'), /*#__PURE__*/React.createElement("input", {
      type: "text",
      value: newRuleValue,
      onChange: e => {
        setNewRuleValue(e.target.value);
        handleFetchRuleExamples(newRuleColumn, newRuleMatchType, e.target.value);
      },
      placeholder: newRuleType === 'header_column' && newRuleColumn ? 'Type custom value or click a value above...' : 'Enter value to match...',
      className: "w-full rounded-lg border border-zinc-200/60 dark:border-zinc-800 bg-white dark:bg-zinc-900 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/50"
    })), newRuleType === 'header_column' && newRuleColumn && /*#__PURE__*/React.createElement("div", {
      className: "rounded-lg border border-zinc-200/60 dark:border-zinc-700 overflow-hidden"
    }, /*#__PURE__*/React.createElement("div", {
      className: "px-3 py-1.5 bg-zinc-100/80 dark:bg-zinc-800/60 text-xs font-medium text-zinc-500 dark:text-zinc-400 flex items-center gap-2"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-flask"
    }), "Live examples from your Excel", ruleLoadingExamples && /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-spinner fa-spin ml-auto"
    })), !ruleLoadingExamples && ruleExamples.matches.length === 0 && ruleExamples.non_matches.length === 0 ? /*#__PURE__*/React.createElement("div", {
      className: "px-3 py-2 text-xs text-zinc-400 italic"
    }, newRuleMatchType === 'has_value' ? 'Loading...' : 'Enter a value above to see examples') : /*#__PURE__*/React.createElement("div", {
      className: "divide-y divide-zinc-100 dark:divide-zinc-800"
    }, ruleExamples.matches.map((ex, i) => /*#__PURE__*/React.createElement("div", {
      key: `m${i}`,
      className: "flex items-center gap-2 px-3 py-1.5 bg-green-50/60 dark:bg-green-900/10"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-check text-green-500 w-3 flex-shrink-0"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-xs font-mono font-medium text-zinc-700 dark:text-zinc-300 min-w-0 truncate"
    }, ex.tag), /*#__PURE__*/React.createElement("span", {
      className: "text-xs text-zinc-400 mx-1"
    }, "\u2014"), /*#__PURE__*/React.createElement("span", {
      className: "text-xs text-zinc-500 dark:text-zinc-400 truncate"
    }, ex.column_value))), ruleExamples.non_matches.map((ex, i) => /*#__PURE__*/React.createElement("div", {
      key: `n${i}`,
      className: "flex items-center gap-2 px-3 py-1.5 bg-red-50/40 dark:bg-red-900/10"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-xmark text-red-400 w-3 flex-shrink-0"
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-xs font-mono font-medium text-zinc-500 dark:text-zinc-500 min-w-0 truncate"
    }, ex.tag), /*#__PURE__*/React.createElement("span", {
      className: "text-xs text-zinc-400 mx-1"
    }, "\u2014"), /*#__PURE__*/React.createElement("span", {
      className: "text-xs text-zinc-400 truncate"
    }, ex.column_value))))), /*#__PURE__*/React.createElement("div", {
      className: "space-y-2"
    }, /*#__PURE__*/React.createElement("label", {
      htmlFor: "new-rule-color",
      className: "block text-sm font-medium"
    }, "Highlight Color"), /*#__PURE__*/React.createElement("input", {
      id: "new-rule-color",
      type: "color",
      value: newRuleColor,
      onChange: e => setNewRuleColor(e.target.value),
      className: "h-10 w-20 rounded-lg border border-zinc-300/70 dark:border-zinc-700 bg-white dark:bg-zinc-900 p-1 cursor-pointer"
    })), /*#__PURE__*/React.createElement("div", {
      className: "grid grid-cols-2 gap-2 pt-2"
    }, /*#__PURE__*/React.createElement("button", {
      onClick: handleAddColorRule,
      className: "inline-flex items-center justify-center gap-2 rounded-lg bg-brand text-white px-3 py-2 text-sm font-medium shadow-soft hover:bg-brand-hover transition-all"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-plus"
    }), "Add Rule"), /*#__PURE__*/React.createElement("button", {
      onClick: () => {
        setColorRuleBuilderOpen(false);
        // Reset builder fields
        setNewRuleType('tag_part');
        setNewRulePart(1);
        setNewRuleColumn('');
        setNewRuleValue('');
        setNewRuleMatchType('contains');
        setNewRuleColor('#FFFF00');
        setRuleAvailableHeaderValues([]);
        setRuleExamples({
          matches: [],
          non_matches: []
        });
      },
      className: "inline-flex items-center justify-center gap-2 rounded-lg bg-zinc-200/80 dark:bg-zinc-800 px-3 py-2 text-sm font-medium hover:bg-zinc-300/70 dark:hover:bg-zinc-700 transition-all"
    }, /*#__PURE__*/React.createElement("i", {
      className: "fa-solid fa-xmark"
    }), "Cancel")))))));
  })())), /*#__PURE__*/React.createElement(SectionCard, {
    title: "Actions"
  }, workspaceFiles.pdfs.length > 0 && !selectedExcel && /*#__PURE__*/React.createElement("p", {
    className: "text-sm text-amber-600 dark:text-amber-400 mb-2"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-triangle-exclamation mr-1"
  }), "Excel file needed before processing"), /*#__PURE__*/React.createElement("div", {
    className: "grid gap-3 sm:grid-cols-2 lg:grid-cols-4"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => startProcessing(false),
    className: "inline-flex w-full items-center justify-center gap-2 rounded-xl bg-brand text-white px-4 py-3 font-semibold shadow-soft hover:bg-brand-hover transition-all hover:shadow-md hover:scale-[1.01]"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-play"
  }), /*#__PURE__*/React.createElement("span", {
    className: "flex items-center gap-1.5"
  }, "Start", /*#__PURE__*/React.createElement(HelpIcon, {
    content: HELP_CONTENT.startProcessing,
    position: "top"
  }))), /*#__PURE__*/React.createElement("button", {
    onClick: () => startProcessing(true),
    className: "inline-flex w-full items-center justify-center gap-2 rounded-xl bg-warning text-black px-4 py-3 font-semibold shadow-soft hover:bg-warning-hover/90 transition-all hover:shadow-md hover:scale-[1.01]"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-bolt"
  }), /*#__PURE__*/React.createElement("span", {
    className: "flex items-center gap-1.5"
  }, "Test Run (100 tags)", /*#__PURE__*/React.createElement(HelpIcon, {
    content: HELP_CONTENT.testRun,
    position: "top"
  }))), /*#__PURE__*/React.createElement("button", {
    onClick: handleClearSession,
    className: "inline-flex w-full items-center justify-center gap-2 rounded-xl bg-danger text-white px-4 py-3 font-semibold shadow-soft hover:bg-danger-hover transition-all hover:shadow-md hover:scale-[1.01]"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-trash-can"
  }), "Clear Session"), /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      console.log('FAQ button clicked, current showFAQ:', showFAQ);
      setShowFAQ(true);
      console.log('setShowFAQ(true) called');
    },
    className: "inline-flex w-full items-center justify-center gap-2 rounded-xl bg-zinc-200/90 dark:bg-zinc-800 px-4 py-3 font-semibold hover:bg-zinc-300/80 dark:hover:bg-zinc-700 transition-all"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-circle-question"
  }), "FAQ")))), toast && /*#__PURE__*/React.createElement("div", {
    className: "fixed bottom-6 left-0 right-0 mx-auto w-[92%] max-w-md z-50"
  }, /*#__PURE__*/React.createElement("div", {
    className: cx("rounded-xl px-4 py-3 shadow-soft border backdrop-blur", "bg-white/90 dark:bg-zinc-900/90 border-zinc-200/60 dark:border-zinc-800", "flex items-center gap-3")
  }, /*#__PURE__*/React.createElement("i", {
    className: cx("fa-solid", toast.type === "error" && "fa-circle-xmark text-danger", toast.type === "success" && "fa-circle-check text-success", toast.type === "warning" && "fa-triangle-exclamation text-warning", toast.type === "info" && "fa-circle-info text-brand")
  }), /*#__PURE__*/React.createElement("div", {
    className: "text-sm flex-1"
  }, toast.text), /*#__PURE__*/React.createElement("button", {
    className: "p-2 rounded-lg hover:bg-zinc-200/60 dark:hover:bg-zinc-800",
    onClick: () => setToast(null)
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-xmark"
  })))), /*#__PURE__*/React.createElement(ProgressModal, {
    open: processingOpen,
    modeTitle: processingTitle,
    progress: progress,
    status: statusText,
    fileCount: fileCount,
    error: errorText,
    onClose: closeProcessing,
    onDownload: downloadFromModal,
    reportFilename: reportFilename,
    annotateExcelEnabled: annotateExcel,
    isTestRun: isCurrentTestRun,
    onStartFullRun: () => startProcessing(false)
  }), /*#__PURE__*/React.createElement(ImportProfileModal, {
    open: showImportProfileModal,
    onClose: () => setShowImportProfileModal(false),
    onImport: importProfileFile
  }), /*#__PURE__*/React.createElement(FAQModal, {
    open: showFAQ,
    onClose: () => setShowFAQ(false)
  }), selectedPdfs.length > 0 && selectedExcel && /*#__PURE__*/React.createElement("button", {
    onClick: openPreviewModal,
    className: "fixed z-50 bg-brand hover:bg-brand-dark text-white shadow-lg hover:shadow-xl transition-all active:scale-95 md:bottom-8 md:right-8 md:w-16 md:h-16 md:rounded-full bottom-4 left-4 right-4 h-12 rounded-xl flex items-center justify-center gap-2",
    title: "Preview Highlights"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-eye text-lg"
  }), /*#__PURE__*/React.createElement("span", {
    className: "md:hidden text-sm font-medium"
  }, "Preview Highlights")), previewModalOpen && /*#__PURE__*/React.createElement("div", {
    className: "fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50",
    onClick: closePreviewModal
  }, /*#__PURE__*/React.createElement("div", {
    className: "bg-white dark:bg-zinc-900 rounded-lg shadow-2xl w-full h-full max-w-[90vw] max-h-[90vh] flex flex-col",
    onClick: e => e.stopPropagation()
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex-shrink-0 border-b border-zinc-200 dark:border-zinc-700 p-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-between mb-3"
  }, /*#__PURE__*/React.createElement("h2", {
    className: "text-xl font-bold text-zinc-900 dark:text-zinc-100"
  }, "Preview Highlights"), /*#__PURE__*/React.createElement("button", {
    onClick: closePreviewModal,
    className: "p-2 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors",
    title: "Close (ESC)"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-times text-xl text-zinc-600 dark:text-zinc-400"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "mb-3 p-3 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800/50 rounded-lg flex items-start gap-2"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-info-circle text-amber-600 dark:text-amber-400 mt-0.5"
  }), /*#__PURE__*/React.createElement("p", {
    className: "text-sm text-amber-800 dark:text-amber-200"
  }, /*#__PURE__*/React.createElement("strong", null, "Note:"), " Comment popups are not visible in this preview. Download the preview to see all comment annotations.")), /*#__PURE__*/React.createElement("div", {
    className: "flex flex-wrap items-center gap-3"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => handleModalPageChange('prev'),
    disabled: previewModalPage <= 1 || previewModalLoading,
    className: "px-3 py-2 bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors",
    title: "Previous Page (\u2190)"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-chevron-left"
  })), /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-sm text-zinc-600 dark:text-zinc-400"
  }, "Page"), /*#__PURE__*/React.createElement("input", {
    type: "number",
    min: "1",
    max: previewModalData?.total_pages || 1,
    value: previewModalPage,
    onChange: e => {
      const val = parseInt(e.target.value);
      if (!isNaN(val)) {
        setPreviewModalPage(val);
      }
    },
    onKeyPress: e => {
      if (e.key === 'Enter') {
        handleModalGoToPage(previewModalPage);
      }
    },
    className: "w-16 px-2 py-1 text-center border border-zinc-300 dark:border-zinc-600 bg-white dark:bg-zinc-800 rounded text-sm font-semibold"
  }), /*#__PURE__*/React.createElement("button", {
    onClick: () => handleModalGoToPage(previewModalPage),
    className: "px-2 py-1 bg-brand hover:bg-brand-dark text-white rounded text-sm font-medium transition-colors"
  }, "Go"), /*#__PURE__*/React.createElement("span", {
    className: "text-sm text-zinc-500 dark:text-zinc-400"
  }, "of ", previewModalData?.total_pages || '?')), /*#__PURE__*/React.createElement("button", {
    onClick: () => handleModalPageChange('next'),
    disabled: !previewModalData || previewModalPage >= previewModalData.total_pages || previewModalLoading,
    className: "px-3 py-2 bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 rounded-lg disabled:opacity-30 disabled:cursor-not-allowed transition-colors",
    title: "Next Page (\u2192)"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-chevron-right"
  }))), /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2 ml-auto"
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => handleModalZoom('out'),
    disabled: previewModalZoom <= 0.25,
    className: "px-2 py-1 bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 rounded disabled:opacity-30 disabled:cursor-not-allowed",
    title: "Zoom Out"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-minus"
  })), /*#__PURE__*/React.createElement("input", {
    type: "range",
    min: "0.25",
    max: "4.0",
    step: "0.25",
    value: previewModalZoom,
    onChange: e => handleModalZoom('set', e.target.value),
    className: "w-24 md:w-32"
  }), /*#__PURE__*/React.createElement("button", {
    onClick: () => handleModalZoom('in'),
    disabled: previewModalZoom >= 4.0,
    className: "px-2 py-1 bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 rounded disabled:opacity-30 disabled:cursor-not-allowed",
    title: "Zoom In"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-plus"
  })), /*#__PURE__*/React.createElement("span", {
    className: "text-sm font-medium text-zinc-600 dark:text-zinc-400 min-w-[3.5rem] text-center"
  }, Math.round(previewModalZoom * 100), "%"), /*#__PURE__*/React.createElement("button", {
    onClick: () => handleModalZoom('reset'),
    className: "px-2 py-1 bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 rounded text-xs",
    title: "Reset Zoom"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-undo"
  })), /*#__PURE__*/React.createElement("button", {
    onClick: () => handleModalZoom('fitWidth'),
    className: "hidden md:block px-2 py-1 bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 rounded text-xs",
    title: "Fit Width"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-arrows-left-right"
  })), /*#__PURE__*/React.createElement("button", {
    onClick: () => handleModalZoom('fitHeight'),
    className: "hidden md:block px-2 py-1 bg-zinc-200 dark:bg-zinc-800 hover:bg-zinc-300 dark:hover:bg-zinc-700 rounded text-xs",
    title: "Fit Height"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-arrows-up-down"
  })))), previewModalData && /*#__PURE__*/React.createElement("div", {
    className: "mt-3 flex flex-wrap items-center justify-between gap-4"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex flex-wrap items-center gap-4 text-sm"
  }, previewModalData.stats && /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-3 px-3 py-2 bg-gradient-to-r from-blue-50 to-green-50 dark:from-blue-900/20 dark:to-green-900/20 border border-blue-200 dark:border-blue-800/50 rounded-lg"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-tags text-blue-600 dark:text-blue-400"
  }), /*#__PURE__*/React.createElement("span", {
    className: "font-semibold text-zinc-700 dark:text-zinc-300"
  }, "Tags on page:")), /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-1"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-lg font-bold text-green-600 dark:text-green-400"
  }, previewModalData.stats.colored_tags), /*#__PURE__*/React.createElement("span", {
    className: "text-zinc-500 dark:text-zinc-400"
  }, "/"), /*#__PURE__*/React.createElement("span", {
    className: "text-lg font-bold text-blue-600 dark:text-blue-400"
  }, previewModalData.stats.total_tags), /*#__PURE__*/React.createElement("span", {
    className: "text-xs text-zinc-500 dark:text-zinc-400 ml-1"
  }, "colored")), previewModalData.stats.total_tags > 0 && /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-1 px-2 py-0.5 bg-white/50 dark:bg-zinc-800/50 rounded-full"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-xs font-medium text-zinc-600 dark:text-zinc-400"
  }, Math.round(previewModalData.stats.colored_tags / previewModalData.stats.total_tags * 100), "%"))), previewModalData.stats.conflict_count > 0 && /*#__PURE__*/React.createElement("div", {
    className: "flex items-center gap-2 text-amber-600 dark:text-amber-400"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-exclamation-triangle"
  }), /*#__PURE__*/React.createElement("span", null, previewModalData.stats.conflict_count, " conflicts"))), previewModalData.download_url && /*#__PURE__*/React.createElement("button", {
    onClick: () => {
      window.location.href = previewModalData.download_url;
      setToast({
        type: "success",
        text: `Downloading ${previewModalData.preview_clean_name}`
      });
    },
    className: "px-4 py-2 bg-success hover:bg-success-hover text-white rounded-lg font-medium transition-colors flex items-center gap-2",
    title: "Download single-page annotated PDF"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-download"
  }), /*#__PURE__*/React.createElement("span", {
    className: "hidden sm:inline"
  }, "Download Preview PDF"), /*#__PURE__*/React.createElement("span", {
    className: "sm:hidden"
  }, "Download")))), /*#__PURE__*/React.createElement("div", {
    className: "flex-1 overflow-hidden p-4"
  }, previewModalLoading ? /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-center h-full"
  }, /*#__PURE__*/React.createElement("div", {
    className: "text-center"
  }, /*#__PURE__*/React.createElement("i", {
    className: "fa-solid fa-spinner fa-spin text-4xl text-brand mb-3"
  }), /*#__PURE__*/React.createElement("p", {
    className: "text-zinc-600 dark:text-zinc-400"
  }, "Loading preview..."))) : previewModalData ? /*#__PURE__*/React.createElement("div", {
    ref: previewModalContainerRef,
    className: "w-full h-full overflow-hidden bg-zinc-100 dark:bg-zinc-950 rounded-lg p-4",
    style: {
      cursor: isModalDragging ? 'grabbing' : 'grab'
    },
    onWheel: handleModalWheel,
    onMouseDown: handleModalMouseDown,
    onMouseMove: handleModalMouseMove,
    onMouseUp: handleModalMouseUp,
    onMouseLeave: handleModalMouseUp
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: 'inline-block',
      minWidth: '100%',
      textAlign: 'center',
      transform: `translate(${modalPanOffset.x}px, ${modalPanOffset.y}px)`,
      transition: isModalDragging ? 'none' : 'transform 0.1s ease-out'
    }
  }, /*#__PURE__*/React.createElement("canvas", {
    ref: previewCanvasRef,
    className: "block",
    style: {
      display: 'inline-block',
      margin: '0 auto'
    }
  }))) : /*#__PURE__*/React.createElement("div", {
    className: "flex items-center justify-center h-full"
  }, /*#__PURE__*/React.createElement("p", {
    className: "text-zinc-500 dark:text-zinc-400"
  }, "No preview data"))), previewModalData && previewModalData.legend && /*#__PURE__*/React.createElement("div", {
    className: "flex-shrink-0 border-t border-zinc-200 dark:border-zinc-700 p-4 max-h-32 overflow-y-auto"
  }, /*#__PURE__*/React.createElement("div", {
    className: "flex flex-wrap items-center gap-3"
  }, /*#__PURE__*/React.createElement("span", {
    className: "text-sm font-medium text-zinc-600 dark:text-zinc-400"
  }, "Legend:"), (Array.isArray(previewModalData.legend) ? previewModalData.legend : Object.entries(previewModalData.legend)).map((item, idx) => {
    // Handle both array format and object format
    let color, tagText;
    if (Array.isArray(item)) {
      // Object.entries format: [color, description]
      [color, tagText] = item;
      // If tagText is still an object, extract the tag property
      if (typeof tagText === 'object' && tagText !== null) {
        tagText = tagText.tag || JSON.stringify(tagText);
      }
    } else {
      // Array item format: {color, tag, ...}
      color = item.color;
      if (typeof item.tag === 'string') {
        tagText = item.tag;
      } else if (item.tag && typeof item.tag === 'object') {
        tagText = item.tag.tag || JSON.stringify(item.tag);
      } else {
        tagText = String(item.tag || 'Unknown');
      }
    }
    return /*#__PURE__*/React.createElement("div", {
      key: idx,
      className: "flex items-center gap-2"
    }, /*#__PURE__*/React.createElement("div", {
      className: "w-4 h-4 rounded border border-zinc-300 dark:border-zinc-600",
      style: {
        backgroundColor: color
      }
    }), /*#__PURE__*/React.createElement("span", {
      className: "text-sm text-zinc-700 dark:text-zinc-300"
    }, tagText));
  }))))));
}
ReactDOM.createRoot(document.getElementById("root")).render(/*#__PURE__*/React.createElement(App, null));
