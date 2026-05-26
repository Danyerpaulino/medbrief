from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile


OUT = Path("MedBrief_Stakeholder_Pitch_Single_Slide.pptx")

EMU = 914400
SLIDE_W = 12192000
SLIDE_H = 6858000

P_NS = "http://schemas.openxmlformats.org/presentationml/2006/main"
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
R_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def inch(value: float) -> int:
    return int(value * EMU)


def color_xml(hex_color: str, alpha: int | None = None) -> str:
    alpha_xml = f"<a:alpha val=\"{alpha}\"/>" if alpha is not None else ""
    return f"<a:solidFill><a:srgbClr val=\"{hex_color}\">{alpha_xml}</a:srgbClr></a:solidFill>"


def line_xml(hex_color: str = "FFFFFF", width: int = 0, alpha: int | None = None) -> str:
    if width <= 0:
        return "<a:ln><a:noFill/></a:ln>"
    return f"<a:ln w=\"{width}\">{color_xml(hex_color, alpha)}</a:ln>"


def xfrm(x: float, y: float, w: float, h: float) -> str:
    return (
        "<a:xfrm>"
        f"<a:off x=\"{inch(x)}\" y=\"{inch(y)}\"/>"
        f"<a:ext cx=\"{inch(w)}\" cy=\"{inch(h)}\"/>"
        "</a:xfrm>"
    )


def text_run(text: str, size: int, color: str, bold: bool = False, italic: bool = False) -> str:
    b = " b=\"1\"" if bold else ""
    i = " i=\"1\"" if italic else ""
    return (
        f"<a:r><a:rPr lang=\"en-US\" sz=\"{size}\"{b}{i}>"
        f"{color_xml(color)}"
        "<a:latin typeface=\"Aptos\"/>"
        "<a:cs typeface=\"Aptos\"/>"
        "</a:rPr>"
        f"<a:t>{escape(text)}</a:t></a:r>"
    )


def paragraph(
    text: str,
    size: int,
    color: str,
    bold: bool = False,
    align: str = "l",
    space_after: int = 0,
) -> str:
    spacing = f"<a:spcAft><a:spcPts val=\"{space_after}\"/></a:spcAft>" if space_after else ""
    return (
        "<a:p>"
        f"<a:pPr algn=\"{align}\">{spacing}</a:pPr>"
        f"{text_run(text, size, color, bold)}"
        "</a:p>"
    )


def textbox(
    shape_id: int,
    name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    paragraphs_xml: list[str],
    fill: str | None = None,
    line: str | None = None,
    radius: bool = False,
    margin: int = 91440,
) -> str:
    fill_part = "<a:noFill/>" if fill is None else color_xml(fill)
    line_part = line_xml() if line is None else line
    geom = "roundRect" if radius else "rect"
    return (
        "<p:sp>"
        "<p:nvSpPr>"
        f"<p:cNvPr id=\"{shape_id}\" name=\"{escape(name)}\"/>"
        "<p:cNvSpPr txBox=\"1\"/>"
        "<p:nvPr/>"
        "</p:nvSpPr>"
        f"<p:spPr>{xfrm(x, y, w, h)}<a:prstGeom prst=\"{geom}\"><a:avLst/></a:prstGeom>"
        f"{fill_part}{line_part}</p:spPr>"
        f"<p:txBody><a:bodyPr wrap=\"square\" lIns=\"{margin}\" tIns=\"{margin}\" rIns=\"{margin}\" bIns=\"{margin}\">"
        "<a:spAutoFit/>"
        "</a:bodyPr><a:lstStyle/>"
        f"{''.join(paragraphs_xml)}"
        "</p:txBody>"
        "</p:sp>"
    )


def rect(
    shape_id: int,
    name: str,
    x: float,
    y: float,
    w: float,
    h: float,
    fill: str,
    line_color: str | None = None,
    line_width: int = 0,
    radius: bool = False,
    alpha: int | None = None,
) -> str:
    geom = "roundRect" if radius else "rect"
    line_part = line_xml(line_color or fill, line_width)
    return (
        "<p:sp>"
        "<p:nvSpPr>"
        f"<p:cNvPr id=\"{shape_id}\" name=\"{escape(name)}\"/>"
        "<p:cNvSpPr/>"
        "<p:nvPr/>"
        "</p:nvSpPr>"
        f"<p:spPr>{xfrm(x, y, w, h)}<a:prstGeom prst=\"{geom}\"><a:avLst/></a:prstGeom>"
        f"{color_xml(fill, alpha)}{line_part}</p:spPr>"
        "</p:sp>"
    )


