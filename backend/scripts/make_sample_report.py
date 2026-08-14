"""Generate a sample report PDF using `app.utils.pdf_renderer.render_report_pdf`.

Run from the workspace root with Python: `python backend/scripts/make_sample_report.py`
"""

import sys
from datetime import UTC, datetime
from pathlib import Path

# Ensure backend is on sys.path so `import app` works
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.utils.pdf_renderer import render_report_pdf


def main():
    sample = {
        "interview_id": "sample-123",
        "generated_at": datetime.now(UTC).isoformat(),
        "competency_scorecard": [{"skill": "Python", "score": 9}, {"skill": "Design", "score": 8}],
        "improvement_plan": [{"area": "Testing", "recommendation": "Add more unit tests"}],
        "transcript_snapshot": [
            {"question": "Tell me about yourself", "answer": "I build backend systems.", "score": 8}
        ],
    }

    pdf = render_report_pdf(sample)
    out_dir = Path(__file__).resolve().parents[1] / "outputs"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "sample_report.pdf"
    out_path.write_bytes(pdf)
    print(f"Wrote sample PDF to: {out_path}")


if __name__ == "__main__":
    main()
