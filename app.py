from openai import OpenAI
import gradio as gr
from transformers import pipeline

# Configure API client
client = OpenAI(
    api_key="kluster_api_key",
    base_url="https://api.kluster.ai/v1"
)

# Initialize speech-to-text
stt = pipeline("automatic-speech-recognition", model="openai/whisper-medium")


def process_input(input_type, text=None, audio=None):
    """Handle both text and voice inputs"""
    if input_type == "voice" and audio:
        user_input = stt(audio)["text"]
    else:
        user_input = text

    # Call Kluster.ai API
    response = client.chat.completions.create(
        model="klusterai/Meta-Llama-3.3-70B-Instruct-Turbo",
        messages=[{"role": "user", "content": user_input}],
        temperature=0.6,
        max_tokens=5000
    )

    return response.choices[0].message.content


# Create Gradio interface
with gr.Blocks() as app:
    with gr.Tabs():
        with gr.Tab("Text Input"):
            text_input = gr.Textbox(label="Type your message")
            text_output = gr.Textbox(label="Response", interactive=False)
            text_btn = gr.Button("Send")

        with gr.Tab("Voice Input"):
            audio_input = gr.Audio(source="microphone", type="filepath")
            audio_output = gr.Audio(label="Spoken Response", autoplay=True)
            voice_btn = gr.Button("Record")

    # Connect components
    text_btn.click(
        fn=process_input,
        inputs=[gr.Number(0, visible=False), text_input],
        outputs=text_output
    )

    voice_btn.click(
        fn=process_input,
        inputs=[gr.Number(1, visible=False), None, audio_input],
        outputs=audio_output
    )

if __name__ == "__main__":
    app.launch()
