# Clean Up Unused Cursor Terminal Processes

## The Problem

You're seeing 21+ terminal/process instances for Cursor because:
1. Each terminal command spawns a new process
2. Processes aren't being properly closed after execution
3. Git commands using pagers leave processes hanging
4. Scripts without explicit exit codes leave processes open

## Quick Solution

Run this command in PowerShell to close unused processes:

```powershell
.\scripts\close_unused_processes.ps1
```

Or manually close processes:

1. **Open Task Manager** (Ctrl+Shift+Esc)
2. **Look for**:
   - Multiple `bash.exe` processes
   - Multiple `cmd.exe` processes  
   - Multiple `powershell.exe` processes
   - Multiple `git.exe` processes (if hanging)
3. **End processes** that are:
   - Not actively being used
   - Have no window title
   - Using minimal resources

## What Processes to Keep

**KEEP:**
- Main Cursor application processes
- Active terminal windows you're using
- Language servers (if working)
- Extension processes (if needed)

**CLOSE:**
- Terminal processes with no window title (background/hanging)
- Multiple git processes (likely hanging from pager)
- Orphaned node processes
- Duplicate terminal sessions

## Prevention

The `.cursorrules` file now includes rules to prevent this:
- Always configure git to not use pager
- Add explicit exit codes to scripts
- Use non-interactive flags
- Properly terminate commands

**Make these rules global** in Cursor settings so they apply to all projects.

## Scripts Available

1. `scripts/analyze_cursor_processes.ps1` - Analyze what processes are running
2. `scripts/close_unused_processes.ps1` - Close only unused processes
3. `scripts/close_all_terminals.ps1` - Close all terminal processes (use with caution)

