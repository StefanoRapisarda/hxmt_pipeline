import functools

def decorator(func):
    @functools.wraps(func)
    def check_input(*args,**kwargs):
        