"""
Standalone GPU-Accelerated PDF OCR Pipeline

A production-ready OCR pipeline that:
- Processes PDF files page-by-page with full OCR
- Extracts both native PDF text and OCR text separately
- Supports incremental processing and resume capability
- Provides CPU fallback when GPU is unavailable
- Preserves page boundaries and processing metadata
- Handles errors gracefully without stopping the entire job

Usage:
    python pdf_ocr_pipeline.py <pdf_path> [--dpi 300] [--force-gpu] [--resume]

Example:
    python pdf_ocr_pipeline.py data/input/test.pdf --dpi 300

GPU Requirements:
    - For ONNX Runtime GPU: pip install onnxruntime-gpu
    - For PyTorch GPU: pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
    - Configure RapidOCR backend via config file
"""

import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, asdict, field
from hashlib import sha256
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    import pypdfium2 as pdfium
except ImportError:
    print("ERROR: pypdfium2 is required but not installed.")
    print("Install with: pip install pypdfium2")
    sys.exit(1)

try:
    from rapidocr import RapidOCR
except ImportError:
    print("ERROR: rapidocr is required but not installed.")
    print("Install with: pip install rapidocr")
    sys.exit(1)

try:
    import numpy as np
except ImportError:
    print("ERROR: numpy is required but not installed.")
    print("Install with: pip install numpy")
    sys.exit(1)

from PIL import Image


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


@dataclass
class PageResult:
    """Result from processing a single PDF page."""
    page_number: int
    native_text: str
    ocr_text: str
    ocr_char_count: int
    processing_time_seconds: float
    status: str  # 'success', 'partial', 'failed'
    error: Optional[str] = None
    ocr_box_count: int = 0
    ocr_confidence: List[float] = field(default_factory=list)
    ocr_boxes: List[Any] = field(default_factory=list)
    blank_verified: bool = False
    limitations: List[str] = field(default_factory=list)


@dataclass
class ProcessingManifest:
    """Metadata about the OCR processing job."""
    input_file: str
    output_directory: str
    total_pages: int
    completed_pages: List[int]
    failed_pages: List[int]
    dpi: int
    backend: str
    gpu_enabled: bool
    start_time: str
    end_time: Optional[str] = None
    total_duration_seconds: Optional[float] = None
    partial_pages: List[int] = field(default_factory=list)
    version: str = 'ocr_v2'


