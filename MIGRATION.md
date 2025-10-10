# Migration Guide: From Jupyter Notebook to Python Module

## Overview

This document explains the differences between the old Jupyter notebook implementation and the new `quespm.py` Python module.

## Key Improvements

### 1. Object-Oriented Design

**Before (Notebook):**
```python
# Global variables scattered throughout
LATQ = []
SATQ = []
used = []

# Functions using global state
def cursormoves1(canvas, loca, data):
    global loc
    # ... function code
```

**After (Python Module):**
```python
class QuestionManager:
    """Encapsulates question management logic"""
    def __init__(self):
        self.short_answer_questions = []
        self.long_answer_questions = []
```

### 2. Error Handling

**Before (Notebook):**
```python
file = open(r"/content/qpmaker.txt", "r")  # No error handling
contents = file.read()
```

**After (Python Module):**
```python
try:
    if not os.path.exists(filepath):
        raise QuestionError(f"Question file not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as file:
        contents = file.read()
        questions = ast.literal_eval(contents)
except SyntaxError as e:
    raise QuestionError(f"Invalid format in question file: {e}")
except Exception as e:
    raise QuestionError(f"Error loading questions: {e}")
```

### 3. Configuration Management

**Before (Notebook):**
```python
# Hardcoded paths
file = open(r"/content/qpmaker.txt", "r")
pdfmetrics.registerFont(TTFont("Mainfont", r"/content/Amatic-Bold.ttf"))
```

**After (Python Module):**
```python
# Configurable paths
filepath = input("Enter path to question file: ")
questions = self.question_manager.load_questions_from_file(filepath)

# Optional font with fallback
if not os.path.exists(font_path):
    logger.warning(f"Font file not found, using default font")
```

### 4. Code Reusability

**Before (Notebook):**
- Duplicated code for different question types
- Cannot be imported or reused
- Must run entire notebook

**After (Python Module):**
- Can be used interactively or programmatically
- Reusable classes and methods
- Can be imported: `from quespm import QuestionPaperMaker`

### 5. Input Validation

**Before (Notebook):**
```python
z = int(input("Enter number of LATQs:"))  # No validation
```

**After (Python Module):**
```python
try:
    self.config['marks'] = int(marks) if marks else 100
except ValueError:
    print("Invalid marks, using default: 100")
    self.config['marks'] = 100
```

### 6. Logging and Debugging

**Before (Notebook):**
```python
print("Done ;)")  # Basic print statements
```

**After (Python Module):**
```python
import logging
logger = logging.getLogger(__name__)
logger.info(f"Loaded {len(questions)} questions from {filepath}")
```

## Usage Comparison

### Running the Old Notebook

1. Open Jupyter Notebook
2. Run all cells
3. Follow prompts
4. Hardcoded paths for files

### Running the New Module

**Interactive Mode:**
```bash
python3 quespm.py
```

**Programmatic Mode:**
```python
from quespm import QuestionPaperMaker

maker = QuestionPaperMaker()
maker.config = {...}
maker.question_manager.add_short_answer_questions([...])
maker.generate_pdf()
```

## Class Structure

```
quespm.py
├── Custom Exceptions
│   ├── ConfigurationError
│   ├── QuestionError
│   └── PDFGenerationError
│
├── QuestionManager
│   ├── load_questions_from_file()
│   ├── select_random_questions()
│   ├── add_short_answer_questions()
│   ├── add_long_answer_questions()
│   └── get_all_questions()
│
├── PDFGenerator
│   ├── initialize_canvas()
│   ├── register_font()
│   ├── draw_header()
│   ├── draw_questions()
│   └── save()
│
└── QuestionPaperMaker (Main orchestrator)
    ├── get_user_input()
    ├── get_question_input()
    ├── generate_pdf()
    └── run()
```

## Benefits of the New Implementation

1. **Maintainability**: Clear separation of concerns, easier to modify
2. **Testability**: Can unit test individual methods and classes
3. **Reliability**: Comprehensive error handling prevents crashes
4. **Flexibility**: Can be used as a library or standalone tool
5. **Portability**: No hardcoded paths, works on any system
6. **Documentation**: Docstrings and type hints for better understanding
7. **Logging**: Better debugging with proper logging
8. **Best Practices**: Follows Python conventions and PEP 8

## Migration Steps

If you were using the old notebook:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Convert your question files to the new format (Python lists)

3. Use the new module:
   ```bash
   python3 quespm.py
   ```

4. Or integrate it into your code:
   ```python
   from quespm import QuestionPaperMaker
   ```

## Backward Compatibility

The old notebook files are preserved in the repository for reference:
- `QuesPM.ipynb`
- `QuesPMupdate.ipynb`
- `Copy_of_QuesPMupdate.ipynb`

However, the new `quespm.py` is the recommended version going forward.
