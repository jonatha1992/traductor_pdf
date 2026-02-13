
import fitz
import os
from translator.pdf_layout import replace_text_in_page

class MockTranslator:
    def translate(self, text):
        # Return a very long string to force overflow
        return "This is a very long translated text that should definitely not fit in the original small box and would cause overflow if not handled correctly by the new logic. " * 5

def create_test_pdf(filename):
    doc = fitz.open()
    page = doc.new_page()
    # Insert a small text box near the right edge
    rect = fitz.Rect(500, 100, 550, 150) # 50 width
    page.insert_textbox(rect, "Short text", fontsize=12)
    doc.save(filename)
    doc.close()

def test_overflow():
    input_pdf = "overflow_test_input.pdf"
    output_pdf = "overflow_test_output.pdf"
    
    create_test_pdf(input_pdf)
    
    translator = MockTranslator()
    
    doc = fitz.open(input_pdf)
    out_doc = fitz.open()
    out_doc.insert_pdf(doc)
    
    page = doc[0]
    out_page = out_doc[0]
    
    print("Running replacement...")
    replace_text_in_page(page, out_page, translator)
    
    out_doc.save(output_pdf)
    print(f"Saved {output_pdf}")
    
    # Verify content
    # We can't easily check visual overflow, but we can check if the script crashed
    # and we can inspect the text in the output page to see if it's all there (or truncated/wrapped)
    # and if it's within the page bounds.
    
    out_doc = fitz.open(output_pdf)
    page = out_doc[0]
    # Get all text blocks
    blocks = page.get_text("dict")["blocks"]
    for b in blocks:
        for l in b["lines"]:
            for s in l["spans"]:
                # Check if any character is outside the page width (approx 595)
                bbox = fitz.Rect(s["bbox"])
                if bbox.x1 > 600: # Page width is usually 595
                    print(f"FAILURE: Text overflow detected! bbox: {bbox}")
                    return False
                print(f"Text span: '{s['text']}' bbox: {bbox}")
                
    print("SUCCESS: No overflow detected.")
    return True

if __name__ == "__main__":
    try:
        if test_overflow():
            print("Test PASSED")
        else:
            print("Test FAILED")
    except Exception as e:
        print(f"Test CRASHED: {e}")
        import traceback
        traceback.print_exc()