class PDFOCRPipeline:
    """
    Standalone PDF-to-text OCR pipeline with GPU acceleration support.
    
    Design principles:
    - Unconditional OCR: Always run OCR on every page
    - Separate storage: Keep native PDF text and OCR text separate
    - Incremental saving: Save results after each page
    - Resume capability: Skip already-processed pages
    - Error isolation: Page failures don't stop the job
    - No interpretation: Extract text only, no descriptions or summaries
    """
    
    def __init__(
        self,
        dpi: int = 300,
        force_gpu: bool = False,
        verbose: bool = True
    ):
        """
        Initialize the OCR pipeline.
        
        Args:
            dpi: Resolution for PDF page rendering (default: 300)
            force_gpu: Require GPU backend or fail (default: False)
            verbose: Enable detailed logging (default: True)
        """
        self.dpi = dpi
        self.force_gpu = force_gpu
        self.verbose = verbose
        
        # Initialize OCR engine
        self.ocr_engine = None
        self.backend = "unknown"
        self.gpu_enabled = False
        
        self._initialize_ocr()
    
    def _initialize_ocr(self) -> None:
        """
        Initialize RapidOCR with best available backend.
        
        Priority:
        1. GPU backend (if available and requested)
        2. CPU backend (default fallback)
        
        Raises:
            RuntimeError: If force_gpu=True but GPU backend is unavailable
        """
        logger.info("Initializing OCR engine...")
        
        # Check for ONNX Runtime (most common backend)
        try:
            import onnxruntime as ort
            
            providers = ort.get_available_providers()
            has_cuda = 'CUDAExecutionProvider' in providers
            has_tensorrt = 'TensorrtExecutionProvider' in providers
            
            if has_cuda or has_tensorrt:
                logger.info(f"ONNX Runtime GPU providers available: {providers}")
                self.gpu_enabled = True
                self.backend = "onnxruntime-gpu"
            else:
                logger.info(f"ONNX Runtime CPU provider available")
                self.backend = "onnxruntime-cpu"
                
        except ImportError:
            logger.warning("ONNX Runtime not installed. Install with: pip install onnxruntime")
            logger.info("Attempting to use RapidOCR without explicit backend...")
            self.backend = "rapidocr-default"
        
        # Check if GPU is required but unavailable
        if self.force_gpu and not self.gpu_enabled:
            raise RuntimeError(
                "GPU backend required (--force-gpu) but GPU not available.\n"
                "Install GPU dependencies:\n"
                "  pip install onnxruntime-gpu  # For CUDA support\n"
                "  OR\n"
                "  pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121"
            )
        
        # Initialize RapidOCR
        try:
            # RapidOCR 3.9.2 accepts config_path and params
            # The engine will auto-detect available backend
            self.ocr_engine = RapidOCR()
            logger.info(f"✓ OCR engine initialized: {self.backend}")
            logger.info(f"  GPU enabled: {self.gpu_enabled}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OCR engine: {e}")
            if "onnxruntime is not installed" in str(e):
                logger.error("\nInstall ONNX Runtime:")
                logger.error("  CPU: pip install onnxruntime")
                logger.error("  GPU: pip install onnxruntime-gpu")
            raise
    
    def process_pdf(
        self,
        pdf_path: str,
        resume: bool = True
    ) -> ProcessingManifest:
        """
        Process an entire PDF file with OCR.
        
        Args:
            pdf_path: Path to input PDF file
            resume: Skip already-processed pages (default: True)
            
        Returns:
            ProcessingManifest with processing results
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        logger.info("=" * 80)
        logger.info(f"PDF OCR PIPELINE")
        logger.info("=" * 80)
        logger.info(f"Input: {pdf_path}")
        logger.info(f"DPI: {self.dpi}")
        logger.info(f"Backend: {self.backend}")
        logger.info(f"GPU: {'Yes' if self.gpu_enabled else 'No'}")
        logger.info(f"Resume: {'Yes' if resume else 'No'}")
        
        # Set up output directory
        output_dir = self._setup_output_directory(pdf_path)
        logger.info(f"Output: {output_dir}")
        
        # Load or create manifest
        manifest_path = output_dir / "manifest.json"
        manifest = self._load_or_create_manifest(
            manifest_path=manifest_path,
            pdf_path=str(pdf_path),
            output_dir=str(output_dir)
        )
        
        # Open PDF
        try:
            pdf = pdfium.PdfDocument(str(pdf_path))
            page_count = len(pdf)
            manifest.total_pages = page_count
            
            logger.info(f"Total pages: {page_count}")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"Failed to open PDF: {e}")
            raise
        
        # Process each page
        start_time = time.time()
        results: List[PageResult] = []
        
        for page_idx in range(page_count):
            page_number = page_idx + 1
            
            # Skip if already processed (resume mode)
            saved_page=output_dir/'pages'/f'page_{page_number:04d}.json'
            verified_saved=(saved_page.exists() and json.loads(saved_page.read_text(encoding='utf-8')).get('status')=='success')
            if resume and page_number in manifest.completed_pages and verified_saved:
                logger.info(f"[Page {page_number}/{page_count}] Skipping (already completed)")
                continue
            
            # Process page
            result=None
            try:
                result = self._process_page(
                    pdf=pdf,
                    page_idx=page_idx,
                    page_number=page_number,
                    total_pages=page_count,
                    output_dir=output_dir
                )
                
                results.append(result)
                
                # Update manifest
                # A retry replaces state, without accumulating duplicate completion.
                for bucket in (manifest.completed_pages,manifest.failed_pages,manifest.partial_pages):
                    if page_number in bucket:
                        bucket.remove(page_number)
                if result.status == "success":
                    manifest.completed_pages.append(page_number)
                elif result.status == 'partial':
                    manifest.partial_pages.append(page_number)
                else:
                    manifest.failed_pages.append(page_number)
                
                # Save progress incrementally
                self._save_page_result(result, output_dir)
                self._save_manifest(manifest, manifest_path)
                
            except Exception as e:
                logger.error(f"[Page {page_number}] Unexpected error: {e}")
                for bucket in (manifest.completed_pages,manifest.failed_pages,manifest.partial_pages):
                    if page_number in bucket:
                        bucket.remove(page_number)
                manifest.failed_pages.append(page_number)
                
                # Save error result
                error_result = PageResult(
                    page_number=page_number,
                    native_text=result.native_text if result else '',
                    ocr_text=result.ocr_text if result else '',
                    ocr_char_count=result.ocr_char_count if result else 0,
                    processing_time_seconds=0.0,
                    status="failed",
                    error=str(e),
                    ocr_confidence=result.ocr_confidence if result else [],
                    ocr_boxes=result.ocr_boxes if result else [],
                    ocr_box_count=result.ocr_box_count if result else 0,
                    blank_verified=result.blank_verified if result else False,
                    limitations=['Page or artifact persistence failed; any extracted content retained']
                )
                results.append(error_result)
                self._save_page_result(error_result, output_dir)
        
        # Close PDF
        pdf.close()
        
        # Finalize manifest
        end_time = time.time()
        manifest.end_time = datetime.now().isoformat()
        manifest.total_duration_seconds = end_time - start_time
        self._save_manifest(manifest, manifest_path)
        
        # Generate combined outputs
        self._generate_combined_outputs(output_dir, manifest)
        
        # Summary
        logger.info("=" * 80)
        logger.info("PROCESSING COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total pages: {manifest.total_pages}")
        logger.info(f"Completed: {len(manifest.completed_pages)}")
        logger.info(f"Failed: {len(manifest.failed_pages)}")
        logger.info(f"Duration: {manifest.total_duration_seconds:.2f}s")
        logger.info(f"Output directory: {output_dir}")
        
        return manifest
    
    def _process_page(
        self,
        pdf: Any,
        page_idx: int,
        page_number: int,
        total_pages: int,
        output_dir: Path
    ) -> PageResult:
        """
        Process a single PDF page.
        
        Args:
            pdf: pypdfium2 PdfDocument
            page_idx: Zero-based page index
            page_number: One-based page number
            total_pages: Total number of pages
            output_dir: Output directory path
            
        Returns:
            PageResult with processing outcome
        """
        logger.info(f"[Page {page_number}/{total_pages}] Processing...")
        page_start = time.time()
        native_text=''
        page=None
        
        try:
            # Load page
            page = pdf[page_idx]
            
            # Extract native PDF text
            native_text = self._extract_native_text(page)
            native_char_count = len(native_text.strip())
            
            logger.info(f"[Page {page_number}] Native text: {native_char_count} chars")
            
            # Render page to image
            image = self._render_page(page, self.dpi)
            
            # Run OCR on full page image
            ocr_text, ocr_boxes = self._run_ocr(image)
            ocr_char_count = len(ocr_text.strip())
            
            logger.info(f"[Page {page_number}] OCR text: {ocr_char_count} chars ({len(ocr_boxes)} boxes)")
            
            # Determine status
            # Only a demonstrably uniform rendered page can be called blank.
            pixels=np.asarray(image.convert('L'))
            blank_verified=(not native_text.strip() and not ocr_text.strip() and
                            pixels.size>0 and float(pixels.min())==255)
            if ocr_char_count > 0:
                status = "success"
            elif native_char_count > 0:
                status = "partial"  # Has native text but OCR failed
            elif blank_verified:
                status = 'success'
            else:
                status = 'partial'  # Visible content without recognized text is unresolved.
            
            page_end = time.time()
            duration = page_end - page_start
            
            logger.info(f"[Page {page_number}] ✓ Completed in {duration:.2f}s")
            
            return PageResult(
                page_number=page_number,
                native_text=native_text,
                ocr_text=ocr_text,
                ocr_char_count=ocr_char_count,
                processing_time_seconds=duration,
                status=status,
                ocr_box_count=len(ocr_boxes),ocr_boxes=np.asarray(ocr_boxes).tolist(),
                ocr_confidence=getattr(self,'_last_ocr_confidence',[]),
                blank_verified=blank_verified,
                limitations=[] if status=='success' else ['OCR produced no text; page requires review/recovery']
            )
            
        except Exception as e:
            page_end = time.time()
            duration = page_end - page_start
            
            logger.error(f"[Page {page_number}] ✗ Failed: {e}")
            
            return PageResult(
                page_number=page_number,
                native_text=native_text,
                ocr_text="",
                ocr_char_count=0,
                processing_time_seconds=duration,
                status='partial' if native_text else 'failed',
                error=str(e),limitations=['Page processing failed; retained native text when available']
            )
        finally:
            if page is not None and hasattr(page,'close'):
                page.close()
    
    def _extract_native_text(self, page: Any) -> str:
        """
        Extract native text from a PDF page using pypdfium2.
        
        Args:
            page: pypdfium2 PdfPage
            
        Returns:
            Extracted text string
        """
        try:
            textpage = page.get_textpage()
            text = textpage.get_text_range()
            return text or ""
        except Exception as e:
            logger.warning(f"Failed to extract native text: {e}")
            raise RuntimeError(f'Native text extraction failed: {e}') from e
    
    def _render_page(self, page: Any, dpi: int) -> Image.Image:
        """
        Render PDF page to PIL Image.
        
        Args:
            page: pypdfium2 PdfPage
            dpi: Target resolution
            
        Returns:
            PIL Image
        """
        # Calculate scale factor from DPI
        # pypdfium2 uses 72 DPI as base
        scale = dpi / 72.0
        
        # Render page
        bitmap = page.render(
            scale=scale,
            rotation=0,
        )
        
        # Convert to PIL Image
        pil_image = bitmap.to_pil()
        
        return pil_image
    
    def _run_ocr(self, image: Image.Image) -> tuple[str, List[Any]]:
        """
        Run OCR on an image.
        
        Args:
            image: PIL Image
            
        Returns:
            Tuple of (extracted_text, bounding_boxes)
        """
        try:
            # Convert PIL Image to numpy array (RGB)
            img_array = np.array(image)
            
            # Run RapidOCR
            # Returns: RapidOCROutput object with attributes:
            #   - boxes: bounding boxes array
            #   - txts: tuple of recognized texts
            #   - scores: confidence scores
            # or None if no text detected
            result = self.ocr_engine(img_array)
            self._last_ocr_confidence=[]
            
            if result is None:
                return "", []
            
            # Extract text results
            boxes = getattr(result, 'boxes', None)
            txts = getattr(result, 'txts', None)
            scores=getattr(result,'scores',None)
            self._last_ocr_confidence=[float(s) for s in scores] if scores is not None else []
            
            if txts is None or len(txts) == 0:
                return "", []
            
            # txts is a tuple of strings
            # Combine texts with newlines
            combined_text = "\n".join(str(text) for text in txts if text)
            
            return combined_text, boxes if boxes is not None else []
            
        except Exception as e:
            logger.error(f"OCR failed: {e}")
            raise RuntimeError(f'OCR failed: {e}') from e
    
    def _setup_output_directory(self, pdf_path: Path) -> Path:
        """
        Create output directory for OCR results.
        
        Args:
            pdf_path: Input PDF file path
            
        Returns:
            Path to output directory
        """
        pdf_name = pdf_path.stem
        # Never overwrite the historical unversioned OCR experiment.
        source_hash=sha256(pdf_path.read_bytes()).hexdigest()[:16]
        output_dir = Path('data/output/pdf_ocr_v2') / f'{pdf_name}_{source_hash}_{self.dpi}dpi'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create pages subdirectory
        (output_dir / "pages").mkdir(exist_ok=True)
        
        return output_dir
    
    def _load_or_create_manifest(
        self,
        manifest_path: Path,
        pdf_path: str,
        output_dir: str
    ) -> ProcessingManifest:
        """
        Load existing manifest or create a new one.
        
        Args:
            manifest_path: Path to manifest file
            pdf_path: Input PDF path
            output_dir: Output directory path
            
        Returns:
            ProcessingManifest
        """
        if manifest_path.exists():
            try:
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                manifest = ProcessingManifest(
                    input_file=data['input_file'],
                    output_directory=data['output_directory'],
                    total_pages=data['total_pages'],
                    completed_pages=[n for n in data['completed_pages'] if n not in data.get('partial_pages',[])],
                    failed_pages=data['failed_pages'],
                    dpi=data['dpi'],
                    backend=data['backend'],
                    gpu_enabled=data['gpu_enabled'],
                    start_time=data['start_time'],
                    end_time=data.get('end_time'),
                    total_duration_seconds=data.get('total_duration_seconds'),
                    partial_pages=data.get('partial_pages',[])
                )
                
                logger.info(f"Loaded existing manifest: {len(manifest.completed_pages)} pages completed")
                return manifest
                
            except Exception as e:
                raise ValueError(f'OCR manifest is unreadable; preserve it for investigation: {manifest_path}') from e
        
        # Create new manifest
        return ProcessingManifest(
            input_file=pdf_path,
            output_directory=output_dir,
            total_pages=0,
            completed_pages=[],
            failed_pages=[],
            dpi=self.dpi,
            backend=self.backend,
            gpu_enabled=self.gpu_enabled,
            start_time=datetime.now().isoformat()
        )
    
    def _save_manifest(self, manifest: ProcessingManifest, manifest_path: Path) -> None:
        """Save manifest to JSON file."""
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(manifest), f, indent=2, ensure_ascii=False)
    
    def _save_page_result(self, result: PageResult, output_dir: Path) -> None:
        """
        Save individual page result to disk.
        
        Args:
            result: PageResult to save
            output_dir: Output directory path
        """
        page_num_str = f"{result.page_number:04d}"
        
        # Save page text file
        page_txt_path = output_dir / "pages" / f"page_{page_num_str}.txt"
        with open(page_txt_path, 'w', encoding='utf-8') as f:
            f.write(f"=== PAGE {result.page_number} ===\n\n")
            f.write(f"--- Native PDF Text ({len(result.native_text)} chars) ---\n")
            f.write(result.native_text)
            f.write(f"\n\n--- OCR Text ({len(result.ocr_text)} chars) ---\n")
            f.write(result.ocr_text)
        
        # Save page JSON
        page_json_path = output_dir / "pages" / f"page_{page_num_str}.json"
        if page_json_path.exists():
            previous=page_json_path.read_bytes()
            history=output_dir/'pages/history'
            history.mkdir(exist_ok=True)
            old=history/f'page_{page_num_str}_{sha256(previous).hexdigest()}.json'
            if not old.exists():
                with old.open('xb') as f:
                    f.write(previous)
        with open(page_json_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(result), f, indent=2, ensure_ascii=False)
    
    def _generate_combined_outputs(self, output_dir: Path, manifest: ProcessingManifest) -> None:
        """
        Generate combined output files from individual page results.
        
        Args:
            output_dir: Output directory path
            manifest: Processing manifest
        """
        logger.info("Generating combined outputs...")
        
        # Collect all page results in order
        all_results: List[PageResult] = []
        
        for page_num in range(1, manifest.total_pages + 1):
            page_json_path = output_dir / "pages" / f"page_{page_num:04d}.json"
            
            if page_json_path.exists():
                with open(page_json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    result = PageResult(**data)
                    all_results.append(result)
            else:
                # Missing page
                all_results.append(PageResult(
                    page_number=page_num,
                    native_text="",
                    ocr_text="",
                    ocr_char_count=0,
                    processing_time_seconds=0.0,
                    status="missing",
                    error="Page not processed"
                ))
        
        # Generate full_text.txt (OCR only)
        full_text_path = output_dir / "full_text.txt"
        with open(full_text_path, 'w', encoding='utf-8') as f:
            for result in all_results:
                f.write(f"=== PAGE {result.page_number} ===\n\n")
                f.write(result.ocr_text)
                f.write("\n\n")
        
        logger.info(f"✓ Saved: {full_text_path}")
        
        # Generate full_text.md (structured)
        full_md_path = output_dir / "full_text.md"
        with open(full_md_path, 'w', encoding='utf-8') as f:
            f.write(f"# OCR Results\n\n")
            f.write(f"**Input**: {manifest.input_file}\n\n")
            f.write(f"**Total Pages**: {manifest.total_pages}\n\n")
            f.write(f"**Backend**: {manifest.backend}\n\n")
            f.write(f"**GPU Enabled**: {manifest.gpu_enabled}\n\n")
            f.write(f"---\n\n")
            
            for result in all_results:
                f.write(f"## Page {result.page_number}\n\n")
                
                if result.status == "success":
                    f.write(f"**Status**: ✓ Success\n\n")
                elif result.status == "partial":
                    f.write(f"**Status**: ⚠ Partial (OCR failed, native text available)\n\n")
                elif result.status == "failed":
                    f.write(f"**Status**: ✗ Failed\n\n")
                    f.write(f"**Error**: {result.error}\n\n")
                else:
                    f.write(f"**Status**: ? {result.status}\n\n")
                
                f.write(f"**OCR Characters**: {result.ocr_char_count}\n\n")
                f.write(f"**Processing Time**: {result.processing_time_seconds:.2f}s\n\n")
                
                if result.ocr_text:
                    f.write("### OCR Text\n\n")
                    f.write("```\n")
                    f.write(result.ocr_text)
                    f.write("\n```\n\n")
                
                if result.native_text and result.native_text != result.ocr_text:
                    f.write("### Native PDF Text\n\n")
                    f.write("```\n")
                    f.write(result.native_text)
                    f.write("\n```\n\n")
                
                f.write("---\n\n")
        
        logger.info(f"✓ Saved: {full_md_path}")
        
        # Generate full_text.json (complete data)
        full_json_path = output_dir / "full_text.json"
        with open(full_json_path, 'w', encoding='utf-8') as f:
            output_data = {
                "manifest": asdict(manifest),
                "pages": [asdict(r) for r in all_results]
            }
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Saved: {full_json_path}")


def main():
    """Command-line interface for PDF OCR pipeline."""
    parser = argparse.ArgumentParser(
        description="Standalone GPU-Accelerated PDF OCR Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pdf_ocr_pipeline.py data/input/test.pdf
  python pdf_ocr_pipeline.py document.pdf --dpi 300
  python pdf_ocr_pipeline.py scan.pdf --force-gpu
  python pdf_ocr_pipeline.py large.pdf --resume

GPU Setup:
  For ONNX Runtime GPU support:
    pip install onnxruntime-gpu
  
  For PyTorch GPU support:
    pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
        """
    )
    
    parser.add_argument(
        "pdf_path",
        help="Path to input PDF file"
    )
    
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="DPI for PDF page rendering (default: 300)"
    )
    
    parser.add_argument(
        "--force-gpu",
        action="store_true",
        help="Require GPU backend or fail"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        default=True,
        help="Resume from existing progress (default: True)"
    )
    
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Start fresh, ignore existing progress"
    )
    
    args = parser.parse_args()
    
    # Determine resume mode
    resume = args.resume and not args.no_resume
    
    try:
        # Initialize pipeline
        pipeline = PDFOCRPipeline(
            dpi=args.dpi,
            force_gpu=args.force_gpu,
            verbose=True
        )
        
        # Process PDF
        manifest = pipeline.process_pdf(
            pdf_path=args.pdf_path,
            resume=resume
        )
        
        # Success
        logger.info("✓ Pipeline completed successfully")
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠ Pipeline interrupted by user")
        logger.info("Progress has been saved. Use --resume to continue.")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"✗ Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
