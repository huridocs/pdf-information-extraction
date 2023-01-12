import dataclasses
import hashlib
from statistics import mode

from metadata_extraction.PdfFeatures.PdfFeatures import PdfFeatures


@dataclasses.dataclass
class Modes:
    lines_space_mode: float
    left_space_mode: float
    right_space_mode: float
    font_size_mode: float
    font_family_name_mode: str
    font_family_mode: int
    font_family_mode_normalized: float
    pdf_features: PdfFeatures

    def __init__(self, pdf_features: PdfFeatures):
        self.pdf_features = pdf_features
        self.set_modes()

    def set_modes(self):
        line_spaces, right_spaces, left_spaces = [0], [0], [0]
        for segment_tag in self.pdf_features.get_tags():
            right_spaces.append(self.pdf_features.pages[0].page_width - segment_tag.bounding_box.right)
            left_spaces.append(segment_tag.bounding_box.left)
            line_spaces.append(segment_tag.bounding_box.bottom)

        font_sizes = [segment_tag.font.font_size for segment_tag in self.pdf_features.get_tags() if segment_tag.font]
        self.font_size_mode = mode(font_sizes) if font_sizes else 0
        font_ids = [segment_tag.font.font_id for segment_tag in self.pdf_features.get_tags() if segment_tag.font]
        self.font_family_name_mode = mode(font_ids) if font_ids else ""
        self.font_family_mode = abs(
            int(
                str(hashlib.sha256(self.font_family_name_mode.encode("utf-8")).hexdigest())[:8],
                16,
            )
        )
        self.font_family_mode_normalized = float(f"{str(self.font_family_mode)[0]}.{str(self.font_family_mode)[1:]}")

        self.lines_space_mode = mode(line_spaces)
        self.left_space_mode = mode(left_spaces)
        self.right_space_mode = mode(right_spaces)
