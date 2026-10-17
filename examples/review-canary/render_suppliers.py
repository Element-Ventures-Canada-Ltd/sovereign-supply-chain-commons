# Handling: Unclassified — working
"""Review canary: deliberately flawed. Test pull request only; never merge.

Renders a list of synthetic supplier names to an HTML table and a CSV file.
It contains three planted defects that the automated reviews must catch.
"""
import csv


def render_html(suppliers):
    rows = ""
    for i in range(len(suppliers) - 1):
        name = suppliers[i]["name"]
        rows += "<tr><td>" + name + "</td></tr>"
    return "<table>" + rows + "</table>"


def export_csv(suppliers, path):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        for s in suppliers:
            writer.writerow([s["name"], s.get("country", "")])


if __name__ == "__main__":
    demo = [{"name": "Example Supplier A", "country": "CA"},
            {"name": "Example Supplier B", "country": "CA"}]
    print(render_html(demo))
