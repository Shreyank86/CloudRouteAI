import os
import re
from fpdf import FPDF

class SetupGuidePDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        self.set_font('helvetica', 'B', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'CLOUDROUTEAI - DOCKEY MULTI-LAPTOP SETUP GUIDE', border=0, align='R')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label, level=1):
        self.set_text_color(30, 41, 59) # Slate-800
        if level == 1:
            self.set_font('helvetica', 'B', 18)
            self.ln(6)
            self.cell(0, 10, label, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
            # Add a blue horizontal rule
            self.set_draw_color(59, 130, 246) # Blue-500
            self.set_line_width(1)
            self.line(self.get_x(), self.get_y(), self.get_x() + 180, self.get_y())
            self.ln(4)
        elif level == 2:
            self.set_font('helvetica', 'B', 14)
            self.ln(4)
            self.cell(0, 8, label, new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
        elif level == 3:
            self.set_font('helvetica', 'B', 11)
            self.ln(3)
            self.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
            self.ln(1)

    def paragraph(self, text, style=''):
        self.set_text_color(71, 85, 105) # Slate-600
        self.set_font('helvetica', style, 10)
        # Handle bold formatting in paragraph (e.g. **text**)
        # Basic parsing: split by ** and alternate style
        parts = text.split('**')
        for idx, part in enumerate(parts):
            if idx % 2 == 1:
                self.set_font('helvetica', 'B', 10)
            else:
                self.set_font('helvetica', style, 10)
            
            # Print without new line unless it's the last part
            is_last = (idx == len(parts) - 1)
            self.write(5, part)
        self.ln(5)

    def list_item(self, text, number=None):
        self.set_text_color(71, 85, 105)
        self.set_font('helvetica', '', 10)
        prefix = f" {number}. " if number else " -  "
        self.write(5, prefix)
        
        parts = text.split('**')
        for idx, part in enumerate(parts):
            if idx % 2 == 1:
                self.set_font('helvetica', 'B', 10)
            else:
                self.set_font('helvetica', '', 10)
            self.write(5, part)
        self.ln(5)

    def code_block(self, lines):
        self.set_fill_color(241, 245, 249) # Slate-100
        self.set_text_color(15, 23, 42) # Slate-900
        self.set_font('courier', '', 9.5)
        
        # Calculate height needed
        height = len(lines) * 5 + 4
        
        # Check if code block fits on current page, if not, add page break
        if self.get_y() + height > 270:
            self.add_page()
            
        self.cell(0, 2, '', new_x="LMARGIN", new_y="NEXT", fill=True)
        for line in lines:
            # Add padding
            self.cell(4, 5, '', fill=True)
            self.cell(0, 5, line, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.cell(0, 2, '', new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(3)

    def alert_box(self, text, type_='WARNING'):
        # Yellowish warning box
        self.set_fill_color(254, 243, 199) # Amber-100
        self.set_draw_color(245, 158, 11) # Amber-500
        self.set_text_color(180, 83, 9) # Amber-800
        self.set_line_width(0.5)
        
        # Draw box manually
        self.set_font('helvetica', 'B', 9)
        # Estimate height
        num_lines = max(1, len(text) // 80)
        box_height = num_lines * 5 + 6
        
        start_y = self.get_y()
        self.rect(self.get_x(), start_y, 180, box_height, style='DF')
        
        self.set_y(start_y + 3)
        self.cell(5, 5, '')
        self.write(5, f"[{type_}] {text}")
        self.set_y(start_y + box_height + 3)
        self.ln(2)

def generate_pdf(md_path, pdf_path):
    pdf = SetupGuidePDF()
    pdf.add_page()
    
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    in_code_block = False
    code_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Code block handler
        if line.strip().startswith('```'):
            if in_code_block:
                in_code_block = False
                pdf.code_block(code_lines)
                code_lines = []
            else:
                in_code_block = True
            i += 1
            continue
            
        if in_code_block:
            code_lines.append(line)
            i += 1
            continue
            
        # Alert boxes (GitHub blockquotes)
        if line.strip().startswith('> [!WARNING]'):
            warning_text = ""
            i += 1
            while i < len(lines) and lines[i].strip().startswith('>'):
                warning_text += lines[i].replace('>', '').strip() + " "
                i += 1
            pdf.alert_box(warning_text.strip(), 'WARNING')
            continue
            
        if line.strip().startswith('> [!IMPORTANT]'):
            important_text = ""
            i += 1
            while i < len(lines) and lines[i].strip().startswith('>'):
                important_text += lines[i].replace('>', '').strip() + " "
                i += 1
            pdf.alert_box(important_text.strip(), 'IMPORTANT')
            continue

        # Headings
        if line.startswith('# '):
            pdf.chapter_title(line[2:], level=1)
        elif line.startswith('## '):
            pdf.chapter_title(line[3:], level=2)
        elif line.startswith('### '):
            pdf.chapter_title(line[4:], level=3)
        # List items
        elif line.strip().startswith('- ') or line.strip().startswith('* '):
            clean_line = line.strip()[2:]
            pdf.list_item(clean_line)
        elif re.match(r'^\d+\.\s', line.strip()):
            match = re.match(r'^(\d+)\.\s(.*)', line.strip())
            num = match.group(1)
            item_text = match.group(2)
            pdf.list_item(item_text, number=num)
        # Empty lines
        elif not line.strip():
            pdf.ln(2)
        # Regular paragraph
        else:
            pdf.paragraph(line.strip())
            
        i += 1

    pdf.output(pdf_path)
    print(f"Successfully generated PDF: {pdf_path}")

if __name__ == '__main__':
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md = os.path.join(base_dir, 'multi_laptop_setup.md')
    pdf = os.path.join(base_dir, 'multi_laptop_setup.pdf')
    generate_pdf(md, pdf)
