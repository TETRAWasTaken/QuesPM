# QuesPM - Question Paper Maker

A Python-based tool to generate customizable question papers in PDF format with support for Multiple Choice Questions (MCQ), Objective Questions, and Subjective Questions with ruled writing spaces.

## Features

- **Multiple Question Types**:
  - **MCQ (Multiple Choice Questions)**: 4 options (A, B, C, D) formatted dynamically in balanced 2-column or 1-column layouts.
  - **Reasoned MCQ (Reasoning Multiple Choice Questions)**: 4 options (A, B, C, D) plus a designated writing space underneath with a "Reason:" prompt for students to justify their choice.
  - **Objective / One-Word Questions**: Brief questions with clean answer lines (`Ans: ________`).
  - **Subjective Questions**: Short and long answer questions with dedicated light-gray ruled writing lines or blank response spaces.
- **Section-Based Organization**: Groups questions into dynamically numbered sections (Section A: Multiple Choice Questions (MCQ), Section B: Reasoned Multiple Choice Questions (Reasoned MCQ), Section C: Objective Questions, Section D: Short Answer Questions, Section E: Long Answer Questions).
- **Marks System**: Every question displays its allocated marks on the right margin (e.g. `[1 Mark]`, `[5 Marks]`), and total marks are tallied for each section and synchronized with the paper's maximum marks.
- **CSV Question Bank Support**: Clean CSV templates for easy editing and bulk question loading.
- **CLI & Interactive Modes**: Run directly with command-line arguments via `argparse` or use the interactive terminal prompt.
- **Text Wrapping & Pagination**: Automatic text wrapping to prevent margin overflow and page-break checks for long questions and ruled answer spaces.
- **Backwards Compatible**: Works with legacy text files containing Python lists as well.

---

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Install Dependencies

```bash
pip install reportlab colorama
```

---

## Question Bank CSV Formats

QuesPM provides separate, dedicated CSV formats for each question type:

### 1. Multiple Choice Questions (`sample_mcq_questions.csv`)
Columns: `question,option_a,option_b,option_c,option_d,marks,correct_answer`

```csv
question,option_a,option_b,option_c,option_d,marks,correct_answer
"What is the output of print(type([])) in Python?","<class 'list'>","<class 'tuple'>","<class 'dict'>","<class 'set'>",1,A
"Which keyword is used to define a function in Python?","func","def","define","function",1,B
"Which data structure follows LIFO?","Queue","Stack","Array","Linked List",1,B
```

### 2. Reasoned Multiple Choice Questions (`sample_reasoned_mcq_questions.csv`)
Columns: `question,option_a,option_b,option_c,option_d,lines,marks,correct_answer`
- `lines`: Number of ruled writing lines for reason (default: 2)
- `marks`: Allocated marks (default: 2.0)

```csv
question,option_a,option_b,option_c,option_d,lines,marks,correct_answer
"Which data structure is most suitable for implementing a priority queue efficiently?","Array","Linked List","Binary Heap","Hash Table",2,2,C
"Why is QuickSort preferred over MergeSort for sorting in-place arrays in memory?","Lower auxiliary space O(1)","Better worst-case time complexity","Stable sorting property","Guaranteed linear time",2,2,A
```

### 3. Objective / One-Word Questions (`sample_objective_questions.csv`)
Columns: `question,marks,answer`

```csv
question,marks,answer
"What is the keyword used to create a class in Python?",1,"class"
"Which built-in Python function returns the number of items in an object?",1,"len"
"What data type is used to represent True or False values?",1,"bool"
```

### 3. Subjective Questions (`sample_subjective_questions.csv`)
Columns: `question,type,lines,marks`
- `type`: `short` or `long`
- `lines`: Number of ruled writing lines to generate (default: 4 for short, 8 for long)
- `marks`: Allocated marks (default: 3 for short, 5 for long)

```csv
question,type,lines,marks
"Define encapsulation and explain its importance in OOP.",short,4,3
"Explain the difference between mutable and immutable data types in Python.",short,4,3
"Discuss the four fundamental pillars of Object-Oriented Programming with examples.",long,8,5
"Explain the SOLID principles in software engineering with real-world examples.",long,10,5
```

