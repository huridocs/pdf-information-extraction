from extractors.pdf_to_text_extractor.methods.SegmentSelectorDateParserMethod import SegmentSelectorSameInputOutputMethod
from extractors.text_to_text_extractor.methods.DateParserWithBreaksMethod import DateParserWithBreaksMethod


class SegmentSelectorDateParserWithBreaksMethod(SegmentSelectorSameInputOutputMethod):

    SEMANTIC_METHOD = DateParserWithBreaksMethod
