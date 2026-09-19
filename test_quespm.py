#!/usr/bin/env python3
"""
Comprehensive test suite for QuesPM (Question Paper Maker).
Tests:
- MCQ, Objective, and Subjective question models
- CSV loading for all question bank types
- Random selection and validation
- Marks system and calculation
- PDF generation with sections, 4 MCQ options, and ruled writing spaces
- CLI argument parsing and non-interactive workflows
- Backward compatibility
"""

import sys
import os
import tempfile
import csv

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quespm import (
    MCQQuestion,
    ReasonedMCQQuestion,
    MCQ,
    ReasonedMCQ,
    ObjectiveQuestion,
    SubjectiveQuestion,
    QuestionManager,
    PDFGenerator,
    QuestionPaperMaker,
    QuestionError,
    PDFGenerationError,
    build_argument_parser
)


def test_question_models():
    """Test question data models."""
    print("\n" + "=" * 60)
    print("Testing Question Data Models")
    print("=" * 60)

    # MCQ Question
    mcq = MCQQuestion(
        question="What is Python?",
        options=["Option A", "Option B", "Option C", "Option D"],
        marks=2,
        correct_answer="A"
    )
    assert mcq.question == "What is Python?"
    assert len(mcq.options) == 4
    assert mcq.marks == 2.0
    assert mcq.correct_answer == "A"
    assert MCQ is MCQQuestion, "MCQ alias should refer to MCQQuestion"
    print("✓ Test 1: MCQQuestion model initialization & MCQ alias")

    # MCQ Auto-padding if fewer than 4 options
    mcq_padded = MCQ(
        question="Short MCQ?",
        options=["Opt1", "Opt2"]
    )
    assert len(mcq_padded.options) == 4
    assert mcq_padded.options[2] == "Option C"
    print("✓ Test 2: MCQQuestion auto-padding to 4 options")

    # Reasoned MCQ Question
    rmcq = ReasonedMCQQuestion(
        question="Why is quicksort in-place?",
        options=["O(1) auxiliary memory", "Uses linked lists", "Tree based", "None"],
        lines=2,
        marks=2.0,
        correct_answer="A"
    )
    assert rmcq.question == "Why is quicksort in-place?"
    assert len(rmcq.options) == 4
    assert rmcq.lines == 2
    assert rmcq.marks == 2.0
    assert rmcq.correct_answer == "A"
    assert ReasonedMCQ is ReasonedMCQQuestion, "ReasonedMCQ alias should refer to ReasonedMCQQuestion"
    print("✓ Test 3: ReasonedMCQQuestion model initialization & ReasonedMCQ alias")

    # Reasoned MCQ Auto-padding if fewer than 4 options
    rmcq_padded = ReasonedMCQ(
        question="Short Reasoned MCQ?",
        options=["Opt1"]
    )
    assert len(rmcq_padded.options) == 4
    assert rmcq_padded.lines == 2
    assert rmcq_padded.marks == 2.0
    print("✓ Test 4: ReasonedMCQQuestion auto-padding to 4 options & default lines")

    # Objective Question
    obj = ObjectiveQuestion(question="Name the operator for floor division.", marks=1, answer="//")
    assert obj.question == "Name the operator for floor division."
    assert obj.marks == 1.0
    assert obj.answer == "//"
    print("✓ Test 5: ObjectiveQuestion model initialization")

    # Subjective Question
    subj_short = SubjectiveQuestion(question="Define polymorphism.", subtype="short", lines=4, marks=3)
    assert subj_short.subtype == "short"
    assert subj_short.lines == 4
    assert subj_short.marks == 3.0

    subj_long = SubjectiveQuestion(question="Explain OOP.", subtype="long", lines=10, marks=5)
    assert subj_long.subtype == "long"
    assert subj_long.lines == 10
    assert subj_long.marks == 5.0
    print("✓ Test 6: SubjectiveQuestion model initialization (short & long)")

    return True


