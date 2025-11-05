# SpendSenseAI Setup Guide

This guide will help you set up SpendSenseAI for development.

## Prerequisites

- **Python 3.9 or higher**
- **Git** (with Git Bash installed)
- **pip** (Python package manager)
- **Virtual environment tool** (venv, recommended)

### Terminal Configuration

This project is configured to use **Git Bash** as the default terminal in Cursor/VS Code. The workspace settings (`.vscode/settings.json`) are already configured.

**To verify Git Bash is set as default:**
- Open a new terminal in Cursor (`` Ctrl+` ``)
- The terminal should open with Git Bash
- If not, manually select "Git Bash" from the terminal profile dropdown

**Git Bash is recommended because:**
- Better Unix-like command syntax
- Native SSH support
- Consistent with Linux/macOS development
- Better Git integration

## Installation Steps

### 1. Clone the Repository

```bash
git clone git@github.com:sainathyai/SpendSenseAI.git
cd SpendSenseAI
```

### 2. Create Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify Installation

```bash
python --version  # Should be 3.9+
pip list  # Should show installed packages
```

### 5. Run Tests (once available)

```bash
pytest
```

## Project Structure

```
SpendSenseAI/
├── ingest/           # Data loading and validation
├── features/         # Signal detection
├── personas/         # Persona assignment
├── recommend/        # Recommendation engine
├── guardrails/       # Consent and safety
├── ui/              # User interfaces
├── eval/            # Evaluation metrics
├── docs/            # Documentation
├── data/            # Data storage
│   ├── raw/         # Raw synthetic data
│   └── processed/   # Processed features
├── tests/           # Test suite
│   ├── unit/        # Unit tests
│   └── integration/ # Integration tests
└── README.md        # Project overview
```

## Configuration

Configuration files will be added in future PRs.

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout main
git pull origin main
git checkout -b pr-###-feature-name
```

### 2. Make Changes

- Write code
- Add tests
- Update documentation

### 3. Run Tests

```bash
pytest
```

### 4. Commit and Push

```bash
git add .
git commit -m "[PR-###] Your descriptive message"
git push origin pr-###-feature-name
```

### 5. Create Pull Request

- Go to GitHub repository
- Create pull request from your branch to `main`
- Fill in PR template with details

## Common Issues

### Issue: Module not found
**Solution:** Ensure virtual environment is activated and dependencies installed

### Issue: Permission denied
**Solution:** Check file permissions, may need to run as administrator

### Issue: Python version mismatch
**Solution:** Install Python 3.9+ and recreate virtual environment

## Next Steps

After setup:
1. Review the PRD: `Platinum Project_ Peak6_SpendSense.md`
2. Check the implementation plan: `PR_by_PR_Implementation_Plan.md`
3. Read contributing guidelines: `CONTRIBUTING.md`
4. Start with current PR tasks

## Tools Recommendations

### Code Formatting
```bash
# Format code
black .

# Sort imports
isort .

# Lint code
flake8
```

### Testing
```bash
# Run tests with coverage
pytest --cov=. --cov-report=html

# Open coverage report
# On Windows: .\htmlcov\index.html
# On macOS/Linux: open htmlcov/index.html
```

## Environment Variables

Create a `.env` file (not committed to git) for local configuration:

```env
# Database
DATABASE_PATH=data/spendsense.db

# API
API_HOST=localhost
API_PORT=8000

# Logging
LOG_LEVEL=INFO
```

## Database Setup

Database initialization will be covered in PR #4 (Data Ingestion).

## Running the Application

Application run instructions will be added as APIs are built.

## Support

For questions or issues:
- Check documentation in `docs/`
- Review project planning documents
- Contact: Bryce Harris - bharris@peak6.com

---

**Ready to build!** 🚀

