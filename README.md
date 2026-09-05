# Aadhaar OCR Verification System

A Python-based OCR system for extracting and verifying **12-digit Aadhaar numbers** from Aadhaar document images and PDF files.

The system uses **OpenCV, Tesseract OCR, PyMuPDF, Pandas, and regular expressions** to process documents, extract Aadhaar numbers, compare them against expected values in a CSV dataset, and generate an Excel verification report.

---

## 📌 Project Overview

The project automates the process of checking whether an Aadhaar number extracted from a document matches the expected Aadhaar number stored in a verification dataset.

The system supports:

* `.jpg`
* `.jpeg`
* `.png`
* `.pdf`

For image files, the system preprocesses the image before OCR and also attempts multiple rotations if the Aadhaar number cannot initially be extracted.

For PDF files, the system first attempts direct text extraction. If the Aadhaar number is not found, each page is rendered as an image and passed through the image OCR pipeline.

After processing the complete dataset, the system generates an Excel report containing individual verification results and an overall summary.

---

## 🔄 System Workflow

```text
                Input Document
                      │
             ┌────────┴────────┐
             │                 │
          Image               PDF
             │                 │
             ▼                 ▼
     Image Preprocessing   Direct Text Extraction
             │                 │
             ▼                 ▼
        Tesseract OCR     Aadhaar Found?
             │              │       │
             │             Yes      No
             │              │       │
             │              │       ▼
             │              │   Render PDF Page
             │              │       │
             │              │       ▼
             │              │    OCR Image
             └──────────────┴───────┘
                        │
                        ▼
               Aadhaar Extraction
                        │
                        ▼
              Compare With Expected
                        │
                ┌───────┴───────┐
                │               │
              MATCH          MISMATCH
                │               │
                └───────┬───────┘
                        ▼
                Excel Verification
                     Report
```

---

# 🧠 OCR Processing

The main implementation is contained in:

```text
aadhaar_verification.py
```

The project uses:

```python
import cv2
import pytesseract
import fitz
import pandas as pd
import re
```

---

## 🖼️ Image Preprocessing

Images are loaded using OpenCV.

The preprocessing pipeline:

1. Reads the image.
2. Converts it from BGR to grayscale.
3. Applies Otsu's binary thresholding.

The implementation uses:

```python
cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
```

followed by:

```python
cv2.threshold(
    gray,
    0,
    255,
    cv2.THRESH_BINARY + cv2.THRESH_OTSU
)
```

This processed image is then supplied to Tesseract OCR.

---

# 🔤 Tesseract OCR

The project uses Tesseract through:

```python
pytesseract.image_to_string()
```

The OCR configuration is:

```text
--oem 3 --psm 11
```

The system first attempts OCR on the processed image.

If a valid Aadhaar number is not found, it performs additional OCR attempts using rotated versions of the original image.

---

# 🔄 Image Rotation Handling

The implementation attempts three additional orientations:

```text
90° clockwise
180°
90° counter-clockwise
```

The rotated images are temporarily saved as PNG files, processed through the same preprocessing and OCR pipeline, and then deleted.

If a valid Aadhaar number is found during any rotation, the system immediately returns it.

If no valid number is found, the system keeps the OCR text containing the greatest amount of text and performs the final extraction attempt.

---

# 📄 PDF Processing

PDF processing is implemented using **PyMuPDF (`fitz`)**.

For every PDF page, the system first attempts direct text extraction:

```python
page.get_text()
```

If an Aadhaar number is found, the process ends successfully.

If no Aadhaar number is found through direct extraction, the page is rendered into an image using:

```python
page.get_pixmap(
    matrix=fitz.Matrix(4, 4)
)
```

The generated page image is then processed through the image OCR pipeline.

This provides a fallback for PDFs whose content is image-based rather than directly extractable text.

---

# 🔢 Aadhaar Number Extraction

The extraction logic is implemented using Python regular expressions.

Before matching, the OCR text undergoes several common OCR corrections:

```text
O → 0
o → 0
I → 1
l → 1
| → 1
```

The system searches for two formats:

```text
XXXX XXXX XXXX
XXXXXXXXXXXX
```