def test_csv_loaders():
    """Test CSV loaders for MCQ, Reasoned MCQ, Objective, and Subjective questions."""
    print("\n" + "=" * 60)
    print("Testing CSV Loaders")
    print("=" * 60)

    qm = QuestionManager()

    # 1. Test MCQ CSV loading
    if os.path.exists("sample_mcq_questions.csv"):
        mcqs = qm.load_mcq_from_csv("sample_mcq_questions.csv")
        assert len(mcqs) > 0, "Should load MCQ questions from CSV"
        assert len(mcqs[0].options) == 4, "MCQ question must have 4 options"
        assert mcqs[0].marks > 0, "MCQ question should have marks"
        print(f"✓ Test 1: Loaded {len(mcqs)} MCQ questions from CSV")

    # 2. Test Reasoned MCQ CSV loading
    if os.path.exists("sample_reasoned_mcq_questions.csv"):
        rmcqs = qm.load_reasoned_mcq_from_csv("sample_reasoned_mcq_questions.csv")
        assert len(rmcqs) > 0, "Should load Reasoned MCQ questions from CSV"
        assert len(rmcqs[0].options) == 4, "Reasoned MCQ question must have 4 options"
        assert rmcqs[0].lines > 0, "Reasoned MCQ must have writing space lines"
        assert rmcqs[0].marks > 0, "Reasoned MCQ question should have marks"
        print(f"✓ Test 2: Loaded {len(rmcqs)} Reasoned MCQ questions from CSV")

    # 3. Test Objective CSV loading
    if os.path.exists("sample_objective_questions.csv"):
        objs = qm.load_objective_from_csv("sample_objective_questions.csv")
        assert len(objs) > 0, "Should load Objective questions from CSV"
        assert objs[0].marks > 0, "Objective question should have marks"
        print(f"✓ Test 3: Loaded {len(objs)} Objective questions from CSV")

    # 4. Test Subjective CSV loading
    if os.path.exists("sample_subjective_questions.csv"):
        subjs = qm.load_subjective_from_csv("sample_subjective_questions.csv")
        assert len(subjs) > 0, "Should load Subjective questions from CSV"
        assert subjs[0].lines > 0, "Subjective question should specify lines"
        assert subjs[0].marks > 0, "Subjective question should specify marks"
        print(f"✓ Test 4: Loaded {len(subjs)} Subjective questions from CSV")

    # 5. Error handling for non-existent file
    try:
        qm.load_mcq_from_csv("non_existent_file.csv")
        assert False, "Should raise QuestionError for missing file"
    except QuestionError:
        print("✓ Test 5: Correctly raises QuestionError for missing CSV")

    # 6. Malformed CSV error handling
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        tmp.write("")  # Empty CSV
        tmp_path = tmp.name

    try:
        qm.load_mcq_from_csv(tmp_path)
        assert False, "Should raise error for empty CSV"
    except QuestionError:
        print("✓ Test 6: Correctly handles empty CSV")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return True


