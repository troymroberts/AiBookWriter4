"""Provide a class for yWriter location representation.

Copyright (c) 2023 Peter Triesberger
For further information see https://github.com/peter88213/PyWriter
Published under the MIT License (https://opensource.org/licenses/mit-license.php)
"""
from .world_element import WorldElement

class Location(WorldElement):
    """yWriter location representation.

    Public instance variables:
        title: str -- location title.
        desc: str -- location description.
        aka: str -- alternate name.
        tags -- list of tags.
        image: str -- image file path.
    """

    def __init__(self):
        """Initialize instance variables.
        
        Extends the superclass constructor.
        """
        super().__init__()