"""Provide a class for yWriter item representation.

Copyright (c) 2023 Peter Triesberger
For further information see https://github.com/peter88213/PyWriter
Published under the MIT License (https://opensource.org/licenses/mit-license.php)
"""
from .world_element import WorldElement

class Item(WorldElement):
    """yWriter item representation.

    Public instance variables:
        title: str -- item title.
        desc: str -- item description.
        aka: str -- alternate name.
        tags -- list of tags.
        image: str -- image file path.
    """

    def __init__(self):
        """Initialize instance variables.
        
        Extends the superclass constructor.
        """
        super().__init__()