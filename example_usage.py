#!/usr/bin/env python3
"""
Example usage of QuesPM - Question Paper Maker

This script demonstrates how to use quespm.py programmatically with:
- Multiple Choice Questions (MCQ) with 4 options
- Objective / One-Word Questions
- Subjective Questions with ruled writing spaces
- Dynamic Question Marks Calculation
- Section-based generation from CSV banks
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quespm import (
    QuestionPaperMaker,
    MCQQuestion,
    ObjectiveQuestion,
    SubjectiveQuestion
)

def main():
    """Create a sample question paper programmatically."""
    print("=" * 60)
    print("QuesPM - Question Paper Maker - Example Usage")
    print("=" * 60)

    # 1. Initialize QuestionPaperMaker
    maker = QuestionPaperMaker()

    # 2. Configure paper details
    maker.config = {
        'filename': 'example_question_paper.pdf',
        'title': 'Computer Science Semester Examination',
        'subtitle': 'End Semester Examination - 2024',
        'subject': 'Computer Science & Engineering',
        'marks': 50,
        'time': 120,
        'logo_path': None,
        'ruled_lines': True  # Draw ruled lines for writing space in subjective questions
    }

    print("\nInitial Configuration:")
    print(f"  Title: {maker.config['title']}")
    print(f"  Subject: {maker.config['subject']}")
    print(f"  Time: {maker.config['time']} minutes")

    qm = maker.question_manager

    # 3. Load MCQ questions from CSV (or create programmatically)
    mcq_csv = 'sample_mcq_questions.csv'
    if os.path.exists(mcq_csv):
        mcqs = qm.load_mcq_from_csv(mcq_csv)
        selected_mcqs = qm.select_random_questions(mcqs, 4)
        qm.add_mcq_questions(selected_mcqs)
        print(f"\n✓ Loaded and selected {len(selected_mcqs)} MCQ questions from {mcq_csv}")
    else:
        # Fallback programmatic creation
        qm.add_mcq_questions([
            MCQQuestion(
                question="What is the output of print(type([])) in Python?",
                options=["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'set'>"],
                marks=1.0,
                correct_answer="A"
            )
        ])

    # 4. Load Objective questions from CSV
    obj_csv = 'sample_objective_questions.csv'
    if os.path.exists(obj_csv):
        objs = qm.load_objective_from_csv(obj_csv)
        selected_objs = qm.select_random_questions(objs, 3)
        qm.add_objective_questions(selected_objs)
        print(f"✓ Loaded and selected {len(selected_objs)} Objective questions from {obj_csv}")

    # 5. Load Subjective questions from CSV (with writing lines)
    subj_csv = 'sample_subjective_questions.csv'
    if os.path.exists(subj_csv):
        subjs = qm.load_subjective_from_csv(subj_csv)
        # Select 2 short questions and 2 long questions
        short_q = [q for q in subjs if q.subtype == 'short']
        long_q = [q for q in subjs if q.subtype == 'long']
        selected_subjs = qm.select_random_questions(short_q, 2) + qm.select_random_questions(long_q, 2)
        qm.add_subjective_questions(selected_subjs)
        print(f"✓ Loaded and selected {len(selected_subjs)} Subjective questions from {subj_csv}")

    # 6. Reconcile marks
    total_marks = qm.calculate_total_marks()
    maker.config['marks'] = int(total_marks) if total_marks.is_integer() else total_marks
    print(f"\n✓ Calculated total marks from questions: {maker.config['marks']}")

    # 7. Generate PDF
    print("\nGenerating PDF...")
    success = maker.generate_pdf()

    if success:
        print(f"\n✓ PDF generated successfully: {maker.config['filename']}")
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
