from pathlib import Path

pdf_path = Path('public/sample-prospectus.pdf')
pdf_content = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n4 0 obj\n<< /Length 98 >>\nstream\nBT /F1 24 Tf 72 720 Td (Kulima OS Prospectus Sample) Tj ET\nBT /F1 12 Tf 72 680 Td (This document is a demo placeholder.) Tj ET\nendstream\nendobj\n5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\nxref\n0 6\n0000000000 65535 f \n0000000010 00000 n \n0000000060 00000 n \n0000000110 00000 n \n0000000220 00000 n \n0000000320 00000 n \ntrailer\n<< /Root 1 0 R /Size 6 >>\nstartxref\n410\n%%EOF\n"
pdf_path.parent.mkdir(parents=True, exist_ok=True)
pdf_path.write_bytes(pdf_content)
print(f'Created {pdf_path}')
