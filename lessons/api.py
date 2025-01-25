import os
import json
import PyPDF2
from openai import AzureOpenAI

RESPONSE_JSON = {
    "1": {
        "no": "1",
        "mcq": "multiple choice question",
        "options": {
            "a": "choice here",
            "b": "choice here",
            "c": "choice here",
            "d": "choice here",
        },
        "correct": "correct answer",
    },
    "2": {
        "no": "2",
        "mcq": "multiple choice question",
        "options": {
            "a": "choice here",
            "b": "choice here",
            "c": "choice here",
            "d": "choice here",
        },
        "correct": "correct answer",
    },
    "3": {
        "no": "3",
        "mcq": "multiple choice question",
        "options": {
            "a": "choice here",
            "b": "choice here",
            "c": "choice here",
            "d": "choice here",
        },
        "correct": "correct answer",
    },
}
#number = 10
mcq_count = 10
grade= 3
#tone = "curios"
path = 'ml_algo.pdf'
response_json = json.dumps(RESPONSE_JSON)

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file using PyPDF2."""
    with open(file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text



def parse_file(file):
    if file.name.endswith(".pdf"):
        try:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            return text
        except PyPDF2.utils.PdfReadError:
            raise Exception("Error reading the PDF file.")

    elif file.name.endswith(".txt"):
        return file.read().decode("utf-8")

    else:
        raise Exception(
            "Unsupported file format. Only PDF and TXT files are supported."
        )

'''text = parse_file(open(path, "rb"))
data = chat_with_openai(text[:3000], number, grade, tone, response_json)
data = json.loads(data)

for key, value in data.items():
    print(f"Question {value['no']}: {value['mcq']}")
    print("Options:")
    for option_key, option_value in value['options'].items():
        print(f"  {option_key}: {option_value}")
    print(f"Correct Answer: {value['correct']}")
    print("-" * 50)'''

def generate_qa_from_pdf(text):
    """Generate questions and answers from a PDF and return as JSON."""
    #text = extract_text_from_pdf(pdf_path)
    qa_response = chat_with_openai(text)

    try:
        # Parse the response into JSON
        qa_json = json.loads(qa_response)
    except json.JSONDecodeError:
        print("Failed to decode JSON. The response might not be formatted correctly.")
        qa_json = {"error": "Invalid JSON response from API", "raw_response": qa_response}

    return qa_json



import PyPDF2

def extract_text_from_pdf(pdf_path):
    """
    Extrait tout le texte d'un document PDF.
    
    Args:
        pdf_path (str): Le chemin du fichier PDF.
    
    Returns:
        str: Le texte extrait du PDF.
    """
    extracted_text = ""
    
    # Ouverture du fichier PDF en mode lecture binaire
    with open(pdf_path, 'rb') as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        
        # Parcourir toutes les pages et extraire le texte
        for page in reader.pages:
            extracted_text += page.extract_text() + "\n"
    
    return extracted_text
