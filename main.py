import os.path
from kivy.core.window import Window
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from openai import OpenAI
from kivy.uix.scrollview import ScrollView


API_KEY_PATH = 'api_key.txt'


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


class AIChatApp(App):
    def build(self):
        mainlayout = BoxLayout(orientation='vertical', spacing=10, padding=10)

        if os.path.exists(API_KEY_PATH):
            with open(API_KEY_PATH, 'rt') as f:
                self.api_key = f.read()
                print(f'Loaded api ky from file: {self.api_key}')
                self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None

        self.input_text = TextInput(hint_text="Enter your message here", size_hint=(1, 0.2))
        mainlayout.add_widget(self.input_text)

        # # Label to show response
        scrollview = ScrollView(size_hint=(1, 1), do_scroll_x=False, do_scroll_y=True, scroll_type=['bars'])
        self.response_label = TextInput(
            text="", size_hint_y=None, height='1000dp', readonly=True, multiline=True, font_size=18,
            cursor_blink=True,
        )

        scrollview.add_widget(self.response_label)
        mainlayout.add_widget(scrollview)

        # Keyboard: Allow message send with shift+enter
        def _on_keyboard(instance, key, scancode, codepoint, modifiers):
            if key == 13 and 'shift' in modifiers:
                self.send_message()
        Window.bind(on_keyboard=_on_keyboard)

        # Buttons:
        buttons_size = (1, 0.3)
        button_layout = BoxLayout(size_hint=buttons_size)

        # Spinner for model selection.
        # To view full list run:  print('Available models:\n', [model.id for model in self.client.models.list()])
        models = ('gpt-4o', 'gpt-4-turbo', 'chatgpt-4o-latest', 'gpt-3.5-turbo', 'gpt-4')
        self.model_spinner = Spinner(
            text=models[0],
            values=models,
            size_hint=buttons_size
        )
        button_layout.add_widget(self.model_spinner)

        # Button to send message
        self.send_button = Button(text='Send (Shift+Enter)', size_hint=buttons_size)
        self.send_button.bind(on_press=lambda instance: self.send_message())
        button_layout.add_widget(self.send_button)

        # Button to load API Key
        load_api_key_button = Button(text='Load API Key', size_hint=buttons_size)
        load_api_key_button.bind(on_release=self.show_api_key_popup)
        button_layout.add_widget(load_api_key_button)

        mainlayout.add_widget(button_layout)
        return mainlayout

    def show_api_key_popup(self, instance):
        popup = ApiKeyPopup(on_confirm=self.set_api_key)
        popup.open()

    def set_api_key(self, api_key):
        self.api_key = api_key
        if not api_key:
            self.response_label.text = "API key empty. Please load an API key."
            self.client = None
            return
        print(f"API key set: {self.api_key}")
        self.client = OpenAI(api_key=api_key)
        with open(API_KEY_PATH, 'wt') as f:
            f.write(api_key)

    def send_message(self):

        if self.client is None:
            self.response_label.text = "Please load an API key."
            return

        message = self.input_text.text

        if not message:  # Don't send empty message
            self.response_label.text = ''
            return

        selected_model = self.model_spinner.text
        response = self.call_ai_api(message, selected_model)
        self.response_label.text = response

    def call_ai_api(self, message, model):
        try:
            completion = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": message}])
        except Exception as e:
            return str(e)
        data = completion.model_dump()
        response = data['choices'][0]['message']['content']
        return response


if __name__ == '__main__':
    AIChatApp().run()
