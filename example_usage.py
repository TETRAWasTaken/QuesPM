#!/usr/bin/env python3
"""
Example usage of QuesPM - Question Paper Maker

This script demonstrates how to use quespm.py programmatically.
"""

import sys
import os

# Add the current directory to path to import quespm
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quespm import QuestionPaperMaker

def main():
    """Create a sample question paper."""
    print("=" * 60)
    print("QuesPM - Question Paper Maker - Example Usage")
    print("=" * 60)
    
    # Create instance
    maker = QuestionPaperMaker()
    
    # Set configuration programmatically
    maker.config = {
        'filename': 'example_question_paper.pdf',
        'title': 'Computer Science Final Examination',
        'subtitle': 'End Semester Examination - 2024',
        'marks': 100,
        'time': 180,
        'subject': 'Computer Science',
        'logo_path': None  # Set to image path if you have a logo
    }
    
    print("\nConfiguration:")
    print(f"  Title: {maker.config['title']}")
    print(f"  Subject: {maker.config['subject']}")
    print(f"  Max Marks: {maker.config['marks']}")
    print(f"  Time: {maker.config['time']} minutes")
    
    # Add short answer questions
    short_questions = [
        "What is Python and what are its key features",
        "Define Object-Oriented Programming",
        "Explain the concept of inheritance",
        "What is polymorphism in OOP",
        "Define encapsulation with an example"
    ]
    
    maker.question_manager.add_short_answer_questions(short_questions)
    print(f"\n✓ Added {len(short_questions)} short answer questions")
    
    # Add long answer questions
    long_questions = [
        "Explain the concept of Object-Oriented Programming with detailed examples",
        "Describe the difference between procedural and object-oriented programming paradigms",
        "Discuss the SOLID principles in software design and their importance"
    ]
    
    maker.question_manager.add_long_answer_questions(long_questions)
    print(f"✓ Added {len(long_questions)} long answer questions")
    
    # Generate PDF
    print("\nGenerating PDF...")
    success = maker.generate_pdf()
    
    if success:
        print(f"\n✓ PDF generated successfully: {maker.config['filename']}")
        
        # Check file size
        if os.path.exists(maker.config['filename']):
            size = os.path.getsize(maker.config['filename'])
            print(f"✓ File size: {size:,} bytes")
    else:
        print("\n✗ PDF generation failed")
        return 1
    
    print("\n" + "=" * 60)
    print("Example completed successfully!")
    print("=" * 60)
    return 0

if __name__ == "__main__":
    sys.exit(main())
