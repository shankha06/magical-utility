from rich import inspect
from rich.progress import track
from rich.console import Console
from rich.progress import Progress

import pandas as pd
from datetime import datetime
from time import sleep


def process_data():
    sleep(0.02)

def console_process(
    data: list, 
    console: Console,
    ) -> None:
    """_summary_

    Args:
        data (list): _description_
        console (Console): _description_
    """
    while data:
        num = data.pop(0)
        sleep(1)
        console.log(f"[magenta]custom text[/magenta] {num}")
    console.log(f'[bold][blue]Completed console output!')

if __name__ == "__main__":

    print("<<------------------------------------ Initialization ------------------------------------------->>")
    sample_data = {
        "Date": [
            datetime(year=2019, month=12, day=20),
            datetime(year=2018, month=5, day=25),
            datetime(year=2017, month=12, day=15),
        ],
        "Title": [
            "Star Wars: The Rise of Skywalker",
            "[red]Solo[/red]: A Star Wars Story",
            "Star Wars Ep. VIII: The Last Jedi",
        ],
        "Production Budget": ["$275,000,000", "$275,000,000", "$262,000,000"],
        "Box Office": ["$375,126,118", "$393,151,347", "$1,332,539,889"],
    }
    df = pd.DataFrame(sample_data)

    # Inspect element or fucntion or library
    # print(inspect(process_data, docs=True, all=True))
    print(inspect(inspect))

    # Progress bar from Loop
    for _ in track(range(100), description='[magenta]custom text'):
        process_data()
    
    # cleaner progress bar with Console
    console = Console()

    data = [1, 2, 3, 4, 5]
    with console.status("[bold purple]Fetching data...") as status:
        console_process(data,console)

    # Progress bar with variable progress at each step
    with Progress() as progress:
        task1 = progress.add_task("[red]what you eant to write ...", total=100)
        task3 = progress.add_task("[cyan]custom ...", total=100)

        while not progress.finished:
            progress.update(task1, advance=0.9)
            progress.update(task3, advance=0.3)
            sleep(0.02)
