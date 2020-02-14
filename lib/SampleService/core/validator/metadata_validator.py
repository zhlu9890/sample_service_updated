'''
Contains a Sample Service metadata validator class.
'''

import maps as _maps
from typing import Dict, List, Callable, Optional
from pygtrie import CharTrie as _CharTrie
from SampleService.core.core_types import PrimitiveType
from SampleService.core.errors import MetadataValidationError as _MetadataValidationError


class MetadataValidator:
    '''
    A validator of metadata.
    '''

    def __init__(
        self,
        validators:
            Dict[str, List[Callable[[str, Dict[str, PrimitiveType]], Optional[str]]]] = None,
        prefix_validators:
            Dict[str, List[Callable[[str, str, Dict[str, PrimitiveType]], Optional[str]]]] = None):
        '''
        Create the validator.

        :param validators: A map from metadata keys to a list of validators for that key.
          The arguments to each validator are the metadata key and the value mapped from the key.
        :param prefix_validators: A map from metadata prefix keys to a list of validators for
          that key. These keys match any metadata key for which they are a prefix, and their
          validators will be run on any matching key.
          The arguments to each validator are the metadata key, the prefix key that matched the
          key, and the value mapped from the metadata key.
        '''
        self._vals = dict(validators) if validators else {}  # remove possible defaultdict
        self._prefix_vals = _CharTrie(prefix_validators if prefix_validators else {})

    def keys(self):
        '''
        Get the keys with assigned metadata validators.
        :returns: the metadata keys.
        '''
        return self._vals.keys()

    def prefix_keys(self):
        '''
        Get the keys with assigned prefix metadata validators.
        :returns: the metadata keys.
        '''
        return self._prefix_vals.keys()

    def validator_count(self, key: str):
        '''
        Get the number of validators assigned to a key.
        :param key: the key to query.
        :returns: the number of validators assigned to the key.
        '''
        if not self._vals.get(key):
            raise ValueError(f'No validators for key {key}')
        return len(self._vals[key])

    def prefix_validator_count(self, prefix: str):
        '''
        Get the number of validators assigned to a prefix key.
        :param prefix: the key to query.
        :returns: the number of validators assigned to the key.
        '''
        if not self._prefix_vals.get(prefix):
            raise ValueError(f'No prefix validators for prefix {prefix}')
        return len(self._prefix_vals[prefix])

    def call_validator(
            self,
            key: str,
            index: int,
            value: Dict[str, PrimitiveType]
            ) -> Optional[str]:
        '''
        Call a particular validator for a metadata key.
        :param key: the key for which a validator should be called.
        :param index: the index of the validator in the list of validators.
        :param value: the metdata value to pass to the validator as an argument.
        :returns: the return value of the validator.
        '''
        if not self._vals.get(key):
            raise ValueError(f'No validators for key {key}')
        if index >= len(self._vals[key]):
            raise IndexError(
                f'Requested validator index {index} for key {key} but maximum index ' +
                f'is {len(self._vals[key]) - 1}')
        return self._vals[key][index](key, value)

    def call_prefix_validator(
            self,
            prefix: str,
            index: int,
            key: str,
            value: Dict[str, PrimitiveType]
            ) -> Optional[str]:
        '''
        Call a particular validator for a metadata key prefix.
        :param prefix: the prefix for which a valiator should be called.
        :param index: the index of the validator in the list of validators.
        :param key: the key to to pass to the validator as an argument.
        :param value: the metdata value to pass to the validator as an argument.
        :returns: the return value of the validator.
        '''
        if not self._prefix_vals.get(prefix):
            raise ValueError(f'No prefix validators for prefix {prefix}')
        if index >= len(self._prefix_vals[prefix]):
            raise IndexError(
                f'Requested validator index {index} for prefix {prefix} but maximum ' +
                f'index is {len(self._prefix_vals[prefix]) - 1}')
        return self._prefix_vals[prefix][index](prefix, key, value)

    def validate_metadata(self, metadata: Dict[str, Dict[str, PrimitiveType]]):
        '''
        Validate a set of metadata key/value pairs.

        :param metadata: the metadata.
        :raises MetadataValidationError: if the metadata is invalid.
        '''
        # if not isinstance(metadata, dict):  # doesn't work
        if type(metadata) != dict and type(metadata) != _maps.FrozenMap:
            raise ValueError('metadata must be a dict')
        for k in metadata:
            sp = self._prefix_vals.shortest_prefix(k)
            if not self._vals.get(k) and not (sp and sp.value):
                raise _MetadataValidationError(
                    f'No validator available for metadata key {k}')
            for valfunc in self._vals.get(k, []):
                ret = valfunc(k, metadata[k])
                if ret:
                    raise _MetadataValidationError(f'Key {k}: ' + ret)
            for p, funcs in self._prefix_vals.prefixes(k):
                for f in funcs:
                    ret = f(p, k, metadata[k])
                    if ret:
                        raise _MetadataValidationError(
                            f'Prefix validator {p}, key {k}: ' + ret)

# TODO add to config and set up
# TODO integration test
# TODO docs
