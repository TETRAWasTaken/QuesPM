# QuesPM - Question Paper Maker

A Python-based tool to generate customizable question papers in PDF format with support for multiple question types.

## Features

- **Object-Oriented Design**: Clean, maintainable code using OOP principles
- **Error Handling**: Comprehensive error handling and validation
- **Multiple Question Types**: Support for Short Answer and Long Answer questions
- **Flexible Input**: Load questions from files or enter manually
- **Random Selection**: Automatically select random questions from question banks
- **PDF Generation**: Professional PDF output with customizable headers and formatting
- **Logging**: Built-in logging for debugging and tracking

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip install reportlab colorama
```

## Usage

### Basic Usage

Run the program interactively:

```bash
python3 quespm.py
```

Follow the prompts to:
1. Enter question paper details (title, subject, marks, time)
2. Optionally add a logo image
3. Select question types
4. Load questions from files or enter manually
5. Generate the PDF

### Question File Format

Create text files with questions in Python list format:

**sample_short_questions.txt:**
```python
["What is Python", "Define OOP", "Explain inheritance", "What is polymorphism"]
```

**sample_long_questions.txt:**
```python
["Explain the concept of OOP with examples", "Discuss SOLID principles in software design"]
```

### Programmatic Usage

You can also use the classes programmatically:

```python
from quespm import QuestionPaperMaker

# Create instance
maker = QuestionPaperMaker()

# Set configuration
maker.config = {
    'filename': 'my_exam.pdf',
    'title': 'Final Exam',
    'subtitle': 'Semester 1',
    'marks': 100,
    'time': 180,
    'subject': 'Computer Science',
    'logo_path': None
}

# Add questions
maker.question_manager.add_short_answer_questions([
    "Question 1",
    "Question 2"
])

# Generate PDF
maker.generate_pdf()
```

## Project Structure

- `quespm.py` - Main Python file with OOP implementation
- `sample_short_questions.txt` - Example short answer questions
- `sample_long_questions.txt` - Example long answer questions
- `*.ttf` - Font files for PDF generation (optional)
- `*.ipynb` - Legacy Jupyter notebook files (deprecated)

## Classes

### QuestionPaperMaker
Main class that orchestrates the entire process.

### QuestionManager
Manages question loading, selection, and storage.

### PDFGenerator
Handles PDF creation and formatting.

## Error Handling

The application includes custom exceptions:
- `ConfigurationError` - Invalid configuration
- `QuestionError` - Issues with questions
- `PDFGenerationError` - PDF creation failures

## Legacy Files

The repository contains Jupyter notebook files (`.ipynb`) which are the original implementation. The new `quespm.py` file is the recommended version with:
- Better code organization
- Error handling
- OOP design
- Improved maintainability

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is open source and available for educational purposes. 
