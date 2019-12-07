"Runs the lint for entire python files"
import os
import subprocess

VENV_PATTERN = "env"
FILTERS = [
    "ocr.py",
]

def main():
    "Start from here"
    python_files = get_python_files()
    for python_file in python_files:
        run_lint(python_file)


def run_lint(file):
    "Run lint and print the output of lint result"
    output = subprocess.check_output(
        ["pylint.exe", file, "--exit-zero"],
        universal_newlines=True
    ).strip()

    if "rated at 10.00/10" not in output:
        print("Lint results for {0}".format(file))
        print(output)

def get_python_files():
    "returns the entire python files"
    for root, _, files in os.walk("."):
        try:
            top_level = root.split("\\")[1]
        except IndexError:
            pass
        else:
            if VENV_PATTERN in top_level:
                continue

        for file in files:
            if file.endswith(".py") and file not in FILTERS:
                yield os.path.realpath(os.path.join(root, file))


if __name__ == "__main__":
    main()
