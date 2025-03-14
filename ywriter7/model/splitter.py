"""Provide a helper class for scene and chapter splitting.

Copyright (c) 2023 Peter Triesberger
For further information see https://github.com/peter88213/PyWriter
Published under the MIT License (https://opensource.org/licenses/mit-license.php)
"""
from ..pywriter_globals import *
from .chapter import Chapter
from .scene import Scene
from .id_generator import create_id


class Splitter:
    """Helper class for scene and chapter splitting.
    
    When importing scenes to yWriter, they may contain manually inserted scene and chapter dividers.
    The Splitter class updates a Novel instance by splitting such scenes and creating new chapters and scenes. 
    
    Public methods:
        split_scenes(novel) -- Split scenes by inserted chapter and scene dividers.
        
    Public class constants:
        PART_SEPARATOR -- marker indicating the beginning of a new part, splitting a scene.
        CHAPTER_SEPARATOR -- marker indicating the beginning of a new chapter, splitting a scene.
        SCENE_SEPARATOR -- marker indicating the beginning of a new scene, splitting a scene.
        DESC_SEPARATOR -- marker separating title and description of a chapter or scene.
    """
    PART_SEPARATOR = '#'
    CHAPTER_SEPARATOR = '##'
    SCENE_SEPARATOR = '###'
    DESC_SEPARATOR = '|'
    _CLIP_TITLE = 20
    # Maximum length of newly generated scene titles.

    def split_scenes(self, file):
        """Split scenes by inserted chapter and scene dividers.
        
        Update a Novel instance by generating new chapters and scenes 
        if there are dividers within the scene content.
        
        Positional argument: 
            file -- File instance to update.
        
        Return True if the sructure has changed, 
        otherwise return False.        
        """

        def create_chapter(chapterId: str, title: str, desc: str, level: int):
            """Create a new chapter and add it to the file.novel.
            
            Positional arguments:
                chapterId -- str: ID of the chapter to create.
                title -- str: title of the chapter to create.
                desc -- str: description of the chapter to create.
                level -- int: chapter level (part/chapter).           
            """
            newChapter = Chapter()
            newChapter.title = title
            newChapter.desc = desc
            newChapter.chLevel = level
            newChapter.chType = 0
            file.novel.chapters[chapterId] = newChapter

        def create_scene(sceneId: str, parent: str, splitCount: int, title: str, desc: str):
            """Create a new scene and add it to the file.novel.
            
            Positional arguments:
                sceneId -- str: ID of the scene to create.
                parent -- Scene instance: parent scene.
                splitCount -- int: number of parent's splittings.
                title -- str: title of the scene to create.
                desc -- str: description of the scene to create.
            """
            WARNING = '(!)'

            # Mark metadata of split scenes.
            newScene = Scene()
            if title:
                newScene.title = title
            elif parent.title:
                if len(parent.title) > self._CLIP_TITLE:
                    title = f'{parent.title[:self._CLIP_TITLE]}...'
                else:
                    title = parent.title
                newScene.title = f'{title} Split: {splitCount}'
            else:
                newScene.title = f'{_("New Scene")} Split: {splitCount}'
            if desc:
                newScene.desc = desc
            if parent.desc and not parent.desc.startswith(WARNING):
                parent.desc = f'{WARNING}{parent.desc}'
            if parent.goal and not parent.goal.startswith(WARNING):
                parent.goal = f'{WARNING}{parent.goal}'
            if parent.conflict and not parent.conflict.startswith(WARNING):
                parent.conflict = f'{WARNING}{parent.conflict}'
            if parent.outcome and not parent.outcome.startswith(WARNING):
                parent.outcome = f'{WARNING}{parent.outcome}'

            # Reset the parent's status to Draft, if not Outline.
            if parent.status > 2:
                parent.status = 2
            newScene.status = parent.status
            newScene.scType = parent.scType
            newScene.date = parent.date
            newScene.time = parent.time
            newScene.day = parent.day
            newScene.lastsDays = parent.lastsDays
            newScene.lastsHours = parent.lastsHours
            newScene.lastsMinutes = parent.lastsMinutes
            file.novel.scenes[sceneId] = newScene

        # Process chapters and scenes.
        scenesSplit = False
        srtChapters = []
        for chId in file.novel.srtChapters:
            srtChapters.append(chId)
            chapterId = chId
            srtScenes = []
            for scId in file.novel.chapters[chId].srtScenes:
                srtScenes.append(scId)
                if not file.novel.scenes[scId].sceneContent:
                    continue

                sceneId = scId
                lines = file.novel.scenes[scId].sceneContent.split('\n')
                newLines = []
                inScene = True
                sceneSplitCount = 0

                # Search scene content for dividers.
                for line in lines:
                    heading = line.strip('# ').split(self.DESC_SEPARATOR)
                    title = heading[0]
                    try:
                        desc = heading[1]
                    except:
                        desc = ''
                    if line.startswith(self.SCENE_SEPARATOR):
                        # Split the scene.
                        file.novel.scenes[sceneId].sceneContent = '\n'.join(newLines)
                        newLines = []
                        sceneSplitCount += 1
                        sceneId = create_id(file.novel.scenes)
                        create_scene(sceneId, file.novel.scenes[scId], sceneSplitCount, title, desc)
                        srtScenes.append(sceneId)
                        scenesSplit = True
                        inScene = True
                    elif line.startswith(self.CHAPTER_SEPARATOR):
                        # Start a new chapter.
                        if inScene:
                            file.novel.scenes[sceneId].sceneContent = '\n'.join(newLines)
                            newLines = []
                            sceneSplitCount = 0
                            inScene = False
                        file.novel.chapters[chapterId].srtScenes = srtScenes
                        srtScenes = []
                        chapterId = create_id(file.novel.chapters)
                        if not title:
                            title = _('New Chapter')
                        create_chapter(chapterId, title, desc, 0)
                        srtChapters.append(chapterId)
                        scenesSplit = True
                    elif line.startswith(self.PART_SEPARATOR):
                        # start a new part.
                        if inScene:
                            file.novel.scenes[sceneId].sceneContent = '\n'.join(newLines)
                            newLines = []
                            sceneSplitCount = 0
                            inScene = False
                        file.novel.chapters[chapterId].srtScenes = srtScenes
                        srtScenes = []
                        chapterId = create_id(file.novel.chapters)
                        if not title:
                            title = _('New Part')
                        create_chapter(chapterId, title, desc, 1)
                        srtChapters.append(chapterId)
                    elif not inScene:
                        # Append a scene without heading to a new chapter or part.
                        newLines.append(line)
                        sceneSplitCount += 1
                        sceneId = create_id(file.novel.scenes)
                        create_scene(sceneId, file.novel.scenes[scId], sceneSplitCount, '', '')
                        srtScenes.append(sceneId)
                        scenesSplit = True
                        inScene = True
                    else:
                        newLines.append(line)
                if inScene:
                    file.novel.scenes[sceneId].sceneContent = '\n'.join(newLines)
            file.novel.chapters[chapterId].srtScenes = srtScenes
        file.novel.srtChapters = srtChapters
        return scenesSplit
