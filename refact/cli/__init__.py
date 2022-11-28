import logging
import sys
from termcolor import colored

import click

    
logging.basicConfig(
    level=logging.INFO,
    format="%(filename)s: "
    "%(levelname)s: "
    "%(funcName)s(): "
    "%(lineno)d:\t"
    "%(message)s",
)

logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option("--debug", is_flag=True, default=False, help="Debug switch")
@click.pass_context
def cli(context, debug):
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    if debug:
        logging.basicConfig(
            format="%(asctime)s : %(name)s %(levelname)s : %(message)s",
            level=logging.DEBUG,
        )
    else:
        logging.basicConfig(
            format="%(asctime)s : %(name)s %(levelname)s : %(message)s",
            level=logging.INFO,
        )

    logging.debug("Debug ON")
    if len(sys.argv) == 1:
        click.echo(context.get_help())

@cli.command()
@click.option("-r","--root", required=True, help="Source directory root")
@click.option("-d","--distance", required=False, default=10, help="Levenshtein distance threshhold")
@click.option("-g","--glob", required=True, help="Glob pattern of files to check")
@click.option("-m","--method", required=False, default=None, help="Analyze a specific method")
@click.option("-s","--source",is_flag=True, required=False, default=False, help="Show the source code only")
def check(root, distance, glob, method, source):
    """ Check for code duplications and refactor opportunities """
    from .check import find_refactors
    from prettytable import PrettyTable
    
    x = PrettyTable()
    
    """ Check source files for duplicate code """
    tree, calls = find_refactors(root, glob, distance)
    
    if not source:
        if not method:
            x.field_names = ["Method", "Defines", "Calls", "Min Difference", "Max Difference"]
            for method in tree:
                min_tuple = min(tree[method], key=lambda tup: tup[0])
                max_tuple = max(tree[method], key=lambda tup: tup[0])
                x.add_row([colored(method,'green'), len(set([meth[1]["module"].name+meth[1]["class"].name for meth in tree[method]])), calls[method] if method in calls else 0, min_tuple[0], max_tuple[0]])
        else:
            seen = []
            x.field_names = ["Distance", "Module 1", "Class 1", "Module 2", "Class 2"]
            for match in tree[method]:
                key = ''.join(sorted([match[1]["module"].name,match[1]["class"].name,match[2]["module"].name,match[2]["class"].name]))
                
                if key not in seen:
                    x.add_row([match[0], match[1]["module"].name, colored(match[1]["class"].name, 'green'), match[2]["module"].name, colored(match[2]["class"].name,'green')])
                    seen += [key]
                    
        print(x)
    else:
        sources = []
        modules = {}
        
        for match in tree[method]:
            if match[1]["source"] not in sources:
                sources += [match[1]["source"]]
            modules[match[1]["module"].name] = colored(match[1]["class"].name, "red")+"\n"+match[1]["source"]
            if match[2]["source"] not in sources:
                sources += [match[2]["source"]]
            modules[match[2]["module"].name] = colored(match[2]["class"].name, "red")+"\n"+match[2]["source"]
                
        for module in modules:
            print(colored(module+":", "green")+modules[module])
                
    