import parser
import model
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

cur_dir = Path(__file__).parent
env = Environment(
    loader=FileSystemLoader(cur_dir / "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)


def generate_can_dbc(database, output_dir: Path):
    template = env.get_template("dbc.j2")
    output_text = template.render(database=database, ByteOrder=model.ByteOrder)
    with open(output_dir / "can.dbc", "w", encoding="utf-8") as f:
        f.write(output_text)

if __name__ == "__main__":
    database = parser.parse_load_workbook()
    # print(database)
    generate_can_dbc(database, cur_dir / "output")