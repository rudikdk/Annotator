# Python 3.13 Compatibility Fix

## Problem

You're encountering this error when starting the application:

```
ValueError: Invalid async_mode specified
```

This happens because **eventlet is not compatible with Python 3.13**. The application is trying to initialize Flask-SocketIO with threading mode, but having eventlet installed creates a conflict.

## Solution

### Quick Fix (Run this now)

1. **Double-click on `fix_python313.bat`** - This will automatically:
   - Uninstall the incompatible eventlet package
   - Reinstall dependencies properly

2. **Run the application** using `start_annotator.bat`

### Manual Fix (if the script doesn't work)

Open Command Prompt in this directory and run:

```bash
python -m pip uninstall -y eventlet
python -m pip install -r requirements.txt
```

## What Changed

### Updated Files

1. **requirements.txt** - Commented out eventlet:
   ```
   # eventlet==0.33.3  # Disabled: Not compatible with Python 3.13
   ```

2. **app.py** - Already configured correctly:
   - Uses `threading` mode by default (line 52)
   - Falls back to environment variable `SOCKETIO_ASYNC_MODE` if needed

## Deployment Considerations

### Local Development (Windows/Mac/Linux)
- **Async mode:** `threading` (default)
- **No eventlet needed**
- Works perfectly with Python 3.13

### Docker Production (Raspberry Pi 5)
- **Async mode:** `eventlet` (via environment variable)
- **Python version:** 3.11 (as specified in Dockerfile)
- Eventlet works fine with Python 3.11 in containers

### Environment Variable Override

If you need to switch modes, set this environment variable:

```bash
# Windows
set SOCKETIO_ASYNC_MODE=threading

# Linux/Mac/Docker
export SOCKETIO_ASYNC_MODE=eventlet
```

## Technical Details

### Why Does This Happen?

Python 3.13 includes changes to internal APIs that eventlet hasn't adapted to yet:
- Eventlet monkey-patches low-level Python networking
- Python 3.13's new socket/asyncio internals break these patches
- Flask-SocketIO detects eventlet is installed and tries to use it
- This fails with "Invalid async_mode specified"

### Which Mode Should I Use?

| Environment | Recommended Mode | Why |
|-------------|-----------------|-----|
| Local development | `threading` | Simple, no extra dependencies |
| Docker + Gunicorn | `eventlet` | Better performance for concurrent connections |
| Production (bare metal) | `gevent` or `eventlet` | Production-grade async workers |

### Performance Impact

For typical usage (< 10 concurrent users):
- **No noticeable difference** between threading and eventlet
- Both modes support WebSocket real-time updates
- Threading mode is actually simpler and more reliable for development

## Verification

After applying the fix, you should see:

```
========================================
   PID Annotator - Starting...
========================================

[OK] Python is installed
[OK] Dependencies are installed

========================================
Starting PID Annotator on port 5001...
========================================

 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5001
```

## Troubleshooting

### Still Getting Errors?

1. **Check Python version:**
   ```bash
   python --version
   ```
   Should show Python 3.13.x

2. **Verify eventlet is uninstalled:**
   ```bash
   python -m pip show eventlet
   ```
   Should show "WARNING: Package(s) not found: eventlet"

3. **Check Flask-SocketIO version:**
   ```bash
   python -m pip show flask-socketio
   ```
   Should show version 5.3.6

### Need Eventlet for Production?

If you're deploying to production and need eventlet:
- **Option 1:** Use Python 3.11 or 3.12 instead of 3.13
- **Option 2:** Use Docker with Python 3.11 base image (already configured)
- **Option 3:** Wait for eventlet to release Python 3.13 support

## Related Files

- [app.py](app.py#L49-L55) - SocketIO initialization
- [requirements.txt](requirements.txt) - Python dependencies
- [Dockerfile](Dockerfile) - Uses Python 3.11 for compatibility
- [CLAUDE.md](CLAUDE.md#L137-L160) - Architecture documentation

## Support

If you continue to experience issues:
1. Check the [Flask-SocketIO documentation](https://flask-socketio.readthedocs.io/)
2. Review Python 3.13 [release notes](https://docs.python.org/3.13/whatsnew/3.13.html)
3. Open an issue with your error logs
