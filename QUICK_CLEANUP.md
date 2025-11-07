# Quick Cleanup - Close Unused Processes

## Option 1: Run with Bypass (Recommended)

```powershell
powershell.exe -ExecutionPolicy Bypass -NoProfile -File "scripts\close_unused_processes.ps1"
```

## Option 2: Use Batch File

```cmd
scripts\close_unused_processes.bat
```

Or double-click: `scripts\close_unused_processes.bat`

## Option 3: Change Execution Policy (Permanent)

If you want to allow scripts to run permanently:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then you can run:
```powershell
.\scripts\close_unused_processes.ps1
```

## What It Does

- Closes terminal processes with no window (unused/hanging)
- Closes hanging git processes
- Closes orphaned node processes
- **Keeps** active terminal windows you're using
- **Keeps** essential Cursor processes

## Manual Alternative

1. Open **Task Manager** (Ctrl+Shift+Esc)
2. Go to **Details** tab
3. Look for multiple instances of:
   - `bash.exe`
   - `cmd.exe`
   - `powershell.exe`
   - `git.exe`
4. End processes that:
   - Have no window title
   - Are using minimal resources
   - You're not actively using

