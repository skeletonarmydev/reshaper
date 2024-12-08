# Go Code Migration Tool

An AI-powered tool for automated Go code migration and improvement. This tool performs targeted transformations to enhance code quality while preserving functionality.

## Features

- **Centralized Error Handling**: Automatically transforms various error handling patterns into a consistent approach
- **Import Management**: Intelligently manages and optimizes import statements
- **Pattern-Based Transformations**: Configurable patterns for different types of code changes
- **Multi-Stage Validation**: Ensures code correctness after transformations
- **Comment Preservation**: Maintains existing code comments during transformations

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Create a `.env` file with your OpenAI API key:
```
LLM_API_KEY=your_api_key_here
```

## Usage

Run the tool on your Go project:

```bash
python main.py
```

The tool will:
1. Analyze your Go codebase
2. Apply configured transformations
3. Validate the changes
4. Save the modified files

## Configuration

The tool's behavior is controlled by `config.py`:

- `FILE_EXTENSIONS`: File types to process (default: [".go"])
- `IGNORE_DIRS`: Directories to skip (default: ["vendor", "node_modules", ".git"])
- `DEPENDENCY_ORDER`: Processing order for different components

## Transformations

### Error Handling
- Replaces `fmt.Println(err)` with `utils.CheckErr`
- Replaces `fmt.Println(err.Error())` with `utils.CheckErr`
- Replaces `os.Exit(1)` with appropriate error handling

### Import Management
- Adds required utility imports
- Removes unused imports
- Maintains import block structure
- Preserves necessary third-party imports

## Requirements

- Python 3.8+
- OpenAI API key
- Go 1.16+ (for validation)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

MIT License
