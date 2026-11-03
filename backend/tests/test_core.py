from app.services.report_extraction import extract_parameters
from app.services.report_analysis import analyze, compare
from app.ml.classification import topic
from pathlib import Path
from app.services.document_ocr import extract_document
from app.services.ai_service import _demo_topic
def test_ranges_are_report_supplied_only():
    result=analyze(extract_parameters("Haemoglobin 11.2 g/dL (13.0 - 17.0)\nVitamin D 18 ng/mL"))
    states={p["name"]:p["status"] for p in result["parameters"]}
    assert states["Haemoglobin"]=="below_range"
    assert states["Vitamin D"]=="no_reference_range"
def test_compare():
    old=analyze(extract_parameters("Glucose 100 mg/dL (70 - 100)"))
    new=analyze(extract_parameters("Glucose 90 mg/dL (70 - 100)"))
    assert compare(old,new)[0]["change"]==-10

def test_table_style_report_rows_extract_printed_ranges_and_confidence():
    params = extract_parameters(
        "Hemoglobin 13.4 g/dL 12.0 16.0\n"
        "WBC 7.2 4.0-11.0 x10^3/uL\n"
    )
    assert [(p.name, p.value, p.ref_low, p.ref_high) for p in params] == [
        ("Hemoglobin", 13.4, 12.0, 16.0),
        ("WBC", 7.2, 4.0, 11.0),
    ]
    assert all(p.confidence > 0.9 for p in params)

def test_multi_page_text_tracks_source_page():
    params = extract_parameters("Hemoglobin 13.4 g/dL (12.0 - 16.0)\fWBC 7.2 x10^3/uL (4.0 - 11.0)")
    assert [p.source_page for p in params] == [1, 2]

def test_packaged_sample_lab_pdf_regression():
    sample = Path(__file__).resolve().parents[2] / "assets" / "sample_lab_report.pdf"
    document = extract_document(sample.read_bytes(), sample.name, "application/pdf")
    params = extract_parameters(document.text)
    assert document.method == "pdf-text"
    assert params, "The included sample lab report should continue to yield parameters."
def test_topic_classifier():
    assert topic("explain my cholesterol results")=="lipid"

def test_demo_assistant_matches_topics_without_substring_false_positives():
    assert _demo_topic("What does a high LDL mean?") == "lipid"
    assert _demo_topic("Can salty food affect me?") == "general"
    assert _demo_topic("How can I improve my neend?") == "sleep"
    assert _demo_topic("Mera blood sugar high hai") == "diabetes"