def test_question_manager():
    """Test QuestionManager selection, aggregation, and marks."""
    print("\n" + "=" * 60)
    print("Testing QuestionManager & Marks System")
    print("=" * 60)

    qm = QuestionManager()

    # 1. Random Selection
    items = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    selected = qm.select_random_questions(items, 3)
    assert len(selected) == 3
    assert len(set(selected)) == 3
    print("✓ Test 1: Random selection of unique questions")

    # 2. Add question types
    mcq1 = MCQQuestion("MCQ 1", ["A", "B", "C", "D"], marks=1.0)
    mcq2 = MCQQuestion("MCQ 2", ["A", "B", "C", "D"], marks=1.0)
    qm.add_mcq_questions([mcq1, mcq2])

    rmcq1 = ReasonedMCQQuestion("Reasoned MCQ 1", ["A", "B", "C", "D"], lines=2, marks=2.0)
    qm.add_reasoned_mcq_questions([rmcq1])

    obj1 = ObjectiveQuestion("Obj 1", marks=2.0)
    qm.add_objective_questions([obj1])

    subj1 = SubjectiveQuestion("Subj 1", subtype="short", lines=4, marks=3.0)
    subj2 = SubjectiveQuestion("Subj 2", subtype="long", lines=8, marks=5.0)
    qm.add_subjective_questions([subj1, subj2])

    # 3. Calculate total marks
    total_marks = qm.calculate_total_marks()
    expected_marks = 1.0 + 1.0 + 2.0 + 2.0 + 3.0 + 5.0  # 14.0
    assert total_marks == expected_marks, f"Expected {expected_marks}, got {total_marks}"
    print(f"✓ Test 2: Marks calculation is correct ({total_marks} marks)")

    # 4. Sections structure
    sections = qm.get_sections()
    assert len(sections) == 5, "Should have MCQ, Reasoned MCQ, Objective, Short, and Long sections"
    assert "SECTION A: MULTIPLE CHOICE QUESTIONS" in sections[0][0]
    assert "SECTION B: REASONED MULTIPLE CHOICE QUESTIONS" in sections[1][0]
    assert "SECTION C: OBJECTIVE QUESTIONS" in sections[2][0]
    assert "SECTION D: SHORT ANSWER QUESTIONS" in sections[3][0]
    assert "SECTION E: LONG ANSWER QUESTIONS" in sections[4][0]
    print("✓ Test 3: Sections are dynamically organized and labeled with MCQ and Reasoned MCQ")

    # 5. Dict retrieval
    all_dict = qm.get_all_questions()
    assert "MCQ" in all_dict
    assert "Reasoned MCQ" in all_dict
    print("✓ Test 4: get_all_questions includes MCQ and Reasoned MCQ keys")

    # 6. Backward compatibility with short/long string additions
    qm_legacy = QuestionManager()
    qm_legacy.add_short_answer_questions(["Short 1", "Short 2"])
    qm_legacy.add_long_answer_questions(["Long 1"])
    all_q = qm_legacy.get_all_questions()
    assert len(all_q["Short answer type"]) == 2
    assert len(all_q["Long answer type"]) == 1
    print("✓ Test 5: Backward compatibility with legacy string lists maintained")

    # 7. Legacy file loader
    if os.path.exists("sample_short_questions.txt"):
        loaded = qm_legacy.load_questions_from_file("sample_short_questions.txt")
        assert len(loaded) > 0
        print(f"✓ Test 6: Legacy .txt file loader works ({len(loaded)} questions)")

    return True


def test_pdf_generator():
    """Test PDFGenerator with all question formats, options, and spaces."""
    print("\n" + "=" * 60)
    print("Testing PDFGenerator (MCQs, Reasoned MCQs, Writing Spaces, Marks)")
    print("=" * 60)

    config = {
        'title': 'Unit Test Examination',
        'subtitle': 'Department of Computer Science',
        'marks': 25,
        'time': 60,
        'subject': 'Software Engineering',
        'logo_path': None,
        'ruled_lines': True
    }

    pdf_gen = PDFGenerator(config)

    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        pdf_gen.initialize_canvas(tmp_path)
        pdf_gen.draw_header()

        # Build test sections with MCQ, Reasoned MCQ, Objective, and Subjective
        sections = [
            ("SECTION A: MULTIPLE CHOICE QUESTIONS (MCQ) (2 Marks)", [
                MCQQuestion(
                    question="Which data structure follows the LIFO principle in computing?",
                    options=["Queue", "Stack", "Array", "Tree"],
                    marks=1.0,
                    correct_answer="B"
                ),
                MCQQuestion(
                    question="Which algorithm is used for finding shortest paths in a graph?",
                    options=["Prim's Algorithm", "Dijkstra's Algorithm", "Kruskal's Algorithm", "Floyd's Algorithm"],
                    marks=1.0,
                    correct_answer="B"
                )
            ]),
            ("SECTION B: REASONED MULTIPLE CHOICE QUESTIONS (REASONED MCQ) (4 Marks)", [
                ReasonedMCQQuestion(
                    question="Why is QuickSort preferred over MergeSort for in-memory array sorting?",
                    options=["Lower auxiliary space O(1)", "Better worst-case O(n)", "Stable sorting", "Simpler recursion"],
                    lines=2,
                    marks=2.0,
                    correct_answer="A"
                ),
                ReasonedMCQQuestion(
                    question="Why are tuples preferred over lists as dictionary keys in Python?",
                    options=["Tuples use less memory", "Tuples are immutable & hashable", "Tuples can only store strings", "None of these"],
                    lines=2,
                    marks=2.0,
                    correct_answer="B"
                )
            ]),
            ("SECTION C: OBJECTIVE QUESTIONS (2 Marks)", [
                ObjectiveQuestion(
                    question="Name the built-in function to find length of a string in Python.",
                    marks=1.0,
                    answer="len"
                ),
                ObjectiveQuestion(
                    question="What boolean value does empty list evaluate to in Python?",
                    marks=1.0,
                    answer="False"
                )
            ]),
            ("SECTION D: SUBJECTIVE QUESTIONS (10 Marks)", [
                SubjectiveQuestion(
                    question="Define encapsulation and explain its role in data hiding.",
                    subtype="short",
                    lines=4,
                    marks=3.0
                ),
                SubjectiveQuestion(
                    question="Explain the SOLID principles in software engineering with real-world design examples.",
                    subtype="long",
                    lines=8,
                    marks=7.0
                )
            ])
        ]

        pdf_gen.draw_questions(sections)
        pdf_gen.save()

        assert os.path.exists(tmp_path), "PDF file should exist"
        size = os.path.getsize(tmp_path)
        assert size > 0, "PDF should have content"
        print(f"✓ Test 1: Full PDF with MCQs, Reasoned MCQs, writing lines, and marks generated ({size:,} bytes)")

    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return True