---

## Usage

### 1. Command-Line Arguments (Non-Interactive)

Generate question papers directly by providing CLI arguments:

```bash
python3 quespm.py \
  --title "Computer Science Mid-Term" \
  --subtitle "Semester II Examination" \
  --subject "Computer Science" \
  --mcq-file sample_mcq_questions.csv \
  --num-mcq 4 \
  --objective-file sample_objective_questions.csv \
  --num-objective 3 \
  --subjective-file sample_subjective_questions.csv \
  --num-subjective 3 \
  --output exam_paper.pdf
```

#### Available CLI Arguments:
| Argument | Description | Default |
|---|---|---|
| `-t`, `--title` | Title of the examination paper | "Question Paper" |
| `--subtitle` | Subheading / Exam name | "Examination" |
| `-s`, `--subject` | Subject name | "General" |
| `-m`, `--marks` | Maximum marks | 100 (or synchronized to sum of questions) |
| `--time` | Time allotted in minutes | 180 |
| `--logo` | Path to logo image | None |
| `-o`, `--output` | Output PDF file path | `question_paper.pdf` |
| `--mcq-file` | Path to MCQ questions CSV | None |
| `--num-mcq` | Number of MCQ questions to pick | All in file |
| `--reasoned-mcq-file` | Path to Reasoned MCQ questions CSV | None |
| `--num-reasoned-mcq` | Number of Reasoned MCQ questions to pick | All in file |
| `--objective-file` | Path to Objective questions CSV | None |
| `--num-objective` | Number of Objective questions to pick | All in file |
| `--subjective-file` | Path to Subjective questions CSV | None |
| `--num-subjective` | Number of Subjective questions to pick | All in file |
| `--no-ruled-lines` | Disable ruled lines in writing spaces | False (ruled lines enabled) |
| `-i`, `--interactive` | Force interactive prompt mode | False |

---

### 2. Interactive Terminal Mode

Run without question bank arguments to launch the guided interactive wizard:

```bash
python3 quespm.py
```

Follow the prompts to:
1. Enter paper details (title, subtitle, subject, marks, time, logo)
2. Select sections to include (MCQ, Objective, Subjective, or All)
3. Provide CSV files or enter questions manually in the terminal
4. Specify question counts and review the total marks tally
5. Generate the PDF

---

### 3. Programmatic Usage

You can also use QuesPM as a Python module:

```python
from quespm import QuestionPaperMaker

maker = QuestionPaperMaker()
maker.config = {
    'filename': 'exam.pdf',
    'title': 'Final Exam',
    'subtitle': 'Semester 1',
    'subject': 'Computer Science',
    'time': 180,
    'marks': 50,
    'ruled_lines': True
}

qm = maker.question_manager

# Load from CSV banks
mcqs = qm.load_mcq_from_csv('sample_mcq_questions.csv')
qm.add_mcq_questions(qm.select_random_questions(mcqs, 4))

objs = qm.load_objective_from_csv('sample_objective_questions.csv')
qm.add_objective_questions(qm.select_random_questions(objs, 3))

subjs = qm.load_subjective_from_csv('sample_subjective_questions.csv')
qm.add_subjective_questions(qm.select_random_questions(subjs, 2))

# Sync marks and generate PDF
maker.config['marks'] = int(qm.calculate_total_marks())
maker.generate_pdf()
```

---

## Project Structure

- `quespm.py` - Core application containing models, QuestionManager, PDFGenerator, and CLI logic
- `sample_mcq_questions.csv` - Sample MCQ question bank with 4 options and marks
- `sample_objective_questions.csv` - Sample objective / one-word question bank
- `sample_subjective_questions.csv` - Sample subjective question bank with writing lines & marks
- `example_usage.py` - Programmatic usage script
- `test_quespm.py` - Comprehensive unit and integration test suite
- `sample_short_questions.txt` - Legacy short answer questions (for backward compatibility)
- `sample_long_questions.txt` - Legacy long answer questions (for backward compatibility)

---

## Testing

Run the comprehensive test suite:

```bash
python3 test_quespm.py
```

---

## License

This project is open source and available for educational purposes.
