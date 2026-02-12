# Contributing to SkyWatch

Thank you for your interest in contributing to SkyWatch! We welcome contributions from the community.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue on GitHub with:
- A clear description of the bug
- Steps to reproduce
- Expected vs actual behavior
- Your environment (OS, Python version, camera model)
- Relevant logs or screenshots

### Suggesting Features

Feature requests are welcome! Please open an issue describing:
- The feature you'd like to see
- Your use case
- How it would benefit other users

### Code Contributions

1. **Fork the repository**
2. **Create a branch** for your feature (`git checkout -b feature/amazing-feature`)
3. **Make your changes**
4. **Test thoroughly**
5. **Commit with clear messages** (`git commit -m 'Add amazing feature'`)
6. **Push to your fork** (`git push origin feature/amazing-feature`)
7. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/skywatch.git
cd skywatch

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python main.py
```

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Comment complex logic
- Keep functions focused and modular

### Testing

Before submitting a PR:
- Test with different camera streams if possible
- Verify all capture modes work
- Check the web interface on mobile and desktop
- Ensure no breaking changes to existing functionality

### Areas for Contribution

We especially welcome contributions in:
- AI/ML integration for object detection
- Additional camera protocol support
- Video processing enhancements
- Mobile app development
- Documentation improvements
- Bug fixes and optimizations

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on the best solution for all users
- Help others learn and grow

## Questions?

Feel free to open an issue with the "question" label if you need help or clarification.

Thank you for contributing to SkyWatch! 🌤️