def slide_xml() -> str:
    shapes: list[str] = []

    # Base and brand structure.
    shapes.append(rect(2, "Background", 0, 0, 13.333, 7.5, "F6F8F5"))
    shapes.append(rect(3, "Top Accent", 0, 0, 13.333, 0.12, "31A59A"))
    shapes.append(rect(4, "Left Panel", 0, 0, 3.05, 7.5, "123F4B"))
    shapes.append(rect(5, "Left Panel Accent", 2.95, 0, 0.10, 7.5, "31A59A"))

    shapes.append(
        textbox(
            6,
            "Brand",
            0.35,
            0.42,
            2.35,
            0.74,
            [
                paragraph("MedBrief", 3200, "FFFFFF", True),
                paragraph("AI condition briefings for health-system strategy", 1050, "CFE8E5"),
            ],
            margin=0,
        )
    )

    shapes.append(
        textbox(
            7,
            "Demo Proof",
            0.35,
            1.55,
            2.25,
            2.35,
            [
                paragraph("Trust layer", 1500, "FFFFFF", True, space_after=400),
                paragraph("Citation-grounded outputs", 1050, "DCEDEA"),
                paragraph("Input validation guardrails", 1050, "DCEDEA"),
                paragraph("Confidence scoring for every briefing", 1050, "DCEDEA"),
            ],
            fill="1A5060",
            line=line_xml("6BC5BB", 14000),
            radius=True,
            margin=110000,
        )
    )

    shapes.append(
        textbox(
            8,
            "Decision Ask",
            0.35,
            5.25,
            2.25,
            1.55,
            [
                paragraph("Decision ask", 1300, "123F4B", True),
                paragraph(
                    "Fund a 90-day pilot to turn the demo into a governed decision-intelligence workflow.",
                    1150,
                    "123F4B",
                ),
            ],
            fill="E6F2EE",
            line=line_xml("31A59A", 12000),
            radius=True,
            margin=115000,
        )
    )

    # Main message.
    shapes.append(
        textbox(
            9,
            "Headline",
            3.48,
            0.48,
            8.95,
            0.82,
            [paragraph("Fund trusted clinical intelligence, not just faster research", 2850, "14313A", True)],
            margin=0,
        )
    )
    shapes.append(
        textbox(
            10,
            "Subhead",
            3.50,
            1.26,
            8.45,
            0.50,
            [
                paragraph(
                    "MedBrief turns fragmented literature and trial data into citation-backed, guarded, confidence-aware briefings for strategic decisions.",
                    1320,
                    "486365",
                )
            ],
            margin=0,
        )
    )

    # Process strip.
    steps = [
        ("Condition", "E7F2EF", "123F4B"),
        ("Validation guard", "FBEAE6", "8D3D2B"),
        ("Grounded synthesis", "EAF1FA", "1F4E79"),
        ("Confidence score", "FFF3D9", "7A5212"),
    ]
    x = 3.50
    for i, (label, fill, color) in enumerate(steps):
        shapes.append(
            textbox(
                11 + i,
                f"Step {i + 1}",
                x + i * 2.05,
                1.95,
                1.62,
                0.45,
                [paragraph(label, 1050, color, True, align="c")],
                fill=fill,
                line=line_xml("D6E3DF", 9000),
                radius=True,
                margin=35000,
            )
        )
        if i < len(steps) - 1:
            shapes.append(
                textbox(
                    20 + i,
                    f"Arrow {i + 1}",
                    x + i * 2.05 + 1.64,
                    1.99,
                    0.36,
                    0.30,
                    [paragraph(">", 1150, "7B9292", True, align="c")],
                    margin=0,
                )
            )

    # Outcome cards.
    cards = [
        (
            "Trust the source base",
            "Citation grounding",
            "Tie claims back to PubMed and ClinicalTrials.gov evidence so stakeholders can inspect why the answer is credible.",
            "31A59A",
        ),
        (
            "Reduce misuse risk",
            "Input validation guard",
            "Reject unsafe or off-scope prompts before processing, demonstrating safety-first product discipline.",
            "2F6F9F",
        ),
        (
            "Make uncertainty visible",
            "Confidence scoring",
            "Show where the system is strong, weak, or evidence-limited so leaders know when to escalate review.",
            "D69A2D",
        ),
    ]
    card_x = [3.50, 6.40, 9.30]
    for idx, (title, metric, body, accent) in enumerate(cards):
        shapes.append(rect(30 + idx, f"Card {idx + 1} Base", card_x[idx], 2.85, 2.58, 2.18, "FFFFFF", "DBE4E0", 10000, True))
        shapes.append(rect(40 + idx, f"Card {idx + 1} Accent", card_x[idx], 2.85, 2.58, 0.10, accent, radius=True))
        shapes.append(
            textbox(
                50 + idx,
                f"Card {idx + 1} Text",
                card_x[idx] + 0.18,
                3.08,
                2.20,
                1.62,
                [
                    paragraph(title, 1450, "14313A", True),
                    paragraph(metric, 1120, accent, True),
                    paragraph(body, 970, "526B6C"),
                ],
                margin=0,
            )
        )

    # Funding outcome band.
    shapes.append(rect(60, "Funding Outcome Band", 3.50, 5.55, 8.65, 1.22, "14313A", radius=True))
    shapes.append(
        textbox(
            61,
            "Funding Outcome Text",
            3.78,
            5.74,
            4.25,
            0.84,
            [
                paragraph("Funding outcome", 1220, "9DE0D6", True),
                paragraph(
                    "A measured pilot proving faster diligence with traceable evidence, safer usage boundaries, and transparent confidence.",
                    1150,
                    "FFFFFF",
                ),
            ],
            margin=0,
        )
    )
    shapes.append(rect(62, "Band Divider", 8.25, 5.72, 0.015, 0.84, "4E7577"))
    shapes.append(
        textbox(
            63,
            "Pilot Deliverables",
            8.48,
            5.72,
            3.25,
            0.88,
            [
                paragraph("Pilot deliverables", 1050, "9DE0D6", True),
                paragraph("Citation grounding | validation guardrails | confidence scoring | export-ready briefings", 940, "DDEDEA"),
            ],
            margin=0,
        )
    )

    sp_tree = (
        "<p:spTree>"
        "<p:nvGrpSpPr><p:cNvPr id=\"1\" name=\"\"/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>"
        "<p:grpSpPr><a:xfrm><a:off x=\"0\" y=\"0\"/><a:ext cx=\"0\" cy=\"0\"/>"
        "<a:chOff x=\"0\" y=\"0\"/><a:chExt cx=\"0\" cy=\"0\"/></a:xfrm></p:grpSpPr>"
        f"{''.join(shapes)}"
        "</p:spTree>"
    )

    return (
        "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
        f"<p:sld xmlns:a=\"{A_NS}\" xmlns:r=\"{R_NS}\" xmlns:p=\"{P_NS}\">"
        "<p:cSld>"
        f"<p:bg><p:bgPr>{color_xml('F6F8F5')}<a:effectLst/></p:bgPr></p:bg>"
        f"{sp_tree}"
        "</p:cSld>"
        "<p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>"
        "</p:sld>"
    )


