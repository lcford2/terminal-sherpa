# Mutation Testing Guide

This project uses [Cosmic Ray](https://cosmic-ray.readthedocs.io/) for mutation testing to ensure our test suite effectively catches bugs.

## What is Mutation Testing?

Mutation testing works by making small changes (mutations) to your source code and running your test suite against each mutation. If a test fails, the mutant is "killed" (good!). If all tests pass, the mutant "survives" (potentially bad - might indicate a gap in your tests).

Not all mutations are created equal. Some arise from logically equivalent code, and are therefore acceptable.

## Quick Start

```bash
# Run tests with coverage
uv run task test

# Run mutation testing
uv run task mutation-test
```

## What the Mutation Script Does

The mutation testing script automatically:

1. **Installs cosmic-ray** if needed
2. **Creates configuration** targeting the `ask` module, excluding type annotation operators
3. **Runs baseline tests** to ensure your test suite passes
4. **Discovers mutations** and shows how many will be tested
5. **Executes mutation testing** with verbose output
6. **Generates reports** in `mutation_reports/`
   - `report.txt` - Text summary
   - `report.html` - Interactive HTML report

## Understanding Results

### Survival Rate

- **Good**: 0-10% survival rate
- **Acceptable**: 10-20% survival rate
- **Needs Improvement**: >20% survival rate

### Common Surviving Mutants

1. **Dead Code**: Unused conditionals or branches → Remove dead code or add tests
2. **Equivalent Mutations**: `a <= b` vs `a < b` when logically equivalent → Usually acceptable

## CI Integration

The GitHub Actions workflow at `.github/workflows/mutation-testing.yml` runs mutation testing automatically on pushes and pull requests.

## Best Practices

1. **Run mutation testing occasionally** (it's slow)
2. **Review HTML reports** to understand what needs better testing
3. **Don't aim for 0% survival** - some equivalent mutations are acceptable
4. **Use alongside code coverage** for comprehensive test quality

```bash
# Run both together
uv run pytest test/ --cov=ask --cov-report=html --cov-report=term  # Shows what code is executed
./scripts/run_mutation_testing.sh                                  # Shows what code is meaningfully tested
```
