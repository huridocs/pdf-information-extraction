from typing import List

from pydantic import BaseModel

from data.Option import Option
from data.SegmentBox import SegmentBox


class LabeledDataMultiOption(BaseModel):
    tenant: str
    property_name: str
    xml_file_name: str
    language_iso: str
    options: List[Option]
    page_width: float
    page_height: float
    xml_segments_boxes: List[SegmentBox]
    label_segments_boxes: List[SegmentBox]

    def correct_data_scale(self):
        self.label_segments_boxes = [x.correct_input_data_scale() for x in self.label_segments_boxes]
        return self
