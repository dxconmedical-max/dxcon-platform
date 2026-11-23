from app.reception_workspace.barcode_engine import code128_svg, render_tube_label_html


def test_code128_svg_has_bars():
    svg = code128_svg("SMP-0001")
    assert svg.startswith("<svg") and "<rect" in svg


def test_tube_label_sizes():
    labels = [{"code": "SMP-0001", "title": "Sample", "lines": ["Glucose (GLU)"], "sample": {"sample_type": "Serum"}}]
    assert "size: 50mm 25mm" in render_tube_label_html(labels, size="tube50")
    assert "size: 45mm 25mm" in render_tube_label_html(labels, size="tube45")
