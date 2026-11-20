"""
Diagnostic script to identify where ingestion stalls.

Measures timing for each step of the Docling parsing process.
"""

import time
from pathlib import Path
from docling.document_converter import DocumentConverter

def time_operation(name, func):
    """Time a function and print results"""
    print(f"\n{'='*60}")
    print(f"TIMING: {name}")
    print('='*60)
    start = time.time()
    try:
        result = func()
        elapsed = time.time() - start
        print(f"✓ Completed in {elapsed:.2f} seconds")
        return result, elapsed, None
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ Failed after {elapsed:.2f} seconds: {e}")
        return None, elapsed, str(e)

def main():
    pdf_path = "data/input/test.pdf"
    
    print("="*60)
    print("INGESTION DIAGNOSTIC")
    print("="*60)
    print(f"PDF: {pdf_path}")
    print(f"Exists: {Path(pdf_path).exists()}")
    print(f"Size: {Path(pdf_path).stat().st_size if Path(pdf_path).exists() else 'N/A'} bytes")
    
    # Step 1: Create converter
    converter, t1, e1 = time_operation(
        "Create DocumentConverter",
        lambda: DocumentConverter()
    )
    
    if e1:
        print(f"\n✗ Failed at converter creation")
        return
    
    # Step 2: Convert document
    print(f"\nStarting document conversion...")
    print(f"This may take a while with OCR-enabled parsing...")
    
    result, t2, e2 = time_operation(
        "Convert document (Docling)",
        lambda: converter.convert(str(pdf_path))
    )
    
    if e2:
        print(f"\n✗ Failed at document conversion")
        return
    
    doc = result.document
    
    # Step 3: Access document properties
    _, t3, e3 = time_operation(
        "Access doc.num_pages()",
        lambda: doc.num_pages()
    )
    
    _, t4, e4 = time_operation(
        "Access doc.body.children",
        lambda: list(doc.body.children)
    )
    
    # Step 4: Iterate and resolve children
    def iterate_children():
        count = 0
        for child in doc.body.children:
            item = child.resolve(doc)
            count += 1
        return count
    
    count, t5, e5 = time_operation(
        "Iterate and resolve all children",
        iterate_children
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("TIMING SUMMARY")
    print('='*60)
    print(f"1. Create converter:      {t1:.2f}s")
    print(f"2. Convert document:      {t2:.2f}s  ← LIKELY BOTTLENECK")
    print(f"3. Get page count:        {t3:.2f}s")
    print(f"4. Get children list:     {t4:.2f}s")
    print(f"5. Resolve {count} children: {t5:.2f}s")
    print(f"\nTOTAL:                    {t1+t2+t3+t4+t5:.2f}s")
    print('='*60)
    
    if t2 > 10:
        print(f"\n⚠ WARNING: Document conversion took {t2:.2f}s")
        print(f"  This is the Docling OCR pipeline running")
        print(f"  On Windows, this can be very slow or crash")
    
    print(f"\n✓ Diagnostic complete")
    print(f"  Document has {doc.num_pages()} pages")
    print(f"  Document has {count} items")

if __name__ == "__main__":
    main()
