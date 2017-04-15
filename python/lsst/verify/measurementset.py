# See COPYRIGHT file at the top of the source tree.
from __future__ import print_function, division

__all__ = ['MeasurementSet']

from .measurement import Measurement
from .naming import Name


class MeasurementSet(object):
    """A collection of measurements of metrics.

    Parameters
    ----------
    measurements : `list` of `lsst.verify.Measurement`\ s
        Measurements to include in the set.
    """

    def __init__(self, measurements=None):
        self._items = {}
        for measurement in measurements:
            self[measurement.metric_name] = measurement

    def __getitem__(self, key):
        if not isinstance(key, Name):
            key = Name(metric=key)

        return self._items[key]

    def __setitem__(self, key, value):
        if not isinstance(key, Name):
            key = Name(metric=key)

        if not key.is_metric:
            raise KeyError('Key {0} is not a metric name'.format(key))

        if not isinstance(value, Measurement):
            message = ('Measurement {0} is not a '
                       'lsst.verify.Measurement-type')
            raise TypeError(message.format(value))

        if key != value.metric_name:
            message = ("Key {0} is inconsistent with the measurement's "
                       "metric name, {1}")
            raise KeyError(message.format(key, value.metric_name))

        self._items[key] = value

    def __len__(self):
        return len(self._items)

    def __contains__(self, key):
        if not isinstance(key, Name):
            key = Name(metric=key)

        return key in self._items

    def __delitem__(self, key):
        if not isinstance(key, Name):
            key = Name(metric=key)

        del self._items[key]

    def __iter__(self):
        for key in self._items:
            yield key

    def __str__(self):
        count = len(self)
        if count == 0:
            count_str = 'empty'
        elif count == 1:
            count_str = '1 Measurement'
        else:
            count_str = '{count:d} Measurements'.format(count=count)
        return '<MeasurementSet: {0}>'.format(count_str)

    def items(self):
        """Iterete over (`Name`, `Measurement`) pairs in the set.

        Yields
        ------
        item : tuple
            Tuple containing:

            - `Name` of the measurement's `Metric`
            - `Measurement` instance
        """
        for item in self._items.items():
            yield item

    def insert(self, measurement):
        """Insert a measurement into the set."""
        self[measurement.metric_name] = measurement