def content_types() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/>
  <Override PartName="/ppt/slideMasters/slideMaster1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"/>
  <Override PartName="/ppt/slideLayouts/slideLayout1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"/>
  <Override PartName="/ppt/theme/theme1.xml" ContentType="application/vnd.openxmlformats-officedocument.theme+xml"/>
  <Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/>
</Types>"""


def root_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def app_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
  <PresentationFormat>On-screen Show (16:9)</PresentationFormat>
  <Slides>1</Slides>
  <Notes>0</Notes>
  <HiddenSlides>0</HiddenSlides>
  <MMClips>0</MMClips>
  <ScaleCrop>false</ScaleCrop>
  <HeadingPairs><vt:vector size="2" baseType="variant"><vt:variant><vt:lpstr>Slides</vt:lpstr></vt:variant><vt:variant><vt:i4>1</vt:i4></vt:variant></vt:vector></HeadingPairs>
  <TitlesOfParts><vt:vector size="1" baseType="lpstr"><vt:lpstr>MedBrief stakeholder pitch</vt:lpstr></vt:vector></TitlesOfParts>
  <Company>MedBrief</Company>
  <LinksUpToDate>false</LinksUpToDate>
  <SharedDoc>false</SharedDoc>
  <HyperlinksChanged>false</HyperlinksChanged>
  <AppVersion>16.0000</AppVersion>
</Properties>"""


def core_xml() -> str:
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>MedBrief stakeholder pitch</dc:title>
  <dc:subject>Single-slide funding pitch</dc:subject>
  <dc:creator>Codex</dc:creator>
  <cp:keywords>MedBrief, funding, pilot, medical intelligence</cp:keywords>
  <dc:description>One-slide executive pitch focused on business outcomes from funding MedBrief.</dc:description>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified>
</cp:coreProperties>"""


def presentation_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}">
  <p:sldMasterIdLst>
    <p:sldMasterId id="2147483648" r:id="rId1"/>
  </p:sldMasterIdLst>
  <p:sldIdLst>
    <p:sldId id="256" r:id="rId2"/>
  </p:sldIdLst>
  <p:sldSz cx="{SLIDE_W}" cy="{SLIDE_H}" type="wide"/>
  <p:notesSz cx="6858000" cy="9144000"/>
  <p:defaultTextStyle>
    <a:defPPr>
      <a:defRPr lang="en-US"/>
    </a:defPPr>
  </p:defaultTextStyle>
</p:presentation>"""