def test_cli_argument_parsing():
    """Test CLI argument parsing and non-interactive workflows."""
    print("\n" + "=" * 60)
    print("Testing CLI Argument Parsing")
    print("=" * 60)

    parser = build_argument_parser()

    # Parse CLI flags including Reasoned MCQ
    args = parser.parse_args([
        "--title", "Final Exam",
        "--subtitle", "Semester 1",
        "--subject", "Algorithms",
        "--marks", "50",
        "--time", "90",
        "--mcq-file", "sample_mcq_questions.csv",
        "--num-mcq", "3",
        "--reasoned-mcq-file", "sample_reasoned_mcq_questions.csv",
        "--num-reasoned-mcq", "2",
        "--objective-file", "sample_objective_questions.csv",
        "--num-objective", "2",
        "--subjective-file", "sample_subjective_questions.csv",
        "--num-subjective", "2",
        "--output", "cli_test.pdf"
    ])

    assert args.title == "Final Exam"
    assert args.subject == "Algorithms"
    assert args.marks == 50
    assert args.time == 90
    assert args.num_mcq == 3
    assert args.num_reasoned_mcq == 2
    assert args.num_objective == 2
    assert args.num_subjective == 2
    print("✓ Test 1: CLI arguments parsed accurately")

    # Test QuestionPaperMaker non-interactive loading
    maker = QuestionPaperMaker(cli_args=args)
    assert not maker.is_interactive(), "Should detect non-interactive mode when question files are passed"

    # Test loading
    maker.get_user_input()
    assert maker.config['title'] == "Final Exam"
    assert maker.config['subject'] == "Algorithms"

    has_q = maker.load_from_cli_args()
    assert has_q, "Should load questions from CLI files"
    assert len(maker.question_manager.mcq_questions) == 3
    assert len(maker.question_manager.reasoned_mcq_questions) == 2
    assert len(maker.question_manager.objective_questions) == 2
    assert len(maker.question_manager.subjective_questions) == 2
    print("✓ Test 2: Questions loaded and selected from CLI args (MCQ + Reasoned MCQ + Obj + Subj)")

    # Generate PDF
    try:
        success = maker.generate_pdf()
        assert success, "PDF generation should succeed"
        assert os.path.exists("cli_test.pdf"), "cli_test.pdf should exist"
        print("✓ Test 3: CLI generated PDF successfully created")
    finally:
        if os.path.exists("cli_test.pdf"):
            os.unlink("cli_test.pdf")

    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("QuesPM Comprehensive Test Suite")
    print("=" * 60)

    try:
        test_question_models()
        test_csv_loaders()
        test_question_manager()
        test_pdf_generator()
        test_cli_argument_parsing()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
