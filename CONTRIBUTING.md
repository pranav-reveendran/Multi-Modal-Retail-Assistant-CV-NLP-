# Contributing to Multi-Modal Retail Assistant

Thank you for your interest in contributing to the Multi-Modal Retail Assistant! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Bugs

1. Check if the bug has already been reported in [Issues](https://github.com/yourusername/Multi-Modal-Retail-Assistant-CV-NLP-/issues)
2. If not, create a new issue with:
   - Clear, descriptive title
   - Detailed description of the bug
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version, etc.)
   - Screenshots if applicable

### Suggesting Enhancements

1. Check existing [Issues](https://github.com/yourusername/Multi-Modal-Retail-Assistant-CV-NLP-/issues) and [Pull Requests](https://github.com/yourusername/Multi-Modal-Retail-Assistant-CV-NLP-/pulls)
2. Create a new issue with:
   - Clear description of the enhancement
   - Use case and benefits
   - Possible implementation approach
   - Examples if applicable

### Pull Requests

1. Fork the repository
2. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following our coding standards
4. Add tests for new functionality
5. Ensure all tests pass:
   ```bash
   make test
   ```
6. Format code with black:
   ```bash
   black .
   ```
7. Commit with clear, descriptive messages
8. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
9. Open a Pull Request

## 💻 Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Multi-Modal-Retail-Assistant-CV-NLP-.git
   cd Multi-Modal-Retail-Assistant-CV-NLP-
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install pytest black flake8  # Development dependencies
   ```

4. **Set up pre-commit hooks** (optional but recommended)
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## 🧪 Testing

- Write tests for all new features
- Ensure existing tests pass
- Aim for >80% code coverage
- Run tests with:
  ```bash
  pytest tests/ -v
  pytest tests/ --cov=. --cov-report=html
  ```

## 📝 Coding Standards

### Python Style Guide

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Maximum line length: 127 characters
- Use type hints where appropriate
- Write docstrings for all functions/classes

### Example:

```python
def search_by_image(
    image: Image.Image,
    k: int = 5,
    search_mode: str = "image"
) -> List[Dict]:
    """
    Search for similar products using an image

    Args:
        image: PIL Image object
        k: Number of results to return
        search_mode: Search mode ("image" or "text")

    Returns:
        List of result dictionaries
    """
    # Implementation here
    pass
```

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example:
```
feat: add category filtering to search results

- Add category parameter to search endpoints
- Update frontend UI with category selector
- Add tests for category filtering
```

## 🏗️ Project Structure

```
backend/          # FastAPI backend code
frontend/         # Streamlit frontend code
scripts/          # Utility scripts (embeddings, dataset, etc.)
tests/            # Test files
data/             # Data files (not committed)
.github/          # GitHub Actions workflows
```

## 📚 Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add comments for complex logic
- Include examples in docstrings

## 🎯 Areas for Contribution

### High Priority
- [ ] Add category filtering to search
- [ ] Implement hybrid image+text queries
- [ ] Add user feedback mechanism
- [ ] Improve test coverage
- [ ] Performance optimizations

### Medium Priority
- [ ] Multi-language support
- [ ] Batch image upload
- [ ] Redis caching
- [ ] Analytics dashboard
- [ ] Mobile-responsive UI

### Nice to Have
- [ ] Video product search
- [ ] Browser extension
- [ ] Slack/Discord bot integration
- [ ] GraphQL API
- [ ] Admin dashboard

## 🔍 Code Review Process

1. All PRs require at least one review
2. CI/CD checks must pass
3. Code coverage should not decrease
4. Documentation must be updated
5. Follow-up on review comments promptly

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## ❓ Questions?

- Open an issue with the `question` label
- Join our community discussions
- Contact maintainers directly

## 🌟 Recognition

Contributors will be recognized in:
- README.md Contributors section
- Release notes
- GitHub contributors page

Thank you for contributing to make Multi-Modal Retail Assistant better!
