try:
    from tqdm import tqdm, trange

    TQDM = True

except ModuleNotFoundError:
    TQDM = False


def tqdm_progress(iterable=None):
    pass


def vanilla_progress(iterable):
    pass


progress = tqdm_progress if TQDM else vanilla_progress
