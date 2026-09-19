#!/usr/bin/env python3
"""
Question Paper Maker (QuesPM)
A tool to generate question papers in PDF format with customizable settings.

Features:
- Object-oriented design
- Support for Multiple Choice Questions (MCQs) with 4 options
- Support for Objective / One-Word questions
- Support for Subjective questions with ruled writing spaces
- Question marks system with section and paper marks tallying
- CSV format question banks for each question type
- Section-based paper organization
- Command-line arguments via argparse & interactive CLI mode
- Text wrapping and robust pagination
"""

import os
import sys
import ast
import csv
import random
import logging
import argparse
from typing import List, Dict, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from pathlib import Path
import re

try:
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase import pdfmetrics
    from reportlab.lib import colors
except ImportError:
    print("Error: reportlab is not installed. Please install it using: pip install reportlab")
    sys.exit(1)

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
except ImportError:
    print("Error: colorama is not installed. Please install it using: pip install colorama")
    sys.exit(1)


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass


class QuestionError(Exception):
    """Raised when there's an issue with questions."""
    pass


class PDFGenerationError(Exception):
    """Raised when PDF generation fails."""
    pass


# ---------------------------------------------------------------------------
# Question Data Models
# ---------------------------------------------------------------------------

@dataclass
class MCQQuestion:
    """Represents a multiple choice question with 4 options."""
    question: str
    options: List[str]  # 4 options [A, B, C, D]
    marks: float = 1.0
    correct_answer: Optional[str] = None

    def __post_init__(self):
        try:
            self.marks = float(self.marks)
        except (ValueError, TypeError):
            self.marks = 1.0
        # Ensure 4 options
        if len(self.options) < 4:
            while len(self.options) < 4:
                self.options.append(f"Option {chr(65 + len(self.options))}")


@dataclass
class ReasonedMCQQuestion:
    """Represents a Reasoning Multiple Choice Question with 4 options and a writing space for reason."""
    question: str
    options: List[str]  # 4 options [A, B, C, D]
    lines: int = 2      # Small writing space for reason (default: 2 lines)
    marks: float = 2.0  # Marks for question (default: 2.0)
    correct_answer: Optional[str] = None

    def __post_init__(self):
        try:
            self.marks = float(self.marks)
        except (ValueError, TypeError):
            self.marks = 2.0
        try:
            self.lines = int(self.lines)
        except (ValueError, TypeError):
            self.lines = 2
        # Ensure 4 options
        if len(self.options) < 4:
            while len(self.options) < 4:
                self.options.append(f"Option {chr(65 + len(self.options))}")


# Aliases for explicit and concise naming
MCQ = MCQQuestion
ReasonedMCQ = ReasonedMCQQuestion


@dataclass
class ObjectiveQuestion:
    """Represents a basic one-word / short objective question."""
    question: str
    marks: float = 1.0
    answer: Optional[str] = None

    def __post_init__(self):
        try:
            self.marks = float(self.marks)
        except (ValueError, TypeError):
            self.marks = 1.0


@dataclass
class SubjectiveQuestion:
    """Represents a subjective question with designated writing space."""
    question: str
    subtype: str = "short"  # "short" or "long"
    lines: int = 4          # Number of writing lines to render
    marks: float = 3.0
    answer: Optional[str] = None

    def __post_init__(self):
        try:
            self.marks = float(self.marks)
        except (ValueError, TypeError):
            self.marks = 3.0 if self.subtype == "short" else 5.0
        try:
            self.lines = int(self.lines)
        except (ValueError, TypeError):
            self.lines = 4 if self.subtype == "short" else 8


# ---------------------------------------------------------------------------
# Question Manager
# ---------------------------------------------------------------------------

