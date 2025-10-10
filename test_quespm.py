#!/usr/bin/env python3
"""
Comprehensive test suite for quespm.py
Tests all major functionality
"""

import sys
import os
import tempfile

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quespm import (
    QuestionManager, 
    PDFGenerator, 
    QuestionPaperMaker,
    QuestionError,
    PDFGenerationError
)

def test_question_manager():
    """Test QuestionManager class"""
    print("\n" + "=" * 60)
    print("Testing QuestionManager")
    print("=" * 60)
    
    qm = QuestionManager()
    
    # Test 1: Random selection
    questions = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    selected = qm.select_random_questions(questions, 3)
    assert len(selected) == 3, "Should select 3 questions"
    assert len(set(selected)) == 3, "Should select unique questions"
    print("✓ Test 1: Random selection works")
    
    # Test 2: Error on too many questions
    try:
        qm.select_random_questions(questions, 10)
        assert False, "Should raise error"
    except QuestionError:
        print("✓ Test 2: Correctly raises error for invalid count")
    
    # Test 3: Add questions
    qm.add_short_answer_questions(["Q1", "Q2"])
    qm.add_long_answer_questions(["LQ1"])
    all_q = qm.get_all_questions()
    assert len(all_q["Short answer type"]) == 2, "Should have 2 short questions"
    assert len(all_q["Long answer type"]) == 1, "Should have 1 long question"
    print("✓ Test 3: Add questions works")
    
    # Test 4: Load from file
    if os.path.exists("sample_short_questions.txt"):
        loaded = qm.load_questions_from_file("sample_short_questions.txt")
        assert len(loaded) > 0, "Should load questions from file"
        print(f"✓ Test 4: Loaded {len(loaded)} questions from file")
    
    print("\n✓ All QuestionManager tests passed!")
    return True

def test_pdf_generator():
    """Test PDFGenerator class"""
    print("\n" + "=" * 60)
    print("Testing PDFGenerator")
    print("=" * 60)
    
    config = {
        'title': 'Test Paper',
        'subtitle': 'Test Exam',
        'marks': 100,
        'time': 180,
        'subject': 'Testing',
        'logo_path': None
    }
    
    pdf_gen = PDFGenerator(config)
    print("✓ Test 1: PDFGenerator initialized")
    
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        tmp_path = tmp.name
    
    try:
        pdf_gen.initialize_canvas(tmp_path)
        print("✓ Test 2: Canvas initialized")
        
        pdf_gen.draw_header()
        print("✓ Test 3: Header drawn")
        
        questions = {
            "Short answer type": ["Q1", "Q2"],
            "Long answer type": ["LQ1"]
        }
        pdf_gen.draw_questions(questions)
        print("✓ Test 4: Questions drawn")
        
        pdf_gen.save()
        print("✓ Test 5: PDF saved")
        
        # Verify file exists and has content
        assert os.path.exists(tmp_path), "PDF file should exist"
        assert os.path.getsize(tmp_path) > 0, "PDF should have content"
        print(f"✓ Test 6: PDF file created ({os.path.getsize(tmp_path)} bytes)")
        
    finally:
        # Clean up
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    
    print("\n✓ All PDFGenerator tests passed!")
    return True

def test_integration():
    """Test complete workflow"""
    print("\n" + "=" * 60)
    print("Testing Complete Workflow")
    print("=" * 60)
    
    maker = QuestionPaperMaker()
    
    # Set config
    maker.config = {
        'filename': 'test_integration.pdf',
        'title': 'Integration Test',
        'subtitle': 'Test Exam',
        'marks': 100,
        'time': 180,
        'subject': 'Testing',
        'logo_path': None
    }
    print("✓ Test 1: Configuration set")
    
    # Add questions
    maker.question_manager.add_short_answer_questions([
        "Test question 1",
        "Test question 2"
    ])
    maker.question_manager.add_long_answer_questions([
        "Long test question 1"
    ])
    print("✓ Test 2: Questions added")
    
    # Generate PDF
    try:
        success = maker.generate_pdf()
        assert success, "PDF generation should succeed"
        print("✓ Test 3: PDF generated")
        
        # Verify file
        assert os.path.exists('test_integration.pdf'), "PDF should exist"
        print("✓ Test 4: PDF file exists")
        
    finally:
        # Clean up
        if os.path.exists('test_integration.pdf'):
            os.unlink('test_integration.pdf')
    
    print("\n✓ All integration tests passed!")
    return True

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("QuesPM Test Suite")
    print("=" * 60)
    
    try:
        test_question_manager()
        test_pdf_generator()
        test_integration()
        
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
