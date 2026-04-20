from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 18)
        self.cell(0, 10, "Project Description: AI Food Detective", 0, 1, "C")
        self.ln(10)

def generate_description_pdf():
    pdf = PDF()
    pdf.add_page()
    
    # Title & Intro
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Overview", 0, 1)
    pdf.set_font("helvetica", "", 12)
    intro = (
        "The AI Food Detective is a state-of-the-art computer vision platform designed to transform "
        "how we interact with our food. By merging advanced Object Detection (YOLOv11) with specialized "
        "Image Processing (OpenCV), the system provides real-time analysis of food items to determine "
        "their type, quality, and safety for consumption."
    )
    pdf.multi_cell(0, 8, intro)
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Core Concept", 0, 1)
    pdf.set_font("helvetica", "", 12)
    concept = (
        "In a world where food waste is a major global challenge and food safety is paramount, this "
        "platform acts as an automated 'Food Inspector.' It uses high-speed AI to identify common fruits, "
        "vegetables, and prepared meals, then instantly evaluates their freshness using biometric-style "
        "heuristics like color distribution, texture roughness, and decay patterns."
    )
    pdf.multi_cell(0, 8, concept)
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Key Features", 0, 1)
    pdf.set_font("helvetica", "", 12)
    features = (
        "- Multi-Level Intelligent Detection: Simultaneously identifies what the food is and exactly how fresh it is.\n"
        "- Heuristic Freshness Analysis: Uses OpenCV kernels to detect brown spots, mold, and color desaturation.\n"
        "- Actionable Safety Insights: Provides clear labels: Safe to Eat, Sellable, or Not Safe.\n"
        "- Shelf-Life Estimation: Predicts the remaining 'window of freshness' in days.\n"
        "- Premium Visual Experience: Glassmorphism-themed frontend for webcams and mobile browsers.\n"
        "- Cloud-Native & Scalable: Dockerized and optimized for lightweight cloud infrastructure."
    )
    pdf.multi_cell(0, 8, features)
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Technical Architecture", 0, 1)
    pdf.set_font("helvetica", "", 12)
    tech = (
        "- Deep Learning Engine: Ultralytics YOLOv11 (Nano-series for high FPS).\n"
        "- Backend Nerves: FastAPI (Asynchronous Python) for ultra-low latency inference.\n"
        "- Image Processing: OpenCV for HSV color analysis and edge-based texture mapping.\n"
        "- Frontend: Modern HTML5/CSS3 with Vanilla JS and Dynamic Canvas rendering.\n"
        "- Infrastructure: Docker, Git-based CI/CD."
    )
    pdf.multi_cell(0, 8, tech)
    pdf.ln(5)

    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 10, "Value Proposition", 0, 1)
    pdf.set_font("helvetica", "", 12)
    value = (
        "This system is ideal for Smart Kitchens, Supermarket Quality Control, and Personal Nutrition Apps, "
        "helping users reduce waste, save money, and ensure they are eating only the healthiest, freshest food."
    )
    pdf.multi_cell(0, 8, value)

    output_path = "AI_Food_Detective_Description.pdf"
    pdf.output(output_path)
    print(f"PDF successfully generated at {output_path}")

if __name__ == "__main__":
    generate_description_pdf()