class QuestionManager:
    """Manages question loading, selection, and organization across types."""

    def __init__(self):
        """Initialize the QuestionManager."""
        self.mcq_questions: List[MCQQuestion] = []
        self.reasoned_mcq_questions: List[ReasonedMCQQuestion] = []
        self.objective_questions: List[ObjectiveQuestion] = []
        self.subjective_questions: List[SubjectiveQuestion] = []

    # Backwards compatibility properties
    @property
    def short_answer_questions(self) -> List[str]:
        return [q.question for q in self.subjective_questions if q.subtype == "short"]

    @property
    def long_answer_questions(self) -> List[str]:
        return [q.question for q in self.subjective_questions if q.subtype == "long"]

    # ---------------- CSV Loaders ----------------

    def load_mcq_from_csv(self, filepath: str) -> List[MCQQuestion]:
        """
        Load MCQ questions from a CSV file.
        Expected columns: question, option_a, option_b, option_c, option_d, [marks, correct_answer]
        """
        if not os.path.exists(filepath):
            raise QuestionError(f"MCQ question file not found: {filepath}")

        questions: List[MCQQuestion] = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise QuestionError(f"Empty or invalid CSV file: {filepath}")

                for row in reader:
                    cleaned = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    q_text = cleaned.get('question') or cleaned.get('q') or cleaned.get('text')
                    if not q_text:
                        continue

                    opt_a = cleaned.get('option_a') or cleaned.get('option1') or cleaned.get('a') or cleaned.get('opt_a') or ''
                    opt_b = cleaned.get('option_b') or cleaned.get('option2') or cleaned.get('b') or cleaned.get('opt_b') or ''
                    opt_c = cleaned.get('option_c') or cleaned.get('option3') or cleaned.get('c') or cleaned.get('opt_c') or ''
                    opt_d = cleaned.get('option_d') or cleaned.get('option4') or cleaned.get('d') or cleaned.get('opt_d') or ''
                    options = [opt_a, opt_b, opt_c, opt_d]

                    raw_marks = cleaned.get('marks') or cleaned.get('mark') or cleaned.get('score') or '1'
                    try:
                        marks = float(raw_marks)
                    except ValueError:
                        marks = 1.0

                    correct = cleaned.get('correct_answer') or cleaned.get('answer') or cleaned.get('correct')

                    questions.append(MCQQuestion(
                        question=q_text,
                        options=options,
                        marks=marks,
                        correct_answer=correct
                    ))

            logger.info(f"Loaded {len(questions)} MCQ questions from {filepath}")
            return questions

        except Exception as e:
            if isinstance(e, QuestionError):
                raise
            raise QuestionError(f"Error loading MCQ questions from {filepath}: {e}")

    def load_reasoned_mcq_from_csv(self, filepath: str) -> List[ReasonedMCQQuestion]:
        """
        Load Reasoned MCQ questions from a CSV file.
        Expected columns: question, option_a, option_b, option_c, option_d, [lines, marks, correct_answer]
        """
        if not os.path.exists(filepath):
            raise QuestionError(f"Reasoned MCQ question file not found: {filepath}")

        questions: List[ReasonedMCQQuestion] = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise QuestionError(f"Empty or invalid CSV file: {filepath}")

                for row in reader:
                    cleaned = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    q_text = cleaned.get('question') or cleaned.get('q') or cleaned.get('text')
                    if not q_text:
                        continue

                    opt_a = cleaned.get('option_a') or cleaned.get('option1') or cleaned.get('a') or cleaned.get('opt_a') or ''
                    opt_b = cleaned.get('option_b') or cleaned.get('option2') or cleaned.get('b') or cleaned.get('opt_b') or ''
                    opt_c = cleaned.get('option_c') or cleaned.get('option3') or cleaned.get('c') or cleaned.get('opt_c') or ''
                    opt_d = cleaned.get('option_d') or cleaned.get('option4') or cleaned.get('d') or cleaned.get('opt_d') or ''
                    options = [opt_a, opt_b, opt_c, opt_d]

                    raw_lines = cleaned.get('lines') or cleaned.get('writing_space') or cleaned.get('space') or '2'
                    try:
                        lines = int(raw_lines)
                    except ValueError:
                        lines = 2

                    raw_marks = cleaned.get('marks') or cleaned.get('mark') or cleaned.get('score') or '2'
                    try:
                        marks = float(raw_marks)
                    except ValueError:
                        marks = 2.0

                    correct = cleaned.get('correct_answer') or cleaned.get('answer') or cleaned.get('correct')

                    questions.append(ReasonedMCQQuestion(
                        question=q_text,
                        options=options,
                        lines=lines,
                        marks=marks,
                        correct_answer=correct
                    ))

            logger.info(f"Loaded {len(questions)} Reasoned MCQ questions from {filepath}")
            return questions

        except Exception as e:
            if isinstance(e, QuestionError):
                raise
            raise QuestionError(f"Error loading Reasoned MCQ questions from {filepath}: {e}")

    def load_objective_from_csv(self, filepath: str) -> List[ObjectiveQuestion]:
        """
        Load Objective / One-word questions from a CSV file.
        Expected columns: question, [marks, answer]
        """
        if not os.path.exists(filepath):
            raise QuestionError(f"Objective question file not found: {filepath}")

        questions: List[ObjectiveQuestion] = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise QuestionError(f"Empty or invalid CSV file: {filepath}")

                for row in reader:
                    cleaned = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    q_text = cleaned.get('question') or cleaned.get('q') or cleaned.get('text')
                    if not q_text:
                        continue

                    raw_marks = cleaned.get('marks') or cleaned.get('mark') or cleaned.get('score') or '1'
                    try:
                        marks = float(raw_marks)
                    except ValueError:
                        marks = 1.0

                    answer = cleaned.get('answer') or cleaned.get('ans')

                    questions.append(ObjectiveQuestion(
                        question=q_text,
                        marks=marks,
                        answer=answer
                    ))

            logger.info(f"Loaded {len(questions)} objective questions from {filepath}")
            return questions

        except Exception as e:
            if isinstance(e, QuestionError):
                raise
            raise QuestionError(f"Error loading objective questions from {filepath}: {e}")

    def load_subjective_from_csv(self, filepath: str) -> List[SubjectiveQuestion]:
        """
        Load Subjective questions from a CSV file.
        Expected columns: question, [type, lines, marks, answer]
        """
        if not os.path.exists(filepath):
            raise QuestionError(f"Subjective question file not found: {filepath}")

        questions: List[SubjectiveQuestion] = []
        try:
            with open(filepath, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise QuestionError(f"Empty or invalid CSV file: {filepath}")

                for row in reader:
                    cleaned = {k.strip().lower(): v.strip() for k, v in row.items() if k}
                    q_text = cleaned.get('question') or cleaned.get('q') or cleaned.get('text')
                    if not q_text:
                        continue

                    subtype = cleaned.get('type') or cleaned.get('subtype') or 'short'
                    subtype = subtype.lower().strip()
                    if subtype not in ['short', 'long']:
                        subtype = 'short'

                    default_lines = 4 if subtype == 'short' else 8
                    raw_lines = cleaned.get('lines') or cleaned.get('writing_space') or cleaned.get('space')
                    try:
                        lines = int(raw_lines) if raw_lines else default_lines
                    except ValueError:
                        lines = default_lines

                    default_marks = 3.0 if subtype == 'short' else 5.0
                    raw_marks = cleaned.get('marks') or cleaned.get('mark') or cleaned.get('score')
                    try:
                        marks = float(raw_marks) if raw_marks else default_marks
                    except ValueError:
                        marks = default_marks

                    answer = cleaned.get('answer') or cleaned.get('ans')

                    questions.append(SubjectiveQuestion(
                        question=q_text,
                        subtype=subtype,
                        lines=lines,
                        marks=marks,
                        answer=answer
                    ))

            logger.info(f"Loaded {len(questions)} subjective questions from {filepath}")
            return questions

        except Exception as e:
            if isinstance(e, QuestionError):
                raise
            raise QuestionError(f"Error loading subjective questions from {filepath}: {e}")

    def load_questions_from_file(self, filepath: str) -> List[str]:
        """
        Load questions from a legacy text file (Python literal list) or CSV.
        Maintains backwards compatibility.
        """
        try:
            if not os.path.exists(filepath):
                raise QuestionError(f"Question file not found: {filepath}")

            if filepath.lower().endswith('.csv'):
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    first_line = f.readline().lower()
                    if 'option' in first_line:
                        mcqs = self.load_mcq_from_csv(filepath)
                        return [q.question for q in mcqs]
                    elif 'type' in first_line or 'lines' in first_line:
                        subjs = self.load_subjective_from_csv(filepath)
                        return [q.question for q in subjs]
                    else:
                        objs = self.load_objective_from_csv(filepath)
                        return [q.question for q in objs]

            with open(filepath, 'r', encoding='utf-8') as file:
                contents = file.read()
                questions = ast.literal_eval(contents)

            if not isinstance(questions, list):
                raise QuestionError("Question file must contain a list")

            logger.info(f"Loaded {len(questions)} questions from {filepath}")
            return questions

        except SyntaxError as e:
            raise QuestionError(f"Invalid format in question file: {e}")
        except Exception as e:
            if isinstance(e, QuestionError):
                raise
            raise QuestionError(f"Error loading questions: {e}")

    def select_random_questions(self, questions: List[Any], count: int) -> List[Any]:
        """
        Select random unique questions from a list.
        """
        if count > len(questions):
            raise QuestionError(
                f"Cannot select {count} questions from {len(questions)} available questions"
            )

        if count < 0:
            raise QuestionError("Question count must be non-negative")

        selected = []
        available = questions.copy()

        while len(selected) < count:
            question = random.choice(available)
            available.remove(question)
            selected.append(question)

        return selected

    # ---------------- Adders ----------------

    def add_mcq_questions(self, questions: List[MCQQuestion]):
        """Add MCQ questions."""
        self.mcq_questions.extend(questions)

    def add_reasoned_mcq_questions(self, questions: List[ReasonedMCQQuestion]):
        """Add Reasoned MCQ questions."""
        self.reasoned_mcq_questions.extend(questions)

    def add_objective_questions(self, questions: List[ObjectiveQuestion]):
        """Add Objective / One-Word questions."""
        self.objective_questions.extend(questions)

    def add_subjective_questions(self, questions: List[SubjectiveQuestion]):
        """Add Subjective questions."""
        self.subjective_questions.extend(questions)

    def add_short_answer_questions(self, questions: List[Union[str, SubjectiveQuestion]]):
        """Add short answer subjective questions (backward compatible)."""
        for q in questions:
            if isinstance(q, SubjectiveQuestion):
                self.subjective_questions.append(q)
            else:
                self.subjective_questions.append(
                    SubjectiveQuestion(question=str(q), subtype="short", lines=4, marks=3.0)
                )

    def add_long_answer_questions(self, questions: List[Union[str, SubjectiveQuestion]]):
        """Add long answer subjective questions (backward compatible)."""
        for q in questions:
            if isinstance(q, SubjectiveQuestion):
                self.subjective_questions.append(q)
            else:
                self.subjective_questions.append(
                    SubjectiveQuestion(question=str(q), subtype="long", lines=8, marks=5.0)
                )

    # ---------------- Aggregations ----------------

    def calculate_total_marks(self) -> float:
        """Calculate the sum of marks of all currently added questions."""
        total = 0.0
        for q in self.mcq_questions:
            total += q.marks
        for q in self.reasoned_mcq_questions:
            total += q.marks
        for q in self.objective_questions:
            total += q.marks
        for q in self.subjective_questions:
            total += q.marks
        return total

    def get_sections(self, separate: bool = True) -> List[Tuple[str, List[Any]]]:
        """
        Return structured sections dynamically ordered and labeled with letter and marks.
        If separate is False, returns all questions together in a single continuous section.
        """
        if not separate:
            all_qs: List[Any] = []
            all_qs.extend(self.mcq_questions)
            all_qs.extend(self.reasoned_mcq_questions)
            all_qs.extend(self.objective_questions)
            all_qs.extend(self.subjective_questions)
            return [("QUESTIONS", all_qs)] if all_qs else []

        sections: List[Tuple[str, List[Any]]] = []
        section_idx = 0
        letters = ["A", "B", "C", "D", "E", "F", "G"]

        if self.mcq_questions:
            letter = letters[section_idx]
            section_idx += 1
            sec_marks = sum(q.marks for q in self.mcq_questions)
            marks_str = f"{int(sec_marks)} Marks" if sec_marks.is_integer() else f"{sec_marks:.1f} Marks"
            sections.append((f"SECTION {letter}: MULTIPLE CHOICE QUESTIONS (MCQ) ({marks_str})", self.mcq_questions))

        if self.reasoned_mcq_questions:
            letter = letters[section_idx]
            section_idx += 1
            sec_marks = sum(q.marks for q in self.reasoned_mcq_questions)
            marks_str = f"{int(sec_marks)} Marks" if sec_marks.is_integer() else f"{sec_marks:.1f} Marks"
            sections.append((f"SECTION {letter}: REASONED MULTIPLE CHOICE QUESTIONS (REASONED MCQ) ({marks_str})", self.reasoned_mcq_questions))

        if self.objective_questions:
            letter = letters[section_idx]
            section_idx += 1
            sec_marks = sum(q.marks for q in self.objective_questions)
            marks_str = f"{int(sec_marks)} Marks" if sec_marks.is_integer() else f"{sec_marks:.1f} Marks"
            sections.append((f"SECTION {letter}: OBJECTIVE QUESTIONS ({marks_str})", self.objective_questions))

        short_subjs = [q for q in self.subjective_questions if q.subtype == "short"]
        long_subjs = [q for q in self.subjective_questions if q.subtype == "long"]

        if short_subjs and long_subjs:
            letter = letters[section_idx]
            section_idx += 1
            sec_marks = sum(q.marks for q in short_subjs)
            marks_str = f"{int(sec_marks)} Marks" if sec_marks.is_integer() else f"{sec_marks:.1f} Marks"
            sections.append((f"SECTION {letter}: SHORT ANSWER QUESTIONS ({marks_str})", short_subjs))

            letter = letters[section_idx]
            section_idx += 1
            sec_marks = sum(q.marks for q in long_subjs)
            marks_str = f"{int(sec_marks)} Marks" if sec_marks.is_integer() else f"{sec_marks:.1f} Marks"
            sections.append((f"SECTION {letter}: LONG ANSWER QUESTIONS ({marks_str})", long_subjs))
        elif self.subjective_questions:
            letter = letters[section_idx]
            section_idx += 1
            sec_marks = sum(q.marks for q in self.subjective_questions)
            marks_str = f"{int(sec_marks)} Marks" if sec_marks.is_integer() else f"{sec_marks:.1f} Marks"
            sections.append((f"SECTION {letter}: SUBJECTIVE QUESTIONS ({marks_str})", self.subjective_questions))

        return sections

    def get_all_questions(self) -> Dict[str, List[Any]]:
        """Get all questions organized by type/section (backwards compatible)."""
        res: Dict[str, List[Any]] = {}
        if self.mcq_questions:
            res["Multiple Choice Questions"] = self.mcq_questions
            res["MCQ"] = self.mcq_questions
        if self.reasoned_mcq_questions:
            res["Reasoned Multiple Choice Questions"] = self.reasoned_mcq_questions
            res["Reasoned MCQ"] = self.reasoned_mcq_questions
        if self.objective_questions:
            res["Objective Questions"] = self.objective_questions

        short_subjs = [q for q in self.subjective_questions if q.subtype == "short"]
        long_subjs = [q for q in self.subjective_questions if q.subtype == "long"]

        if short_subjs:
            res["Short answer type"] = short_subjs
        if long_subjs:
            res["Long answer type"] = long_subjs

        return res


# ---------------------------------------------------------------------------
# PDF Generator
# ---------------------------------------------------------------------------

class PDFGenerator:
    """Handles PDF generation for question papers with sections, marks, and spaces."""

    def __init__(self, config: Dict):
        """
        Initialize the PDF generator.

        Args:
            config: Configuration dictionary containing PDF settings
        """
        self.config = config
        self.canvas: Optional[Canvas] = None
        self.current_y: float = 650.0
        self.left_margin: float = 40.0
        self.right_margin: float = 555.0
        self.bottom_limit: float = 50.0
        self.top_margin: float = 790.0
        self.ruled_lines: bool = config.get('ruled_lines', True)
        self.separate_sections: bool = config.get('separate_sections', config.get('sections', True))

    def initialize_canvas(self, filename: str):
        """Initialize the PDF canvas."""
        try:
            self.canvas = Canvas(filename, pagesize=A4)
            logger.info(f"Initialized PDF canvas for {filename}")
        except Exception as e:
            raise PDFGenerationError(f"Failed to initialize canvas: {e}")

    def register_font(self, font_name: str, font_path: str):
        """Register a custom font."""
        try:
            if not os.path.exists(font_path):
                logger.warning(f"Font file not found: {font_path}, using default font")
                return

            pdfmetrics.registerFont(TTFont(font_name, font_path))
            logger.info(f"Registered font: {font_name}")
        except Exception as e:
            logger.warning(f"Failed to register font: {e}, using default font")

    def draw_header(self):
        """Draw the PDF header with title, logo, time, marks, and metadata."""
        try:
            title = str(self.config.get('title', 'Question Paper')).upper()
            subtitle = str(self.config.get('subtitle', 'Examination')).upper()
            logo_path = self.config.get('logo_path')

            # Logo (if provided) - determine aspect ratio and positioning
            has_wide_logo = False
            if logo_path and os.path.exists(logo_path):
                try:
                    from PIL import Image
                    with Image.open(logo_path) as img:
                        orig_w, orig_h = img.size
                    aspect = orig_w / max(1, orig_h)
                    
                    if aspect >= 2.0:
                        # Wide horizontal banner logo: center cleanly at top above title
                        has_wide_logo = True
                        logo_w = min(180.0, 22.0 * aspect)
                        logo_h = logo_w / aspect
                        logo_x = 297.5 - (logo_w / 2.0)
                        logo_y = 788.0
                        self.canvas.drawImage(logo_path, logo_x, logo_y, width=logo_w, height=logo_h, mask='auto', preserveAspectRatio=True)
                    else:
                        # Standard / square logo: place in top-right corner with preserved aspect ratio
                        max_w, max_h = 65.0, 65.0
                        if aspect >= max_w / max_h:
                            w = max_w
                            h = max_w / aspect
                        else:
                            h = max_h
                            w = max_h * aspect
                        logo_x = self.right_margin - w
                        logo_y = 745.0 + (max_h - h) / 2.0
                        self.canvas.drawImage(logo_path, logo_x, logo_y, width=w, height=h, mask='auto', preserveAspectRatio=True)
                except Exception as e:
                    logger.warning(f"Failed to add logo with PIL/drawImage: {e}")
                    try:
                        self.canvas.drawInlineImage(logo_path, 490, 745, 65, 65, showBoundary=False)
                    except Exception as err:
                        logger.warning(f"Fallback logo drawing failed: {err}")

            # Title & Subtitle positioning
            title_y = 762.0 if has_wide_logo else 780.0
            subtitle_y = 742.0 if has_wide_logo else 755.0

            # Auto-scale title font size to prevent overflow
            title_font_size = 18 if has_wide_logo else 22
            max_title_w = self.right_margin - self.left_margin - (20 if has_wide_logo else (85 if logo_path else 20))
            while title_font_size > 11 and pdfmetrics.stringWidth(title, 'Helvetica-Bold', title_font_size) > max_title_w:
                title_font_size -= 1

            self.canvas.setFont('Helvetica-Bold', title_font_size)
            self.canvas.setFillColor(colors.black)
            self.canvas.drawCentredString(297.5, title_y, title)

            # Subtitle
            self.canvas.setFont("Helvetica-Bold", 13 if has_wide_logo else 14)
            self.canvas.drawCentredString(297.5, subtitle_y, subtitle)

            # Subject
            subject_str = f"Subject: {self.config.get('subject', 'General')}"
            self.canvas.setFont("Helvetica", 11)
            self.canvas.drawString(self.left_margin, 725, subject_str)

            # Time and marks
            time_val = self.config.get('time', 'N/A')
            marks_val = self.config.get('marks', 'N/A')
            time_str = f"Time Allowed: {time_val} mins"
            marks_str = f"Maximum Marks: {marks_val}"

            self.canvas.drawRightString(self.right_margin, 725, marks_str)
            self.canvas.drawString(self.left_margin, 708, time_str)

            # Line separator
            self.canvas.setStrokeColor(colors.black)
            self.canvas.setLineWidth(1.2)
            self.canvas.line(self.left_margin, 698, self.right_margin, 698)

            self.current_y = 675.0
            logger.info("Header drawn successfully")
        except Exception as e:
            raise PDFGenerationError(f"Failed to draw header: {e}")

    def draw_guidelines(self, guidelines_input: Optional[Union[str, List[str]]] = None):
        """
        Draw candidate guidelines/instructions section on the PDF canvas below the header.
        Can receive guidelines as a file path, string, or list of strings, or read from config.
        """
        try:
            content = guidelines_input
            if content is None:
                content = self.config.get('guidelines')
            if content is None and self.config.get('guidelines_file'):
                g_file = self.config.get('guidelines_file')
                if os.path.exists(g_file):
                    with open(g_file, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                else:
                    logger.warning(f"Guidelines file not found: {g_file}")
                    return

            if not content:
                return

            # If content is a filepath that exists, read it
            if isinstance(content, str) and os.path.exists(content) and "\n" not in content:
                try:
                    with open(content, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()
                except Exception as e:
                    logger.warning(f"Error reading guidelines from {content}: {e}")

            if isinstance(content, list):
                raw_lines = [str(l).rstrip() for l in content if str(l).strip()]
            elif isinstance(content, str):
                raw_lines = [l.rstrip() for l in content.strip().splitlines() if l.strip()]
            else:
                return

            if not raw_lines:
                return

            # Check if first line is a section heading
            first_line = raw_lines[0].strip()
            is_heading = False
            lower_first = first_line.lower()
            if any(k in lower_first for k in ["guideline", "instruction", "note", "direction"]):
                is_heading = True
            elif not any(first_line.startswith(p) for p in ["-", "*", "•", "●", "○", "1.", "1)", "(1)"]):
                is_heading = True

            if is_heading:
                heading_text = first_line.rstrip(":") + ":"
                item_lines = raw_lines[1:]
            else:
                heading_text = "TEST GUIDELINES:"
                item_lines = raw_lines

            self._check_page_break(needed_space=40.0)

            # Draw Heading
            self.canvas.setFont("Helvetica-Bold", 10.5)
            self.canvas.setFillColor(colors.HexColor("#1A1A1A"))
            self.canvas.drawString(self.left_margin, self.current_y, heading_text)
            self.current_y -= 15

            self.canvas.setFont("Helvetica", 9.5)
            self.canvas.setFillColor(colors.HexColor("#333333"))

            font_name = "Helvetica"
            font_size = 9.5
            line_height = 13.0

            for raw in item_lines:
                self._check_page_break(needed_space=18.0)
                l_stripped = raw.strip()
                leading_spaces = len(raw) - len(raw.lstrip())

                is_subitem = (
                    leading_spaces >= 3 or
                    l_stripped.startswith("○") or
                    l_stripped.startswith("- ") or
                    l_stripped.startswith("* ") or
                    bool(re.match(r"^[a-zA-Z]\b[\.\)]", l_stripped))
                )

                base_indent = 24.0 if is_subitem else 12.0
                bullet_marker = "–  " if is_subitem else "•  "

                # Strip bullet characters
                clean_text = re.sub(r"^[\s\-\*•●○]+", "", l_stripped)
                num_match = re.match(r"^(\d+[\.\)])\s*(.*)", clean_text)
                alpha_match = re.match(r"^([a-zA-Z][\.\)])\s*(.*)", clean_text)
                if num_match:
                    bullet_marker = f"{num_match.group(1)}  "
                    clean_text = num_match.group(2)
                elif alpha_match and is_subitem:
                    bullet_marker = f"{alpha_match.group(1)}  "
                    clean_text = alpha_match.group(2)

                bullet_w = pdfmetrics.stringWidth(bullet_marker, font_name, font_size)
                text_x = self.left_margin + base_indent + bullet_w
                max_text_w = self.right_margin - text_x

                # Wrap text
                words = clean_text.split()
                wrapped_lines = []
                cur_words = []
                for w in words:
                    test_line = " ".join(cur_words + [w])
                    if pdfmetrics.stringWidth(test_line, font_name, font_size) <= max_text_w:
                        cur_words.append(w)
                    else:
                        if cur_words:
                            wrapped_lines.append(" ".join(cur_words))
                            cur_words = [w]
                        else:
                            wrapped_lines.append(w)
                if cur_words:
                    wrapped_lines.append(" ".join(cur_words))

                if not wrapped_lines:
                    wrapped_lines = [""]

                # First line with marker
                self.canvas.drawString(self.left_margin + base_indent, self.current_y, bullet_marker)
                self.canvas.drawString(text_x, self.current_y, wrapped_lines[0])
                self.current_y -= line_height

                # Subsequent continuation lines
                for sub_line in wrapped_lines[1:]:
                    self._check_page_break(needed_space=14.0)
                    self.canvas.drawString(text_x, self.current_y, sub_line)
                    self.current_y -= line_height

            # Subtle horizontal divider below guidelines
            self.current_y -= 4
            self.canvas.setStrokeColor(colors.HexColor("#D0D0D0"))
            self.canvas.setLineWidth(0.6)
            self.canvas.line(self.left_margin, self.current_y, self.right_margin, self.current_y)
            self.current_y -= 16

            # Reset canvas styles
            self.canvas.setFillColor(colors.black)
            self.canvas.setStrokeColor(colors.black)
            logger.info("Guidelines drawn successfully")
        except Exception as e:
            logger.warning(f"Error drawing guidelines: {e}")

    def _format_marks(self, marks: float) -> str:
        """Format marks string, e.g., '[1 Mark]' or '[3 Marks]'."""
        if marks.is_integer():
            m_val = int(marks)
        else:
            m_val = marks
        return f"[{m_val} Mark]" if m_val == 1 else f"[{m_val} Marks]"

    def _wrap_question_text(self, text: str, font_name: str, font_size: float,
                            first_max_w: float, sub_max_w: float) -> List[str]:
        """Wrap question text: first line fits first_max_w, subsequent fit sub_max_w."""
        words = text.split()
        if not words:
            return [""]

        lines = []
        current_words = []
        max_w = first_max_w

        for word in words:
            test_line = " ".join(current_words + [word])
            width = pdfmetrics.stringWidth(test_line, font_name, font_size)
            if width <= max_w:
                current_words.append(word)
            else:
                if current_words:
                    lines.append(" ".join(current_words))
                    current_words = [word]
                    max_w = sub_max_w
                else:
                    lines.append(word)
                    current_words = []
                    max_w = sub_max_w

        if current_words:
            lines.append(" ".join(current_words))

        return lines

    def _wrap_text(self, text: str, font_name: str, font_size: float, max_width: float) -> List[str]:
        """Wrap text to fit within max_width using font metrics."""
        words = text.split()
        if not words:
            return [""]

        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            width = pdfmetrics.stringWidth(test_line, font_name, font_size)
            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                else:
                    lines.append(word)
                    current_line = []

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _check_page_break(self, needed_space: float = 40.0):
        """Check if remaining space is below needed_space; if so, trigger new page."""
        if self.current_y - needed_space <= self.bottom_limit:
            self.canvas.showPage()
            self.current_y = self.top_margin

    def draw_questions(self, questions_input: Union[Dict[str, List[Any]], List[Tuple[str, List[Any]]]]):
        """
        Draw structured sections and questions on the PDF canvas.
        Handles MCQ 4 options, subjective writing space, objective questions, and marks.
        """
        if isinstance(questions_input, dict):
            raw_sections = list(questions_input.items())
        else:
            raw_sections = list(questions_input)

        global_q_idx = 1
        letters = ["A", "B", "C", "D", "E", "F"]

        for s_idx, (section_title, questions) in enumerate(raw_sections):
            if not questions:
                continue

            # Draw Section Header if section separation is enabled
            if self.separate_sections and section_title.strip():
                # Format section header nicely if not already prefixed with SECTION
                sec_upper = section_title.upper()
                if not sec_upper.startswith("SECTION"):
                    let = letters[s_idx] if s_idx < len(letters) else str(s_idx + 1)
                    # Calculate section marks if possible
                    try:
                        s_marks = sum(getattr(q, 'marks', 1.0) for q in questions)
                        m_label = f"{int(s_marks)} Marks" if float(s_marks).is_integer() else f"{s_marks:.1f} Marks"
                        display_header = f"SECTION {let}: {sec_upper} ({m_label})"
                    except Exception:
                        display_header = f"SECTION {let}: {sec_upper}"
                else:
                    display_header = sec_upper

                # Check space for section header
                self._check_page_break(needed_space=60.0)

                # Draw Section Header
                self.canvas.setFont("Helvetica-Bold", 13)
                self.canvas.setFillColor(colors.HexColor("#222222"))
                self.canvas.drawCentredString(297.5, self.current_y, display_header)
                self.current_y -= 8

                # Underline under section header
                header_width = min(pdfmetrics.stringWidth(display_header, "Helvetica-Bold", 13) + 20, 500)
                self.canvas.setStrokeColor(colors.HexColor("#666666"))
                self.canvas.setLineWidth(0.8)
                self.canvas.line(297.5 - header_width / 2, self.current_y, 297.5 + header_width / 2, self.current_y)
                self.current_y -= 22

                # Reset drawing colors
                self.canvas.setFillColor(colors.black)
                self.canvas.setStrokeColor(colors.black)
            elif s_idx > 0:
                # Add slight vertical spacing when transitioning between unseparated sections
                self.current_y -= 8

            # Draw Questions in this section
            for item in questions:
                if isinstance(item, ReasonedMCQQuestion):
                    self._draw_reasoned_mcq_question(global_q_idx, item)
                elif isinstance(item, MCQQuestion):
                    self._draw_mcq_question(global_q_idx, item)
                elif isinstance(item, ObjectiveQuestion):
                    self._draw_objective_question(global_q_idx, item)
                elif isinstance(item, SubjectiveQuestion):
                    self._draw_subjective_question(global_q_idx, item)
                elif isinstance(item, str):
                    # Legacy string format support
                    sec_lower = section_title.lower()
                    if "long" in sec_lower:
                        self._draw_subjective_question(global_q_idx, SubjectiveQuestion(question=item, subtype="long", lines=8, marks=5.0))
                    elif "short" in sec_lower:
                        self._draw_subjective_question(global_q_idx, SubjectiveQuestion(question=item, subtype="short", lines=4, marks=3.0))
                    else:
                        self._draw_objective_question(global_q_idx, ObjectiveQuestion(question=item, marks=1.0))
                else:
                    q_text = getattr(item, 'question', str(item))
                    marks = getattr(item, 'marks', 1.0)
                    self._draw_objective_question(global_q_idx, ObjectiveQuestion(question=q_text, marks=marks))

                global_q_idx += 1

        logger.info("Questions drawn successfully")

    def _draw_question_text_with_marks(self, q_idx: int, text: str, marks: float):
        """Draw the question text with wrapped lines and right-aligned marks."""
        marks_str = self._format_marks(marks)
        marks_font = "Helvetica-Bold"
        marks_font_size = 10
        marks_width = pdfmetrics.stringWidth(marks_str, marks_font, marks_font_size)

        prefix = f"Q. {q_idx}) "
        q_font = "Helvetica"
        q_font_size = 11
        prefix_width = pdfmetrics.stringWidth(prefix, "Helvetica-Bold", q_font_size)

        first_line_max_w = (self.right_margin - self.left_margin) - prefix_width - marks_width - 15
        subsequent_line_max_w = (self.right_margin - self.left_margin) - prefix_width

        wrapped_lines = self._wrap_question_text(text, q_font, q_font_size, first_line_max_w, subsequent_line_max_w)

        # Check page break before drawing question
        self._check_page_break(needed_space=40.0)

        # Draw Question Prefix
        self.canvas.setFont("Helvetica-Bold", q_font_size)
        self.canvas.setFillColor(colors.black)
        self.canvas.drawString(self.left_margin, self.current_y, prefix)

        # Draw First Line
        self.canvas.setFont(q_font, q_font_size)
        if wrapped_lines:
            self.canvas.drawString(self.left_margin + prefix_width, self.current_y, wrapped_lines[0])

        # Draw Marks on the right margin of the first line
        self.canvas.setFont(marks_font, marks_font_size)
        self.canvas.drawRightString(self.right_margin, self.current_y, marks_str)

        # Draw any additional wrapped lines
        for sub_line in wrapped_lines[1:]:
            self.current_y -= 16
            self._check_page_break(needed_space=20.0)
            self.canvas.setFont(q_font, q_font_size)
            self.canvas.drawString(self.left_margin + prefix_width, self.current_y, sub_line)

        self.current_y -= 18

    def _draw_mcq_question(self, q_idx: int, mcq: MCQQuestion):
        """Draw an MCQ question with 4 options (A, B, C, D)."""
        opt_labels = ["(A)", "(B)", "(C)", "(D)"]
        opts = mcq.options[:4]
        while len(opts) < 4:
            opts.append(f"Option {opt_labels[len(opts)][1]}")

        col_width = (self.right_margin - self.left_margin) / 2
        max_col_avail_w = col_width - 25

        fits_2col = all(
            pdfmetrics.stringWidth(f"{lbl} {opt}", "Helvetica", 10.5) <= max_col_avail_w
            for lbl, opt in zip(opt_labels, opts)
        )
        opts_height = 42.0 if fits_2col else 72.0
        self._check_page_break(needed_space=45.0 + opts_height)

        self._draw_question_text_with_marks(q_idx, mcq.question, mcq.marks)

        self.canvas.setFont("Helvetica", 10.5)
        self.canvas.setFillColor(colors.black)

        if fits_2col:
            # 2-column layout: (A) and (B) on row 1, (C) and (D) on row 2
            col1_x = self.left_margin + 20
            col2_x = self.left_margin + col_width + 10

            self._check_page_break(needed_space=20.0)
            self.canvas.drawString(col1_x, self.current_y, f"(A) {opts[0]}")
            self.canvas.drawString(col2_x, self.current_y, f"(B) {opts[1]}")
            self.current_y -= 16

            self._check_page_break(needed_space=20.0)
            self.canvas.drawString(col1_x, self.current_y, f"(C) {opts[2]}")
            self.canvas.drawString(col2_x, self.current_y, f"(D) {opts[3]}")
            self.current_y -= 20
        else:
            # 1-column layout: stack all 4 options
            opt_x = self.left_margin + 20
            for idx, opt in enumerate(opts):
                self._check_page_break(needed_space=18.0)
                full_opt_text = f"{opt_labels[idx]} {opt}"
                wrapped = self._wrap_text(full_opt_text, "Helvetica", 10.5, (self.right_margin - opt_x))
                for w_line in wrapped:
                    self.canvas.drawString(opt_x, self.current_y, w_line)
                    self.current_y -= 14
                self.current_y -= 2
            self.current_y -= 8

    def _draw_reasoned_mcq_question(self, q_idx: int, r_mcq: ReasonedMCQQuestion):
        """Draw a Reasoned MCQ question with 4 options and a writing space for reason."""
        opt_labels = ["(A)", "(B)", "(C)", "(D)"]
        opts = r_mcq.options[:4]
        while len(opts) < 4:
            opts.append(f"Option {opt_labels[len(opts)][1]}")

        col_width = (self.right_margin - self.left_margin) / 2
        max_col_avail_w = col_width - 25

        fits_2col = all(
            pdfmetrics.stringWidth(f"{lbl} {opt}", "Helvetica", 10.5) <= max_col_avail_w
            for lbl, opt in zip(opt_labels, opts)
        )
        opts_height = 42.0 if fits_2col else 72.0
        reason_height = (max(1, r_mcq.lines) * 18.0) + 12.0
        self._check_page_break(needed_space=45.0 + opts_height + reason_height)

        self._draw_question_text_with_marks(q_idx, r_mcq.question, r_mcq.marks)

        opt_labels = ["(A)", "(B)", "(C)", "(D)"]
        opts = r_mcq.options[:4]
        while len(opts) < 4:
            opts.append(f"Option {opt_labels[len(opts)][1]}")

        col_width = (self.right_margin - self.left_margin) / 2
        max_col_avail_w = col_width - 25

        # Check if all options fit within 2-column layout width
        fits_2col = all(
            pdfmetrics.stringWidth(f"{lbl} {opt}", "Helvetica", 10.5) <= max_col_avail_w
            for lbl, opt in zip(opt_labels, opts)
        )

        self.canvas.setFont("Helvetica", 10.5)
        self.canvas.setFillColor(colors.black)

        if fits_2col:
            # 2-column layout: (A) and (B) on row 1, (C) and (D) on row 2
            col1_x = self.left_margin + 20
            col2_x = self.left_margin + col_width + 10

            # Row 1: A and B
            self._check_page_break(needed_space=20.0)
            self.canvas.drawString(col1_x, self.current_y, f"(A) {opts[0]}")
            self.canvas.drawString(col2_x, self.current_y, f"(B) {opts[1]}")
            self.current_y -= 16

            # Row 2: C and D
            self._check_page_break(needed_space=20.0)
            self.canvas.drawString(col1_x, self.current_y, f"(C) {opts[2]}")
            self.canvas.drawString(col2_x, self.current_y, f"(D) {opts[3]}")
            self.current_y -= 18
        else:
            # 1-column layout: stack all 4 options
            opt_x = self.left_margin + 20
            for idx, opt in enumerate(opts):
                self._check_page_break(needed_space=18.0)
                full_opt_text = f"{opt_labels[idx]} {opt}"
                wrapped = self._wrap_text(full_opt_text, "Helvetica", 10.5, (self.right_margin - opt_x))
                for w_line in wrapped:
                    self.canvas.drawString(opt_x, self.current_y, w_line)
                    self.current_y -= 14
                self.current_y -= 2
            self.current_y -= 6

        # Draw writing space for reasoning
        lines_to_draw = max(1, r_mcq.lines)
        line_spacing = 18.0

        # Draw "Reason:" prompt label
        self._check_page_break(needed_space=line_spacing + 5.0)
        self.canvas.setFont("Helvetica-BoldOblique", 9.5)
        self.canvas.setFillColor(colors.HexColor("#444444"))
        self.canvas.drawString(self.left_margin + 20, self.current_y, "Reason:")

        if self.ruled_lines:
            # First line starts next to the "Reason:" label
            self.canvas.setStrokeColor(colors.HexColor("#C0C0C0"))
            self.canvas.setLineWidth(0.6)
            self.canvas.line(self.left_margin + 68, self.current_y - 2, self.right_margin, self.current_y - 2)

            # Subsequent lines span full width from left margin
            for _ in range(lines_to_draw - 1):
                self.current_y -= line_spacing
                self._check_page_break(needed_space=line_spacing)
                self.canvas.setStrokeColor(colors.HexColor("#C0C0C0"))
                self.canvas.setLineWidth(0.6)
                self.canvas.line(self.left_margin + 20, self.current_y, self.right_margin, self.current_y)

            self.canvas.setStrokeColor(colors.black)
            self.canvas.setLineWidth(1.0)
            self.canvas.setFillColor(colors.black)
            self.current_y -= 14
        else:
            # Blank space reserved for reasoning
            for _ in range(lines_to_draw):
                self._check_page_break(needed_space=line_spacing)
                self.current_y -= line_spacing
            self.canvas.setFillColor(colors.black)
            self.current_y -= 8

    def _draw_objective_question(self, q_idx: int, obj_q: ObjectiveQuestion):
        """Draw an objective / one-word question with answer line."""
        self._draw_question_text_with_marks(q_idx, obj_q.question, obj_q.marks)

        # Draw answer blank
        self._check_page_break(needed_space=24.0)
        self.canvas.setFont("Helvetica-Oblique", 9.5)
        self.canvas.setFillColor(colors.HexColor("#555555"))
        self.canvas.drawString(self.left_margin + 20, self.current_y, "Ans:")
        self.canvas.setStrokeColor(colors.HexColor("#AAAAAA"))
        self.canvas.setLineWidth(0.7)
        self.canvas.line(self.left_margin + 50, self.current_y - 1, self.left_margin + 250, self.current_y - 1)
        self.canvas.setStrokeColor(colors.black)
        self.canvas.setFillColor(colors.black)
        self.current_y -= 22

    def _draw_subjective_question(self, q_idx: int, subj_q: SubjectiveQuestion):
        """Draw a subjective question with ruled writing spaces."""
        self._draw_question_text_with_marks(q_idx, subj_q.question, subj_q.marks)

        lines_to_draw = subj_q.lines
        line_spacing = 20.0

        if self.ruled_lines:
            for _ in range(lines_to_draw):
                self._check_page_break(needed_space=line_spacing)
                self.canvas.setStrokeColor(colors.HexColor("#D0D0D0"))
                self.canvas.setLineWidth(0.6)
                self.canvas.line(self.left_margin + 15, self.current_y, self.right_margin, self.current_y)
                self.current_y -= line_spacing
            self.canvas.setStrokeColor(colors.black)
            self.canvas.setLineWidth(1.0)
            self.current_y -= 10
        else:
            # Blank space
            for _ in range(lines_to_draw):
                self._check_page_break(needed_space=line_spacing)
                self.current_y -= line_spacing
            self.current_y -= 10

    def save(self):
        """Save the PDF file."""
        try:
            if self.canvas:
                self.canvas.save()
                logger.info("PDF saved successfully")
        except Exception as e:
            raise PDFGenerationError(f"Failed to save PDF: {e}")


# ---------------------------------------------------------------------------
# Argument Parser & CLI Orchestration
# ---------------------------------------------------------------------------

def build_argument_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser for QuesPM."""
    parser = argparse.ArgumentParser(
        description="QuesPM: Generate customized question paper PDFs with MCQs, Objective, and Subjective questions."
    )
    # Paper configuration
    parser.add_argument("-t", "--title", type=str, default=None, help="Title of the examination paper")
    parser.add_argument("--subtitle", type=str, default=None, help="Subtitle / sub-heading (e.g., End Semester Examination)")
    parser.add_argument("-s", "--subject", type=str, default=None, help="Subject name")
    parser.add_argument("-m", "--marks", type=int, default=None, help="Maximum marks for the paper")
    parser.add_argument("--time", type=int, default=None, help="Time allotted in minutes")
    parser.add_argument("--logo", type=str, default=None, help="Path to logo image file")
    parser.add_argument("-o", "--output", type=str, default=None, help="Output PDF file path")

    # Question bank CSVs and counts
    parser.add_argument("--mcq-file", type=str, default=None, help="Path to MCQ questions CSV file")
    parser.add_argument("--num-mcq", type=int, default=None, help="Number of MCQ questions to select")

    parser.add_argument("--reasoned-mcq-file", type=str, default=None, help="Path to Reasoned MCQ questions CSV file")
    parser.add_argument("--num-reasoned-mcq", type=int, default=None, help="Number of Reasoned MCQ questions to select")

    parser.add_argument("--objective-file", type=str, default=None, help="Path to Objective / One-Word questions CSV file")
    parser.add_argument("--num-objective", type=int, default=None, help="Number of Objective questions to select")

    parser.add_argument("--subjective-file", type=str, default=None, help="Path to Subjective questions CSV file")
    parser.add_argument("--num-subjective", type=int, default=None, help="Number of Subjective questions to select")

    # Options
    parser.add_argument("--no-ruled-lines", action="store_true", help="Disable ruled lines for subjective writing spaces")
    parser.add_argument("--no-sections", action="store_true", help="Disable section separation headers and render all questions continuously")
    parser.add_argument("--separate-sections", dest="separate_sections", action="store_true", default=None, help="Explicitly enable section separation headers (default: True)")
    parser.add_argument("--guidelines-file", "--guidelines", dest="guidelines_file", type=str, default=None,
                        help="Path to a plain text file (.txt) containing guidelines/instructions for candidates")
    parser.add_argument("-i", "--interactive", action="store_true", help="Force interactive prompt mode")

    return parser


class QuestionPaperMaker:
    """Main class for creating question papers via CLI args or interactive mode."""

    def __init__(self, cli_args: Optional[argparse.Namespace] = None):
        """Initialize QuestionPaperMaker with optional CLI arguments."""
        self.question_manager = QuestionManager()
        self.config: Dict[str, Any] = {}
        self.cli_args = cli_args

    def is_interactive(self) -> bool:
        """Determine if QuesPM should run in interactive prompt mode."""
        if not self.cli_args:
            return True
        if self.cli_args.interactive:
            return True
        # If any question files are provided via CLI, run non-interactively
        if (self.cli_args.mcq_file or
            self.cli_args.reasoned_mcq_file or
            self.cli_args.objective_file or
            self.cli_args.subjective_file):
            return False
        # If no arguments were given on CLI at all, default to interactive
        if len(sys.argv) <= 1:
            return True
        return False

    def get_user_input(self) -> bool:
        """Get configuration input interactively from user or from CLI args."""
        try:
            # If running in non-interactive CLI mode, configure directly without prompts
            if not self.is_interactive():
                filename = self.cli_args.output if (self.cli_args and self.cli_args.output) else "question_paper"
                if not filename.lower().endswith(".pdf"):
                    filename += ".pdf"
                self.config['filename'] = filename
                self.config['title'] = self.cli_args.title if (self.cli_args and self.cli_args.title) else "Question Paper"
                self.config['subtitle'] = self.cli_args.subtitle if (self.cli_args and self.cli_args.subtitle) else "Examination"
                self.config['subject'] = self.cli_args.subject if (self.cli_args and self.cli_args.subject) else "General"
                self.config['marks'] = self.cli_args.marks if (self.cli_args and self.cli_args.marks) else 100
                self.config['time'] = self.cli_args.time if (self.cli_args and self.cli_args.time) else 180
                self.config['logo_path'] = self.cli_args.logo if (self.cli_args and self.cli_args.logo) else None
                self.config['ruled_lines'] = not (self.cli_args and self.cli_args.no_ruled_lines)
                if self.cli_args and self.cli_args.no_sections:
                    self.config['separate_sections'] = False
                elif self.cli_args and self.cli_args.separate_sections is not None:
                    self.config['separate_sections'] = self.cli_args.separate_sections
                else:
                    self.config['separate_sections'] = True

                # Guidelines file
                self.config['guidelines_file'] = self.cli_args.guidelines_file if (self.cli_args and self.cli_args.guidelines_file) else None
                if self.config['guidelines_file']:
                    self.config['guidelines'] = self.load_guidelines_file(self.config['guidelines_file'])

                return True

            # Interactive Mode
            print(Fore.GREEN + "=" * 60)
            print(Fore.GREEN + "       WELCOME TO THE QUESTION PAPER MAKER (QuesPM)")
            print(Fore.GREEN + "=" * 60 + "\n")

            # Output filename
            filename = input(Fore.CYAN + "Enter output PDF filename [default: question_paper]: ").strip()
            if not filename:
                filename = "question_paper"
            if not filename.lower().endswith(".pdf"):
                filename += ".pdf"
            self.config['filename'] = filename

            # Title
            title = input(Fore.CYAN + "Enter examination title [default: Question Paper]: ").strip()
            self.config['title'] = title if title else "Question Paper"

            # Subtitle
            subtitle = input(Fore.CYAN + "Enter subheading [default: Examination]: ").strip()
            self.config['subtitle'] = subtitle if subtitle else "Examination"

            # Subject
            subject = input(Fore.CYAN + "Enter subject [default: General]: ").strip()
            self.config['subject'] = subject if subject else "General"

            # Time
            time_input = input(Fore.CYAN + "Enter time allotted in minutes [default: 180]: ").strip()
            try:
                self.config['time'] = int(time_input) if time_input else 180
            except ValueError:
                print(Fore.YELLOW + "Invalid time, using default: 180")
                self.config['time'] = 180

            # Marks
            marks_input = input(Fore.CYAN + "Enter maximum marks [default: 100]: ").strip()
            try:
                self.config['marks'] = int(marks_input) if marks_input else 100
            except ValueError:
                print(Fore.YELLOW + "Invalid marks, using default: 100")
                self.config['marks'] = 100

            # Logo path
            logo_path = input(Fore.CYAN + "Enter logo file path (press Enter to skip): ").strip()
            self.config['logo_path'] = logo_path if logo_path else None

            # Ruled lines
            ruled_ans = input(Fore.CYAN + "Enable ruled lines for subjective writing spaces? (y/n) [default: y]: ").strip().lower()
            self.config['ruled_lines'] = False if ruled_ans == 'n' else True

            # Section separation
            sec_ans = input(Fore.CYAN + "Keep sections separated with section headers? (y/n) [default: y]: ").strip().lower()
            self.config['separate_sections'] = False if sec_ans == 'n' else True

            # Guidelines file
            guidelines_path = input(Fore.CYAN + "Enter guidelines text file path (press Enter to skip): ").strip()
            self.config['guidelines_file'] = guidelines_path if guidelines_path else None
            if self.config['guidelines_file']:
                self.config['guidelines'] = self.load_guidelines_file(self.config['guidelines_file'])

            print(Fore.GREEN + "\n✓ Examination details configured successfully\n")
            return True

        except KeyboardInterrupt:
            print(Fore.RED + "\nOperation cancelled by user")
            return False
        except Exception as e:
            logger.error(f"Error getting configuration: {e}")
            return False

    def load_from_cli_args(self) -> bool:
        """
        Load questions specified via CLI arguments.
        Returns True if questions were loaded from CLI flags, False otherwise.
        """
        if not self.cli_args:
            return False

        has_questions = False

        # 1. MCQ
        if self.cli_args.mcq_file:
            mcqs = self.question_manager.load_mcq_from_csv(self.cli_args.mcq_file)
            count = self.cli_args.num_mcq if self.cli_args.num_mcq is not None else len(mcqs)
            selected = self.question_manager.select_random_questions(mcqs, count)
            self.question_manager.add_mcq_questions(selected)
            print(Fore.GREEN + f"✓ Selected {len(selected)} MCQ questions from {self.cli_args.mcq_file}")
            has_questions = True

        # 2. Reasoned MCQ
        if self.cli_args.reasoned_mcq_file:
            r_mcqs = self.question_manager.load_reasoned_mcq_from_csv(self.cli_args.reasoned_mcq_file)
            count = self.cli_args.num_reasoned_mcq if self.cli_args.num_reasoned_mcq is not None else len(r_mcqs)
            selected = self.question_manager.select_random_questions(r_mcqs, count)
            self.question_manager.add_reasoned_mcq_questions(selected)
            print(Fore.GREEN + f"✓ Selected {len(selected)} Reasoned MCQ questions from {self.cli_args.reasoned_mcq_file}")
            has_questions = True

        # 3. Objective
        if self.cli_args.objective_file:
            objs = self.question_manager.load_objective_from_csv(self.cli_args.objective_file)
            count = self.cli_args.num_objective if self.cli_args.num_objective is not None else len(objs)
            selected = self.question_manager.select_random_questions(objs, count)
            self.question_manager.add_objective_questions(selected)
            print(Fore.GREEN + f"✓ Selected {len(selected)} Objective questions from {self.cli_args.objective_file}")
            has_questions = True

        # 4. Subjective
        if self.cli_args.subjective_file:
            subjs = self.question_manager.load_subjective_from_csv(self.cli_args.subjective_file)
            count = self.cli_args.num_subjective if self.cli_args.num_subjective is not None else len(subjs)
            selected = self.question_manager.select_random_questions(subjs, count)
            self.question_manager.add_subjective_questions(selected)
            print(Fore.GREEN + f"✓ Selected {len(selected)} Subjective questions from {self.cli_args.subjective_file}")
            has_questions = True

        return has_questions

    def get_question_input(self) -> bool:
        """
        Interactive menu to acquire questions across MCQ, Objective, and Subjective types.
        """
        try:
            print(Fore.GREEN + "Select sections to include:")
            print(Fore.GREEN + "  1) MCQ (Standard 4 Options)")
            print(Fore.GREEN + "  2) Reasoned MCQ (4 Options + Writing Space for Reason)")
            print(Fore.GREEN + "  3) Objective / One-Word Questions")
            print(Fore.GREEN + "  4) Subjective Questions (with writing spaces)")
            print(Fore.GREEN + "  5) All Sections")
            print(Fore.GREEN + "  6) Done adding questions\n")

            while True:
                choice = input(Fore.CYAN + "Enter choice (1-5 or 6 when finished): ").strip()
                if choice == '1':
                    self._get_mcq_input()
                elif choice == '2':
                    self._get_reasoned_mcq_input()
                elif choice == '3':
                    self._get_objective_input()
                elif choice == '4':
                    self._get_subjective_input()
                elif choice == '5':
                    self._get_mcq_input()
                    self._get_reasoned_mcq_input()
                    self._get_objective_input()
                    self._get_subjective_input()
                    break
                elif choice in ['6', 'done', 'q']:
                    break
                else:
                    print(Fore.YELLOW + "Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")

            total_q = (len(self.question_manager.mcq_questions) +
                       len(self.question_manager.reasoned_mcq_questions) +
                       len(self.question_manager.objective_questions) +
                       len(self.question_manager.subjective_questions))

            if total_q == 0:
                print(Fore.YELLOW + "No questions were added.")
                return False

            self._reconcile_marks()
            return True

        except KeyboardInterrupt:
            print(Fore.RED + "\nOperation cancelled by user")
            return False
        except Exception as e:
            logger.error(f"Error getting question input: {e}")
            return False

    def _get_mcq_input(self):
        """Interactive input for MCQ questions."""
        try:
            print(Fore.MAGENTA + "\n--- Multiple Choice Questions (MCQ) ---")
            filepath = input(Fore.CYAN + "Enter path to MCQ CSV file (or Enter for manual entry): ").strip()
            if filepath:
                mcqs = self.question_manager.load_mcq_from_csv(filepath)
                count_str = input(Fore.CYAN + f"Enter number of MCQs to select (max {len(mcqs)}) [default: {len(mcqs)}]: ").strip()
                count = int(count_str) if count_str else len(mcqs)
                selected = self.question_manager.select_random_questions(mcqs, count)
                self.question_manager.add_mcq_questions(selected)
                print(Fore.GREEN + f"✓ Added {len(selected)} MCQ questions\n")
            else:
                count = int(input(Fore.CYAN + "How many MCQ questions would you like to enter? "))
                selected = []
                for i in range(count):
                    print(Fore.MAGENTA + f"\nMCQ #{i+1}:")
                    q_text = input(Fore.CYAN + "  Question: ").strip()
                    opt_a = input(Fore.CYAN + "  Option A: ").strip()
                    opt_b = input(Fore.CYAN + "  Option B: ").strip()
                    opt_c = input(Fore.CYAN + "  Option C: ").strip()
                    opt_d = input(Fore.CYAN + "  Option D: ").strip()
                    marks_str = input(Fore.CYAN + "  Marks [default: 1]: ").strip()
                    marks = float(marks_str) if marks_str else 1.0
                    selected.append(MCQQuestion(
                        question=q_text,
                        options=[opt_a, opt_b, opt_c, opt_d],
                        marks=marks
                    ))
                self.question_manager.add_mcq_questions(selected)
                print(Fore.GREEN + f"✓ Added {len(selected)} MCQ questions\n")
        except Exception as e:
            print(Fore.RED + f"Error adding MCQ questions: {e}")

    def _get_reasoned_mcq_input(self):
        """Interactive input for Reasoned MCQ questions."""
        try:
            print(Fore.MAGENTA + "\n--- Reasoned MCQ (4 Options + Writing Space for Reason) ---")
            filepath = input(Fore.CYAN + "Enter path to Reasoned MCQ CSV file (or Enter for manual entry): ").strip()
            if filepath:
                r_mcqs = self.question_manager.load_reasoned_mcq_from_csv(filepath)
                count_str = input(Fore.CYAN + f"Enter number of Reasoned MCQs to select (max {len(r_mcqs)}) [default: {len(r_mcqs)}]: ").strip()
                count = int(count_str) if count_str else len(r_mcqs)
                selected = self.question_manager.select_random_questions(r_mcqs, count)
                self.question_manager.add_reasoned_mcq_questions(selected)
                print(Fore.GREEN + f"✓ Added {len(selected)} Reasoned MCQ questions\n")
            else:
                count = int(input(Fore.CYAN + "How many Reasoned MCQ questions would you like to enter? "))
                selected = []
                for i in range(count):
                    print(Fore.MAGENTA + f"\nReasoned MCQ #{i+1}:")
                    q_text = input(Fore.CYAN + "  Question: ").strip()
                    opt_a = input(Fore.CYAN + "  Option A: ").strip()
                    opt_b = input(Fore.CYAN + "  Option B: ").strip()
                    opt_c = input(Fore.CYAN + "  Option C: ").strip()
                    opt_d = input(Fore.CYAN + "  Option D: ").strip()
                    lines_str = input(Fore.CYAN + "  Reasoning lines [default: 2]: ").strip()
                    lines = int(lines_str) if lines_str else 2
                    marks_str = input(Fore.CYAN + "  Marks [default: 2]: ").strip()
                    marks = float(marks_str) if marks_str else 2.0
                    selected.append(ReasonedMCQQuestion(
                        question=q_text,
                        options=[opt_a, opt_b, opt_c, opt_d],
                        lines=lines,
                        marks=marks
                    ))
                self.question_manager.add_reasoned_mcq_questions(selected)
                print(Fore.GREEN + f"✓ Added {len(selected)} Reasoned MCQ questions\n")
        except Exception as e:
            print(Fore.RED + f"Error adding Reasoned MCQ questions: {e}")

    def _get_objective_input(self):
        """Interactive input for Objective / One-Word questions."""
        try:
            print(Fore.MAGENTA + "\n--- Objective / One-Word Questions ---")
            filepath = input(Fore.CYAN + "Enter path to Objective CSV file (or Enter for manual entry): ").strip()
            if filepath:
                objs = self.question_manager.load_objective_from_csv(filepath)
                count_str = input(Fore.CYAN + f"Enter number of Objective questions to select (max {len(objs)}) [default: {len(objs)}]: ").strip()
                count = int(count_str) if count_str else len(objs)
                selected = self.question_manager.select_random_questions(objs, count)
                self.question_manager.add_objective_questions(selected)
                print(Fore.GREEN + f"✓ Added {len(selected)} Objective questions\n")
            else:
                count = int(input(Fore.CYAN + "How many Objective questions would you like to enter? "))
                selected = []
                for i in range(count):
                    print(Fore.MAGENTA + f"\nObjective Q#{i+1}:")
                    q_text = input(Fore.CYAN + "  Question: ").strip()
                    marks_str = input(Fore.CYAN + "  Marks [default: 1]: ").strip()
                    marks = float(marks_str) if marks_str else 1.0
                    selected.append(ObjectiveQuestion(question=q_text, marks=marks))
                self.question_manager.add_objective_questions(selected)
                print(Fore.GREEN + f"✓ Added {len(selected)} Objective questions\n")
        except Exception as e:
            print(Fore.RED + f"Error adding Objective questions: {e}")

    def _get_subjective_input(self):
        """Interactive input for Subjective questions."""
        try:
            print(Fore.MAGENTA + "\n--- Subjective Questions (with Writing Space) ---")
            filepath = input(Fore.CYAN + "Enter path to Subjective CSV file (or Enter for manual entry): ").strip()
            if filepath:
                subjs = self.question_manager.load_subjective_from_csv(filepath)
                count_str = input(Fore.CYAN + f"Enter number of Subjective questions to select (max {len(subjs)}) [default: {len(subjs)}]: ").strip()
                count = int(count_str) if count_str else len(subjs)
                selected = self.question_manager.select_random_questions(subjs, count)
                self.question_manager.add_subjective_questions(selected)
                print(Fore.GREEN + f"✓ Added {len(selected)} Subjective questions\n")
            else:
                count = int(input(Fore.CYAN + "How many Subjective questions would you like to enter? "))
                selected = []
                for i in range(count):
                    print(Fore.MAGENTA + f"\nSubjective Q#{i+1}:")
                    q_text = input(Fore.CYAN + "  Question: ").strip()
                    stype = input(Fore.CYAN + "  Type (short/long) [default: short]: ").strip().lower()
                    if stype not in ['short', 'long']:
                        stype = 'short'
                    def_lines = 4 if stype == 'short' else 8
                    lines_str = input(Fore.CYAN + f"  Writing space lines [default: {def_lines}]: ").strip()
                    lines = int(lines_str) if lines_str else def_lines
                    def_marks = 3.0 if stype == 'short' else 5.0
                    marks_str = input(Fore.CYAN + f"  Marks [default: {def_marks}]: ").strip()
                    marks = float(marks_str) if marks_str else def_marks
                    selected.append(SubjectiveQuestion(
                        question=q_text,
                        subtype=stype,
                        lines=lines,
                        marks=marks
                    ))
                self.question_manager.add_subjective_questions(selected)
                print(Fore.GREEN + f"✓ Added {len(selected)} Subjective questions\n")
        except Exception as e:
            print(Fore.RED + f"Error adding Subjective questions: {e}")

    def _reconcile_marks(self):
        """Check total questions marks against configured maximum marks."""
        total_marks = self.question_manager.calculate_total_marks()
        paper_marks = self.config.get('marks')
        print(Fore.CYAN + f"Total marks from selected questions: {total_marks}")
        print(Fore.CYAN + f"Configured Maximum marks for paper: {paper_marks}")

        if paper_marks is None or (paper_marks == 100 and total_marks != 100):
            self.config['marks'] = int(total_marks) if total_marks.is_integer() else total_marks
            print(Fore.GREEN + f"✓ Synchronized paper Maximum Marks to match questions total: {self.config['marks']}\n")
        elif paper_marks != total_marks:
            print(Fore.YELLOW + f"Note: Total question marks ({total_marks}) does not equal maximum marks ({paper_marks})\n")

    def load_guidelines_file(self, filepath: str) -> Optional[str]:
        """Load candidate examination guidelines from a plain text file."""
        if not filepath:
            return None
        if not os.path.exists(filepath):
            print(Fore.YELLOW + f"Guidelines file not found: {filepath}")
            logger.warning(f"Guidelines file not found: {filepath}")
            return None
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            print(Fore.GREEN + f"✓ Loaded guidelines from: {filepath}")
            return content
        except Exception as e:
            print(Fore.RED + f"Error reading guidelines file: {e}")
            logger.error(f"Error reading guidelines file {filepath}: {e}")
            return None

    def generate_pdf(self) -> bool:
        """
        Generate the question paper PDF.
        """
        try:
            print(Fore.YELLOW + "Generating PDF...")

            pdf_gen = PDFGenerator(self.config)
            pdf_gen.initialize_canvas(self.config['filename'])
            pdf_gen.draw_header()

            # Draw Guidelines section if available
            pdf_gen.draw_guidelines()

            separate = self.config.get('separate_sections', self.config.get('sections', True))
            sections = self.question_manager.get_sections(separate=separate)
            pdf_gen.draw_questions(sections)

            pdf_gen.save()

            print(Fore.GREEN + "\n" + "=" * 60)
            print(Fore.GREEN + "✓ PDF generated successfully!")
            print(Fore.GREEN + f"✓ Saved as: {self.config['filename']}")
            print(Fore.GREEN + f"✓ Total Marks: {self.question_manager.calculate_total_marks()}")
            print(Fore.GREEN + "=" * 60)
            return True

        except PDFGenerationError as e:
            print(Fore.RED + f"PDF Generation Error: {e}")
            logger.error(f"PDF generation failed: {e}")
            return False
        except Exception as e:
            print(Fore.RED + f"Unexpected error: {e}")
            logger.error(f"Unexpected error during PDF generation: {e}")
            return False

    def run(self):
        """Main execution method."""
        try:
            if not self.get_user_input():
                return

            has_cli_questions = self.load_from_cli_args()

            # If no questions provided via CLI or forced interactive, prompt
            if not has_cli_questions or (self.cli_args and self.cli_args.interactive):
                if not self.get_question_input():
                    return
            else:
                self._reconcile_marks()

            self.generate_pdf()

        except Exception as e:
            print(Fore.RED + f"Fatal error: {e}")
            logger.error(f"Fatal error in main execution: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    try:
        parser = build_argument_parser()
        args = parser.parse_args()
        maker = QuestionPaperMaker(cli_args=args)
        maker.run()
    except KeyboardInterrupt:
        print(Fore.RED + "\n\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(Fore.RED + f"\nFatal error: {e}")
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
