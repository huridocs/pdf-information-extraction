import shutil
from os.path import join
from unittest import TestCase

from config import DATA_PATH, APP_PATH
from data.SegmentBox import SegmentBox
from data.SegmentationData import SegmentationData
from metadata_extraction.PdfMetadata import PdfMetadata
from metadata_extraction.XmlFile import XmlFile
from pdf_token_type_labels.TokenType import TokenType


class TestPdfSegments(TestCase):
    test_file_path = f"{APP_PATH}/tenant_test/extraction_id/xml_to_train/test.xml"
    no_pages_file_path = f"{APP_PATH}/tenant_test/extraction_id/xml_to_train/no_pages.xml"

    def test_get_pdf_features(self):
        tenant = "tenant_save"
        extraction_id = "property_save"

        shutil.rmtree(join(DATA_PATH, tenant), ignore_errors=True)

        segmentation_data = SegmentationData(
            page_width=612,
            page_height=792,
            xml_segments_boxes=[
                SegmentBox(
                    left=495.1, top=42.6323, width=56.96199999999999, height=18.2164, page_number=1, type=TokenType.TEXT
                ),
                SegmentBox(left=123.38, top=48.1103, width=82.9812, height=12.7624, page_number=1, type=TokenType.TEXT),
                SegmentBox(
                    left=123.38, top=72.8529, width=148.656, height=17.895700000000005, page_number=1, type=TokenType.TEXT
                ),
                SegmentBox(left=123.38, top=245.184, width=317.406, height=27.5377, page_number=1, type=TokenType.TEXT),
            ],
            label_segments_boxes=[SegmentBox(left=125, top=247, width=319, height=29, page_number=1, type=TokenType.TEXT)],
        )

        with open(self.test_file_path, "rb") as file:
            xml_file = XmlFile(
                tenant=tenant,
                extraction_id=extraction_id,
                to_train=True,
                xml_file_name="test.xml",
            )

            xml_file.save(file=file.read())

        pdf_segments = PdfMetadata.from_xml_file(xml_file, segmentation_data, [])

        self.assertEqual(612, pdf_segments.pdf_features.pages[0].page_width)
        self.assertEqual(792, pdf_segments.pdf_features.pages[0].page_height)
        self.assertEqual(1, len([segment for segment in pdf_segments.pdf_metadata_segments if segment.ml_label == 1]))
        self.assertEqual("A /INF/76/1", pdf_segments.pdf_metadata_segments[0].text_content)
        self.assertEqual("United Nations", pdf_segments.pdf_metadata_segments[1].text_content)
        self.assertEqual("General Assembly", pdf_segments.pdf_metadata_segments[2].text_content)
        self.assertEqual(
            "Opening dates of forthcoming regular sessions of the General Assembly and of the general debate",
            [segment for segment in pdf_segments.pdf_metadata_segments if segment.ml_label == 1][0].text_content,
        )

        shutil.rmtree(join(DATA_PATH, tenant), ignore_errors=True)

    def test_get_pdf_features_when_no_pages(self):
        tenant = "tenant_save"
        extraction_id = "property_save"

        shutil.rmtree(join(DATA_PATH, tenant), ignore_errors=True)
        segmentation_data = SegmentationData(
            page_width=1,  # 612
            page_height=2,  # 396
            xml_segments_boxes=[],
            label_segments_boxes=[],
        )

        with open(self.no_pages_file_path, "rb") as file:
            xml_file = XmlFile(
                tenant=tenant,
                extraction_id=extraction_id,
                to_train=True,
                xml_file_name="no_pages.xml",
            )

            xml_file.save(file=file.read())

        pdf_features = PdfMetadata.from_xml_file(xml_file, segmentation_data, [])

        self.assertEqual(0, len(pdf_features.pdf_metadata_segments))

        shutil.rmtree(join(DATA_PATH, tenant), ignore_errors=True)

    def test_get_pdf_features_when_no_file(self):
        tenant = "tenant_save"
        extraction_id = "property_save"

        shutil.rmtree(join(DATA_PATH, tenant), ignore_errors=True)
        segmentation_data = SegmentationData(
            page_width=1,  # 612
            page_height=2,  # 396
            xml_segments_boxes=[],
            label_segments_boxes=[],
        )

        xml_file = XmlFile(
            tenant=tenant,
            extraction_id=extraction_id,
            to_train=True,
            xml_file_name="test.xml",
        )

        pdf_segments = PdfMetadata.from_xml_file(xml_file, segmentation_data, [])

        self.assertEqual(0, len(pdf_segments.pdf_metadata_segments))

        shutil.rmtree(join(DATA_PATH, tenant), ignore_errors=True)

    def test_get_pdf_features_should_be_empty_when_no_file_because_different_extraction_id(
        self,
    ):
        tenant = "tenant_save"
        extraction_id = "property_save"

        shutil.rmtree(join(DATA_PATH, tenant), ignore_errors=True)

        segmentation_data = SegmentationData(
            page_width=1,  # 612
            page_height=2,  # 396
            xml_segments_boxes=[
                SegmentBox(left=0, top=0.3282828, width=1, height=0.1767676, page_number=2),
            ],
            label_segments_boxes=[
                SegmentBox(
                    left=0.49019,
                    top=0.37878,
                    width=0.008169,
                    height=0.0126,
                    page_number=2,
                )
            ],
        )
        with open(self.test_file_path, "rb") as file:
            XmlFile(
                tenant=tenant,
                extraction_id="different_extraction_id",
                to_train=False,
                xml_file_name="test.xml",
            ).save(file=file.read())

        xml_file = XmlFile(
            tenant=tenant,
            extraction_id=extraction_id,
            to_train=False,
            xml_file_name="test.xml",
        )

        pdf_features = PdfMetadata.from_xml_file(xml_file, segmentation_data, [])

        self.assertEqual(0, len(pdf_features.pdf_metadata_segments))

        shutil.rmtree(join(DATA_PATH, tenant), ignore_errors=True)

    def test_filter_valid_segment_pages(self):
        tenant = "tenant_save"
        extraction_id = "property_save"

        shutil.rmtree(join(DATA_PATH, tenant), ignore_errors=True)

        segmentation_data = SegmentationData(
            page_width=612,
            page_height=792,
            xml_segments_boxes=[SegmentBox(left=1, top=1, width=56.96199999999999, height=18.2164, page_number=1)],
            label_segments_boxes=[SegmentBox(left=125, top=247, width=319, height=29, page_number=1)],
        )

        with open(self.test_file_path, "rb") as file:
            xml_file = XmlFile(
                tenant=tenant,
                extraction_id=extraction_id,
                to_train=True,
                xml_file_name="test.xml",
            )

            xml_file.save(file=file.read())

        pdf_segments = PdfMetadata.from_xml_file(xml_file, segmentation_data, [1])

        self.assertEqual(0, len([segment for segment in pdf_segments.pdf_metadata_segments if segment.page_number > 1]))

        shutil.rmtree(join(DATA_PATH, tenant), ignore_errors=True)
