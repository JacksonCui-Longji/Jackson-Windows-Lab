import parser
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

current_dir = Path(__file__).parent
env = Environment(loader=FileSystemLoader(current_dir / "templates"), 
                    trim_blocks=True,
                    lstrip_blocks=True,)

def generate_can_id_h(database, output_dir: Path):
    template = env.get_template("can_id_h.j2")
    output_text = template.render(database=database)
    with open(output_dir / "can_id.h", "w") as f:
        f.write(output_text)

def generate_can_signal_id_h(database, output_dir: Path):
    template = env.get_template("can_signal_id_h.j2")
    output_text = template.render(database=database)
    with open(output_dir / "can_signal_id.h", "w") as f:
        f.write(output_text)

def generate_can_if_h(database, output_dir: Path):
    template = env.get_template("can_if_h.j2")
    output_text = template.render(database=database)
    with open(output_dir / "can_if.h", "w") as f:
        f.write(output_text)

def generate_can_if_c(database, output_dir: Path):
    template = env.get_template("can_if_c.j2")
    output_text = template.render(database=database)
    with open(output_dir / "can_if.c", "w") as f:
        f.write(output_text)

if __name__ == "__main__":
    with open(current_dir / "input" / "vehicle.dbc", "r") as f:
        dbc_content = f.read()
    database = parser.ParserCANDBC(dbc_content)
    generate_can_id_h(database, current_dir / "output")
    generate_can_signal_id_h(database, current_dir / "output")
    generate_can_if_c(database, current_dir / "output")
    generate_can_if_h(database, current_dir / "output")
    