The corresponding regular expressions are:

```python
r"\b\d{4}\s?\d{4}\s?\d{4}\b"
```

and:

```python
r"\b\d{12}\b"
```

The extracted value is normalized by removing non-digit characters.

A value is accepted only when it contains exactly:

```text
12 digits
```

---

# 📁 Supported File Types

The `process_file()` function supports:

| Extension | Processing                         |
| --------- | ---------------------------------- |
| `.jpg`    | Image OCR                          |
| `.jpeg`   | Image OCR                          |
| `.png`    | Image OCR                          |
| `.pdf`    | PDF text extraction + OCR fallback |

Unsupported extensions result in a `ValueError`.

---

# 📊 Verification Dataset

The project uses:

```text
aadhaar_dataset.csv
```

The dataset contains two columns:

| Column          | Purpose                            |
| --------------- | ---------------------------------- |
| `aadhar_number` | Expected Aadhaar number            |
| `document_path` | Path to the corresponding document |

The current dataset contains **15 verification records**.

Example structure:

```csv
aadhar_number,document_path
1043 3218 1960,documents/doc_1.png
0133 8908 3863,documents/doc_2.png
7940 2654 2351,documents/doc_3.png
```

The expected Aadhaar number is normalized by removing spaces before comparison.

---

# ✅ Verification Process

The `verify_dataset()` function:

1. Loads `aadhaar_dataset.csv`.
2. Processes every document.
3. Extracts the Aadhaar number.
4. Compares the extracted value with the expected value.
5. Marks the result as `MATCH` or `MISMATCH`.
6. Counts successful matches.
7. Calculates verification accuracy.
8. Generates an Excel report.

The comparison is:

```python
"MATCH" if extracted == expected else "MISMATCH"
```

---

# 📑 Excel Report

The system generates:

```text
verification_results.xlsx
```

using Pandas and `openpyxl`.

The Excel workbook contains two sheets.

## 1. Verification Results

Contains:

| Column      | Description                  |
| ----------- | ---------------------------- |
| `File`      | Processed document path      |
| `Expected`  | Expected Aadhaar number      |
| `Extracted` | OCR-extracted Aadhaar number |
| `Result`    | `MATCH` or `MISMATCH`        |

## 2. Summary

Contains:

| Metric       |
| ------------ |
| Total Files  |
| Matched      |
| Mismatched   |
| Accuracy (%) |

The accuracy is calculated as:

```text
Matched Files
───────────── × 100
 Total Files
```

---

# 📂 Project Structure

```text
Aadhaar-OCR-Verification-System/
│
├── aadhaar_verification.py
├── aadhaar_dataset.csv
├── verification_results.xlsx
└── README.md
```

The current GitHub repository contains these four files.

The dataset references document files under:

```text
documents/
```

For the verification script to process those records successfully, the referenced document files need to exist at the corresponding paths.

---

# 🛠️ Technologies Used

| Technology          | Purpose                                                     |
| ------------------- | ----------------------------------------------------------- |
| Python              | Core implementation                                         |
| OpenCV              | Image loading, grayscale conversion, thresholding, rotation |
| Tesseract OCR       | Text recognition                                            |
| Pytesseract         | Python interface for Tesseract                              |
| PyMuPDF (`fitz`)    | PDF text extraction and page rendering                      |
| Pandas              | Dataset handling and report generation                      |
| Regular Expressions | Aadhaar number pattern detection                            |
| OpenPyXL            | Excel file generation through Pandas                        |

---

# ⚙️ Prerequisites

The project requires:

* Python
* Tesseract OCR
* Python packages used by the implementation

Tesseract must be installed separately because the Python `pytesseract` package communicates with the Tesseract executable.

The current Python implementation is configured for the Windows installation path:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

This path is defined directly in `aadhaar_verification.py` and should be changed if Tesseract is installed elsewhere.

---

# 📦 Installation

Clone the repository:

```bash
git clone https://github.com/HacBoy777/Aadhaar-OCR-Verification-System.git
```

Navigate to the project directory:

```bash
cd Aadhaar-OCR-Verification-System
```

