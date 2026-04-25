import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) 
engine.setProperty('rate', 170)            
engine.setProperty('volume', 1.0)

def speak(text):
    global is_speaking
    is_speaking = True

    print("🤖:", text)  # optional: show text
    engine.say(text)
    engine.runAndWait()

    is_speaking = False
    
speak('Albin, Could you please explain the core concepts of the RAG Pipelines and Data Science. Also say about your family?')