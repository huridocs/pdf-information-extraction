import json
from os.path import join
from pathlib import Path

from pdf_topic_classification.PdfLabels import PdfLabels

PDF_TOPIC_CLASSIFICATION_LABELED_DATA_PATH = join(Path(__file__).parent, "labeled_data")


class PdfTopicClassificationLabeledData:
    def __init__(self, labeled_data_task: str):
        self.labeled_data_task = labeled_data_task

        with open(join(PDF_TOPIC_CLASSIFICATION_LABELED_DATA_PATH, labeled_data_task, "options.json"), mode="r") as file:
            self.options: list[str] = json.load(file)

        with open(join(PDF_TOPIC_CLASSIFICATION_LABELED_DATA_PATH, labeled_data_task, "labels.json"), mode="r") as file:
            labels_dict: dict[str, list[str]] = json.load(file)
            self.pdfs_labels: list[PdfLabels] = [PdfLabels.from_dicts(label_dict) for label_dict in labels_dict.items()]

        self.multi_option = len([pdf_label for pdf_label in self.pdfs_labels if len(pdf_label.labels) > 1]) != 0

    def get_pdfs_names(self):
        return [x.pdf_name for x in self.pdfs_labels]
