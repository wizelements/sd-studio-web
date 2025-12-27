# Contributing

## Quick Start

```bash
git clone https://github.com/wizelements/[repo].git
cd [repo]
pnpm install
cp .env.example .env
pnpm dev
```

## Pull Request Process

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes and commit: `git commit -m "feat: add feature"`
4. Push and open PR
5. Ensure CI passes

## Commit Messages

Use conventional commits:
- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation
- `refactor:` code changes without feature/fix
- `test:` adding tests
- `chore:` maintenance

## Code Standards

- TypeScript strict mode
- ESLint must pass
- Prettier formatting
- Tests for new features
