import sys


def progressbar(t, n):
    """
    Implement a cool and good progress bar illustrating the experiment progress and write it to output
    :param t: current episode
    :param n: max episodes
    """
    progress = t / n
    bar = round(progress * 100)
    totalbar = '[' + (bar * '#') + ((100 - bar) * '_') + '] ' + str(bar) + '%'
    sys.stdout.write('%s\r' % totalbar)
    sys.stdout.flush()


def clear_progressbar():
    """
    Clears the progress bar from the terminal
    """
    empty = ' ' * 120
    sys.stdout.write('%s\r' % empty)