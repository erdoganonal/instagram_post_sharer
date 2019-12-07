
"This is where the program starts."
from common.initial import initial_check
from common.controller import start_app


def main():
    "Starts the program"
    initial_check()
    start_app()


if __name__ == "__main__":
    main()
