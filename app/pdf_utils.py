import os
from typing import List, Tuple


def _ensure_parent_dir(path: str) -> None:
    parent_dir = os.path.dirname(os.path.abspath(path))
    if parent_dir and not os.path.exists(parent_dir):
        os.makedirs(parent_dir, exist_ok=True)


def generate_pdf_from_html(html_content: str, output_pdf_path: str) -> Tuple[bool, str, List[str]]:
    """
    Attempt to generate a PDF from HTML using multiple backends.

    Returns a tuple of:
    - success: bool
    - output_path: str (PDF path on success, otherwise a fallback path to an HTML file)
    - attempts_log: List[str] describing attempts and errors for debugging
    """

    attempts_log: List[str] = []
    _ensure_parent_dir(output_pdf_path)

    # 1) Try pdfkit (wkhtmltopdf)
    try:
        import pdfkit  # type: ignore

        attempts_log.append("Trying pdfkit (wkhtmltopdf)...")
        try:
            config = pdfkit.configuration()
        except Exception as config_err:  # wkhtmltopdf missing or not found
            attempts_log.append(f"pdfkit configuration error: {config_err}")
            config = None

        options = {
            "quiet": "",
            "enable-local-file-access": None,
        }

        success = pdfkit.from_string(html_content, output_pdf_path, configuration=config, options=options)
        if success:
            attempts_log.append(f"pdfkit succeeded: {output_pdf_path}")
            return True, output_pdf_path, attempts_log
        else:
            attempts_log.append("pdfkit returned False (unknown reason)")
    except Exception as e:
        attempts_log.append(f"pdfkit failed: {e}")

    # 2) Try WeasyPrint
    try:
        attempts_log.append("Trying WeasyPrint...")
        from weasyprint import HTML  # type: ignore

        HTML(string=html_content).write_pdf(output_pdf_path)
        attempts_log.append(f"WeasyPrint succeeded: {output_pdf_path}")
        return True, output_pdf_path, attempts_log
    except Exception as e:
        attempts_log.append(f"WeasyPrint failed: {e}")

    # 3) Try xhtml2pdf (pisa)
    try:
        attempts_log.append("Trying xhtml2pdf (pisa)...")
        from xhtml2pdf import pisa  # type: ignore

        with open(output_pdf_path, "wb") as output_stream:
            result = pisa.CreatePDF(src=html_content, dest=output_stream)
        if not result.err:
            attempts_log.append(f"xhtml2pdf succeeded: {output_pdf_path}")
            return True, output_pdf_path, attempts_log
        else:
            attempts_log.append(f"xhtml2pdf reported errors (err={result.err})")
    except Exception as e:
        attempts_log.append(f"xhtml2pdf failed: {e}")

    # 4) Fallback: write HTML to a .html file for partial report
    try:
        html_fallback_path = (
            os.path.splitext(output_pdf_path)[0] + ".html"
        )
        with open(html_fallback_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        attempts_log.append(
            f"All PDF backends failed. Wrote HTML fallback: {html_fallback_path}"
        )
        return False, html_fallback_path, attempts_log
    except Exception as e:
        # As a last resort, return the intended PDF path with an error note
        attempts_log.append(f"Failed to write HTML fallback: {e}")
        return False, output_pdf_path, attempts_log