def presentation_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="slideMasters/slideMaster1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/>
</Relationships>"""


def slide_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
</Relationships>"""


def slide_master_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldMaster xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}">
  <p:cSld>
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMap bg1="lt1" tx1="dk1" bg2="lt2" tx2="dk2" accent1="accent1" accent2="accent2" accent3="accent3" accent4="accent4" accent5="accent5" accent6="accent6" hlink="hlink" folHlink="folHlink"/>
  <p:sldLayoutIdLst><p:sldLayoutId id="2147483649" r:id="rId1"/></p:sldLayoutIdLst>
  <p:txStyles>
    <p:titleStyle/><p:bodyStyle/><p:otherStyle/>
  </p:txStyles>
</p:sldMaster>"""


def slide_master_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout" Target="../slideLayouts/slideLayout1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/theme" Target="../theme/theme1.xml"/>
</Relationships>"""


def slide_layout_xml() -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sldLayout xmlns:a="{A_NS}" xmlns:r="{R_NS}" xmlns:p="{P_NS}" type="blank" preserve="1">
  <p:cSld name="Blank">
    <p:spTree>
      <p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr>
      <p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr>
    </p:spTree>
  </p:cSld>
  <p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr>
</p:sldLayout>"""


def slide_layout_rels() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideMaster" Target="../slideMasters/slideMaster1.xml"/>
</Relationships>"""


def theme_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="MedBrief">
  <a:themeElements>
    <a:clrScheme name="MedBrief">
      <a:dk1><a:srgbClr val="14313A"/></a:dk1>
      <a:lt1><a:srgbClr val="FFFFFF"/></a:lt1>
      <a:dk2><a:srgbClr val="123F4B"/></a:dk2>
      <a:lt2><a:srgbClr val="F6F8F5"/></a:lt2>
      <a:accent1><a:srgbClr val="31A59A"/></a:accent1>
      <a:accent2><a:srgbClr val="2F6F9F"/></a:accent2>
      <a:accent3><a:srgbClr val="D69A2D"/></a:accent3>
      <a:accent4><a:srgbClr val="8DAA5A"/></a:accent4>
      <a:accent5><a:srgbClr val="8E6B9E"/></a:accent5>
      <a:accent6><a:srgbClr val="486365"/></a:accent6>
      <a:hlink><a:srgbClr val="2F6F9F"/></a:hlink>
      <a:folHlink><a:srgbClr val="8E6B9E"/></a:folHlink>
    </a:clrScheme>
    <a:fontScheme name="Aptos">
      <a:majorFont><a:latin typeface="Aptos Display"/><a:ea typeface=""/><a:cs typeface=""/></a:majorFont>
      <a:minorFont><a:latin typeface="Aptos"/><a:ea typeface=""/><a:cs typeface=""/></a:minorFont>
    </a:fontScheme>
    <a:fmtScheme name="MedBrief">
      <a:fillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:fillStyleLst>
      <a:lnStyleLst>
        <a:ln w="6350" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
        <a:ln w="12700" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
        <a:ln w="19050" cap="flat" cmpd="sng" algn="ctr"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:prstDash val="solid"/></a:ln>
      </a:lnStyleLst>
      <a:effectStyleLst>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
        <a:effectStyle><a:effectLst/></a:effectStyle>
      </a:effectStyleLst>
      <a:bgFillStyleLst>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
        <a:solidFill><a:schemeClr val="phClr"/></a:solidFill>
      </a:bgFillStyleLst>
    </a:fmtScheme>
  </a:themeElements>
  <a:objectDefaults/>
  <a:extraClrSchemeLst/>
</a:theme>"""


def main() -> None:
    files = {
        "[Content_Types].xml": content_types(),
        "_rels/.rels": root_rels(),
        "docProps/app.xml": app_xml(),
        "docProps/core.xml": core_xml(),
        "ppt/presentation.xml": presentation_xml(),
        "ppt/_rels/presentation.xml.rels": presentation_rels(),
        "ppt/slides/slide1.xml": slide_xml(),
        "ppt/slides/_rels/slide1.xml.rels": slide_rels(),
        "ppt/slideMasters/slideMaster1.xml": slide_master_xml(),
        "ppt/slideMasters/_rels/slideMaster1.xml.rels": slide_master_rels(),
        "ppt/slideLayouts/slideLayout1.xml": slide_layout_xml(),
        "ppt/slideLayouts/_rels/slideLayout1.xml.rels": slide_layout_rels(),
        "ppt/theme/theme1.xml": theme_xml(),
    }

    with ZipFile(OUT, "w", ZIP_DEFLATED) as pptx:
        for path, xml in files.items():
            pptx.writestr(path, xml)

    print(OUT.resolve())


if __name__ == "__main__":
    main()
