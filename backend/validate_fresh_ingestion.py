"""
Validate fresh PDF ingestion from input file through source-unit generation.

This script:
1. Ingests a PDF from data/input
2. Generates source units during this run
3. Verifies the output is newly created
4. Reports document ID and source-unit count
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import shutil

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.ingestion.docling_parser import DoclingParser


def validate_fresh_ingestion(pdf_path: Path, output_dir: Path):
    """
    Validate fresh ingestion of a PDF file.
    
    Args:
        pdf_path: Path to input PDF
        output_dir: Directory for output artifacts
        
    Returns:
        True if ingestion succeeds, False otherwise
    """
    
    print("=" * 80)
    print("FRESH PDF INGESTION VALIDATION")
    print("=" * 80)
    
    # Check input exists
    if not pdf_path.exists():
        print(f"ERROR: Input PDF not found: {pdf_path}")
        return False
    
    print(f"\n1. Input PDF: {pdf_path}")
    print(f"   Size: {pdf_path.stat().st_size:,} bytes")
    print(f"   Modified: {datetime.fromtimestamp(pdf_path.stat().st_mtime)}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "source_units.json"
    
    # Remove old output if exists (to ensure fresh generation)
    if output_file.exists():
        print(f"\n2. Removing old output: {output_file}")
        backup_file = output_dir / f"source_units_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy(output_file, backup_file)
        print(f"   Backed up to: {backup_file}")
        output_file.unlink()
    else:
        print(f"\n2. No previous output found (fresh run)")
    
    # Run ingestion
    print(f"\n3. Running Docling ingestion...")
    print(f"   Parser: DoclingParser")
    print(f"   Input: {pdf_path}")
    
    try:
        start_time = datetime.now()
        
        # Initialize parser
        parser = DoclingParser()
        
        # Parse PDF
        source_doc = parser.parse(str(pdf_path))
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n4. Ingestion completed in {duration:.2f} seconds")
        print(f"   Document ID: {source_doc.document_id}")
        print(f"   Filename: {source_doc.filename}")
        print(f"   Page count: {source_doc.page_count}")
        print(f"   Source units: {len(source_doc.source_units)}")
        
        # Validate output
        if len(source_doc.source_units) == 0:
            print(f"\nERROR: No source units generated!")
            return False
        
        # Save output
        print(f"\n5. Saving output to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(source_doc.model_dump(), f, indent=2, ensure_ascii=False)
        
        # Verify file was written
        if not output_file.exists():
            print(f"\nERROR: Output file was not created!")
            return False
        
        output_size = output_file.stat().st_size
        output_mtime = datetime.fromtimestamp(output_file.stat().st_mtime)
        
        print(f"\n6. Output verified:")
        print(f"   File: {output_file}")
        print(f"   Size: {output_size:,} bytes")
        print(f"   Created: {output_mtime}")
        print(f"   Fresh: {(datetime.now() - output_mtime).total_seconds() < 10} (within 10 seconds)")
        
        # Sample source units
        print(f"\n7. Sample source units (first 3):")
        for i, unit in enumerate(source_doc.source_units[:3]):
            print(f"   [{i+1}] {unit.source_id} - {unit.type} - page {unit.page}")
            if unit.text:
                preview = unit.text[:60].replace('\n', ' ')
                print(f"       Text: {preview}...")
        
        print("\n" + "=" * 80)
        print("✓ FRESH INGESTION VALIDATION PASSED")
        print("=" * 80)
        print(f"\nSummary:")
        print(f"  • PDF successfully ingested from {pdf_path}")
        print(f"  • Generated {len(source_doc.source_units)} source units")
        print(f"  • Output written to {output_file}")
        print(f"  • Document ID: {source_doc.document_id}")
        print(f"  • Processing time: {duration:.2f} seconds")
        
        return True
        
    except Exception as e:
        print(f"\nERROR during ingestion:")
        print(f"  Exception type: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        
        import traceback
        print(f"\nTraceback:")
        traceback.print_exc()
        
        return False


def main():
    """Main entry point."""
    
    # Use test.pdf (smaller, faster)
    pdf_path = Path("data/input/test.pdf")
    output_dir = Path("data/output/fresh_ingestion_test")
    
    success = validate_fresh_ingestion(pdf_path, output_dir)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
