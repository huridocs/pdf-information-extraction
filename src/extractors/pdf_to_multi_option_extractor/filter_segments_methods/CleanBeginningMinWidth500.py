from copy import deepcopy

from pdf_features.Rectangle import Rectangle
from pdf_token_type_labels.TokenType import TokenType

from data.PdfDataSegment import PdfDataSegment
from extractors.pdf_to_multi_option_extractor.FilterSegmentsMethod import FilterSegmentsMethod


class CleanBeginningMinWidth500(FilterSegmentsMethod):
    valid_types = [TokenType.TEXT, TokenType.LIST_ITEM]

    def get_first_tokens(self, pdf_data_segments: list[PdfDataSegment], text_length: int) -> list[PdfDataSegment]:
        total_text = ""
        filtered_segments: list[PdfDataSegment] = list()
        for pdf_data_segment in [x for x in pdf_data_segments if x.segment_type in self.valid_types]:
            pdf_data_segment_copy = self.clean_content_pdf_token(pdf_data_segment, text_length - len(total_text))

            if not pdf_data_segment_copy:
                break

            if pdf_data_segment_copy.text_content and "." == pdf_data_segment.text_content[-1]:
                pdf_data_segment_copy.text_content += "."

            total_text += " " + pdf_data_segment_copy.text_content
            filtered_segments.append(pdf_data_segment_copy)

        if not pdf_data_segments or "".join([x.text_content.strip() for x in filtered_segments]) == "":
            return [PdfDataSegment(1, Rectangle(0, 0, 0, 0), "no text")]

        return filtered_segments

    @staticmethod
    def clean_content_pdf_token(pdf_data_segment: PdfDataSegment, character_limit: int):
        if character_limit <= 0:
            return None

        pdf_data_segment.ml_label = 1
        pdf_data_segment_copy = deepcopy(pdf_data_segment)
        words = list()
        text = ""
        for word in pdf_data_segment_copy.text_content.split():
            clean_word = "".join([x for x in word if x.isalpha()])

            if len(text + " " + clean_word) > character_limit:
                break

            if clean_word:
                words.append(clean_word)
                text += " " + word

        pdf_data_segment_copy.text_content = " ".join(words)
        return pdf_data_segment_copy

    def filter_segments(self, pdf_data_segments: list[PdfDataSegment]) -> list[PdfDataSegment]:
        if not pdf_data_segments:
            return pdf_data_segments

        min_left = min([x.bounding_box.left for x in pdf_data_segments])
        max_right = max([x.bounding_box.right for x in pdf_data_segments])
        min_width = (max_right - min_left) * 0.9

        min_width_segments = []
        while 0 < min_width:
            min_width_segments = [
                x for x in pdf_data_segments if x.bounding_box.width > min_width and x.segment_type in self.valid_types
            ]
            if not min_width_segments:
                min_width -= 10
                continue
            break

        return self.get_first_tokens(min_width_segments, 500)
