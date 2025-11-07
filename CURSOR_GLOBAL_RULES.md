# Cursor Global Rules Setup

## Current Status

The `.cursorrules` file in this project is **project-specific** and only applies to this repository.

## Making Rules Global

To make cursor rules apply to **all projects and instances**, you need to configure them in Cursor's global settings.

### Option 1: Cursor Settings UI (Recommended)

1. Open Cursor
2. Go to **Settings** (Ctrl+, or Cmd+,)
3. Search for "cursor rules" or "rules"
4. Look for **"Cursor Rules"** or **"AI Rules"** section
5. Paste the rules content there

### Option 2: Cursor Settings JSON

1. Open Cursor
2. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
3. Type "Preferences: Open User Settings (JSON)"
4. Add or update the cursor rules configuration:

```json
{
  "cursor.rules": "# Cursor Rules for All Projects\n\n## Terminal Process Management\n\n**CRITICAL: Always ensure terminal processes close properly**\n\nWhen using `run_terminal_cmd`:\n1. **Always configure git to not use pager**: Use `git config --global core.pager cat` or `git --no-pager` for git commands\n2. **Add explicit exit codes**: Scripts should end with `exit 0` (success) or `exit 1` (failure)\n3. **Use non-interactive flags**: Add `--yes`, `-y`, `--no-prompt` flags where available\n4. **Avoid commands that wait for input**: Use environment variables or config files instead of interactive prompts\n5. **Set proper error handling**: Use `$ErrorActionPreference = \"Stop\"` in PowerShell scripts\n6. **Close processes explicitly**: Batch files should use `exit /b %ERRORLEVEL%` to properly close\n7. **Never leave processes hanging**: If a command might hang, add timeout or use background execution with proper cleanup\n8. **Always terminate commands**: Ensure every command completes and doesn't wait for input\n9. **Use explicit termination**: Add `| cat` to commands that might use pagers, or use `--no-pager` flags\n10. **Close terminal sessions**: After running commands, ensure the terminal session is properly closed\n\n### Best Practices:\n- For git commands: Always use `--no-pager` or configure `core.pager = cat`\n- For PowerShell: Use `-NoProfile` and `-ExecutionPolicy Bypass` flags\n- For batch files: Always end with explicit exit codes\n- For long-running commands: Use background execution (`is_background: true`) or add timeouts\n- Always check `$LASTEXITCODE` or `%ERRORLEVEL%` before proceeding"
}
```

### Option 3: Global Rules File Location

Cursor may also support a global rules file. Check these locations:

**Windows:**
- `%APPDATA%\Cursor\User\globalRules.md`
- `%USERPROFILE%\.cursor\rules.md`

**Mac:**
- `~/Library/Application Support/Cursor/User/globalRules.md`
- `~/.cursor/rules.md`

**Linux:**
- `~/.config/Cursor/User/globalRules.md`
- `~/.cursor/rules.md`

## Recommended Approach

1. **Keep project-specific rules** in `.cursorrules` for project-specific conventions
2. **Set global rules** in Cursor settings for universal best practices (like terminal management)
3. **Combine both**: Global rules apply everywhere, project rules add project-specific guidance

## Current Project Rules

The `.cursorrules` file in this project contains:
- Terminal Process Management (should be global)
- Code Style (project-specific)
- Testing (project-specific)
- Documentation (project-specific)

## Next Steps

1. Copy the Terminal Process Management section to Cursor's global settings
2. Keep project-specific rules in `.cursorrules`
3. Test that global rules apply in a new project

