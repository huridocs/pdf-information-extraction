import os
import shutil
from math import exp
from os.path import join, exists
from pathlib import Path
import ollama
from config import ROOT_PATH
from data.Option import Option
from data.ExtractionData import ExtractionData
from data.TrainingSample import TrainingSample
from extractors.pdf_to_multi_option_extractor.MultiLabelMethod import MultiLabelMethod


class ZeroShot20Classes(MultiLabelMethod):
    top_options = [
        "intellectual property",
        "telecommunication",
        "access to information",
        "privacy",
        "freedom of expression",
        "constitution",
        "electronic communications",
        "data protection and retention",
        "trademark",
        "cybercrime",
        "copyright",
        "media/press",
        "defamation",
        "data protection",
        "intermediary liability",
        "e-transactions",
        "broadcasting networks",
        "surveillance",
        "internet service providers",
        "national security",
    ]

    def can_be_used(self, extraction_data: ExtractionData) -> bool:
        return True

    @staticmethod
    def get_text(sample: TrainingSample) -> str:
        file_name = sample.pdf_data.pdf_features.file_name.replace(".pdf", ".txt")
        text = Path(ROOT_PATH, "data", "cyrilla_summaries", file_name).read_text()

        if "three sentence" in text.split(":")[0]:
            text = ":".join(text.split(":")[1:]).strip()

        return text if text else "No text"

    def train(self, multi_option_data: ExtractionData):
        pass

    def predict(self, multi_option_data: ExtractionData) -> list[list[Option]]:
        option_labels = [option.label for option in self.options]
        predictions = list()
        for sample in multi_option_data.samples:
            predictions.append(list())
            text = self.get_text(sample)
            response = ollama.chat(
                model="llama3.1:latest",
                messages=[
                    {
                        "role": "user",
                        "content": f'''Answer the question based on the following context:
                    
                    {text}
                    
                    Select the most relevant keywords from the following list based on the above text: 
                    {'\n'.join(self.top_options)}
''',
                    }
                ],
            )

            responses = response["message"]["content"]

            for keyword in self.top_options:
                response_keywords = [x.lower() for x in responses.split("**")]
                if keyword.lower() in response_keywords:
                    index = option_labels.index(keyword)
                    predictions[-1].append(self.options[index])

        return predictions
