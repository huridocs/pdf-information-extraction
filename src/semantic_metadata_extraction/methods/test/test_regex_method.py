from unittest import TestCase

from data.PdfTagData import PdfTagData
from data.SemanticExtractionData import SemanticExtractionData
from data.SemanticPredictionData import SemanticPredictionData
from semantic_metadata_extraction.methods.RegexMethod import RegexMethod


class TestRegexMethod(TestCase):
    def test_performance_100(self):
        semantic_information_data = [
            SemanticExtractionData(text="12", pdf_tags=[PdfTagData.from_text("one 12")], language_iso="en") for _ in range(6)
        ]
        regex_method = RegexMethod("regex_test", "regex_test")
        self.assertEqual(100, regex_method.performance(semantic_information_data, 3)[0])

    def test_performance_0(self):
        semantic_information_data = [
            SemanticExtractionData(text="12", pdf_tags=[PdfTagData.from_text("one two")], language_iso="en")
            for _ in range(6)
        ]
        regex_method = RegexMethod("regex_test", "regex_test")
        self.assertEqual(0, regex_method.performance(semantic_information_data, 3)[0])

    def test_performance_50(self):
        semantic_information_data = [
            SemanticExtractionData(text="12", pdf_tags=[PdfTagData.from_text("one 12")], language_iso="en") for _ in range(3)
        ]

        semantic_information_data += [
            SemanticExtractionData(text="no regex", pdf_tags=[PdfTagData.from_text("one two")], language_iso="en")
            for _ in range(1)
        ]
        regex_method = RegexMethod("regex_test", "regex_test")

        self.assertEqual(75, regex_method.performance(semantic_information_data, 3)[0])

    def test_performance_no_samples(self):
        regex_method = RegexMethod("regex_test", "regex_test")

        self.assertEqual((0, []), regex_method.performance([], 3))

    def test_performance_one_sample(self):
        semantic_information_data = [
            SemanticExtractionData(text="12", pdf_tags=[PdfTagData.from_text("one 12")], language_iso="en")
        ]
        regex_method = RegexMethod("regex_test", "regex_test")

        self.assertEqual(100, regex_method.performance(semantic_information_data, 3)[0])

    def test_predict(self):
        semantic_information_data = [SemanticExtractionData(text="12", pdf_tags=[], language_iso="")]
        semantic_information_data += [SemanticExtractionData(text="34", pdf_tags=[], language_iso="")]
        regex_method = RegexMethod("regex_test", "regex_test")

        regex_method.train(semantic_information_data)
        predictions = regex_method.predict(SemanticPredictionData.from_texts(["one 12", "13", "14 foo"]))
        self.assertEqual(3, len(predictions))
        self.assertEqual("12", predictions[0])
        self.assertEqual("13", predictions[1])
        self.assertEqual("14", predictions[2])

    def test_predict_void(self):
        semantic_information_data = [SemanticExtractionData(text="124", pdf_tags=[], language_iso="")]
        semantic_information_data += [SemanticExtractionData(text="344", pdf_tags=[], language_iso="")]
        regex_method = RegexMethod("regex_test", "regex_test")

        regex_method.train(semantic_information_data)
        predictions = regex_method.predict([SemanticPredictionData.from_text("14 foo" "")])
        self.assertEqual(1, len(predictions))
        self.assertEqual("", predictions[0])

    def test_retrain(self):
        semantic_information_data = [SemanticExtractionData(text="1", pdf_tags=[], language_iso="")]
        regex_method = RegexMethod("regex_test", "regex_test")
        regex_method.train(semantic_information_data)

        semantic_information_data = [SemanticExtractionData(text="111", pdf_tags=[], language_iso="")]

        regex_method.train(semantic_information_data)

        predictions = regex_method.predict([SemanticPredictionData.from_text("111")])
        self.assertEqual(1, len(predictions))
        self.assertEqual("111", predictions[0])
