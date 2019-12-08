"""
Prints the messages with color.
"""
import sys
from colorama import init, deinit, Fore


def _stdout_renderer(function):
    def wrapper(*args, **kwargs):
        stdout_original = sys.stdout
        sys.stdout = sys.__stdout__

        init(autoreset=True)
        function(*args, **kwargs)
        deinit()

        sys.stdout = stdout_original

    return wrapper


class Colored:
    "Owner of the colored print functions"
    BLACK = Fore.BLACK
    RED = Fore.RED
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    BLUE = Fore.BLUE
    MAGENTA = Fore.MAGENTA
    CYAN = Fore.CYAN
    WHITE = Fore.WHITE
    RESET = Fore.RESET

    @classmethod
    def _prepare_message(cls, *args, sep=' ', end='\n'):
        return sep.join(str(arg) for arg in args) + end

    @classmethod
    @_stdout_renderer
    def print_with_color(cls, *args, color, sep=' ', end='\n', flush=True):
        "prints the given message with the given color"
        message = color + sep.join(str(arg) for arg in args) + end

        sys.stdout.write(message)
        if flush:
            sys.stdout.flush()

    @classmethod
    def print_debug(cls, *args, sep=' ', end='\n', flush=True):
        "prints the given message with blue color"
        cls.print_with_color(
            *args, color=cls.BLUE,
            sep=sep, end=end,
            flush=flush
        )

    @classmethod
    def print_info(cls, *args, sep=' ', end='\n', flush=True):
        "prints the given message with green color"
        cls.print_with_color(
            *args, color=cls.GREEN,
            sep=sep, end=end,
            flush=flush
        )

    @classmethod
    def print_warning(cls, *args, sep=' ', end='\n', flush=True):
        "prints the given message with yellow color"
        cls.print_with_color(
            *args, color=cls.YELLOW,
            sep=sep, end=end,
            flush=flush
        )

    @classmethod
    def print_error(cls, *args, sep=' ', end='\n', flush=True):
        "prints the given message with red color"
        cls.print_with_color(
            *args, color=cls.RED,
            sep=sep, end=end,
            flush=flush
        )

    print_blue = print_debug
    print_green = print_info
    print_yellow = print_warning
    print_red = print_error

    @classmethod
    def print_magenta(cls, *args, sep=' ', end='\n', flush=True):
        "prints the given message with magenta color"
        cls.print_with_color(
            *args, color=cls.MAGENTA,
            sep=sep, end=end,
            flush=flush
        )


def main():
    "Test function for coloring"
    Colored.print_debug("I am debug message with blue color")
    Colored.print_info("I am info message with green color")
    Colored.print_warning("I am warning message with yellow color")
    Colored.print_error("I am error message with red color")
    Colored.print_with_color(
        "I am colored message with cyan color",
        color=Colored.CYAN
    )


if __name__ == "__main__":
    main()
