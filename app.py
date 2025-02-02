from new_moms_assitant import *
from flask import Flask, render_template, request,redirect,url_for

app = Flask(__name__)

@app.route('/new_chat', methods=['GET'])
def new_chat():
        # Reset the chat history
        write_chat_history({})  # Clear the chat history file

        # Redirect back to the main chat page
        return redirect(url_for('chat'))
@app.route('/', methods=['GET', 'POST'])
def chat():
    # Load existing chat history
    chat_history = read_chat_history()
    userresponse = read_user_responses()
    response_message = ""
    ai_response = ""

    if request.method == 'POST':
        user_input = request.form['user_input']
        # Get the current timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        userresponse[timestamp]={
             'userinput': user_input
        }
        write_user_responses(user_input)




        # Handle file upload
        file_url = None  # Initialize file_url for file uploads
        file_name = None  # Initialize file_name for uploaded files

        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename:  # Check if a file is uploaded
                file_path = os.path.join(UPLOAD_FOLDER, file.filename)  # Full path for the saved file
                file.save(file_path)  # Save the original file
                file_name = file.filename  # Store the file name
                response_message = f"File '{file.filename}' uploaded successfully!"
                
                file_url = "uploads/" + file_name 
                data = read_file_from_path(file_path)
                ai_response = report_summarizer(data)
            else:
                ai_response = simple_assitant(user_input)


        chat_history[timestamp] = {
            'user_input': user_input,
            'ai_response': ai_response,  # Store the AI response
            'file_url': file_url,  # Store the file URL if available
            'file_name': file_name  # Store the file name if available
        }

        # Write updated chat history back to the file
        write_chat_history(chat_history)

    # Prepare chat history for rendering in the template
    sorted_chat_history = sorted(chat_history.items(), key=lambda x: x[0])

    return render_template('index.html', response=response_message, chat_history=sorted_chat_history)

if __name__ == '__main__':
    app.run(debug=True)