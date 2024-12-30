import os.path
import threading
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from openai import OpenAI
from kivy.uix.scrollview import ScrollView
from kivy.clock import mainthread
from bidi.algorithm import get_display
import subprocess
import os
import webbrowser
from kivy.uix.togglebutton import ToggleButton  # Import ToggleButton


def convert_markdown_to_output(input_text, output_format):
    """
    Convert Markdown text with optional LaTeX into an output file (PDF or HTML).

    Args:
        input_text (str): The Markdown/LaTeX input as a string.
        output_format (str): The output format, either 'pdf' or 'html'.
    """
    # Write the input text to a temporary Markdown file
    temp_md_file = "temp_input.md"
    with open(temp_md_file, "w", encoding="utf-8") as f:
        f.write(input_text)

    output_file = f'output.{output_format}'

    # Use Pandoc to convert the Markdown file to the desired output format
    try:
        subprocess.run(
            ["pandoc", temp_md_file, '-s', '--to', 'html',
             "--mathjax",
             "-o", output_file, ],
            check=True
        )
        print(f"Successfully created {output_format.upper()} file: {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"Error during Pandoc conversion: {e}")
    finally:
        # Remove the temporary Markdown file
        os.remove(temp_md_file)

    # Open the generated file using the default system viewer
    if output_format == "html":  # Open HTML in the browser
        webbrowser.open(output_file)
    elif output_format == "pdf":  # Open PDF using system viewer
        if os.name == "nt":  # Windows
            os.startfile(output_file)
        elif os.name == "posix":  # macOS or Linux
            subprocess.run(["open" if os.uname().sysname == "Darwin" else "xdg-open", output_file])


API_KEY_PATH = 'api_key.txt'

help_msg = '''To find your API key or create new ones:
https://platform.openai.com/api-keys
To add credit to your balance:
https://platform.openai.com/settings/organization/billing/overview
'''


class ApiKeyPopup(Popup):
    def __init__(self, on_confirm, **kwargs):
        super(ApiKeyPopup, self).__init__(**kwargs)
        self.title = "Enter API Key"
        self.on_confirm = on_confirm
        self.size_hint = (0.8, 0.3)
        content = BoxLayout(orientation='vertical')

        self.api_key_input = TextInput(hint_text='Enter your API key', multiline=False)
        content.add_widget(self.api_key_input)

        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.3)
        ok_button = Button(text='OK')
        ok_button.bind(on_release=self.on_ok)
        cancel_button = Button(text='Cancel')
        cancel_button.bind(on_release=self.dismiss)

        button_layout.add_widget(ok_button)
        button_layout.add_widget(cancel_button)
        content.add_widget(button_layout)

        self.add_widget(content)

    def on_ok(self, instance):
        print(f"Entered API Key: {self.api_key_input.text}")
        self.on_confirm(self.api_key_input.text)
        self.dismiss()
# 054 2082499