Install the Python dependencies:

```bash
pip install opencv-python pytesseract pandas pymupdf openpyxl
```

Install Tesseract OCR separately and make sure the executable path matches the configuration in:

```text
aadhaar_verification.py
```

---

# ▶️ Running the Project

Place the verification documents in the paths referenced by:

```text
aadhaar_dataset.csv
```

Then run:

```bash
python aadhaar_verification.py
```

The script will:

```text
Load Dataset
     ↓
Process Documents
     ↓
Extract Aadhaar Numbers
     ↓
Compare Expected vs Extracted
     ↓
Calculate Accuracy
     ↓
Generate verification_results.xlsx
```

The console displays:

```text
Verification Complete
Accuracy: XX.XX%
Excel Report Generated: verification_results.xlsx
```

---

# 🧪 Verification Output

For every document, the system records:

```text
File
Expected
Extracted
Result
```

For example:

```text
File: documents/doc_1.png
Expected: 104332181960
Extracted: 104332181960
Result: MATCH
```

The exact output depends on the documents being processed.

---

# 📈 Accuracy Calculation

The system calculates verification accuracy using:

```python
accuracy = (correct / len(df)) * 100
```

where:

```text
correct = number of MATCH results
len(df) = total verification records
```

The final value is rounded to two decimal places in the Excel summary.

---

# 🔍 Error Handling

The implementation handles several possible processing failures.

### Invalid Image

If OpenCV cannot read an image:

```text
FileNotFoundError
```

is raised.

### Unsupported File

If the file extension is not:

```text
.pdf
.jpg
.jpeg
.png
```

the system raises:

```text
ValueError
```

### Document Processing Error

During dataset verification, processing errors are caught and printed, and the corresponding document is treated as having no extracted Aadhaar number.

This allows the remaining dataset records to continue processing.

---

# 🔐 Privacy & Security

This project processes Aadhaar numbers, which are sensitive personal identifiers.

For real-world use:

* Do not commit real Aadhaar numbers to a public repository.
* Do not upload real Aadhaar documents to public repositories.
* Use synthetic or properly anonymized test data.
* Protect generated verification reports.
* Store sensitive documents securely.
* Avoid logging complete Aadhaar numbers in production environments.

The repository currently includes Aadhaar-number-like values in `aadhaar_dataset.csv`; these should be treated as sensitive test data if they correspond to real identities.

---

# 📌 Current Implementation Scope

The current project specifically implements:

* OCR-based Aadhaar number extraction
* Image preprocessing
* OCR rotation fallback
* PDF text extraction
* PDF OCR fallback
* Regular-expression-based Aadhaar detection
* Dataset-based verification
* Match/mismatch classification
* Accuracy calculation
* Excel report generation

It does **not** currently implement:

* Aadhaar QR-code verification
* UIDAI API verification
* Face verification
* Biometric verification
* Aadhaar authenticity verification
* Digital signature verification
* Web interface
* Database integration
* Machine Learning-based OCR
* Cloud deployment

These capabilities are outside the current implementation.

---

# 🎯 Learning Outcomes

This project demonstrates practical implementation of:

* Optical Character Recognition (OCR)
* Image preprocessing
* Thresholding
* Document processing
* PDF processing
* Regular expressions
* Text normalization
* File handling
* Dataset-driven verification
* Automated accuracy calculation
* Excel report generation
* Python automation

---

# 🔮 Possible Future Improvements

Possible extensions include:

* Move the Tesseract path to environment/configuration settings
* Add a web interface
* Add structured logging
* Add document validation before OCR
* Improve OCR preprocessing
* Add confidence-score handling
* Add more robust Aadhaar number validation
* Add QR-code reading
* Add secure database storage
* Add automated test cases
* Add synthetic test-document generation
* Add batch-processing progress reporting

---

# 👨‍💻 Author

**HacBoy777**

GitHub:

https://github.com/HacBoy777

---

# ⭐ Repository

[Aadhaar OCR Verification System](https://github.com/HacBoy777/Aadhaar-OCR-Verification-System)

If you find this project useful, consider giving the repository a ⭐.
