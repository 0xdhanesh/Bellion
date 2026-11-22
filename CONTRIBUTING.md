# Contributing to Docker Environments

Thank you for your interest in contributing! This document provides guidelines for contributing to this project.

## How to Contribute

### Reporting Issues

If you encounter a bug or have a feature request:

1. **Search existing issues** to avoid duplicates
2. **Create a new issue** with a clear title and description
3. **Include relevant details**:
   - Docker version
   - Host OS and architecture
   - Steps to reproduce (for bugs)
   - Expected vs actual behavior
   - Error messages or logs

### Submitting Pull Requests

1. **Fork the repository** and create a new branch from `main`
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the code style guidelines below

3. **Test your changes**:
   ```bash
   ./scripts/verify.sh webPTDocker
   ```

4. **Commit your changes** with clear, descriptive messages:
   ```bash
   git commit -m "Add feature: description of changes"
   ```

5. **Push to your fork** and submit a pull request:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Describe your changes** in the PR description:
   - What problem does it solve?
   - How has it been tested?
   - Any breaking changes?

## Code Style Guidelines

### Dockerfile Standards

- Use clear, concise comments
- Group related commands with `&&` to minimize layers
- Clean up package manager caches (`rm -rf /var/lib/apt/lists/*`)
- Maintain alphabetical order for installed packages
- Use specific package versions when stability is critical

### Documentation

- Use clear, professional language
- Include code examples where applicable
- Keep README.md up to date with new features
- Add usage examples for new tools

## Testing Requirements

Before submitting a PR, ensure:

1. **Docker image builds successfully**:
   ```bash
   docker build -f webPTDocker/Dockerfile -t webptdocker:latest .
   ```

2. **All tools are accessible**:
   ```bash
   docker run --rm -i --network=none webptdocker:latest python3 - < tests/smoke_mcp.py
   ```

3. **Image size is reasonable** (check with `docker images`)

4. **Documentation is updated** to reflect changes

## Development Workflow

1. **Describe major changes** in an issue or the task request
2. **Keep PRs focused** - one feature/fix per PR
3. **Update documentation** alongside code changes
4. **Be responsive** to feedback and review comments

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the code, not the person
- Help others learn and grow

## Questions?

Feel free to open an issue for questions or reach out to:
- **Email**: dhanesh.professional@gmail.com
- **GitHub**: [@0xdhanesh](https://github.com/0xdhanesh)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
