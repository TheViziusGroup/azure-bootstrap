# Contributing to Azure Bootstrap Library

Thank you for contributing to the Azure Bootstrap Library! This document provides guidelines and standards for contributing to this project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Git Workflow](#git-workflow)
- [Quality Standards](#quality-standards)
- [Development Process](#development-process)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

---

## Code of Conduct

### Our Standards

- **Be Respectful**: Treat all contributors with respect and professionalism
- **Be Collaborative**: Work together to improve the library
- **Be Constructive**: Provide helpful feedback and suggestions
- **Be Responsible**: Take ownership of your contributions

### Scope

This library is used across 17+ production Azure Functions applications. Changes impact multiple teams and projects, so quality and reliability are paramount.

---

## Getting Started

### Prerequisites

- Python 3.11 or higher
- Git
- GitHub account
- Familiarity with Azure Functions, App Configuration, and Key Vault

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/TheViziusGroup/azure-bootstrap
cd azure-bootstrap

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Install in editable mode with all dependencies
pip install -e ".[dev]"

# Verify setup
pytest
```

---

## Git Workflow

We use **Gitflow** with the following branch structure:

### Branch Structure

```
main (protected)
├── dev (protected)
    ├── feature/feature-name
    ├── bugfix/bug-description
    ├── hotfix/critical-fix
    └── release/v1.1.0
```

### Branch Types

#### 1. `main` Branch (Production)

- **Purpose**: Production-ready code only
- **Protection**: Direct commits disabled, requires PR approval
- **CI/CD**: Triggers automatic publish to PyPI
- **Tags**: All releases tagged here (e.g., `v1.0.0`)

**Rules**:
- ✅ Only merge from `dev` or `hotfix/*`
- ✅ Must pass all tests and quality checks
- ✅ Requires 2 approvals
- ❌ No direct commits
- ❌ No force push

#### 2. `dev` Branch (Development)

- **Purpose**: Integration branch for features
- **Protection**: Requires PR approval, runs tests
- **CI/CD**: Runs tests but doesn't publish
- **Merge From**: `feature/*`, `bugfix/*`, `release/*`

**Rules**:
- ✅ Merge features here first
- ✅ Must pass all tests
- ✅ Requires 1 approval
- ❌ No direct commits to dev
- ❌ No force push

#### 3. `feature/*` Branches

- **Purpose**: New features and enhancements
- **Naming**: `feature/short-description` (e.g., `feature/add-feature-flags`)
- **Base**: Branch from `dev`
- **Merge To**: `dev` via pull request

**Lifecycle**:
```bash
# Create feature branch
git checkout dev
git pull origin dev
git checkout -b feature/add-feature-flags

# Make changes, commit often
git add .
git commit -m "feat: add feature flag support"

# Push and create PR
git push origin feature/add-feature-flags
# Create PR: feature/add-feature-flags → dev
```

#### 4. `bugfix/*` Branches

- **Purpose**: Non-critical bug fixes
- **Naming**: `bugfix/short-description` (e.g., `bugfix/fix-config-loading`)
- **Base**: Branch from `dev`
- **Merge To**: `dev` via pull request

**Lifecycle**:
```bash
# Create bugfix branch
git checkout dev
git pull origin dev
git checkout -b bugfix/fix-config-loading

# Fix bug, add test
git add .
git commit -m "fix: resolve config loading race condition"

# Push and create PR
git push origin bugfix/fix-config-loading
# Create PR: bugfix/fix-config-loading → dev
```

#### 5. `hotfix/*` Branches

- **Purpose**: Critical production fixes
- **Naming**: `hotfix/critical-issue` (e.g., `hotfix/auth-failure`)
- **Base**: Branch from `main`
- **Merge To**: BOTH `main` AND `dev`

**Lifecycle**:
```bash
# Create hotfix branch
git checkout main
git pull origin main
git checkout -b hotfix/auth-failure

# Fix critical issue
git add .
git commit -m "fix: resolve authentication failure in production"

# Merge to main first
git checkout main
git merge hotfix/auth-failure
git tag v1.0.0
git push origin main --tags

# Then merge to dev
git checkout dev
git merge hotfix/auth-failure
git push origin dev

# Delete hotfix branch
git branch -d hotfix/auth-failure
git push origin --delete hotfix/auth-failure
```

#### 6. `release/*` Branches

- **Purpose**: Prepare new version for release
- **Naming**: `release/v1.1.0`
- **Base**: Branch from `dev`
- **Merge To**: `main` and back to `dev`

**Lifecycle**:
```bash
# Create release branch
git checkout dev
git pull origin dev
git checkout -b release/v1.1.0

# Update version numbers
# - pyproject.toml: version = "1.1.0"
# - azure_bootstrap/__init__.py: __version__ = "1.1.0"
# - CLAUDE.md Version History: Add release notes

git add .
git commit -m "chore: bump version to 1.1.0"

# Merge to main
git checkout main
git merge release/v1.1.0
git tag v1.1.0
git push origin main --tags

# Merge back to dev
git checkout dev
git merge release/v1.1.0
git push origin dev

# Delete release branch
git branch -d release/v1.1.0
```

### Commit Message Convention

We follow **Conventional Commits** specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

#### Commit Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no feature change)
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes
- `ci`: CI/CD pipeline changes
- `chore`: Other changes (dependencies, config)

#### Examples

```bash
# Feature
git commit -m "feat(config): add feature flag support for config loading"

# Bug fix
git commit -m "fix(telemetry): resolve race condition in App Insights initialization"

# Documentation
git commit -m "docs: update installation instructions"

# Breaking change
git commit -m "feat(bootstrap)!: change initialize_application signature

BREAKING CHANGE: initialize_application now requires explicit secrets_repository parameter"
```

---

## Quality Standards

### 1. Code Quality

#### Style & Formatting

- **Formatter**: Black (line length: 100)
- **Linter**: Ruff
- **Type Hints**: Required for all public APIs

```bash
# Format code
black azure_bootstrap/ test/

# Lint code
ruff check azure_bootstrap/ test/

# Type check
mypy azure_bootstrap/
```

#### Code Standards

- ✅ Use descriptive variable names
- ✅ Write docstrings for all public functions/classes
- ✅ Keep functions focused and small (< 50 lines)
- ✅ Use type hints for function signatures
- ✅ Follow PEP 8 style guide
- ❌ No magic numbers (use constants)
- ❌ No commented-out code
- ❌ No print statements (use logging)

### 2. Testing Requirements

#### Coverage Requirements

- **Minimum**: 80% overall coverage
- **New Code**: 90% coverage
- **Critical Paths**: 100% coverage (bootstrap flow, config loading)

```bash
# Run tests with coverage
pytest --cov=azure_bootstrap --cov-report=term-missing --cov-report=html

# View HTML report
open htmlcov/index.html
```

#### Test Structure

```python
class TestFeatureName:
    """Tests for FeatureName functionality."""

    def setup_method(self):
        """Setup before each test."""
        self.original_env = os.environ.copy()

    def teardown_method(self):
        """Cleanup after each test."""
        os.environ.clear()
        os.environ.update(self.original_env)

    def test_specific_behavior(self):
        """Test specific behavior with clear description."""
        # Arrange
        expected = "value"

        # Act
        result = function_under_test()

        # Assert
        assert result == expected
```

#### Test Categories

- **Unit Tests**: Test individual functions/classes in isolation
- **Integration Tests**: Test component interactions
- **Mock External Dependencies**: Azure services, environment variables

#### Testing Checklist

- ✅ Test happy path
- ✅ Test error cases
- ✅ Test edge cases
- ✅ Test with mocked Azure services
- ✅ Test environment variable fallbacks
- ✅ Test configuration precedence
- ✅ Verify no side effects

### 3. Security Standards

#### Security Checklist

- ✅ Never commit secrets or credentials
- ✅ Use Azure Key Vault for secrets
- ✅ Validate all user inputs
- ✅ Use secure defaults
- ✅ Log security events appropriately
- ❌ No hardcoded passwords/keys
- ❌ No sensitive data in logs
- ❌ No SQL injection vulnerabilities

#### Dependency Security

```bash
# Check for known vulnerabilities
pip-audit

# Update dependencies regularly
pip install --upgrade pip setuptools wheel
```

### 4. Complexity Standards

#### Cyclomatic Complexity

- **Target**: < 10 per function
- **Maximum**: < 15 per function
- **Tool**: Radon or Ruff

```bash
# Check complexity
radon cc azure_bootstrap/ -a -nb
```

#### Maintainability Index

- **Target**: > 20 (good)
- **Minimum**: > 10 (acceptable)

```bash
# Check maintainability
radon mi azure_bootstrap/
```

### 5. Documentation Standards

#### Required Documentation

- ✅ Docstrings for all public functions/classes
- ✅ Type hints for all function signatures
- ✅ README examples for new features
- ✅ Version History entries in CLAUDE.md for all changes
- ✅ CLAUDE.md updates for architectural changes

#### Docstring Format

```python
def initialize_application(secrets_repository: Optional[SecretsRepositoryInterface] = None) -> EnhancedConfigRepository:
    """
    Initialize application bootstrap with configuration and telemetry.

    This function orchestrates the complete bootstrap sequence:
    1. Configure bootstrap logging
    2. Setup telemetry
    3. Load configuration from App Config/Key Vault
    4. Upgrade telemetry if App Insights available
    5. Load all configs to os.environ

    Args:
        secrets_repository: Optional custom secrets repository.
                          If not provided, creates default Key Vault repository.

    Returns:
        EnhancedConfigRepository instance with loaded configuration.

    Raises:
        ConfigurationError: If configuration loading fails critically.

    Example:
        >>> config_repo = initialize_application()
        >>> db_host = os.getenv("DATABASE_HOST")
    """
```

---

## Git Hooks

The repository includes pre-commit and pre-push hooks that enforce code quality standards.

### Installation

**Windows (PowerShell)**:
```powershell
powershell -ExecutionPolicy Bypass -File .githooks\install-hooks.ps1
```

**Linux/Mac/Git Bash**:
```bash
bash .githooks/install-hooks.sh
```

**Manual**:
```bash
git config core.hooksPath .githooks
```

### What Gets Checked

#### pre-commit (~30-60 seconds)

Runs on every `git commit`:
1. **Black** - Code formatting (line length 100)
2. **isort** - Import sorting (Black-compatible)
3. **Ruff** - Linting (pycodestyle, pyflakes, bugbear, etc.)
4. **MyPy** - Type checking (with ignore_missing_imports)
5. **Bandit** - Security vulnerability scanning
6. **pip-audit** - Dependency security audit (warning only)
7. **pytest** - Full test suite with **85%+ coverage requirement**

#### pre-push (~60-90 seconds)

Runs on every `git push`:
1. All pre-commit checks
2. Full verbose test suite
3. Package build verification

### Quick Fix Commands

```bash
# Auto-fix formatting and imports
black azure_bootstrap/ test/
isort azure_bootstrap/ test/
ruff check --fix azure_bootstrap/ test/

# Run all checks manually
bash .githooks/pre-commit
```

### Bypassing Hooks

**Not recommended**, but available:
```bash
git commit --no-verify   # Skip pre-commit
git push --no-verify     # Skip pre-push
```

### Disabling / Re-enabling Hooks

```bash
git config core.hooksPath ""          # Disable
git config core.hooksPath .githooks   # Re-enable
```

### Hook Troubleshooting

- **"Virtual environment not found"**: Run `pip install -e ".[dev]"`
- **"Permission denied" (Linux/Mac)**: Run `chmod +x .githooks/pre-commit .githooks/pre-push`
- **Hooks not running**: Check `git config core.hooksPath` outputs `.githooks`

All tool configurations are in `pyproject.toml` (`[tool.black]`, `[tool.isort]`, `[tool.ruff]`, `[tool.mypy]`, `[tool.bandit]`, `[tool.coverage.report]`).

---

## VS Code Setup

The `.vscode/` directory contains workspace configuration for development.

### Configuration Files

- **settings.json** - Python testing (pytest), formatting (Black, line length 100), linting (Ruff), coverage gutters, file exclusions
- **launch.json** - Debug configurations: Debug Tests, Debug Current Test File, Debug Tests with Coverage
- **tasks.json** - Quick tasks: Run Tests, Run with Coverage, Format Code, Lint Code, Type Check, Build Package, Clean Artifacts, Full Quality Check
- **extensions.json** - Recommended extensions: Python/Pylance, Black, Ruff, Test Explorer, Coverage Gutters, TOML support

### Key Shortcuts

- **F5** - Start debugging (with selected launch config)
- **Ctrl+Shift+B** - Run default build task (Build Package)
- **Ctrl+Shift+T** - Run default test task (Run All Tests)
- **Ctrl+Shift+P** → "Tasks: Run Task" - Access all custom tasks

### Coverage Integration

After running tests with coverage, install the "Coverage Gutters" extension and click "Watch" in the status bar. Green/red gutters show line coverage in code files.

**Note**: The virtual environment path is configured as `${workspaceFolder}/.venv/Scripts/python.exe`. Update `python.defaultInterpreterPath` in settings.json if using a different venv location.

---

## Development Process

### 1. Before You Start

- ✅ Check existing issues and PRs
- ✅ Discuss major changes in advance
- ✅ Create an issue for tracking
- ✅ Update your local branches

### 2. During Development

```bash
# Keep your branch updated
git checkout dev
git pull origin dev
git checkout feature/your-feature
git merge dev

# Commit often with good messages
git add specific-files  # Not git add .
git commit -m "feat: descriptive message"

# Run tests frequently
pytest

# Check code quality
black azure_bootstrap/ test/
ruff check azure_bootstrap/ test/
```

### 3. Before Submitting PR

#### Pre-PR Checklist

- ✅ All tests pass: `pytest`
- ✅ Coverage meets requirements: `pytest --cov`
- ✅ Code formatted: `black .`
- ✅ No lint errors: `ruff check .`
- ✅ Type hints added: `mypy azure_bootstrap/`
- ✅ Documentation updated
- ✅ Version History in CLAUDE.md updated
- ✅ Examples added/updated if needed
- ✅ Branch up to date with dev

```bash
# Run full quality check
black azure_bootstrap/ test/
ruff check azure_bootstrap/ test/
mypy azure_bootstrap/
pytest --cov=azure_bootstrap --cov-report=term-missing
```

---

## Pull Request Process

### 1. Creating a Pull Request

```bash
# Push your branch
git push origin feature/your-feature

# Create PR via GitHub CLI
gh pr create \
  --base dev \
  --title "feat: Add feature flag support" \
  --body "Implements feature flags using Azure App Configuration"
```

### 2. PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change
- [ ] Documentation update

## Changes Made
- Item 1
- Item 2

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing
- [ ] Coverage >= 80%

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Version History in CLAUDE.md updated
- [ ] No breaking changes (or documented)
```

### 3. PR Review Process

#### Reviewer Checklist

- ✅ Code quality and readability
- ✅ Test coverage and quality
- ✅ Documentation completeness
- ✅ No security vulnerabilities
- ✅ Backwards compatibility
- ✅ Performance implications

#### Review Response Time

- **Standard PRs**: 2 business days
- **Hotfixes**: 4 hours
- **Small fixes**: 1 business day

### 4. Addressing Feedback

```bash
# Make requested changes
git add changed-files
git commit -m "refactor: address PR feedback"

# Push updates
git push origin feature/your-feature

# PR automatically updates
```

### 5. Merging

- **Merge Strategy**: Squash and merge (for features/bugfixes)
- **Hotfixes**: Regular merge (preserve history)
- **Release branches**: Regular merge

---

## Release Process

### Version Numbering (Semantic Versioning)

- **Major (X.0.0)**: Breaking API changes
- **Minor (0.X.0)**: New features (backwards compatible)
- **Patch (0.0.X)**: Bug fixes

### Release Checklist

1. **Create Release Branch**
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b release/v1.1.0
   ```

2. **Update Version Numbers**
   - `pyproject.toml`: `version = "1.1.0"`
   - `azure_bootstrap/__init__.py`: `__version__ = "1.1.0"`

3. **Update Version History in CLAUDE.md**
   ```markdown
   ## [1.1.0] - 2025-11-22

   ### Added
   - Feature flag support

   ### Changed
   - Improved error messages

   ### Fixed
   - Configuration race condition
   ```

4. **Test Release**
   ```bash
   pytest
   python -m build
   pip install dist/azure_bootstrap-1.1.0-py3-none-any.whl
   ```

5. **Merge to Main**
   ```bash
   git checkout main
   git merge release/v1.1.0
   git tag v1.1.0
   git push origin main --tags
   ```

6. **Merge Back to Dev**
   ```bash
   git checkout dev
   git merge release/v1.1.0
   git push origin dev
   ```

7. **Verify Pipeline**
   - Check Azure Pipeline runs successfully
   - Verify package published to PyPI
   - Test installation from feed

8. **Announce Release**
   - Update documentation
   - Notify consuming teams
   - Post release notes

---

## Additional Guidelines

### Dependencies

- **Adding Dependencies**: Justify new dependencies, prefer stdlib
- **Updating Dependencies**: Test thoroughly, update in minor releases only
- **Security Updates**: Patch releases acceptable

### Breaking Changes

- **Avoid When Possible**: Breaking changes disrupt 17+ projects
- **Deprecation Period**: Deprecate for 1 minor version before removal
- **Communication**: Announce breaking changes in advance
- **Documentation**: Provide migration guide

### Performance

- **Benchmark**: Measure performance impact of changes
- **No Degradation**: Changes shouldn't slow bootstrap time
- **Profile**: Use profiling tools for optimization

---

## Getting Help

### Questions?

- **Documentation**: See [CLAUDE.md](CLAUDE.md)
- **Examples**: See [examples/](examples/)
- **Issues**: Create an issue on GitHub
- **Discussion**: Use Teams channel or email team

### Reporting Bugs

1. Check if bug already reported
2. Create detailed bug report with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details
   - Error messages/logs
3. Add `bug` label

### Requesting Features

1. Check if feature already requested
2. Create feature request with:
   - Use case and benefit
   - Proposed solution
   - Alternative solutions considered
3. Add `enhancement` label

---

## Thank You!

Your contributions help maintain and improve a critical library used across multiple organizations. Thank you for following these guidelines and maintaining high quality standards!