class AIChatApp(App):
    def build(self):
        mainlayout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        if os.path.exists(API_KEY_PATH):
            with open(API_KEY_PATH, 'rt') as f:
                self.api_key = f.read()
                print(f'Loaded api key from file: {self.api_key}')
                self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

        self.input_text = TextInput(hint_text="Enter your message here", size_hint=(1, 0.2),  font_size=24,
                                    font_name='DejaVuSans.ttf',)
        mainlayout.add_widget(self.input_text)

        # Label to show response
        scrollview = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True, scroll_type=['bars'])
        self.response_label = TextInput(
            text="", size_hint_y=None, height='1000dp', readonly=True, multiline=True, font_size=24,
            cursor_blink=True, font_name='DejaVuSans.ttf',
        )

        scrollview.add_widget(self.response_label)
        mainlayout.add_widget(scrollview)
        try:
            available_models = sorted([str(m.id) for m in self.client.models.list()])
            self.response_label.text = 'OpenAI API connection established successfully.'
        except Exception as e:
            self.response_label.text = 'Error connecting to OpenAI. Check your API key.\n'+ help_msg + '\n' + str(e)
            available_models = ['chatgpt-4o-latest', 'gpt-4o', 'gpt-4o-mini', 'gpt-4', 'dall-e-2', 'dall-e-3']

        # Keyboard: Allow message send with shift+enter
        def _on_keyboard(instance, key, scancode, codepoint, modifiers):
            if key == 13 and 'shift' in modifiers:
                self.send_message()

        Window.bind(on_keyboard=_on_keyboard)

        # Buttons:
        buttons_size = (0.5, 0.5)
        button_layout = BoxLayout(size_hint=(1, 0.3))

        # Spinner for model selection.
        models = ('gpt-4o', 'gpt-4-turbo', 'chatgpt-4o-latest', 'gpt-3.5-turbo', 'gpt-4')
        self.model_spinner = Spinner(
            text='chatgpt-4o-latest',
            values=available_models,
            size_hint=(1.2, 1)
        )
        button_layout.add_widget(self.model_spinner)

        # Button to send message
        self.send_button = Button(text='Send\n(Shift+Enter)')
        self.send_button.bind(on_press=lambda instance: self.send_message())
        button_layout.add_widget(self.send_button)

        # Button to load API Key
        load_api_key_button = Button(text='Load API Key')
        load_api_key_button.bind(on_release=self.show_api_key_popup)
        button_layout.add_widget(load_api_key_button)

        # Toggle button to enable/disable Markdown conversion
        self.toggle_button = ToggleButton(text="HTML", state="down")
        button_layout.add_widget(self.toggle_button)

        # mainlayout.add_widget(button_layout)

        # Buttons row 2
        # button_layout = BoxLayout(size_hint=buttons_size)
        self.type_spinner = Spinner(text='Text', values=['Text', 'Image'])
        button_layout.add_widget(self.type_spinner)
        self.image_size_spinner = Spinner(text="1024x1024", values=["1024x1024", "1024x1792", "1792x1024"])
        button_layout.add_widget(self.image_size_spinner)
        self.image_quality_spinner = Spinner(text='standard',values=['standard', 'hd'])
        button_layout.add_widget(self.image_quality_spinner)
        mainlayout.add_widget(button_layout)


        # Add the loading popup
        self.loading_popup = self.create_loading_popup()

        return mainlayout

    def create_loading_popup(self):
        loading_layout = BoxLayout(orientation='vertical', padding=(10, 10))
        loading_label = TextInput(text='Loading, please wait...', readonly=True, size_hint=(1, 0.5), font_size=18)
        loading_layout.add_widget(loading_label)
        loading_popup = Popup(title="Please wait", content=loading_layout, size_hint=(0.5, 0.3), auto_dismiss=False)
        return loading_popup

    def show_api_key_popup(self, instance):
        popup = ApiKeyPopup(on_confirm=self.set_api_key)
        popup.open()

    def set_api_key(self, api_key):
        self.api_key = api_key
        if not api_key:
            self.response_label.text = "API key empty. Please load an API key.\n" + help_msg
            self.client = None
            return
        print(f"API key set: {self.api_key}")
        self.client = OpenAI(api_key=api_key)
        with open(API_KEY_PATH, 'wt') as f:
            f.write(api_key)

    def send_message(self):
        if self.client is None:
            self.response_label.text = "Please load an API key.\n" + help_msg
            return

        message = self.input_text.text

        if not message:  # Don't send empty message
            self.response_label.text = ''
            return

        selected_model = self.model_spinner.text

        # Show loading popup
        self.loading_popup.open()

        # Run the API call in a separate thread
        threading.Thread(target=self.process_response, args=(message, selected_model)).start()

    def process_response(self, message, model):
        response = self.call_ai_api(message, model)

        # Once done, update the UI from the main thread
        self.update_response(response)

    @mainthread
    def update_response(self, response):
        self.loading_popup.dismiss()
        response = get_display(response)  # Hebrew Arabic support
        self.response_label.text = response

        if self.toggle_button.state == "down":  # Only convert if the toggle is "down"
            convert_markdown_to_output(response, "html")
        else:
            print("Skipping Markdown to HTML conversion.")
    def call_ai_api(self, message, model):
        try:
            if self.type_spinner.text == 'Text':

                completion = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": message}])
                data = completion.model_dump()
                response = data['choices'][0]['message']['content']
                return response
            elif self.type_spinner.text == 'Image':
                response = self.client.images.generate(model=model, prompt=message,
                    size=self.image_size_spinner.text,
                    quality=self.image_quality_spinner.text,
                    n=1,)
                image_url = response.data[0].url
                return image_url

        except Exception as e:
            return str(e)


if __name__ == '__main__':
    AIChatApp().run()
