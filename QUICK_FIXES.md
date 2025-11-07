# Quick Fixes for Common Issues

## Change Directory Issue

If you get "Illegal characters in path" error, the path likely has extra characters.

**Wrong:**
```powershell
cd 'C:\Users\Sainatha Yatham\Documents\GauntletAI\Week4\SpendSenseAI>'
```

**Correct:**
```powershell
cd "C:\Users\Sainatha Yatham\Documents\GauntletAI\Week4\SpendSenseAI"
```

Or simply:
```powershell
cd "C:\Users\Sainatha Yatham\Documents\GauntletAI\Week4\SpendSenseAI"
```

## Quick Navigation

If you're already in the project, you can use:
```powershell
cd $PSScriptRoot
```

Or if you're in a subdirectory:
```powershell
cd ..
```

## Common Path Issues

1. **Remove trailing `>`** - Don't copy the prompt character
2. **Use double quotes** for paths with spaces
3. **No quotes needed** for paths without spaces (but quotes are safer)

## Quick Commands

```powershell
# Navigate to project root
cd "C:\Users\Sainatha Yatham\Documents\GauntletAI\Week4\SpendSenseAI"

# Check current directory
pwd

# List files
ls

# Run scripts
.\scripts\close_unused_processes.bat
```

