from fpdf import FPDF

def create_sample_deed():
    pdf = FPDF()
    pdf.add_page()
    
    # Set font
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'SAMPLE PROPERTY DEED', 0, 1, 'C')
    
    # Add content
    pdf.set_font('Arial', '', 12)
    pdf.ln(10)
    pdf.multi_cell(0, 10, 'This is a sample property deed document for testing purposes.')
    
    pdf.ln(10)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, 'Property Details:', 0, 1)
    
    pdf.set_font('Arial', '', 12)
    details = [
        'Title: Test Property',
        'Location: Test Location',
        'Owner: Test Owner',
        'Date: April 10, 2025'
    ]
    
    for detail in details:
        pdf.cell(0, 10, detail, 0, 1)
    
    pdf.ln(10)
    pdf.multi_cell(0, 10, 'This document is for testing the document upload functionality of the TrustRent application.')
    
    pdf.ln(20)
    pdf.cell(0, 10, 'Signed: _________________', 0, 1)
    pdf.cell(0, 10, 'Date: ___________________', 0, 1)
    
    # Save the PDF
    pdf.output('test_files/sample_deed.pdf')

if __name__ == '__main__':
    create_sample_deed()
    print("PDF created successfully at test_files/sample_deed.pdf") 