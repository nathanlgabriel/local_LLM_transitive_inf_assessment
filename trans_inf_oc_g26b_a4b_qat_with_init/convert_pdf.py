from pypdf import PdfReader

def convert_pdf_to_txt(pdf_path, txt_path):
    reader = PdfReader(pdf_path)
    with open(txt_path, 'w', encoding='utf-8') as f:
        for page in reader.pages:
            text = page.extract_text()
            if text:
                f.write(text)
            f.write("\n")

if __name__ == "__main__":
    convert_pdf_to_txt('frenchsicilian_017.pdf', 'frenchsicilian_017.txt')
