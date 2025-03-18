import json
import os
from datetime import datetime
from pypdf import PdfReader
import google.generativeai as genai


USER_DATA = 'user_data.json'
CHAT_HISTORY_FILE = 'chat.json'
UPLOAD_FOLDER = 'static/uploads'


#### Setting up gemini api
api = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api)
model = genai.GenerativeModel("gemini-1.5-flash")
print(api)
# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def read_chat_history():
    """ Read chat history from the chat file"""
    try:
        with open(CHAT_HISTORY_FILE, 'r') as f:
            chat_history = json.load(f)
            return chat_history

    # Exception Handling
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def read_user_responses():
    """ Read the history of user data for memory"""
    try:
        with open(USER_DATA, 'r') as f:
            userresponse = json.load(f)
            return userresponse

    # Exception Handling
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def write_user_responses(user_response):
    """ Write the history of user data for memory"""
    with open(USER_DATA, 'w') as f:
        json.dump(user_response, f, indent=4)


def write_chat_history(chat_history):
    """Write the chat history back to the JSON file."""
    with open(CHAT_HISTORY_FILE, 'w') as f:

        json.dump(chat_history, f, indent=4)


def simple_response_generator(data, prompt):
    userresponse = read_user_responses()
    prompt = "The context of previous chat is " + \
        str(userresponse) + " " + prompt
    prompt = prompt + "     :    " + data

    response = model.generate_content(prompt)
    return response.text


def format_gemini_response(response_text):
    """
    Formats the Gemini response to ensure it's valid JSON without ```json```.
    """
    # Remove ```json and ``` if present
    response_text = response_text.replace("```json", "").replace("```", "").strip()

    # Ensure the response starts and ends with curly braces
    if not response_text.startswith("{") or not response_text.endswith("}"):
        try:
            # Attempt to find the start and end of the JSON
            start_index = response_text.find("{")
            end_index = response_text.rfind("}")

            if start_index != -1 and end_index != -1:
                response_text = response_text[start_index:end_index + 1]
            else:
                # If no curly braces are found, return an error
                return {"error": "Invalid JSON format: No curly braces found."}
        except:
            return {"error": "Invalid JSON format."}

    try:
        # Load the JSON to validate it
        data_json = json.loads(response_text)
        return data_json
    except json.JSONDecodeError:
        return {"error": "Could not decode AI response."}


def response_generator_with_context(data, prompt):
    userresponse = read_user_responses()
    prompt = "The context of previous chat is " + \
        str(userresponse) + " " + prompt
    prompt = prompt + ' ' + data
    response = model.generate_content(prompt)
    speech_text = response.text
    print(speech_text)
    # Format the response to ensure it's valid JSON
    data_json = format_gemini_response(speech_text)

    # Optionally save to med.json
    with open('med.json', 'a') as f:
        json.dump(data_json, f, indent=4)

    return data_json


def find_type_of_report(data):
    prompt = '''
    Given the following data extracted from a medical report concerning a pregnant woman, identify and specify the type of medical report based on its features or type of diagonosis shown in the report
    and give the result as just the report type
    '''
    # prompt=prompt+"    "+data
    report_type = simple_response_generator(data, prompt)
    return report_type


