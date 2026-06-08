import PyPDF2

def convert_pdf_to_txt(pdf_path, txt_path):
    try:
        with open(pdf_path, 'rb') as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
            
            with open(txt_path, 'w', encoding='utf-8') as txt_file:
                txt_file.write(text)
            print(f"Successfully converted {pdf_path} to {txt_path}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    convert_pdf_to_txt('frenchsicilian_017.pdf', 'frenchsicilian_017.txt')
