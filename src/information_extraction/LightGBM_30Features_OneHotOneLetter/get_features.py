from collections import Counter
from pathlib import Path
from typing import List, Tuple, Dict
from numpy import unique
import string
import ast


THIS_SCRIPT_PATH = Path(__file__).parent


class PdfAltoXml:
    def __init__(self, pdf_features):
        self.pdf_features = pdf_features
        self.tuples_to_check = list()

        self.lines_space_mode: float = 0
        self.right_space_mode: float = 0
        self.font_size_mode: float = 0

        self.letter_corpus: Dict[str, int] = dict()
        with open(f"{THIS_SCRIPT_PATH}/letter_corpus.txt", "r") as corpus_file:
            corpus_contents = corpus_file.read()
            self.letter_corpus = ast.literal_eval(corpus_contents)
        self.len_letter_corpus = len(unique(list(self.letter_corpus.values())))

        self.get_modes()
        self.get_mode_font()

    def get_modes(self):
        line_spaces, right_spaces, left_spaces = [0], [0], [0]

        for page in self.pdf_features.pages:
            for tag in page.tags:
                top, height = tag.bounding_box.top, tag.bounding_box.height
                left, width = tag.bounding_box.left, tag.bounding_box.width
                bottom, right = tag.bounding_box.bottom, tag.bounding_box.right

                on_the_bottom = list(filter(lambda x: bottom < x.bounding_box.top, page.tags))

                if len(on_the_bottom) > 0:
                    line_spaces.append(min(map(lambda x: int(x.bounding_box.top - bottom), on_the_bottom)))

                same_line_tags = filter(
                    lambda x: (top <= x.bounding_box.top < bottom) or (top < x.bounding_box.bottom <= bottom), page.tags
                )
                on_the_right = filter(lambda x: right < x.bounding_box.left, same_line_tags)
                on_the_left = filter(lambda x: x.bounding_box.left < left, same_line_tags)

                if len(list(on_the_right)) == 0:
                    right_spaces.append(int(right))

                if len(list(on_the_left)) == 0:
                    left_spaces.append(int(left))

        self.lines_space_mode = max(set(line_spaces), key=line_spaces.count)
        self.right_space_mode = int(self.pdf_features.pages[0].page_width - max(set(right_spaces), key=right_spaces.count))

    def get_mode_font(self):
        fonts_counter: Counter = Counter()
        for page in self.pdf_features.pages:
            for tag in page.tags:
                fonts_counter.update([tag.font.font_id])

        if len(fonts_counter.most_common()) == 0:
            return

        font_mode_id = fonts_counter.most_common()[0][0]
        font_mode_tag = list(filter(lambda x: x.font_id == font_mode_id, self.pdf_features.fonts))
        if len(font_mode_tag) == 1:
            self.font_size_mode: float = float(font_mode_tag[0].font_size)

    def get_features_for_given_tags(self, tag_1, tag_2, tags_for_page):

        top_1 = tag_1.bounding_box.top
        left_1 = tag_1.bounding_box.left
        right_1 = tag_1.bounding_box.right
        height_1 = tag_1.bounding_box.height
        width_1 = tag_1.bounding_box.width

        on_the_right_left_1, on_the_right_right_1 = self.get_on_the_right_block(tag_1, tags_for_page)
        on_the_left_left_1, on_the_left_right_1 = self.get_on_the_left_block(tag_1, tags_for_page)

        right_gap_1 = on_the_right_left_1 - right_1

        top_2 = tag_2.bounding_box.top
        left_2 = tag_2.bounding_box.left
        right_2 = tag_2.bounding_box.right
        height_2 = tag_2.bounding_box.height
        width_2 = tag_2.bounding_box.width

        on_the_right_left_2, on_the_right_right_2 = self.get_on_the_right_block(tag_2, tags_for_page)
        on_the_left_left_2, on_the_left_right_2 = self.get_on_the_left_block(tag_2, tags_for_page)
        left_gap_2 = left_2 - on_the_left_right_2

        absolute_right_1 = max(left_1 + width_1, on_the_right_right_1)
        absolute_right_2 = max(left_2 + width_2, on_the_right_right_2)

        end_lines_difference = abs(absolute_right_1 - absolute_right_2)

        on_the_left_left_1 = left_1 if on_the_left_left_1 == 0 else on_the_left_left_1
        on_the_left_left_2 = left_2 if on_the_left_left_2 == 0 else on_the_left_left_2
        absolute_left_1 = min(left_1, on_the_left_left_1)
        absolute_left_2 = min(left_2, on_the_left_left_2)

        start_lines_differences = absolute_left_1 - absolute_left_2

        tags_in_the_middle = list(filter(lambda x: tag_1.bounding_box.bottom <= x.bounding_box.top < top_2, tags_for_page))
        tags_in_the_middle_top = (
            max(map(lambda x: x.bounding_box.top, tags_in_the_middle)) if len(tags_in_the_middle) > 0 else 0
        )
        tags_in_the_middle_bottom = (
            min(map(lambda x: x.bounding_box.bottom, tags_in_the_middle)) if len(tags_in_the_middle) > 0 else 0
        )

        top_distance = top_2 - top_1 - height_1

        gap_middle_top = tags_in_the_middle_top - top_1 - height_1 if tags_in_the_middle_top > 0 else 0
        gap_middle_bottom = top_2 - tags_in_the_middle_bottom if tags_in_the_middle_bottom > 0 else 0

        top_distance_gaps = top_distance - (gap_middle_bottom - gap_middle_top)

        right_distance = left_2 - left_1 - width_1
        left_distance = left_1 - left_2

        height_difference = height_1 - height_2

        same_font = True if tag_1.font.font_id == tag_2.font.font_id else False

        tag_1_first_letter: List
        tag_1_last_letter: List
        tag_2_first_letter: List
        tag_2_last_letter: List

        if tag_1.id == "pad_tag":
            tag_1_first_letter = self.len_letter_corpus * [-1]
            tag_1_last_letter = self.len_letter_corpus * [-1]
        else:
            tag_1_first_letter = self.len_letter_corpus * [0]
            if tag_1.content[0] in self.letter_corpus.keys():
                tag_1_first_letter[self.letter_corpus[tag_1.content[0]]] = 1
            tag_1_last_letter = self.len_letter_corpus * [0]
            if tag_1.content[-1] in self.letter_corpus.keys():
                tag_1_last_letter[self.letter_corpus[tag_1.content[-1]]] = 1

        if tag_2.id == "pad_tag":
            tag_2_first_letter = self.len_letter_corpus * [-1]
            tag_2_last_letter = self.len_letter_corpus * [-1]
        else:
            tag_2_first_letter = self.len_letter_corpus * [0]
            if tag_2.content[0] in self.letter_corpus.keys():
                tag_2_first_letter[self.letter_corpus[tag_2.content[0]]] = 1
            tag_2_last_letter = self.len_letter_corpus * [0]
            if tag_2.content[-1] in self.letter_corpus.keys():
                tag_2_last_letter[self.letter_corpus[tag_2.content[-1]]] = 1

        features = [
            self.font_size_mode / 100,
            same_font,
            absolute_right_1,
            top_1,
            right_1,
            width_1,
            height_1,
            top_2,
            right_2,
            width_2,
            height_2,
            top_distance,
            top_distance - self.lines_space_mode,
            top_distance_gaps,
            self.lines_space_mode - top_distance_gaps,
            self.right_space_mode - absolute_right_1,
            top_distance - height_1,
            start_lines_differences,
            right_distance,
            left_distance,
            right_gap_1,
            left_gap_2,
            height_difference,
            end_lines_difference,
            len(tag_1.content),
            len(tag_2.content),
            tag_1.content.count(" "),
            tag_2.content.count(" "),
            sum(character in string.punctuation for character in tag_1.content),
            sum(character in string.punctuation for character in tag_2.content),
            # sum(character in tag_1.content for character in string.punctuation),
            # sum(character in tag_2.content for character in string.punctuation),
        ]

        features.extend(tag_1_first_letter)
        features.extend(tag_1_last_letter)
        features.extend(tag_2_first_letter)
        features.extend(tag_2_last_letter)

        return features

    @staticmethod
    def get_on_the_right_block(tag, tags):
        top = tag.bounding_box.top
        height = tag.bounding_box.height
        left = tag.bounding_box.left

        on_the_right = list(
            filter(
                lambda x: (top <= x.bounding_box.top < (top + height)) or (top < (x.bounding_box.bottom) <= (top + height)),
                tags,
            )
        )

        on_the_right = list(filter(lambda x: left < x.bounding_box.left, on_the_right))
        on_the_right_left = 0 if len(on_the_right) == 0 else min(map(lambda x: x.bounding_box.left, on_the_right))
        on_the_right_right = 0 if len(on_the_right) == 0 else max(map(lambda x: x.bounding_box.right, on_the_right))

        return on_the_right_left, on_the_right_right

    @staticmethod
    def get_on_the_left_block(tag, tags):
        top = tag.bounding_box.top
        height = tag.bounding_box.height
        right = tag.bounding_box.right

        on_the_left = list(
            filter(
                lambda x: (top <= x.bounding_box.top < (top + height)) or (top < (x.bounding_box.bottom) <= (top + height)),
                tags,
            )
        )

        on_the_left = list(filter(lambda x: x.bounding_box.right < right, on_the_left))
        on_the_left_left = 0 if len(on_the_left) == 0 else min(map(lambda x: x.bounding_box.left, on_the_left))
        on_the_left_right = 0 if len(on_the_left) == 0 else max(map(lambda x: x.bounding_box.right, on_the_left))

        return on_the_left_left, on_the_left_right
