import time
from functools import wraps


def rate_limited(max_per_second):
    min_interval = 1.0 / max_per_second

    def decorate(func):
        last_time_called = [0.0]

        @wraps(func)
        def rate_limited_function(*args, **kwargs):
            elapsed = time.time() - last_time_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                time.sleep(left_to_wait)

            ret = func(*args, **kwargs)
            last_time_called[0] = time.time()

            return ret

        return rate_limited_function

    return decorate