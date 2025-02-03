# --- ywriter7/yw/yw7_file.py ---
"""Provide a class for yWriter 7 project import and export.

Copyright (c) 2023 Peter Triesberger
For further information see https://github.com/peter88213/PyWriter
Published under the MIT License (https://opensource.org/licenses/mit-license.php)
"""
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import datetime
from urllib.parse import unquote, quote
from ..pywriter_globals import *
from ..file.file import File
from ..model.novel import Novel
from ..model.chapter import Chapter
from ..model.scene import Scene
from ..model.character import Character
from ..model.location import Location
from ..model.item import Item
from ..model.project_note import ProjectNote
from ..model.cross_references import CrossReferences
from ..model.splitter import Splitter
from . import xml_indent  # <--- Changed to relative import of the module
# from .xml_indent import indent  # <---  Alternative, but less recommended import style
from ..config.configuration import Configuration
from ..config import configuration
from .. import pywriter_globals

class Yw7File(File):
    """yWriter 7 project file representation.

    Public methods:
        get_chapter_count() -- Return number of chapters.
        get_scene_count() -- Return number of scenes.
        get_word_count() -- Return total word count.
        get_character_count() -- Return number of characters.
        get_location_count() -- Return number of locations.
        get_item_count() -- Return number of items.
        get_project_note_count() -- Return number of project notes.
        get_date_time() -- Return tuple of date and time strings from time stamp.
        get_timedelta() -- Return time difference in seconds from time stamp.
        get_element_id(xmlElement) -- get element ID from XML tag.
        get_element_title(xmlElement) -- get element title from XML tag.
        get_element_desc(xmlElement) -- get element description from XML tag.
        get_element_notes(xmlElement) -- get element notes from XML tag.
        get_element_tags(xmlElement) -- get element tags from XML tag.
        get_element_aka(xmlElement) -- get element "aka" from XML tag.
        get_element_image(xmlElement) -- get element image path from XML tag.
        get_element_field(xmlElement, fieldId) -- get element custom field from XML tag.
        get_element_status(xmlElement) -- get scene status from XML tag.
        get_element_type(xmlElement) -- get chapter type from XML tag.
        get_element_level(xmlElement) -- get chapter level from XML tag.
        get_element_is_reaction(xmlElement) -- get scene type from XML tag.
        get_element_is_subplot(xmlElement) -- get scene subplot status from XML tag.
        get_element_is_trash(xmlElement) -- get chapter "trash bin" status from XML tag.
        get_element_do_not_export(xmlElement) -- get scene "do not export" status from XML tag.
        get_element_suppress_chapter_title(xmlElement) -- get chapter suppress title setting from XML tag.
        get_element_suppress_chapter_break(xmlElement) -- get chapter suppress break setting from XML tag.
        get_element_append_to_previous(xmlElement) -- get scene append setting from XML tag.

    Instance variables:
        tree -- ElementTree instance (xml tree).
        _config -- Configuration instance.
        xrefs -- CrossReferences instance.
        splitter -- Splitter instance.
    """
    EXTENSION = '.yw7'
    DESCRIPTION = _('yWriter 7 project file')
    VERSION = '0.9.11'
    # Constants for XML tag names
    XML_PROJECT_TAG = 'PROJECT'
    XML_TITLE_TAG = 'Title'
    XML_DESC_TAG = 'Desc'
    XML_AUTHOR_NAME_TAG = 'AuthorName'
    XML_BIO_TAG = 'Bio'
    XML_FIELD_TITLE_TAG = 'FieldTitle'
    XML_WORD_TARGET_TAG = 'WordTarget'
    XML_WORD_COUNT_START_TAG = 'WordCountStart'
    XML_CHAPTERS_TAG = 'CHAPTERS'
    XML_CHAPTER_TAG = 'CHAPTER'
    XML_SCENES_TAG = 'SCENES'
    XML_SCENE_TAG = 'SCENE'
    XML_CHARACTERS_TAG = 'CHARACTERS'
    XML_CHARACTER_TAG = 'CHARACTER'
    XML_LOCATIONS_TAG = 'LOCATIONS'
    XML_LOCATION_TAG = 'LOCATION'
    XML_ITEMS_TAG = 'ITEMS'
    XML_ITEM_TAG = 'ITEM'
    XML_PROJECT_NOTES_TAG = 'PROJECTNOTES'
    XML_PROJECT_NOTE_TAG = 'PROJECTNOTE'
    XML_TAGS_TAG = 'TAGS'
    XML_TAG_TAG = 'TAG'
    XML_USED_TAGS_TAG = 'UsedTags'
    XML_UNUSED_TAG_TAG = 'Unused'
    XML_TYPE_TAG = 'Type'
    XML_CHAPTER_TYPE_TAG = 'ChapterType'
    XML_SECTION_START_TAG = 'SectionStart'
    XML_STATUS_TAG = 'Status'
    XML_NOTES_TAG = 'Notes'
    XML_GOAL_TAG = 'Goal'
    XML_CONFLICT_TAG = 'Conflict'
    XML_OUTCOME_TAG = 'Outcome'
    XML_REACTION_SCENE_TAG = 'ReactionScene'
    XML_SUBPLOT_TAG = 'SubPlot'
    XML_DAY_TAG = 'Day'
    XML_TIME_TAG = 'Time'
    XML_LASTS_DAYS_TAG = 'LastsDays'
    XML_LASTS_HOURS_TAG = 'LastsHours'
    XML_LASTS_MINUTES_TAG = 'LastsMinutes'
    XML_WORD_COUNT_TAG = 'WordCount'
    XML_LETTER_COUNT_TAG = 'LetterCount'
    XML_SCENE_CONTENT_TAG = 'SceneContent'
    XML_IMAGE_FILE_TAG = 'ImageFile'
    XML_AKA_TAG = 'AKA'
    XML_FULL_NAME_TAG = 'FullName'
    XML_BIO_TAG_CHAR = 'Bio'  # Note: different tag for character bio
    XML_GOALS_TAG = 'Goals'  # Note: different tag for character goals
    XML_MAJOR_TAG = 'Major'
    XML_PRJ_NOTE_CHAPTER_TAG = 'PrjChapter'
    XML_PRJ_NOTE_SCENE_TAG = 'PrjScene'
    XML_FIELD1_TAG = 'Field1'
    XML_FIELD2_TAG = 'Field2'
    XML_FIELD3_TAG = 'Field3'
    XML_FIELD4_TAG = 'Field4'
    XML_SPECIFIC_DATE_MODE_TAG = 'SpecificDateMode'
    XML_SPECIFIC_DATE_TIME_TAG = 'SpecificDateTime'
    XML_APPEND_TO_PREV_TAG = 'AppendToPrev'
    XML_EXPORT_COND_SPECIFIC_TAG = 'ExportCondSpecific'
    XML_EXPORT_WHEN_RTF_TAG = 'ExportWhenRTF'
    XML_FIELDS_TAG = 'Fields'
    XML_FIELD_SCENE_TYPE_TAG = 'Field_SceneType'
    XML_FIELD_SCENE_ARCS_TAG = 'Field_SceneArcs'
    XML_FIELD_SCENE_MODE_TAG = 'Field_SceneMode'
    XML_FIELD_IS_TRASH_TAG = 'Field_IsTrash'
    XML_FIELD_SUPPRESS_CHAPTER_TITLE_TAG = 'Field_SuppressChapterTitle'
    XML_FIELD_SUPPRESS_CHAPTER_BREAK_TAG = 'Field_SuppressChapterBreak'
    XML_FIELD_CHAPTER_PREFIX_TAG = 'Field_ChapterPrefix'
    XML_FIELD_CHAPTER_POSTFIX_TAG = 'Field_ChapterPostfix'
    XML_FIELD_SCENE_PREFIX_TAG = 'Field_ScenePrefix'
    XML_FIELD_SCENE_POSTFIX_TAG = 'Field_ScenePostfix'
    XML_FIELD_CHARACTER_PREFIX_TAG = 'Field_CharacterPrefix'
    XML_FIELD_CHARACTER_POSTFIX_TAG = 'Field_CharacterPostfix'
    XML_FIELD_LOCATION_PREFIX_TAG = 'Field_LocationPrefix'
    XML_FIELD_LOCATION_POSTFIX_TAG = 'Field_LocationPostfix'
    XML_FIELD_ITEM_PREFIX_TAG = 'Field_ItemPrefix'
    XML_FIELD_ITEM_POSTFIX_TAG = 'Field_ItemPostfix'
    XML_FIELD_NOTE_PREFIX_TAG = 'Field_NotePrefix'
    XML_FIELD_NOTE_POSTFIX_TAG = 'Field_NotePostfix'
    XML_FIELD_OUTLINE_PREFIX_TAG = 'Field_OutlinePrefix'
    XML_FIELD_OUTLINE_POSTFIX_TAG = 'Field_OutlinePostfix'
    XML_FIELD_PROMPT_PREFIX_TAG = 'Field_PromptPrefix'
    XML_FIELD_PROMPT_POSTFIX_TAG = 'Field_PromptPostfix'
    XML_FIELD_RESPONSE_PREFIX_TAG = 'Field_ResponsePrefix'
    XML_FIELD_RESPONSE_POSTFIX_TAG = 'Field_ResponsePostfix'
    XML_FIELD_SETTING_PREFIX_TAG = 'Field_SettingPrefix'
    XML_FIELD_SETTING_POSTFIX_TAG = 'Field_SettingPostfix'
    XML_FIELD_RESEARCH_PREFIX_TAG = 'Field_ResearchPrefix'
    XML_FIELD_RESEARCH_POSTFIX_TAG = 'Field_ResearchPostfix'

    # Keyword variable names for custom fields in the .yw7 XML file.
    PRJ_KWVAR = [XML_FIELD_CHAPTER_PREFIX_TAG,
                 XML_FIELD_CHAPTER_POSTFIX_TAG,
                 XML_FIELD_SCENE_PREFIX_TAG,
                 XML_FIELD_SCENE_POSTFIX_TAG,
                 XML_FIELD_CHARACTER_PREFIX_TAG,
                 XML_FIELD_CHARACTER_POSTFIX_TAG,
                 XML_FIELD_LOCATION_PREFIX_TAG,
                 XML_FIELD_LOCATION_POSTFIX_TAG,
                 XML_FIELD_ITEM_PREFIX_TAG,
                 XML_FIELD_ITEM_POSTFIX_TAG,
                 XML_FIELD_NOTE_PREFIX_TAG,
                 XML_FIELD_NOTE_POSTFIX_TAG,
                 XML_FIELD_OUTLINE_PREFIX_TAG,
                 XML_FIELD_OUTLINE_POSTFIX_TAG,
                 XML_FIELD_PROMPT_PREFIX_TAG,
                 XML_FIELD_PROMPT_POSTFIX_TAG,
                 XML_FIELD_RESPONSE_PREFIX_TAG,
                 XML_FIELD_RESPONSE_POSTFIX_TAG,
                 XML_FIELD_SETTING_PREFIX_TAG,
                 XML_FIELD_SETTING_POSTFIX_TAG,
                 XML_FIELD_RESEARCH_PREFIX_TAG,
                 XML_FIELD_RESEARCH_POSTFIX_TAG,
                 ]
    CHP_KWVAR = [XML_FIELD_CHAPTER_PREFIX_TAG,
                 XML_FIELD_CHAPTER_POSTFIX_TAG,
                 ]
    SCN_KWVAR = [XML_FIELD_SCENE_PREFIX_TAG,
                 XML_FIELD_SCENE_POSTFIX_TAG,
                 XML_FIELD_SCENE_TYPE_TAG,
                 XML_FIELD_SCENE_ARCS_TAG,
                 XML_FIELD_SCENE_MODE_TAG,
                 ]
    CRT_KWVAR = [XML_FIELD_CHARACTER_PREFIX_TAG,
                 XML_FIELD_CHARACTER_POSTFIX_TAG,
                 ]
    LOC_KWVAR = [XML_FIELD_LOCATION_PREFIX_TAG,
                 XML_FIELD_LOCATION_POSTFIX_TAG,
                 ]
    ITM_KWVAR = [XML_FIELD_ITEM_PREFIX_TAG,
                 XML_FIELD_ITEM_POSTFIX_TAG,
                 ]
    PNT_KWVAR = [XML_FIELD_NOTE_PREFIX_TAG,
                 XML_FIELD_NOTE_POSTFIX_TAG,
                 XML_FIELD_OUTLINE_PREFIX_TAG,
                 XML_FIELD_OUTLINE_POSTFIX_TAG,
                 XML_FIELD_PROMPT_PREFIX_TAG,
                 XML_FIELD_PROMPT_POSTFIX_TAG,
                 XML_FIELD_RESPONSE_PREFIX_TAG,
                 XML_FIELD_RESPONSE_POSTFIX_TAG,
                 XML_FIELD_SETTING_PREFIX_TAG,
                 XML_FIELD_SETTING_POSTFIX_TAG,
                 XML_FIELD_RESEARCH_PREFIX_TAG,
                 XML_FIELD_RESEARCH_POSTFIX_TAG,
                 ]


    def __init__(self, filePath, **kwargs):
        """Initialize instance variables.

        Positional arguments:
            filePath: str -- path to the .yw7 file.
        """
        super().__init__(filePath, **kwargs)
        self.tree = None
        # ElementTree instance

        self._config = Configuration()
        # Configuration instance

        self.xrefs = CrossReferences()
        # CrossReferences instance

        self.splitter = Splitter()
        # Splitter instance


    def get_chapter_count(self):
        """Return number of chapters."""
        return len(self.novel.chapters)


    def get_scene_count(self):
        """Return number of scenes."""
        return len(self.novel.scenes)


    def get_word_count(self):
        """Return total word count."""
        result = 0
        for scId in self.novel.scenes:
            result += self.novel.scenes[scId].wordCount
        return result


    def get_character_count(self):
        """Return number of characters."""
        return len(self.novel.characters)


    def get_location_count(self):
        """Return number of locations."""
        return len(self.novel.locations)


    def get_item_count(self):
        """Return number of items."""
        return len(self.novel.items)


    def get_project_note_count(self):
        """Return number of project notes."""
        return len(self.novel.projectNotes)


    def get_date_time(self):
        """Return tuple of date and time strings from time stamp.

        Return current date and time as strings in yWriter format 
        ('yyyy-mm-dd', 'hh:mm:ss').
        """
        now = datetime.datetime.now()
        dateString = now.strftime('%Y-%m-%d')
        timeString = now.strftime('%H:%M:%S')
        return dateString, timeString


    def get_timedelta(self):
        """Return time difference in seconds from time stamp.

        Return time difference in seconds between the current time and the 
        yWriter time stamp stored in the project file. If no time stamp is 
        found, return None.
        """
        root = self.tree.getroot()
        timeStamp = root.find('TimeStamp')
        if timeStamp is None:
            return None
        ywDateTime = datetime.datetime.strptime(timeStamp.text, '%Y-%m-%d %H:%M:%S')
        now = datetime.datetime.now()
        timeDelta = now - ywDateTime
        return timeDelta.total_seconds()


    def read(self):
        """Parse the .yw7 file and get the instance variables.

        Parse the XML tree and create a Novel instance with all its parts.
        Raise the "Error" exception in case of error.
        """
        try:
            self.tree = ET.parse(self.filePath)
        except ET.ParseError as e:
            raise Error(f'{_("Invalid yWriter 7 project file")}: "{norm_path(self.filePath)}".') from e
        self.novel = Novel()
        root = self.tree.getroot()

        # Project section
        project = root.find('PROJECT')
        if project is not None:
            self.novel.title = self._xml_to_text(project.find(self.XML_TITLE_TAG))
            self.novel.desc = self._xml_to_text(project.find(self.XML_DESC_TAG))
            self.novel.authorName = self._xml_to_text(project.find(self.XML_AUTHOR_NAME_TAG))
            self.novel.authorBio = self._xml_to_text(project.find(self.XML_BIO_TAG))
            self.novel.fieldTitle1 = self._xml_to_text(project.find(self.XML_FIELD_TITLE_TAG + '1'))
            self.novel.fieldTitle2 = self._xml_to_text(project.find(self.XML_FIELD_TITLE_TAG + '2'))
            self.novel.fieldTitle3 = self._xml_to_text(project.find(self.XML_FIELD_TITLE_TAG + '3'))
            self.novel.fieldTitle4 = self._xml_to_text(project.find(self.XML_FIELD_TITLE_TAG + '4'))
            self.novel.wordTarget = self._xml_to_int(project.find(self.XML_WORD_TARGET_TAG))
            self.novel.wordCountStart = self._xml_to_int(project.find(self.XML_WORD_COUNT_START_TAG))
            for kwVarName in self.PRJ_KWVAR:
                self.novel.kwVar[kwVarName] = self._xml_to_bool(project.find(kwVarName))

        # Chapters section
        chapters = root.find(self.XML_CHAPTERS_TAG)
        if chapters is not None:
            for xmlChapter in chapters.findall(self.XML_CHAPTER_TAG):
                chId = self._xml_to_id(xmlChapter)
                if chId in self.novel.chapters:
                    continue # skip if chapter ID already exists (bug fix for yw7 7.1.1.0)
                chapter = Chapter()
                chapter.title = self._xml_to_text(xmlChapter.find(self.XML_TITLE_TAG))
                chapter.desc = self._xml_to_text(xmlChapter.find(self.XML_DESC_TAG))
                chapter.chLevel = self._xml_to_int(xmlChapter.find(self.XML_SECTION_START_TAG))
                chapter.chType = self._get_chapter_type(xmlChapter)
                chapter.suppressChapterTitle = self._get_chapter_suppress_title(xmlChapter)
                chapter.suppressChapterBreak = self._get_chapter_suppress_break(xmlChapter)
                chapter.isTrash = self._get_chapter_is_trash(xmlChapter)
                self.novel.chapters[chId] = chapter
                self.novel.srtChapters.append(chId)
                for kwVarName in self.CHP_KWVAR:
                    chapter.kwVar[kwVarName] = self._xml_to_bool(xmlChapter.find(kwVarName))

        # Scenes section
        scenes = root.find(self.XML_SCENES_TAG)
        if scenes is not None:
            for xmlScene in scenes.findall(self.XML_SCENE_TAG):
                scId = self._xml_to_id(xmlScene)
                scene = Scene()
                scene.title = self._xml_to_text(xmlScene.find(self.XML_TITLE_TAG))
                scene.desc = self._xml_to_text(xmlScene.find(self.XML_DESC_TAG))
                scene.sceneContent = self._xml_to_text(xmlScene.find(self.XML_SCENE_CONTENT_TAG))
                scene.status = self._get_scene_status(xmlScene)
                scene.notes = self._xml_to_text(xmlScene.find(self.XML_NOTES_TAG))
                scene.tags = self._xml_to_list(xmlScene.find(self.XML_TAGS_TAG))
                scene.field1 = self._xml_to_int(xmlScene.find(self.XML_FIELD1_TAG))
                scene.field2 = self._xml_to_int(xmlScene.find(self.XML_FIELD2_TAG))
                scene.field3 = self._xml_to_int(xmlScene.find(self.XML_FIELD3_TAG))
                scene.field4 = self._xml_to_int(xmlScene.find(self.XML_FIELD4_TAG))
                scene.isReactionScene = self._get_scene_is_reaction(xmlScene)
                scene.isSubPlot = self._get_scene_is_subplot(xmlScene)
                scene.day = self._xml_to_int(xmlScene.find(self.XML_DAY_TAG))
                scene.time = self._xml_to_text(xmlScene.find(self.XML_TIME_TAG))
                scene.lastsDays = self._xml_to_text(xmlScene.find(self.XML_LASTS_DAYS_TAG))
                scene.lastsHours = self._xml_to_text(xmlScene.find(self.XML_LASTS_HOURS_TAG))
                scene.lastsMinutes = self._xml_to_text(xmlScene.find(self.XML_LASTS_MINUTES_TAG))
                scene.wordCount = self._xml_to_int(xmlScene.find(self.XML_WORD_COUNT_TAG))
                scene.letterCount = self._xml_to_int(xmlScene.find(self.XML_LETTER_COUNT_TAG))
                scene.image = self._xml_to_text(xmlScene.find(self.XML_IMAGE_FILE_TAG))
                scene.goal = self._xml_to_text(xmlScene.find(self.XML_GOAL_TAG))
                scene.conflict = self._xml_to_text(xmlScene.find(self.XML_CONFLICT_TAG))
                scene.outcome = self._xml_to_text(xmlScene.find(self.XML_OUTCOME_TAG))
                scene.appendToPrev = self._xml_to_bool(xmlScene.find(self.XML_APPEND_TO_PREV_TAG))
                scene.doNotExport = self._get_scene_do_not_export(xmlScene)
                scene.date, scene.time = self._get_scene_date_time(xmlScene)
                scene.scnArcs = self._xml_to_text(xmlScene.find(self.XML_FIELD_SCENE_ARCS_TAG))
                scene.scnMode = self._xml_to_text(xmlScene.find(self.XML_FIELD_SCENE_MODE_TAG))
                self.novel.scenes[scId] = scene
                for kwVarName in self.SCN_KWVAR:
                    scene.kwVar[kwVarName] = self._xml_to_bool(xmlScene.find(kwVarName))

        # Chapter/Scene assignment
        if chapters is not None:
            for xmlChapter in chapters.findall(self.XML_CHAPTER_TAG):
                chId = self._xml_to_id(xmlChapter)
                chapter = self.novel.chapters[chId]
                xmlScenes = xmlChapter.find('Scenes')
                if xmlScenes is not None:
                    for xmlSceneId in xmlScenes.findall('ScID'):
                        scId = self._xml_to_id(xmlSceneId)
                        if scId in self.novel.scenes:
                            chapter.srtScenes.append(scId)

        # Characters section
        characters = root.find(self.XML_CHARACTERS_TAG)
        if characters is not None:
            for xmlCharacter in characters.findall(self.XML_CHARACTER_TAG):
                crId = self._xml_to_id(xmlCharacter)
                character = Character()
                character.title = self._xml_to_text(xmlCharacter.find(self.XML_TITLE_TAG))
                character.desc = self._xml_to_text(xmlCharacter.find(self.XML_DESC_TAG))
                character.notes = self._xml_to_text(xmlCharacter.find(self.XML_NOTES_TAG))
                character.tags = self._xml_to_list(xmlCharacter.find(self.XML_TAGS_TAG))
                character.image = self._xml_to_text(xmlCharacter.find(self.XML_IMAGE_FILE_TAG))
                character.aka = self._xml_to_text(xmlCharacter.find(self.XML_AKA_TAG))
                character.fullName = self._xml_to_text(xmlCharacter.find(self.XML_FULL_NAME_TAG))
                character.bio = self._xml_to_text(xmlCharacter.find(self.XML_BIO_TAG_CHAR))
                character.goals = self._xml_to_text(xmlCharacter.find(self.XML_GOALS_TAG))
                character.isMajor = self._xml_to_bool(xmlCharacter.find(self.XML_MAJOR_TAG))
                self.novel.characters[crId] = character
                self.novel.srtCharacters.append(crId)
                for kwVarName in self.CRT_KWVAR:
                    character.kwVar[kwVarName] = self._xml_to_bool(xmlCharacter.find(kwVarName))

        # Locations section
        locations = root.find(self.XML_LOCATIONS_TAG)
        if locations is not None:
            for xmlLocation in locations.findall(self.XML_LOCATION_TAG):
                lcId = self._xml_to_id(xmlLocation)
                location = Location()
                location.title = self._xml_to_text(xmlLocation.find(self.XML_TITLE_TAG))
                location.desc = self._xml_to_text(xmlLocation.find(self.XML_DESC_TAG))
                location.notes = self._xml_to_text(xmlLocation.find(self.XML_NOTES_TAG))
                location.tags = self._xml_to_list(xmlLocation.find(self.XML_TAGS_TAG))
                location.image = self._xml_to_text(xmlLocation.find(self.XML_IMAGE_FILE_TAG))
                location.aka = self._xml_to_text(xmlLocation.find(self.XML_AKA_TAG))
                self.novel.locations[lcId] = location
                self.novel.srtLocations.append(lcId)
                for kwVarName in self.LOC_KWVAR:
                    location.kwVar[kwVarName] = self._xml_to_bool(xmlLocation.find(kwVarName))

        # Items section
        items = root.find(self.XML_ITEMS_TAG)
        if items is not None:
            for xmlItem in items.findall(self.XML_ITEM_TAG):
                itId = self._xml_to_id(xmlItem)
                item = Item()
                item.title = self._xml_to_text(xmlItem.find(self.XML_TITLE_TAG))
                item.desc = self._xml_to_text(xmlItem.find(self.XML_DESC_TAG))
                item.notes = self._xml_to_text(xmlItem.find(self.XML_NOTES_TAG))
                item.tags = self._xml_to_list(xmlItem.find(self.XML_TAGS_TAG))
                item.image = self._xml_to_text(xmlItem.find(self.XML_IMAGE_FILE_TAG))
                item.aka = self._xml_to_text(xmlItem.find(self.XML_AKA_TAG))
                self.novel.items[itId] = item
                self.novel.srtItems.append(itId)
                for kwVarName in self.ITM_KWVAR:
                    item.kwVar[kwVarName] = self._xml_to_bool(xmlItem.find(kwVarName))

        # Project notes section
        projectNotes = root.find(self.XML_PROJECT_NOTES_TAG)
        if projectNotes is not None:
            for xmlProjectNote in projectNotes.findall(self.XML_PROJECT_NOTE_TAG):
                pnId = self._xml_to_id(xmlProjectNote)
                projectNote = ProjectNote()
                projectNote.title = self._xml_to_text(xmlProjectNote.find(self.XML_TITLE_TAG))
                projectNote.desc = self._xml_to_text(xmlProjectNote.find(self.XML_DESC_TAG))
                self.novel.projectNotes[pnId] = projectNote
                self.novel.srtPrjNotes.append(pnId)
                for kwVarName in self.PNT_KWVAR:
                    projectNote.kwVar[kwVarName] = self._xml_to_bool(xmlProjectNote.find(kwVarName))

        # Sort chapter scene lists and project notes list
        for chId in self.novel.srtChapters:
            self.novel.chapters[chId].srtScenes = sorted(self.novel.chapters[chId].srtScenes, key=lambda x: int(x))
        self.novel.srtPrjNotes = sorted(self.novel.srtPrjNotes, key=lambda x: int(x))

        # Generate cross references
        self.xrefs.generate_xref(self.novel)

        # Check for scene and chapter splitting
        self.splitter.split_scenes(self)

        # Check locale settings
        self.novel.check_locale()

        # Get language list
        self.novel.get_languages()


    def write(self):
        """Write the Novel instance variables to a .yw7 file.

        Create an XML tree from the Novel instance and write it to self.filePath.
        Raise the "Error" exception in case of error.
        """
        root = ET.Element('YWRITER7')
        appVersion = ET.SubElement(root, 'ywVer')
        appVersion.text = self.VERSION
        timeStamp = ET.SubElement(root, 'TimeStamp')
        dateString, timeString = self.get_date_time()
        timeStamp.text = f'{dateString} {timeString}'
        self.tree = ET.ElementTree(root)
        self._build_element_tree()
        self._postprocess_xml_file(self.filePath)


    def _build_element_tree(self):
        """Build the ElementTree instance from Novel instance variables.

        This method is called by self.write() and creates the XML tree from
        scratch, using the Novel instance and its parts.
        """
        root = self.tree.getroot()

        # Project section
        project = ET.SubElement(root, self.XML_PROJECT_TAG)
        ET.SubElement(project, self.XML_TITLE_TAG).text = self._text_to_xml(self.novel.title)
        ET.SubElement(project, self.XML_DESC_TAG).text = self._text_to_xml(self.novel.desc)
        ET.SubElement(project, self.XML_AUTHOR_NAME_TAG).text = self._text_to_xml(self.novel.authorName)
        ET.SubElement(project, self.XML_BIO_TAG).text = self._text_to_xml(self.novel.authorBio)
        ET.SubElement(project, self.XML_FIELD_TITLE_TAG + '1').text = self._text_to_xml(self.novel.fieldTitle1)
        ET.SubElement(project, self.XML_FIELD_TITLE_TAG + '2').text = self._text_to_xml(self.novel.fieldTitle2)
        ET.SubElement(project, self.XML_FIELD_TITLE_TAG + '3').text = self._text_to_xml(self.novel.fieldTitle3)
        ET.SubElement(project, self.XML_FIELD_TITLE_TAG + '4').text = self._text_to_xml(self.novel.fieldTitle4)
        ET.SubElement(project, self.XML_WORD_TARGET_TAG).text = str(self.novel.wordTarget)
        ET.SubElement(project, self.XML_WORD_COUNT_START_TAG).text = str(self.novel.wordCountStart)
        if self.novel.kwVar:
            for kwVarName in self.PRJ_KWVAR:
                if self.novel.kwVar.get(kwVarName) is not None: # write custom fields only if they are set
                    ET.SubElement(project, kwVarName).text = self._bool_to_xml(self.novel.kwVar[kwVarName])

        # Chapters section
        chapters = ET.SubElement(root, self.XML_CHAPTERS_TAG)
        for chId in self.novel.srtChapters:
            chapter = self.novel.chapters[chId]
            xmlChapter = ET.SubElement(chapters, self.XML_CHAPTER_TAG)
            xmlChapter.set('ID', chId)
            ET.SubElement(xmlChapter, self.XML_TITLE_TAG).text = self._text_to_xml(chapter.title)
            ET.SubElement(xmlChapter, self.XML_DESC_TAG).text = self._text_to_xml(chapter.desc)
            ET.SubElement(xmlChapter, self.XML_SECTION_START_TAG).text = self._int_to_xml(chapter.chLevel)
            self._set_chapter_type(xmlChapter, chapter.chType)
            self._set_chapter_suppress_title(xmlChapter, chapter.suppressChapterTitle)
            self._set_chapter_suppress_break(xmlChapter, chapter.suppressChapterBreak)
            self._set_chapter_is_trash(xmlChapter, chapter.isTrash)
            scenes = ET.SubElement(xmlChapter, 'Scenes')
            for scId in chapter.srtScenes:
                ET.SubElement(scenes, 'ScID').text = scId
            if chapter.kwVar:
                for kwVarName in self.CHP_KWVAR:
                    if chapter.kwVar.get(kwVarName) is not None: # write custom fields only if they are set
                        ET.SubElement(xmlChapter, kwVarName).text = self._bool_to_xml(chapter.kwVar[kwVarName])

        # Scenes section
        scenes = ET.SubElement(root, self.XML_SCENES_TAG)
        for scId in self.novel.srtScenes:
            scene = self.novel.scenes[scId]
            xmlScene = ET.SubElement(scenes, self.XML_SCENE_TAG)
            xmlScene.set('ID', scId)
            ET.SubElement(xmlScene, self.XML_TITLE_TAG).text = self._text_to_xml(scene.title)
            ET.SubElement(xmlScene, self.XML_DESC_TAG).text = self._text_to_xml(scene.desc)
            ET.SubElement(xmlScene, self.XML_SCENE_CONTENT_TAG).text = self._text_to_xml(scene.sceneContent)
            self._set_scene_status(xmlScene, scene.status)
            ET.SubElement(xmlScene, self.XML_NOTES_TAG).text = self._text_to_xml(scene.notes)
            ET.SubElement(xmlScene, self.XML_TAGS_TAG).text = self._list_to_xml(scene.tags)
            ET.SubElement(xmlScene, self.XML_FIELD1_TAG).text = self._int_to_xml(scene.field1)
            ET.SubElement(xmlScene, self.XML_FIELD2_TAG).text = self._int_to_xml(scene.field2)
            ET.SubElement(xmlScene, self.XML_FIELD3_TAG).text = self._int_to_xml(scene.field3)
            ET.SubElement(xmlScene, self.XML_FIELD4_TAG).text = self._int_to_xml(scene.field4)
            ET.SubElement(xmlScene, self.XML_REACTION_SCENE_TAG).text = self._bool_to_xml(scene.isReactionScene)
            ET.SubElement(xmlScene, self.XML_SUBPLOT_TAG).text = self._bool_to_xml(scene.isSubPlot)
            ET.SubElement(xmlScene, self.XML_DAY_TAG).text = self._int_to_xml(scene.day)
            ET.SubElement(xmlScene, self.XML_TIME_TAG).text = self._text_to_xml(scene.time)
            ET.SubElement(xmlScene, self.XML_LASTS_DAYS_TAG).text = self._text_to_xml(scene.lastsDays)
            ET.SubElement(xmlScene, self.XML_LASTS_HOURS_TAG).text = self._text_to_xml(scene.lastsHours)
            ET.SubElement(xmlScene, self.XML_LASTS_MINUTES_TAG).text = self._text_to_xml(scene.lastsMinutes)
            ET.SubElement(xmlScene, self.XML_WORD_COUNT_TAG).text = self._int_to_xml(scene.wordCount)
            ET.SubElement(xmlScene, self.XML_LETTER_COUNT_TAG).text = self._int_to_xml(scene.letterCount)
            ET.SubElement(xmlScene, self.XML_IMAGE_FILE_TAG).text = self._text_to_xml(scene.image)
            ET.SubElement(xmlScene, self.XML_GOAL_TAG).text = self._text_to_xml(scene.goal)
            ET.SubElement(xmlScene, self.XML_CONFLICT_TAG).text = self._text_to_xml(scene.conflict)
            ET.SubElement(xmlScene, self.XML_OUTCOME_TAG).text = self._text_to_xml(scene.outcome)
            ET.SubElement(xmlScene, self.XML_APPEND_TO_PREV_TAG).text = self._bool_to_xml(scene.appendToPrev)
            self._set_scene_do_not_export(xmlScene, scene.doNotExport)
            self._set_scene_date_time(xmlScene, scene.date, scene.time)
            ET.SubElement(xmlScene, self.XML_FIELD_SCENE_ARCS_TAG).text = self._text_to_xml(scene.scnArcs)
            ET.SubElement(xmlScene, self.XML_FIELD_SCENE_MODE_TAG).text = self._text_to_xml(scene.scnMode)
            if scene.kwVar:
                for kwVarName in self.SCN_KWVAR:
                    if scene.kwVar.get(kwVarName) is not None: # write custom fields only if they are set
                        ET.SubElement(xmlScene, kwVarName).text = self._bool_to_xml(scene.kwVar[kwVarName])
            if scene.characters:
                characters = ET.SubElement(xmlScene, 'Characters')
                for crId in scene.characters:
                    ET.SubElement(characters, 'CharID').text = crId
            if scene.locations:
                locations = ET.SubElement(xmlScene, 'Locations')
                for lcId in scene.locations:
                    ET.SubElement(locations, 'LocID').text = lcId
            if scene.items:
                items = ET.SubElement(xmlScene, 'Items')
                for itId in scene.items:
                    ET.SubElement(items, 'ItemID').text = itId

        # Characters section
        characters = ET.SubElement(root, self.XML_CHARACTERS_TAG)
        for crId in self.novel.srtCharacters:
            character = self.novel.characters[crId]
            xmlCharacter = ET.SubElement(characters, self.XML_CHARACTER_TAG)
            xmlCharacter.set('ID', crId)
            ET.SubElement(xmlCharacter, self.XML_TITLE_TAG).text = self._text_to_xml(character.title)
            ET.SubElement(xmlCharacter, self.XML_DESC_TAG).text = self._text_to_xml(character.desc)
            ET.SubElement(xmlCharacter, self.XML_NOTES_TAG).text = self._text_to_xml(character.notes)
            ET.SubElement(xmlCharacter, self.XML_TAGS_TAG).text = self._list_to_xml(character.tags)
            ET.SubElement(xmlCharacter, self.XML_IMAGE_FILE_TAG).text = self._text_to_xml(character.image)
            ET.SubElement(xmlCharacter, self.XML_AKA_TAG).text = self._text_to_xml(character.aka)
            ET.SubElement(xmlCharacter, self.XML_FULL_NAME_TAG).text = self._text_to_xml(character.fullName)
            ET.SubElement(xmlCharacter, self.XML_BIO_TAG_CHAR).text = self._text_to_xml(character.bio)
            ET.SubElement(xmlCharacter, self.XML_GOALS_TAG).text = self._text_to_xml(character.goals)
            ET.SubElement(xmlCharacter, self.XML_MAJOR_TAG).text = self._bool_to_xml(character.isMajor)
            if character.kwVar:
                for kwVarName in self.CRT_KWVAR:
                    if character.kwVar.get(kwVarName) is not None: # write custom fields only if they are set
                        ET.SubElement(xmlCharacter, kwVarName).text = self._bool_to_xml(character.kwVar[kwVarName])

        # Locations section
        locations = ET.SubElement(root, self.XML_LOCATIONS_TAG)
        for lcId in self.novel.srtLocations:
            location = self.novel.locations[lcId]
            xmlLocation = ET.SubElement(locations, self.XML_LOCATION_TAG)
            xmlLocation.set('ID', lcId)
            ET.SubElement(xmlLocation, self.XML_TITLE_TAG).text = self._text_to_xml(location.title)
            ET.SubElement(xmlLocation, self.XML_DESC_TAG).text = self._text_to_xml(location.desc)
            ET.SubElement(xmlLocation, self.XML_NOTES_TAG).text = self._text_to_xml(location.notes)
            ET.SubElement(xmlLocation, self.XML_TAGS_TAG).text = self._list_to_xml(location.tags)
            ET.SubElement(xmlLocation, self.XML_IMAGE_FILE_TAG).text = self._text_to_xml(location.image)
            ET.SubElement(xmlLocation, self.XML_AKA_TAG).text = self._text_to_xml(location.aka)
            if location.kwVar:
                for kwVarName in self.LOC_KWVAR:
                    if location.kwVar.get(kwVarName) is not None: # write custom fields only if they are set
                        ET.SubElement(xmlLocation, kwVarName).text = self._bool_to_xml(location.kwVar[kwVarName])

        # Items section
        items = ET.SubElement(root, self.XML_ITEMS_TAG)
        for itId in self.novel.srtItems:
            item = self.novel.items[itId]
            xmlItem = ET.SubElement(items, self.XML_ITEM_TAG)
            xmlItem.set('ID', itId)
            ET.SubElement(xmlItem, self.XML_TITLE_TAG).text = self._text_to_xml(item.title)
            ET.SubElement(xmlItem, self.XML_DESC_TAG).text = self._text_to_xml(item.desc)
            ET.SubElement(xmlItem, self.XML_NOTES_TAG).text = self._text_to_xml(item.notes)
            ET.SubElement(xmlItem, self.XML_TAGS_TAG).text = self._list_to_xml(item.tags)
            ET.SubElement(xmlItem, self.XML_IMAGE_FILE_TAG).text = self._text_to_xml(item.image)
            ET.SubElement(xmlItem, self.XML_AKA_TAG).text = self._text_to_xml(item.aka)
            if item.kwVar:
                for kwVarName in self.ITM_KWVAR:
                    if item.kwVar.get(kwVarName) is not None: # write custom fields only if they are set
                        ET.SubElement(xmlItem, kwVarName).text = self._bool_to_xml(item.kwVar[kwVarName])

        # Project notes section
        projectNotes = ET.SubElement(root, self.XML_PROJECT_NOTES_TAG)
        for pnId in self.novel.srtPrjNotes:
            projectNote = self.novel.projectNotes[pnId]
            xmlProjectNote = ET.SubElement(projectNotes, self.XML_PROJECT_NOTE_TAG)
            xmlProjectNote.set('ID', pnId)
            ET.SubElement(xmlProjectNote, self.XML_TITLE_TAG).text = self._text_to_xml(projectNote.title)
            ET.SubElement(xmlProjectNote, self.XML_DESC_TAG).text = self._text_to_xml(projectNote.desc)
            if projectNote.kwVar:
                for kwVarName in self.PNT_KWVAR:
                    if projectNote.kwVar.get(kwVarName) is not None: # write custom fields only if they are set
                        ET.SubElement(xmlProjectNote, kwVarName).text = self._bool_to_xml(projectNote.kwVar[kwVarName])

        xml_indent.indent(root) # <--- CALL INDENT FUNCTION FROM xml_indent MODULE


    def _postprocess_xml_file(self, filePath):
        """Postprocess xml file created by ElementTree for yWriter.

        Positional argument:
            filePath: str -- path to .yw7 xml file.

        - Add XML declaration,
        - indent XML code for readability.
        """
        rough_string = ET.tostring(self.tree.getroot(), encoding='utf-8')
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding='utf-8').decode()
        # Remove leading and trailing linefeeds
        pretty_xml = pretty_xml.strip()
        # Replace double linefeeds by single ones
        pretty_xml = pretty_xml.replace('\r\n\r\n', '\r\n') # Windows
        pretty_xml = pretty_xml.replace('\n\n', '\n') # Linux/Mac
        try:
            with open(filePath, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
        except(PermissionError):
            raise Error(f'{_("File is write protected")}: "{norm_path(filePath)}".')


    def _xml_to_text(self, xmlElement):
        """Safe access to XML element text.

        Return element text content. If the element is None or has no text 
        content, return None.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        if xmlElement is None:
            return None
        if xmlElement.text:
            return xmlElement.text
        return ''


    def _xml_to_int(self, xmlElement):
        """Safe access to XML element integer.

        Return element text content converted to integer. If the element is None 
        or has no text content, return 0.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        if xmlElement is None:
            return 0
        if xmlElement.text:
            return int(xmlElement.text)
        return 0


    def _xml_to_bool(self, xmlElement):
        """Safe access to XML element boolean.

        Return element text content converted to boolean. If the element is None 
        or has no text content, return False.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        if xmlElement is None:
            return False
        if xmlElement.text == '-1':
            return True
        return False


    def _xml_to_id(self, xmlElement):
        """Safe access to XML element ID.

        Return element tag "ID" attribute value. If the element is None or has 
        no "ID" attribute, return '1'.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        if xmlElement is None:
            return '1'
        if xmlElement.get('ID') is not None:
            return xmlElement.get('ID')
        return '1'


    def _xml_to_list(self, xmlElement):
        """Safe access to XML tag list.

        Return element text content converted to list. If the element is None 
        or has no text content, return None.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        if xmlElement is None:
            return None
        if xmlElement.text:
            return string_to_list(xmlElement.text)
        return []


    def _text_to_xml(self, text):
        """Safe conversion of text for XML output.

        Replace XML special characters. Return None if text is None.

        Positional arguments:
            text -- plain text.
        """
        if text is None:
            return None
        text = str(text) # in case of integer or float
        text = text.replace('&', '&')
        text = text.replace('<', '<')
        text = text.replace('>', '>')
        # text = text.replace("'", ''') # optional
        text = text.replace('"', '"')
        return text


    def _bool_to_xml(self, state):
        """Return yWriter's representation of a boolean value.

        Positional arguments:
            state -- boolean value.
        """
        if state:
            return '-1'
        return '0'


    def _int_to_xml(self, number):
        """Convert integer to XML text.

        Return "0" if number is None.

        Positional arguments:
            number -- integer value or None.
        """
        if number is None:
            return '0'
        return str(number)


    def _list_to_xml(self, tagList):
        """Convert tag list to XML text.

        Return None if tagList is None.

        Positional arguments:
            tagList -- list of tags or None.
        """
        if tagList is None:
            return None
        return list_to_string(tagList)


    def _get_scene_status(self, xmlScene):
        """Get scene status from XML tag.

        Return scene status (integer). If no status is set, return 1 (Outline).

        Positional arguments:
            xmlScene -- ElementTree object.
        """
        status = xmlScene.find(self.XML_STATUS_TAG)
        if status is None:
            return 1
        return int(status.text)


    def _set_scene_status(self, xmlScene, status):
        """Set scene status in XML tag.

        Positional arguments:
            xmlScene -- ElementTree object.
            status -- status code (integer).
        """
        ET.SubElement(xmlScene, self.XML_STATUS_TAG).text = str(status)


    def _get_chapter_type(self, xmlChapter):
        """Get chapter type from XML tag.

        Return chapter type (integer). If no type is set, return 0 (Normal).

        Positional arguments:
            xmlChapter -- ElementTree object.
        """
        chapterType = xmlChapter.find(self.XML_CHAPTER_TYPE_TAG)
        if chapterType is not None:
            return int(chapterType.text) # since yWriter 7.0.7.2
        typeTag = xmlChapter.find(self.XML_TYPE_TAG)
        if typeTag is not None:
            return int(typeTag.text) # yWriter versions before 7.0.7.2
        unusedTag = xmlChapter.find(self.XML_UNUSED_TAG)
        if unusedTag is not None:
            if unusedTag.text == '-1':
                return 3 # Unused
        return 0 # Normal


    def _set_chapter_type(self, xmlChapter, chapterType):
        """Set chapter type in XML tag.

        Positional arguments:
            xmlChapter -- ElementTree object.
            chapterType -- chapter type code (integer).
        """
        ET.SubElement(xmlChapter, self.XML_CHAPTER_TYPE_TAG).text = str(chapterType)


    def _get_scene_is_reaction(self, xmlScene):
        """Get scene type from XML tag.

        Return True if scene type is "reaction". Otherwise return False (action).

        Positional arguments:
            xmlScene -- ElementTree object.
        """
        reactionScene = xmlScene.find(self.XML_REACTION_SCENE_TAG)
        if reactionScene is not None:
            if reactionScene.text == '-1':
                return True
        return False


    def _get_scene_is_subplot(self, xmlScene):
        """Get scene subplot status from XML tag.

        Return True if scene is "subplot". Otherwise return False (main plot).

        Positional arguments:
            xmlScene -- ElementTree object.
        """
        subPlot = xmlScene.find(self.XML_SUBPLOT_TAG)
        if subPlot is not None:
            if subPlot.text == '-1':
                return True
        return False


    def _get_chapter_is_trash(self, xmlChapter):
        """Get chapter "trash bin" status from XML tag.

        Return True if chapter is "trash bin". Otherwise return False (not trash).

        Positional arguments:
            xmlChapter -- ElementTree object.
        """
        field = xmlChapter.find(self.XML_FIELDS_TAG)
        if field is not None:
            isTrash = field.find(self.XML_FIELD_IS_TRASH_TAG)
            if isTrash is not None:
                if isTrash.text == '1':
                    return True
        return False


    def _set_chapter_is_trash(self, xmlChapter, isTrash):
        """Set chapter "trash bin" status in XML tag.

        Positional arguments:
            xmlChapter -- ElementTree object.
            isTrash -- trash bin status (boolean).
        """
        fields = ET.SubElement(xmlChapter, self.XML_FIELDS_TAG)
        ET.SubElement(fields, self.XML_FIELD_IS_TRASH_TAG).text = self._bool_to_xml(isTrash)


    def _get_scene_do_not_export(self, xmlScene):
        """Get scene "do not export" status from XML tag.

        Return True if scene is set to "do not export". Otherwise return False (export).

        Positional arguments:
            xmlScene -- ElementTree object.
        """
        exportCondSpecific = xmlScene.find(self.XML_EXPORT_COND_SPECIFIC_TAG)
        if exportCondSpecific is not None:
            exportWhenRtf = exportCondSpecific.find(self.XML_EXPORT_WHEN_RTF_TAG)
            if exportWhenRtf is not None:
                if exportWhenRtf.text == '0':
                    return True
        return False


    def _set_scene_do_not_export(self, xmlScene, doNotExport):
        """Set scene "do not export" status in XML tag.

        Positional arguments:
            xmlScene -- ElementTree object.
            doNotExport -- do-not-export status (boolean).
        """
        exportCondSpecific = ET.SubElement(xmlScene, self.XML_EXPORT_COND_SPECIFIC_TAG)
        ET.SubElement(exportCondSpecific, self.XML_EXPORT_WHEN_RTF_TAG).text = self._bool_to_xml(doNotExport)


    def _get_chapter_suppress_title(self, xmlChapter):
        """Get chapter suppress title setting from XML tag.

        Return True if chapter title is set to be suppressed in export.
        Otherwise return False (display title).

        Positional arguments:
            xmlChapter -- ElementTree object.
        """
        fields = xmlChapter.find(self.XML_FIELDS_TAG)
        if fields is not None:
            suppressChapterTitle = fields.find(self.XML_FIELD_SUPPRESS_CHAPTER_TITLE_TAG)
            if suppressChapterTitle is not None:
                if suppressChapterTitle.text == '1':
                    return True
        return False


    def _set_chapter_suppress_title(self, xmlChapter, suppressChapterTitle):
        """Set chapter suppress title setting in XML tag.

        Positional arguments:
            xmlChapter -- ElementTree object.
            suppressChapterTitle -- suppress chapter title setting (boolean).
        """
        fields = ET.SubElement(xmlChapter, self.XML_FIELDS_TAG)
        ET.SubElement(fields, self.XML_FIELD_SUPPRESS_CHAPTER_TITLE_TAG).text = self._bool_to_xml(suppressChapterTitle)


    def _get_chapter_suppress_break(self, xmlChapter):
        """Get chapter suppress break setting from XML tag.

        Return True if chapter break is set to be suppressed in export.
        Otherwise return False (display break).

        Positional arguments:
            xmlChapter -- ElementTree object.
        """
        fields = xmlChapter.find(self.XML_FIELDS_TAG)
        if fields is not None:
            suppressChapterBreak = fields.find(self.XML_FIELD_SUPPRESS_CHAPTER_BREAK_TAG)
            if suppressChapterBreak is not None:
                if suppressChapterBreak.text == '1':
                    return True
        return False


    def _set_chapter_suppress_break(self, xmlChapter, suppressChapterBreak):
        """Set chapter suppress break setting in XML tag.

        Positional arguments:
            xmlChapter -- ElementTree object.
            suppressChapterBreak -- suppress chapter break setting (boolean).
        """
        fields = ET.SubElement(xmlChapter, self.XML_FIELDS_TAG)
        ET.SubElement(fields, self.XML_FIELD_SUPPRESS_CHAPTER_BREAK_TAG).text = self._bool_to_xml(suppressChapterBreak)


    def _get_scene_date_time(self, xmlScene):
        """Get scene date and time from XML tag.

        Return date and time strings in yw7 format ('yyyy-mm-dd', 'hh:mm:ss').
        If no date/time is set, return ('0001-01-01', '00:00:00').

        Positional arguments:
            xmlScene -- ElementTree object.
        """
        if self._xml_to_bool(xmlScene.find(self.XML_SPECIFIC_DATE_MODE_TAG)):
            ywDateTime = self._xml_to_text(xmlScene.find(self.XML_SPECIFIC_DATE_TIME_TAG))
            if ywDateTime:
                try:
                    dt = datetime.datetime.strptime(ywDateTime, '%Y-%m-%d %H:%M:%S')
                    dateString = dt.strftime('%Y-%m-%d')
                    timeString = dt.strftime('%H:%M:%S')
                    return dateString, timeString
                except:
                    pass # invalid date/time format
        return Scene.NULL_DATE, Scene.NULL_TIME # default values


    def _set_scene_date_time(self, xmlScene, dateString, timeString):
        """Set scene date and time in XML tag.

        Positional arguments:
            xmlScene -- ElementTree object.
            dateString -- date in yw7 format 'yyyy-mm-dd'.
            timeString -- time in yw7 format 'hh:mm:ss'.
        """
        ET.SubElement(xmlScene, self.XML_SPECIFIC_DATE_MODE_TAG).text = '-1'
        ET.SubElement(xmlScene, self.XML_SPECIFIC_DATE_TIME_TAG).text = f'{dateString} {timeString}'


    def get_element_id(self, xmlElement):
        """get element ID from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._xml_to_id(xmlElement)


    def get_element_title(self, xmlElement):
        """get element title from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._xml_to_text(xmlElement.find(self.XML_TITLE_TAG))


    def get_element_desc(self, xmlElement):
        """get element description from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._xml_to_text(xmlElement.find(self.XML_DESC_TAG))


    def get_element_notes(self, xmlElement):
        """get element notes from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._xml_to_text(xmlElement.find(self.XML_NOTES_TAG))


    def get_element_tags(self, xmlElement):
        """get element tags from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._xml_to_list(xmlElement.find(self.XML_TAGS_TAG))


    def get_element_aka(self, xmlElement):
        """get element "aka" from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._xml_to_text(xmlElement.find(self.XML_AKA_TAG))


    def get_element_image(self, xmlElement):
        """get element image path from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._xml_to_text(xmlElement.find(self.XML_IMAGE_FILE_TAG))


    def get_element_field(self, xmlElement, fieldId):
        """get element custom field from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
            fieldId -- field number (1-4).
        """
        return self._xml_to_int(xmlElement.find(self.XML_FIELD_TITLE_TAG + str(fieldId)))


    def get_element_status(self, xmlElement):
        """get scene status from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._get_scene_status(xmlElement)


    def get_element_type(self, xmlElement):
        """get chapter type from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._get_chapter_type(xmlElement)


    def get_element_level(self, xmlElement):
        """get chapter level from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._xml_to_int(xmlElement.find(self.XML_SECTION_START_TAG))


    def get_element_is_reaction(self, xmlElement):
        """get scene type from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._get_scene_is_reaction(xmlElement)


    def get_element_is_subplot(self, xmlElement):
        """get scene subplot status from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._get_scene_is_subplot(xmlElement)


    def get_element_is_trash(self, xmlElement):
        """get chapter "trash bin" status from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._get_chapter_is_trash(xmlElement)


    def get_element_do_not_export(self, xmlElement):
        """get scene "do not export" status from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._get_scene_do_not_export(xmlElement)


    def get_element_suppress_chapter_title(self, xmlElement):
        """get chapter suppress title setting from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._get_chapter_suppress_title(xmlElement)


    def get_element_suppress_chapter_break(self, xmlElement):
        """get chapter suppress break setting from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._get_chapter_suppress_break(xmlElement)


    def get_element_append_to_previous(self, xmlElement):
        """get scene append setting from XML tag.

        Positional arguments:
            xmlElement -- ElementTree object.
        """
        return self._xml_to_bool(xmlElement.find(self.XML_APPEND_TO_PREV_TAG))