def correct_medical_prompt_picker(report_type):
    prompt = ''
    if "Ultrasound" in report_type:
        prompt = '''
        Act as a professional medical summarizer for the entire pregnancy, from the first day until childbirth.
        Based on the provided reports:
            -- Please summarize the overall health of the mother throughout the pregnancy, noting any concerns or changes in condition. Key: 'Overall Health'
            -- Provide a comprehensive summary of the reports in simple terms, understandable for someone without medical background. Key: 'Comprehensive Summary'
            -- What was the gestational age of the fetus at the last ultrasound and the normal range for that age? Key: 'Latest Gestational Age'
            -- What was the presentation of the fetus at the last ultrasound? Key: 'Latest Fetal Presentation'
            -- What were the fetal measurements at the last ultrasound, how do they compare to the gestational age, and what is the normal range? Key: 'Latest Fetal Measurements'
            -- Was the fetal heartbeat present at the last ultrasound, what was the rate, and what is the normal range? Key: 'Latest Heartbeat'
            -- Were there any visible congenital anomalies noted throughout the ultrasounds? Key: 'Congenital Anomalies'
            -- Give the extracted information in JSON format with the specified key structure, starting from { and ensuring it does not start with ```json ```.
        '''
    elif 'Blood' in report_type:
        prompt = '''
        Act as a professional medical summarizer for the entire pregnancy, from the first day until childbirth.
            -- Provide a comprehensive summary of the reports in simple terms. Key: 'Comprehensive Summary'
            -- Were hemoglobin levels within the normal range throughout the pregnancy? Key: 'Hemoglobin Levels'
            -- What did hemoglobin levels indicate about the risk of anemia throughout the pregnancy? Key: 'Anemia Risk'
            -- Were red blood cell (RBC) counts normal throughout the pregnancy? Key: 'RBC Counts'
            -- What was the significance of white blood cell (WBC) count trends throughout the pregnancy? Key: 'WBC Counts Significance'
            -- Was the platelet count adequate for a healthy pregnancy? Key: 'Platelet Count Adequacy'
            -- Based on the provided reports, please summarize the overall health of the mother and any concerns. Key: 'Overall Health'
            -- Give the extracted information in JSON format with the specified key structure, including only the keys mentioned, starting from { and ensuring it does not start with ```json ```.
        '''
    elif 'Thyroid' in report_type:
        prompt = '''
        Act as a professional medical summarizer for the entire pregnancy, from the first day until childbirth.
            -- Summarize the overall health of the mother and any concerns based on the provided reports. Key: 'Overall Health'
            -- Provide a simple summary of the reports. Key: 'Simple Summary'
            -- Were thyroid hormone levels normal throughout the pregnancy? Key: 'Thyroid Levels'
            -- What did abnormal thyroid levels mean for the pregnancy? Key: 'Thyroid Level Implications'
            -- Was treatment needed at any point due to thyroid levels being out of range? Key: 'Thyroid Treatment'
            -- How did thyroid dysfunction affect the baby’s health, if at all? Key: 'Thyroid Impact on Baby'
            -- How often was thyroid function monitored during pregnancy? Key: 'Thyroid Monitoring Frequency'
            -- Give the extracted information in JSON format, starting from { and ensuring it does not start with ```json ```.
        '''
    else:
        prompt = '''
             Act as a doctor specializing in pediatrics and gynecology for a healthy report of pregnant women from the first day of pregnancy until childbirth.
            Give a simple answer for the given question according to given data.
            -- Give the extracted information in JSON format, starting from { and ensuring it does not start with ```json ```.
        '''
    return prompt


def report_summarizer(data):
    report_type = find_type_of_report(data)
    print(report_type)
    prompt = correct_medical_prompt_picker(report_type)
    res = response_generator_with_context(data, prompt)
    return res


def simple_assitant(data):

    # prompt = '''
    #    Act as a compassionate doctor specializing in gynecology and pediatrics. Respond to patient or guardian questions with empathy, using a conversational tone as if speaking directly to them in a consultation. Provide medically accurate information while explaining complex concepts in a simple, patient-friendly manner. Your answers should reflect the warmth, professionalism, and understanding of a healthcare provider, offering clear advice, reassurance, and support where needed.
    #    Give the extracted information as response : and in JSON format only starting from { and dont give json response with ```json ``` start with { only if out of box questions given just say i am a medical assitant who can assit you and speak like doctor as mentioned above.
    # '''

    prompt = '''
       Act as a compassionate doctor specializing in gynecology and pediatrics. Respond to patient or guardian questions with empathy, using a conversational tone as if speaking directly to them in a consultation. Provide medically accurate information while explaining complex concepts in a simple, patient-friendly manner. Your answers should reflect the warmth, professionalism, and understanding of a healthcare provider, offering clear advice, reassurance, and support where needed.
       And dont give large paragraphs of answer give a simple answer with all key points 
    '''

    res = simple_response_generator(data, prompt)
    return res


def medical_assitant_q_a(data, time_stamp):
    prompt = '''
       Act as a professional medical summarizer for the entire pregnancy, from the first day of pregnancy until childbirth.
        - Based on the provided reports, please summarize the overall health of the mother and any concerns.
        - Give a summary of the reports in a simple and easy-to-understand way, focusing on key points that mothers can easily grasp, avoiding technical or medical jargon, and explaining the findings in a relatable way.
        - Provide only the key information from the reports that a patient can easily understand, offering a clear, general summary.
        - Any suggestions if something was wrong at any point in simple terms.
        - Any suggestions on the baby's health in simple terms.
        - Give the extracted information in JSON format, starting from { and ensuring it does not start with ```json ```.
        - The data is:
    '''

    json_response = response_generator_with_context(data, prompt)
    return json_response


def store_pdf_content_as_json(pdf_content, json_file, time_stamp):
    data = {
        "timestamp": time_stamp,
        "content": pdf_content
    }

    # Store data in JSON
    with open(json_file, 'w') as f:
        json.dump(data, f)


def read_file_from_path(path):
    reader = PdfReader(path)
    data = ""

    for page_no in range(len(reader.pages)):
        page = reader.pages[page_no]
        data += page.extract_text()

    json_data = {
        "time_stamp": datetime.now().isoformat(),  # Current time in ISO format
        "pdf_data": data
    }

    with open('pdf_content.json', 'w') as f:
        json.dump(json_data, f, indent=4)
    return data
