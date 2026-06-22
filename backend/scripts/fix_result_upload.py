from pathlib import Path
import re

p = Path("app/web/result_upload.py")
text = p.read_text()

route_pattern = re.compile(
    r'@result_upload_web_bp\.route\("/portal/result-files/download/<file_id>"\)\s*'
    r'def portal_download_result_file\(file_id\):.*?'
    r'download_name=item\.file_name\s*\n\s*\)',
    re.S
)

matches = route_pattern.findall(text)

print("Found:", len(matches), "portal download routes")

if len(matches) <= 1:
    print("Nothing to fix")
    raise SystemExit

keep = matches[0]

text = route_pattern.sub("", text)

text += "\n\n" + keep + "\n"

p.write_text(text)

print("Fixed. Kept 1 route.")
