from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.listview import ListView, ListItemButton
import pandas as pd
from fuzzywuzzy import process

class HomeopathyNameSearchApp(App):
    def build(self):
        self.title = "Homeopathy Name Search"
        self.data = self.load_data()
        self.lookup_latin_to_common = {row['Latin'].lower(): row['Common'] for _, row in self.data.iterrows()}
        self.lookup_common_to_latin = {row['Common'].lower(): row['Latin'] for _, row in self.data.iterrows()}

        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.search_input = TextInput(hint_text="Enter remedy name", multiline=False)
        self.search_input.bind(text=self.on_text_change)
        layout.add_widget(self.search_input)

        self.direction_spinner = Spinner(text='Latin to Common', values=('Latin to Common', 'Common to Latin'))
        layout.add_widget(self.direction_spinner)

        self.results_scroll = ScrollView(size_hint=(1, 0.7))
        self.results_layout = GridLayout(cols=1, size_hint_y=None)
        self.results_layout.bind(minimum_height=self.results_layout.setter('height'))
        self.results_scroll.add_widget(self.results_layout)
        layout.add_widget(self.results_scroll)

        self.status_label = Label(size_hint_y=None, height=40)
        layout.add_widget(self.status_label)

        return layout

    def load_data(self):
        try:
            df = pd.read_excel('remedies.xlsx', engine='openpyxl')
            return df
        except Exception as e:
            self.status_label.text = f"Error loading data: {e}"
            return pd.DataFrame(columns=["Latin", "Common"])

    def on_text_change(self, instance, value):
        self.results_layout.clear_widgets()
        search_direction = self.direction_spinner.text
        if search_direction == 'Latin to Common':
            self.search_latin(value)
        else:
            self.search_common(value)

    def search_latin(self, query):
        matches = process.extract(query, self.lookup_latin_to_common.keys(), limit=10)
        for match, score in matches:
            if score > 70:  # Fuzzy match threshold
                common_name = self.lookup_latin_to_common[match]
                self.results_layout.add_widget(Label(text=f"{common_name} (Latin: {match})"))

    def search_common(self, query):
        matches = process.extract(query, self.lookup_common_to_latin.keys(), limit=10)
        for match, score in matches:
            if score > 70:  # Fuzzy match threshold
                latin_name = self.lookup_common_to_latin[match]
                self.results_layout.add_widget(Label(text=f"{latin_name} (Common: {match})"))

if __name__ == '__main__':
    HomeopathyNameSearchApp().run()