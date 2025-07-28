import os
import logging
from pathlib import Path
from typing import Optional
import mimetypes

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Process various document formats and extract text content"""
    
    def __init__(self):
        self.supported_formats = {
            '.txt': self._read_text,
            '.docx': self._read_docx,
            '.doc': self._read_doc,
            '.pdf': self._read_pdf,
            '.rtf': self._read_rtf,
            '.odt': self._read_odt,
            '.html': self._read_html,
            '.htm': self._read_html,
            '.xml': self._read_text,
            '.json': self._read_text,
            '.csv': self._read_text,
            '.md': self._read_text,
            '.markdown': self._read_text,
        }
    
    def extract_text(self, file_path: str) -> str:
        """Extract text from various document formats"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Get file extension
        extension = file_path.suffix.lower()
        
        # Try to process based on extension
        if extension in self.supported_formats:
            try:
                return self.supported_formats[extension](file_path)
            except Exception as e:
                logger.warning(f"Failed to process {extension} file with specific handler: {e}")
        
        # Fallback to generic text reading
        return self._read_generic(file_path)
    
    def _read_text(self, file_path: Path) -> str:
        """Read plain text files with multiple encoding attempts"""
        # List of common encodings to try
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1', 'ascii']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                    # If successful, return the content
                    return content
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # If all encodings fail, try with errors='ignore'
        logger.warning(f"Could not detect encoding for {file_path}, reading with errors ignored")
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return f"[Error reading file: {file_path.name}]"
    
    def _read_docx(self, file_path: Path) -> str:
        """Read DOCX files"""
        try:
            import docx
        except ImportError:
            logger.warning("python-docx not installed. Install with: pip install python-docx")
            return self._read_generic(file_path)
        
        try:
            doc = docx.Document(str(file_path))
            full_text = []
            for paragraph in doc.paragraphs:
                full_text.append(paragraph.text)
            return '\n'.join(full_text)
        except Exception as e:
            logger.error(f"Failed to read DOCX file: {e}")
            return self._read_generic(file_path)
    
    def _read_doc(self, file_path: Path) -> str:
        """Read DOC files (legacy Word format)"""
        try:
            import docx
            # Try reading as DOCX first (some .doc files are actually .docx)
            return self._read_docx(file_path)
        except:
            logger.warning("Cannot read legacy .doc files. Consider converting to .docx")
            return self._read_generic(file_path)
    
    def _read_pdf(self, file_path: Path) -> str:
        """Read PDF files"""
        try:
            import PyPDF2
        except ImportError:
            logger.warning("PyPDF2 not installed. Install with: pip install PyPDF2")
            return self._read_generic(file_path)
        
        try:
            text = []
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text.append(page.extract_text())
            return '\n'.join(text)
        except Exception as e:
            logger.error(f"Failed to read PDF file: {e}")
            # Try alternative PDF library
            try:
                import pdfplumber
                text = []
                with pdfplumber.open(str(file_path)) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text.append(page_text)
                return '\n'.join(text)
            except:
                return self._read_generic(file_path)
    
    def _read_rtf(self, file_path: Path) -> str:
        """Read RTF files"""
        try:
            import striprtf
        except ImportError:
            logger.warning("striprtf not installed. Install with: pip install striprtf")
            return self._read_generic(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                rtf_content = f.read()
            return striprtf.rtf_to_text(rtf_content)
        except Exception as e:
            logger.error(f"Failed to read RTF file: {e}")
            return self._read_generic(file_path)
    
    def _read_odt(self, file_path: Path) -> str:
        """Read ODT (OpenDocument Text) files"""
        try:
            from odf import text, teletype
            from odf.opendocument import load
        except ImportError:
            logger.warning("odfpy not installed. Install with: pip install odfpy")
            return self._read_generic(file_path)
        
        try:
            doc = load(str(file_path))
            paragraphs = doc.getElementsByType(text.P)
            return '\n'.join([teletype.extractText(p) for p in paragraphs])
        except Exception as e:
            logger.error(f"Failed to read ODT file: {e}")
            return self._read_generic(file_path)
    
    def _read_html(self, file_path: Path) -> str:
        """Read HTML files and extract text"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            logger.warning("BeautifulSoup not installed. Install with: pip install beautifulsoup4")
            return self._read_text(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            return soup.get_text(separator='\n', strip=True)
        except Exception as e:
            logger.error(f"Failed to parse HTML file: {e}")
            return self._read_text(file_path)
    
    def _read_generic(self, file_path: Path) -> str:
        """Generic fallback for reading files"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        if mime_type and mime_type.startswith('text/'):
            return self._read_text(file_path)
        else:
            # For binary files, just return a placeholder
            logger.warning(f"Cannot extract text from binary file: {file_path}")
            return f"[Binary file: {file_path.name}]"