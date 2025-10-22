from __future__ import annotations

import argparse
import json
from pathlib import Path

from .models import AssessmentInput
from .assessor import AIAssessor
from .report import MarkdownReportGenerator


def main() -> None:
    parser = argparse.ArgumentParser(description="AI Act Risk Assessment CLI")
    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--output", required=True, help="Path to output Markdown report")
    parser.add_argument("--dump-json", dest="dump_json", action="store_true", help="Also dump assessment result JSON next to report")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = json.loads(input_path.read_text(encoding="utf-8"))
    assessment_input = AssessmentInput.from_dict(data)

    assessor = AIAssessor()
    result = assessor.assess(assessment_input)

    report_md = MarkdownReportGenerator().generate(assessment_input, result)
    output_path.write_text(report_md, encoding="utf-8")

    if args.dump_json:
        json_path = output_path.with_suffix(".json")
        json_path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")

    print(f"Report written to {output_path}")


if __name__ == "__main__":
    main()
