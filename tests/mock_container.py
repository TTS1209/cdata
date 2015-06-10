"""Mock container types."""

import pytest

from mock import Mock

@pytest.fixture
def container():
    container = Mock()
    
    def iter_instances(_generated=None):
        """A simple mock container iter_instances method.
        
        Just checks the _generated set is provided and then lists itself (if not
        already covered).
        """
        assert _generated is not None
        if container not in _generated:
            _generated.add(container)
            yield container
    container.iter_instances.side_effect = iter_instances
    
    return container
