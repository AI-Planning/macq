try:
    from tqdm import tqdm, trange

    TQDM = True

except ModuleNotFoundError:
    TQDM = False


def tqdm_progress(iterable=None, *args, **kwargs):
    if isinstance(iterable, range):
        return trange(iterable.start, iterable.stop, iterable.step, *args, **kwargs)
    return tqdm(iterable, *args, **kwargs)


class vanilla_progress:
    def __init__(self, iterable, *args, **kwargs):
        self.iterable = iterable
        self.args = args
        self.kwargs = kwargs

    def __iter__(self):
        if isinstance(self.iterable, range):
            start = self.iterable.start
            stop = self.iterable.stop
            step = self.iterable.step
            total = (stop - start) / step
        else:
            total = len(self.iterable)

        prev = 0
        it = 1
        for i in self.iterable:
            yield i
            new = int(str(it / total)[2])
            if new != prev:
                prev = new
                if new == 0:
                    print("100%")
                else:
                    print(f"{new}0% ...")
            it += 1


progress = tqdm_progress if TQDM else vanilla_progress
