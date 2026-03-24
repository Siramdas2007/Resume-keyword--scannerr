from flask import Flask, render_template, request
import os
import re
from PyPDF2 import PdfReader

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure uploads folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


# ✅ Normalize text (fix C++, etc.)
def normalize_text(text):
    if not text:
        return ""

    text = text.lower()
    text = text.replace("c + +", "c++")
    text = text.replace("c #", "c#")
    text = text.replace("node js", "node.js")

    return text


# ✅ Extract text from PDF
def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""

        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

        return text

    except Exception as e:
        print("PDF Error:", e)
        return ""


# ✅ Extract keywords (FIXED)
def extract_keywords(text):
    if not text:
        return set()

    text = normalize_text(text)

    words = re.findall(r"[a-zA-Z0-9+#\.]+", text)

    # Remove common words
    ignore = {"and", "or", "the", "a", "to", "in", "for", "of", "with"}
    keywords = {word for word in words if word not in ignore}

    return keywords


# ✅ AI Suggestions
def generate_suggestions(missing, score):
    suggestions = []

    if score >= 80:
        suggestions.append("Excellent! Your resume strongly matches the job description.")
    elif score >= 50:
        suggestions.append("Good match, but you can improve further.")
    else:
        suggestions.append("Your resume needs improvement to match the job requirements.")

    if missing:
        suggestions.append(f"Add these important skills: {', '.join(list(missing)[:10])}")

    suggestions.append("Include more relevant projects and experience.")
    suggestions.append("Use strong action verbs like developed, designed, implemented.")
    suggestions.append("Keep your resume clean and ATS-friendly.")

    return suggestions


# ✅ MAIN LOGIC
def scan_resume(resume_text, job_desc):
    resume_words = extract_keywords(resume_text)
    job_words = extract_keywords(job_desc)

    print("Resume Words:", resume_words)
    print("Job Words:", job_words)

    matched = resume_words.intersection(job_words)
    missing = job_words - resume_words

    # ✅ Correct score calculation
    total = len(job_words)
    score = (len(matched) / total) * 100 if total > 0 else 0

    return list(matched), list(missing), round(score, 2)


# ✅ ROUTES
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        file = request.files.get("resume")
        job_desc = request.form.get("jobdesc")

        if not file or file.filename == "":
            return "Please upload a resume"

        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        resume_text = extract_text_from_pdf(filepath)

        matched, missing, score = scan_resume(resume_text, job_desc)

        suggestions = generate_suggestions(missing, score)

        return render_template("result.html",
                               matched=matched,
                               missing=missing,
                               score=score,
                               suggestions=suggestions)

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
