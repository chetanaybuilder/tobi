# Contributing to Tobi

First off, thank you for considering contributing to Tobi! We welcome contributions to make the platform faster, more secure, and feature-rich.

## Getting Started

1. Fork the repository and create your branch from `main`.
2. Install dependencies for Node (`npm install`) and Python (`pip install -r requirements.txt`).
3. Make sure to configure the `.env` file referencing `.env.example`.

## Code Style

- We use **Ruff / Black** for Python code formatting and linting.
- We use **ESLint / Prettier** for frontend formatting.
- Before submitting your pull request, please run:
  ```bash
  ruff check .
  black .
  npm run lint
  ```

## Testing

- Python tests are located in `tests/`.
- Ensure everything passes before submitting:
  ```bash
  pytest tests/
  ```

## Pull Request Process

1. Ensure your PR title follows conventional commits (`feat:`, `fix:`, `chore:`, `docs:`).
2. Fill out the Pull Request template provided in `.github/PULL_REQUEST_TEMPLATE.md`.
3. Your code must pass the GitHub Actions CI pipeline before it can be merged.

Thank you!
