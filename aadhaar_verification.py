import os
import re
import cv2
import pytesseract
import pandas as pd
import fitz

# TESSERACT PATH
pytesseract.pytesseract.tesseract_cmd = (r"C:\Program Files\Tesseract-OCR\tesseract.exe")

# IMAGE PREPROCESSING
def preprocess_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    return gray

# OCR IMAGE
def ocr_image(image_path):
    # First try original image
    processed = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed, config="--oem 3 --psm 11")
    aadhaar = extract_aadhaar(text)
    if aadhaar:
        return aadhaar
    # Load image only if rotation is needed
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Cannot read image: {image_path}")
    rotations = [
        cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE),
        cv2.rotate(image, cv2.ROTATE_180),
        cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    ]
    best_text = text
    for i, img in enumerate(rotations):
        temp_file = f"temp_rotate_{i}.png"
        cv2.imwrite(temp_file, img)
        try:
            processed = preprocess_image(temp_file)
            text = pytesseract.image_to_string(processed, config="--oem 3 --psm 11")
            aadhaar = extract_aadhaar(text)
            if aadhaar:
                return aadhaar
            if len(text) > len(best_text):
                best_text = text
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    return extract_aadhaar(best_text)

# OCR PDF
def ocr_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        # Direct text extraction
        page_text = page.get_text()
        aadhaar = extract_aadhaar(page_text)
        if aadhaar:
            doc.close()
            return aadhaar
        # OCR fallback
        pix = page.get_pixmap(matrix=fitz.Matrix(4, 4))
        temp_file = (f"temp_page_{page_num}.png")
        pix.save(temp_file)
        try:
            aadhaar = ocr_image(temp_file)
            if aadhaar:
                doc.close()
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                return aadhaar
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)
    doc.close()
    return None


# EXTRACT AADHAAR NUMBER
def extract_aadhaar(text):
    if not text:
        return None
    # Common OCR corrections
    text = text.replace("O", "0")
    text = text.replace("o", "0")
    text = text.replace("I", "1")
    text = text.replace("l", "1")
    text = text.replace("|", "1")
    patterns = [r"\b\d{4}\s?\d{4}\s?\d{4}\b", r"\b\d{12}\b"]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            aadhaar = re.sub(r"\D", "", match)
            if len(aadhaar) == 12:
                return aadhaar
    return None

# PROCESS FILE
def process_file(file_path):
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".pdf":
        text = ocr_pdf(file_path)
    elif extension in [".jpg", ".jpeg", ".png"]:
        text = ocr_image(file_path)
    else:
        raise ValueError(f"Unsupported file format: {extension}")
    return extract_aadhaar(text)

# MAIN VERIFICATION
def verify_dataset():
    df = pd.read_csv("aadhaar_dataset.csv")
    results = []
    correct = 0
    for _, row in df.iterrows():
        expected = str(row["aadhar_number"]).replace(" ", "")
        file_path = row["document_path"]
        try:
            extracted = process_file(file_path)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            extracted = None
        result = (
            "MATCH"
            if extracted == expected
            else "MISMATCH"
        )
        if result == "MATCH":
            correct += 1
        results.append({
            "File": file_path,
            "Expected": expected,
            "Extracted": extracted,
            "Result": result
        })
    result_df = pd.DataFrame(results)
    accuracy = (correct / len(df)) * 100
    summary_df = pd.DataFrame({
        "Metric": ["Total Files", "Matched", "Mismatched", "Accuracy (%)"],
        "Value": [len(df), correct, len(df) - correct, round(accuracy, 2)]
    })
    with pd.ExcelWriter("verification_results.xlsx", engine="openpyxl") as writer:
        result_df.to_excel(writer, sheet_name="Verification Results", index=False)
        summary_df.to_excel(writer, sheet_name="Summary", index=False)
        
    print("\nVerification Complete")
    print(f"Accuracy: {accuracy:.2f}%")
    print(
        "Excel Report Generated: verification_results.xlsx"
    )

# RUN
if __name__ == "__main__":
    verify_dataset()