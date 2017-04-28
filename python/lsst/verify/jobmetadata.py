#
# LSST Data Management System
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# See COPYRIGHT file at the top of the source tree.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <https://www.lsstcorp.org/LegalNotices/>.
#
from __future__ import print_function

__all__ = ['Metadata']

# Get ChainMap backport
from future.standard_library import install_aliases
install_aliases()  # noqa: E402

try:
    from collections import ChainMap
except ImportError:
    # future 0.16.0 doesn't do the import right; this will be fixed in 0.16.1
    # https://github.com/PythonCharmers/python-future/issues/226
    from future.backports.misc import ChainMap
import re

from .jsonmixin import JsonSerializationMixin


class Metadata(JsonSerializationMixin):
    """Container for verification framework job metadata.

    Metadata are key-value terms. Both keys and values should be
    JSON-serializable.

    Parameters
    ----------
    measurement_set : `lsst.verify.MeasurementSet`, optional
        When provided, metadata with keys prefixed by metric names are
        deferred to `Metadata` instances attached to measurements
        (`lsst.verify.Measurement.meta`).
    data : `dict`, optional
        Dictionary to seed metadata with.
    """

    # Pattern for detecting metric name prefixes in names
    _prefix_pattern = re.compile('^(\S+\.\S+)\.')

    def __init__(self, measurement_set, data=None):

        # Dict of job metadata not stored with a mesaurement
        self._data = {}

        # Measurement set to get measurement annotations from
        self._meas_set = measurement_set

        # Initialize the ChainMap. The first item in the chain map is the
        # Metadata object's own _data. This is generic metadata. Additional
        # items in the chain are Measurement.notes annotations for all
        # measurements in the measurement_set.
        self._chain = ChainMap(self._data)
        self._cached_prefixes = set()
        self._refresh_chainmap()

        if data is not None:
            self.update(data)

    def _refresh_chainmap(self):
        prefixes = set([str(name) for name in self._meas_set])

        if self._cached_prefixes != prefixes:
            self._cached_prefixes = prefixes

            self._chain = ChainMap(self._data)
            for _, measurement in self._meas_set.items():
                # Get the dict instance directly so we don't use
                # the MeasurementNotes's key auto-prefixing.
                self._chain.maps.append(measurement.notes._data)

    @staticmethod
    def _get_prefix(key):
        """Get the prefix of a measurement not, if it exists.

        Examples
        --------
        >>> Metadata._get_prefix('note') is None
        True
        >>> Metadata._get_prefix('validate_drp.PA1.note')
        'validate_drp.PA1.'

        To get the metric name:

        >>> prefix = Metadata._get_prefix('validate_drp.PA1.note')
        >>> prefix.rstrip('.')
        'validate_drp.PA1'
        """
        match = Metadata._prefix_pattern.match(key)
        if match is not None:
            return match.group(0)
        else:
            return None

    def __getitem__(self, key):
        self._refresh_chainmap()
        return self._chain[key]

    def __setitem__(self, key, value):
        prefix = Metadata._get_prefix(key)
        if prefix is not None:
            metric_name = prefix.rstrip('.')
            if metric_name in self._meas_set:
                # turn prefix into a metric name
                self._meas_set[metric_name].notes[key] = value
                return

        # No matching measurement; insert into general metadata
        self._data[key] = value

    def __delitem__(self, key):
        prefix = Metadata._get_prefix(key)
        if prefix is not None:
            metric_name = prefix.rstrip('.')
            if metric_name in self._meas_set:
                del self._meas_set[metric_name].notes[key]
                return

        # No matching measurement; delete from general metadata
        del self._data[key]

    def __contains__(self, key):
        self._refresh_chainmap()
        return key in self._chain

    def __len__(self):
        self._refresh_chainmap()
        return len(self._chain)

    def __iter__(self):
        self._refresh_chainmap()
        for key in self._chain:
            yield key

    def __eq__(self, other):
        # No explicit chain refresh because __len__ already does it
        if len(self) != len(other):
            return False

        for key, value in other.items():
            if key not in self:
                return False
            if value != self[key]:
                return False

        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        return str(self._chain)

    def __repr__(self):
        return repr(self._chain)

    def keys(self):
        return [key for key in self]

    def items(self):
        self._refresh_chainmap()
        for item in self._chain.items():
            yield item

    def update(self, data):
        for key, value in data.items():
            self[key] = value

    @property
    def json(self):
        self._refresh_chainmap()
        return self.jsonify_dict(self._chain)
