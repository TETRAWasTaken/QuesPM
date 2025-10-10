#!/usr/bin/env python3
"""
Question Paper Maker (QuesPM)
A tool to generate question papers in PDF format with customizable settings.

Features:
- Object-oriented design
- Error handling
- Configurable settings
- Support for multiple question types
"""

import os
import sys
import ast
import random
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path

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
    from colorama import Fore, init as colorama_init
    colorama_init()
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


class QuestionManager:
    """Manages question loading and selection."""
    
    def __init__(self):
        """Initialize the QuestionManager."""
        self.short_answer_questions: List[str] = []
        self.long_answer_questions: List[str] = []
    
    def load_questions_from_file(self, filepath: str) -> List[str]:
        """
        Load questions from a text file.
        
        Args:
            filepath: Path to the question file
            
        Returns:
            List of questions
            
        Raises:
            QuestionError: If file cannot be read or parsed
        """
        try:
            if not os.path.exists(filepath):
                raise QuestionError(f"Question file not found: {filepath}")
            
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
            raise QuestionError(f"Error loading questions: {e}")
    
    def select_random_questions(self, questions: List[str], count: int) -> List[str]:
        """
        Select random unique questions from a list.
        
        Args:
            questions: List of available questions
            count: Number of questions to select
            
        Returns:
            List of selected questions
            
        Raises:
            QuestionError: If count exceeds available questions
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
    
    def add_short_answer_questions(self, questions: List[str]):
        """Add short answer questions."""
        self.short_answer_questions.extend(questions)
    
    def add_long_answer_questions(self, questions: List[str]):
        """Add long answer questions."""
        self.long_answer_questions.extend(questions)
    
    def get_all_questions(self) -> Dict[str, List[str]]:
        """Get all questions organized by type."""
        return {
            "Short answer type": self.short_answer_questions,
            "Long answer type": self.long_answer_questions
        }


class PDFGenerator:
    """Handles PDF generation for question papers."""
    
    def __init__(self, config: Dict):
        """
        Initialize the PDF generator.
        
        Args:
            config: Configuration dictionary containing PDF settings
        """
        self.config = config
        self.canvas: Optional[Canvas] = None
        self.current_y: int = 650
        self.used_lines: List[str] = []
        
    def initialize_canvas(self, filename: str):
        """
        Initialize the PDF canvas.
        
        Args:
            filename: Output PDF filename
            
        Raises:
            PDFGenerationError: If canvas cannot be initialized
        """
        try:
            self.canvas = Canvas(filename, pagesize=A4)
            logger.info(f"Initialized PDF canvas for {filename}")
        except Exception as e:
            raise PDFGenerationError(f"Failed to initialize canvas: {e}")
    
    def register_font(self, font_name: str, font_path: str):
        """
        Register a custom font.
        
        Args:
            font_name: Name to register the font as
            font_path: Path to the font file
            
        Raises:
            PDFGenerationError: If font cannot be registered
        """
        try:
            if not os.path.exists(font_path):
                logger.warning(f"Font file not found: {font_path}, using default font")
                return
            
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            logger.info(f"Registered font: {font_name}")
        except Exception as e:
            logger.warning(f"Failed to register font: {e}, using default font")
    
    def draw_header(self):
        """Draw the PDF header with title, logo, and metadata."""
        try:
            title = self.config.get('title', 'Question Paper').upper()
            subtitle = self.config.get('subtitle', 'Examination').upper()
            logo_path = self.config.get('logo_path')
            
            # Title
            self.canvas.setFont('Helvetica-Bold', 50)
            self.canvas.drawCentredString(297.5, 770, title)
            
            # Logo (if provided)
            if logo_path and os.path.exists(logo_path):
                try:
                    self.canvas.drawInlineImage(logo_path, 505, 752, 80, 80, showBoundary=True)
                except Exception as e:
                    logger.warning(f"Failed to add logo: {e}")
            
            # Subtitle
            self.canvas.setFont("Courier-Bold", 24)
            self.canvas.drawCentredString(297.5, 730, subtitle)
            
            # Time and marks
            time_str = f"Maximum time : {self.config.get('time', 'N/A')} min"
            marks_str = f"Maximum marks : {self.config.get('marks', 'N/A')}"
            
            self.canvas.setFont("Courier-Bold", 14)
            self.canvas.drawString(40, 700, time_str)
            self.canvas.drawRightString(555, 700, marks_str)
            
            # Subject
            subject_str = f"Subject : {self.config.get('subject', 'N/A')}"
            self.canvas.drawString(40, 680, subject_str)
            
            # Line separator
            self.canvas.line(30, 670, 565, 670)
            
            logger.info("Header drawn successfully")
        except Exception as e:
            raise PDFGenerationError(f"Failed to draw header: {e}")
    
    def draw_questions(self, questions_dict: Dict[str, List[str]]):
        """
        Draw questions on the PDF.
        
        Args:
            questions_dict: Dictionary with question types as keys and question lists as values
        """
        for section_name, questions in questions_dict.items():
            if not questions:
                continue
            
            # Draw section header
            self.canvas.setFont("Courier-Bold", 16)
            self.canvas.drawCentredString(297.5, self.current_y, section_name)
            self.current_y -= 30
            
            # Draw questions
            for idx, question in enumerate(questions, 1):
                question_text = f"Q. {idx}) {question}?"
                self._draw_text_line(question_text)
        
        logger.info("Questions drawn successfully")
    
    def _draw_text_line(self, text: str):
        """
        Draw a single line of text, handling page breaks.
        
        Args:
            text: Text to draw
        """
        text_object = self.canvas.beginText()
        text_object.setTextOrigin(40, self.current_y)
        text_object.setFont("Helvetica", 14)
        text_object.textLine(text)
        
        self.canvas.drawText(text_object)
        self.current_y -= 28
        
        # Handle page break
        if self.current_y <= 40:
            self.canvas.showPage()
            self.current_y = 792
    
    def save(self):
        """Save the PDF file."""
        try:
            if self.canvas:
                self.canvas.save()
                logger.info("PDF saved successfully")
        except Exception as e:
            raise PDFGenerationError(f"Failed to save PDF: {e}")


class QuestionPaperMaker:
    """Main class for creating question papers."""
    
    def __init__(self):
        """Initialize the QuestionPaperMaker."""
        self.question_manager = QuestionManager()
        self.config: Dict = {}
    
    def get_user_input(self) -> bool:
        """
        Get configuration input from user.
        
        Returns:
            True if input was successful, False otherwise
        """
        try:
            print(Fore.GREEN + "=" * 50)
            print(Fore.GREEN + "WELCOME TO THE QUESTION PAPER MAKER")
            print(Fore.GREEN + "=" * 50 + "\n")
            
            # File name
            filename = input(Fore.CYAN + "Enter the name of the file: ").strip()
            if not filename:
                filename = "question_paper"
            self.config['filename'] = filename + ".pdf"
            
            # Title
            title = input(Fore.CYAN + "Enter the title: ").strip()
            self.config['title'] = title if title else "Question Paper"
            
            # Logo path (optional)
            logo_path = input(Fore.CYAN + "Enter logo file path (press Enter to skip): ").strip()
            self.config['logo_path'] = logo_path if logo_path else None
            
            # Subtitle
            subtitle = input(Fore.CYAN + "Enter the subheading: ").strip()
            self.config['subtitle'] = subtitle if subtitle else "Examination"
            
            # Marks
            marks = input(Fore.CYAN + "Enter maximum marks: ").strip()
            try:
                self.config['marks'] = int(marks) if marks else 100
            except ValueError:
                print(Fore.YELLOW + "Invalid marks, using default: 100")
                self.config['marks'] = 100
            
            # Time
            time = input(Fore.CYAN + "Enter time allotted (minutes): ").strip()
            try:
                self.config['time'] = int(time) if time else 180
            except ValueError:
                print(Fore.YELLOW + "Invalid time, using default: 180")
                self.config['time'] = 180
            
            # Subject
            subject = input(Fore.CYAN + "Enter the subject: ").strip()
            self.config['subject'] = subject if subject else "General"
            
            print(Fore.GREEN + "\n✓ Configuration acquired successfully\n")
            return True
            
        except KeyboardInterrupt:
            print(Fore.RED + "\nOperation cancelled by user")
            return False
        except Exception as e:
            logger.error(f"Error getting user input: {e}")
            return False
    
    def get_question_input(self) -> bool:
        """
        Get question selection input from user.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print(Fore.GREEN + "Now acquiring question data...")
            print(Fore.GREEN + "\nAvailable question types:")
            print(Fore.GREEN + "  1) Short Answer Type")
            print(Fore.GREEN + "  2) Long Answer Type")
            print(Fore.GREEN + "  3) Both types\n")
            
            choice = input(Fore.CYAN + "Enter your choice (1/2/3): ").strip()
            
            if choice in ['1', '3']:
                self._get_short_answer_questions()
            
            if choice in ['2', '3']:
                self._get_long_answer_questions()
            
            if choice not in ['1', '2', '3']:
                print(Fore.YELLOW + "Invalid choice, no questions added")
                return False
            
            return True
            
        except KeyboardInterrupt:
            print(Fore.RED + "\nOperation cancelled by user")
            return False
        except Exception as e:
            logger.error(f"Error getting question input: {e}")
            return False
    
    def _get_short_answer_questions(self):
        """Get short answer questions from user."""
        try:
            # Try to load from file first
            filepath = input(Fore.CYAN + "Enter path to short answer questions file (or press Enter to skip): ").strip()
            
            if filepath:
                questions = self.question_manager.load_questions_from_file(filepath)
                count = int(input(Fore.CYAN + f"Enter number of short answer questions (max {len(questions)}): "))
                selected = self.question_manager.select_random_questions(questions, count)
            else:
                # Manual entry
                count = int(input(Fore.CYAN + "Enter number of short answer questions: "))
                selected = []
                print(Fore.MAGENTA + "Enter short answer questions:")
                for i in range(count):
                    q = input(Fore.MAGENTA + f"Q{i+1}: ").strip()
                    if q:
                        selected.append(q)
            
            self.question_manager.add_short_answer_questions(selected)
            print(Fore.GREEN + f"✓ Added {len(selected)} short answer questions\n")
            
        except ValueError as e:
            print(Fore.RED + f"Invalid input: {e}")
        except QuestionError as e:
            print(Fore.RED + f"Error: {e}")
    
    def _get_long_answer_questions(self):
        """Get long answer questions from user."""
        try:
            # Try to load from file first
            filepath = input(Fore.CYAN + "Enter path to long answer questions file (or press Enter to skip): ").strip()
            
            if filepath:
                questions = self.question_manager.load_questions_from_file(filepath)
                count = int(input(Fore.CYAN + f"Enter number of long answer questions (max {len(questions)}): "))
                selected = self.question_manager.select_random_questions(questions, count)
            else:
                # Manual entry
                count = int(input(Fore.CYAN + "Enter number of long answer questions: "))
                selected = []
                print(Fore.MAGENTA + "Enter long answer questions:")
                for i in range(count):
                    q = input(Fore.MAGENTA + f"Q{i+1}: ").strip()
                    if q:
                        selected.append(q)
            
            self.question_manager.add_long_answer_questions(selected)
            print(Fore.GREEN + f"✓ Added {len(selected)} long answer questions\n")
            
        except ValueError as e:
            print(Fore.RED + f"Invalid input: {e}")
        except QuestionError as e:
            print(Fore.RED + f"Error: {e}")
    
    def generate_pdf(self) -> bool:
        """
        Generate the question paper PDF.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            print(Fore.YELLOW + "Generating PDF...")
            
            pdf_gen = PDFGenerator(self.config)
            pdf_gen.initialize_canvas(self.config['filename'])
            pdf_gen.draw_header()
            
            questions = self.question_manager.get_all_questions()
            pdf_gen.draw_questions(questions)
            
            pdf_gen.save()
            
            print(Fore.GREEN + "\n" + "=" * 50)
            print(Fore.GREEN + "✓ PDF generated successfully!")
            print(Fore.GREEN + f"✓ Saved as: {self.config['filename']}")
            print(Fore.GREEN + "=" * 50)
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
            
            if not self.get_question_input():
                return
            
            self.generate_pdf()
            
        except Exception as e:
            print(Fore.RED + f"Fatal error: {e}")
            logger.error(f"Fatal error in main execution: {e}")
            sys.exit(1)


def main():
    """Main entry point."""
    try:
        maker = QuestionPaperMaker()
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
