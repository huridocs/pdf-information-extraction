import os
import shutil
from os.path import join, exists
from pathlib import Path
from time import time

import pymongo

from config import config_logger, MONGO_PORT, MONGO_HOST, DATA_PATH
from data.ExtractionIdentifier import ExtractionIdentifier
from data.LabeledData import LabeledData
from data.Option import Option

from data.PredictionData import PredictionData
from data.PredictionSample import PredictionSample
from data.SegmentationData import SegmentationData
from data.Suggestion import Suggestion
from data.ExtractionTask import ExtractionTask
from FilterValidSegmentsPages import FilterValidSegmentsPages
from extractors.ExtractorBase import ExtractorBase
from extractors.NaiveExtractor import NaiveExtractor
from extractors.pdf_to_text_extractor.PdfToTextExtractor import PdfToTextExtractor
from data.PdfData import PdfData

from XmlFile import XmlFile
from data.ExtractionData import ExtractionData
from data.TrainingSample import TrainingSample
from extractors.pdf_to_multi_option_extractor.PdfToMultiOptionExtractor import PdfToMultiOptionExtractor
from extractors.text_to_text_extractor.TextToTextExtractor import TextToTextExtractor


class Extractor:
    EXTRACTORS: list[type[ExtractorBase]] = [
        PdfToMultiOptionExtractor,
        PdfToTextExtractor,
        TextToTextExtractor,
        NaiveExtractor]

    CREATE_MODEL_TASK_NAME = "create_model"
    SUGGESTIONS_TASK_NAME = "suggestions"

    def __init__(self, extraction_identifier: ExtractionIdentifier, options: list[Option] = None, multi_value: bool = False):
        self.extraction_identifier = extraction_identifier
        self.multi_value = multi_value
        self.options = options
        client = pymongo.MongoClient(f"{MONGO_HOST}:{MONGO_PORT}")
        self.pdf_metadata_extraction_db = client["pdf_metadata_extraction"]
        self.mongo_filter = {"tenant": self.extraction_identifier.run_name, "id": self.extraction_identifier.extraction_name}

    def get_labeled_data(self):
        labeled_data_list = []
        for document in self.pdf_metadata_extraction_db.labeled_data.find(self.mongo_filter):
            labeled_data_list.append(LabeledData(**document))

        return labeled_data_list

    def get_extraction_data_for_training(self, labeled_data_list: list[LabeledData]) -> ExtractionData:
        multi_option_samples: list[TrainingSample] = list()
        page_numbers_list = FilterValidSegmentsPages(self.extraction_identifier).for_training(labeled_data_list)
        for labeled_data, page_numbers_to_keep in zip(labeled_data_list, page_numbers_list):
            segmentation_data = SegmentationData.from_labeled_data(labeled_data)
            xml_file = XmlFile(
                extraction_identifier=self.extraction_identifier,
                to_train=True,
                xml_file_name=labeled_data.xml_file_name,
            )

            pdf_data = PdfData.from_xml_file(xml_file, segmentation_data, page_numbers_to_keep)
            sample = TrainingSample(pdf_data=pdf_data, labeled_data=labeled_data, tags_texts=[labeled_data.source_text])
            multi_option_samples.append(sample)

        return ExtractionData(
            samples=multi_option_samples,
            options=self.options,
            multi_value=self.multi_value,
            extraction_identifier=self.extraction_identifier,
        )

    def create_models(self) -> (bool, str):
        start = time()
        config_logger.info(f"Loading data to create model for {str(self.extraction_identifier)}")
        extraction_data: ExtractionData = self.get_extraction_data_for_training(self.get_labeled_data())
        config_logger.info(f"Set data in {round(time() - start, 2)} seconds")

        for extractor in self.EXTRACTORS:
            extractor_instance = extractor(self.extraction_identifier)

            if not extractor_instance.is_valid(extraction_data):
                continue

            self.extraction_identifier.get_extractor_used_path().write_text(extractor_instance.get_name())
            self.delete_training_data()
            return extractor_instance.create_model(extraction_data)

        self.delete_training_data()
        return False, "Error creating extractor"

    def get_prediction_samples(self, prediction_data_list: list[PredictionData] = None) -> list[PredictionSample]:
        filter_valid_pages = FilterValidSegmentsPages(self.extraction_identifier)
        page_numbers_list = filter_valid_pages.for_prediction(prediction_data_list)
        prediction_samples: list[PredictionSample] = []
        for prediction_data, page_numbers in zip(prediction_data_list, page_numbers_list):
            segmentation_data = SegmentationData.from_prediction_data(prediction_data)
            xml_file = XmlFile(
                extraction_identifier=self.extraction_identifier,
                to_train=False,
                xml_file_name=prediction_data.xml_file_name,
            )
            pdfs_data = PdfData.from_xml_file(xml_file, segmentation_data, page_numbers)
            entity_name = prediction_data.entity_name if prediction_data.entity_name else prediction_data.xml_file_name
            sample = PredictionSample(pdf_data=pdfs_data, entity_name=entity_name, tags_texts=[prediction_data.source_text])
            prediction_samples.append(sample)

        return prediction_samples

    def get_prediction_data_from_db(self):
        prediction_data_list = []
        for document in self.pdf_metadata_extraction_db.prediction_data.find(self.mongo_filter):
            prediction_data_list.append(PredictionData(**document))
        return prediction_data_list

    def delete_training_data(self):
        training_xml_path = XmlFile.get_xml_folder_path(extraction_identifier=self.extraction_identifier, to_train=True)
        shutil.rmtree(training_xml_path, ignore_errors=True)
        self.pdf_metadata_extraction_db.labeled_data.delete_many(self.mongo_filter)

    def insert_suggestions_in_db(self, suggestions: list[Suggestion]) -> (bool, str):
        if not suggestions:
            return False, "No data to calculate suggestions"

        config_logger.info(f"Calculated and inserting {len(suggestions)} suggestions")

        self.pdf_metadata_extraction_db.suggestions.insert_many([x.to_dict() for x in suggestions])
        xml_folder_path = XmlFile.get_xml_folder_path(extraction_identifier=self.extraction_identifier, to_train=False)
        for suggestion in suggestions:
            xml_name = {"xml_file_name": suggestion.xml_file_name}
            self.pdf_metadata_extraction_db.prediction_data.delete_many({**self.mongo_filter, **xml_name})
            Path(join(xml_folder_path, suggestion.xml_file_name)).unlink(missing_ok=True)

        return True, ""

    def get_suggestions(self) -> list[Suggestion]:
        prediction_samples = self.get_prediction_samples(self.get_prediction_data_from_db())

        if not self.extraction_identifier.get_extractor_used_path().exists():
            return []

        extractor_name = self.extraction_identifier.get_extractor_used_path().read_text()
        for extractor in self.EXTRACTORS:
            extractor_instance = extractor(self.extraction_identifier)
            if extractor_instance.get_name() != extractor_name:
                continue

            return extractor_instance.get_suggestions(prediction_samples)

    @staticmethod
    def remove_old_models(extractor_identifier: ExtractionIdentifier):
        if exists(extractor_identifier.get_path()):
            os.utime(extractor_identifier.get_path())

        for run_name in os.listdir(DATA_PATH):
            if run_name == "cache":
                continue

            for extraction_name in os.listdir(join(DATA_PATH, run_name)):
                extractor_identifier_to_check = ExtractionIdentifier(run_name=run_name, extraction_name=extraction_name)
                if extractor_identifier_to_check.is_old():
                    shutil.rmtree(extractor_identifier_to_check.get_path(), ignore_errors=True)

    @staticmethod
    def calculate_task(extraction_task: ExtractionTask) -> (bool, str):
        extraction_name = extraction_task.params.id
        extractor_identifier = ExtractionIdentifier(run_name=extraction_task.tenant, extraction_name=extraction_name)
        Extractor.remove_old_models(extractor_identifier)

        if extraction_task.task == Extractor.CREATE_MODEL_TASK_NAME:
            options = extraction_task.params.options
            multi_value = extraction_task.params.multi_value
            extractor = Extractor(extractor_identifier, options, multi_value)
            return extractor.create_models()

        if extraction_task.task == Extractor.SUGGESTIONS_TASK_NAME:
            config_logger.info("Calculating suggestions")
            extractor = Extractor(extractor_identifier)
            suggestions = extractor.get_suggestions()
            return extractor.insert_suggestions_in_db(suggestions)

        return False, "Error"
