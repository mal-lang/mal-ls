import time

__LOG_FORMAT__ = "%(asctime)s {0} [%(levelname)s] %(name)s: %(message)s".format(
    time.localtime().tm_zone
)

__ALL__ = ("__LOG_FORMAT__",)
