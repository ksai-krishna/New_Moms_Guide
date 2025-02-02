import json
import os
from datetime import datetime
from pypdf import PdfReader
import google.generativeai as genai


USER_DATA = 'user_data.json'
CHAT_HISTORY_FILE = 'chat.json'
UPLOAD_FOLDER = 'static/uploads'


#### Setting up gemini api
api=os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api)
model = genai.GenerativeModel("gemini-1.5-flash")

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
    with open(USER_DATA,'+a') as f:
        json.dump(user_response,f,indent=4)

def write_chat_history(chat_history):
    """Write the chat history back to the JSON file."""
    with open(CHAT_HISTORY_FILE, 'w') as f:
        
        json.dump(chat_history, f, indent=4)


def simple_response_generator(data,prompt):
    userresponse=read_user_responses()
    prompt ="The context of previous chat is "+userresponse+" "+prompt
    prompt=prompt+"     :    "+data
    
    response = model.generate_content(prompt)
    return response.text

def response_generator_with_context(data,prompt):
    userresponse=read_user_responses()
    prompt ="The context of previous chat is "+userresponse+" "+prompt
    prompt=prompt+' '+data
    response = model.generate_content(prompt)
    speech_text = response.text
    print(speech_text)
    try:
        data_json = json.loads(speech_text)
    except json.JSONDecodeError:
        data_json = {"error": "Could not decode AI response."}

    # Optionally save to med.json
    with open('med.json', 'a') as f:
        json.dump(data_json, f, indent=4)

    return data_json


def find_type_of_report(data):
    prompt='''
    Given the following data extracted from a medical report concerning a pregnant woman, identify and specify the type of medical report based on its features or type of diagonosis shown in the report
    and give the result as just the report type
    '''
    # prompt=prompt+"    "+data
    report_type = simple_response_generator(data,prompt)
    return report_type





def correct_medical_prompt_picker(report_type):
    prompt=''
    if "Ultrasound" in report_type:
        prompt='''
        Act as a professional medical summarizer for a monthly healthy report of pregnant women from the first day of pregnancy until childbirth.
        - Based on the provided report ,  
                    -- please summarize whether the health of the mother is in good condition or if there are any concerns. With key 'Danger'
                    -- give a summary about the report in simple terms with key 'summary'.  
                    -- What is the gestational age of the fetus and also give the normal range? with key 'gestational age'
                    -- What is the presentation of the fetus ? with key 'presentation of fetus'
                    -- What are the fetal measurements and how do they compare to gestational age and also give the normal range? with key 'fetal measurements'
                    -- Is the fetal heartbeat present and what is the rate and also give the normal range? with key 'heart Beat '
                    -- Are there any visible congenital anomalies? with key 'congential anomalies'
                    -- Give the extracted information in JSON format and with speficied key structure only starting from { and also please it should not start with ```json ``` it should always start {
                    --  
        '''
    elif 'Blood' in report_type:
        prompt= ''''

        Act as a professional medical summarizer for a monthly healthy report of pregnant women from the first day of pregnancy until childbirth.
                    -- give a summary about the report in simple terms
                    -- Is my hemoglobin level within the normal range? with key 'Hemoglobin Level'
                    -- What does my hemoglobin level indicate about my risk of anemia? with key 'risk of anemia' 
                    -- Are my red blood cell (RBC) counts normal? with key 'RBC count'
                    -- What is the significance of my white blood cell (WBC) count? with key 'WBC count'
                    -- Is my platelet count adequate for a healthy pregnancy? with key 'platlet count'
                    -- Based on the provided report, please summarize whether the health of the mother is in good condition or if there are any concerns. with key 'Summary'
                    -- Give the extracted information in JSON format and with appropriate key strucure and please dont include any extra keys only include the keys i have mentioned only starting from { and also please it should not start with ```json ``` it should always start { 
             
        '''
    elif 'Thyroid' in report_type:
        prompt = '''
        Act as a professional medical summarizer for a monthly healthy report of pregnant women from the first day of pregnancy until childbirth.
        - Based on the provided report, please summarize whether the health of the mother is in good condition or if there are any concerns.
                    -- A simply summary about my report
                    -- Are my thyroid hormone levels normal?
                    -- What do abnormal thyroid levels mean for my pregnancy?
                    -- Do I need treatment if my thyroid levels are out of range?
                    -- How can thyroid dysfunction affect my baby’s health?
                    -- How often should I monitor my thyroid function during pregnancy?
                    -- Give the extracted information in JSON format only starting from { and also please it should not start with ```json ``` it should always start {

        '''
    else :
        prompt='''
             Act as a doctor specializing peditrics and gyncology  for a monthly healthy report of pregnant women from the first day of pregnancy until childbi
            Give a simple answer for the given question according to given data
        - Give the extracted information in JSON format only starting from { and also please it should not start with ```json ``` it should always start { 
    '''
    return prompt






def report_summarizer(data):
    report_type = find_type_of_report(data)
    print(report_type)
    prompt = correct_medical_prompt_picker(report_type)
    res = response_generator_with_context(data,prompt)
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


    res=simple_response_generator(data,prompt)
    return res

def medical_assitant_q_a(data,time_stamp):
     prompt = '''
       Act as a professional medical summarizer for a monthly healthy report of pregnant women from the first day of pregnancy until childbirth.
        - Based on the provided report, please summarize whether the health of the mother is in good condition or if there are any concerns.
        - give a Summary of the report in a simple and easy-to-understand way, focusing on key points that mothers can easily grasp. Avoid technical or medical jargon, and explain the findings in a relatable way that helps them understand the information clearly, as if you're talking directly to them and not to medical professionals.
        - Provide only the key information from the report that a patient can easily understand, offering a clear, general summary.
        - Any suggestion if something is wrong in simple terms
        - any suggestions on the baby's health in simple terms
        - Give the extracted information in JSON format only starting from { and also please it should not start with ```json ``` it should always start {
        - the data is 
    '''
    
    #  right_prompt=right_prompt_gen(data)
    
     json_response = response_generator_with_context(data,prompt)
     return json_response


def store_pdf_content_as_json(pdf_content, json_file,time_stamp):
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
