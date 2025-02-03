"""Provide a class for yWriter project note representation.

Copyright (c) 2023 Peter Triesberger
For further information see https://github.com/peter88213/PyWriter
Published under the MIT License (https://opensource.org/licenses/mit-license.php)
"""
from .basic_element import BasicElement

class ProjectNote(BasicElement):
    """Project note representation.
    
    Public instance variables:
        title: str -- project note title.
        desc: str -- project note description.
        kwVar: dict -- custom keyword variables.
    """

    def __init__(self):
        """Initialize instance variables.
        
        Extends the superclass constructor.
        """
        super().__init__()