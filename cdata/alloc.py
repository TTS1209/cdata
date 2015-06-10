"""Utilities for allocating addresses/memory to cdata instances."""

from six import integer_types

def total_size(instance):
    """Calculate the total storage required (in bytes) to store the supplied set
    of instances (and any instances they refer to).
    """
    return sum(i.size for i in instance.iter_instances())


def alloc(instance, start_at):
    """Allocate non-overlapping addresses to all supplied instances.
    
    Parameters
    ----------
    instance : :py:class:`cdata.base.Instance`
        The instance (along with all other accessible instances) to allocate a
        non-overlapping address to. This instance (or its container) will be
        given the address start_at.
    start_at : int
        The first instance listed will be
        allocated this address and all other instances will be allocated
        addresses after this point.
    
    Returns
    -------
    int
        The next free address after the allocation completes.
    """
    address = start_at
    for i in instance.iter_instances():
        i.address = address
        address += i.size
    
    return address
