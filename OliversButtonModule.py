#Version 3.0
#with event based button function execution
#author: OliverMMiller
import pygame
from typing import Callable

class button():
    def updateImages(self, defaultImage: pygame.surface.Surface, 
                     hoverImage: pygame.surface.Surface | None = None, 
                     clickedImage: pygame.surface.Surface | None = None):
        
        self.defaultImage = pygame.transform.scale((defaultImage),(self.myRect.width, self.myRect.height))
        if hoverImage == None:
            self.hoverImage = self.defaultImage.copy()
        else:
            self.hoverImage = pygame.transform.scale((hoverImage),(self.myRect.width, self.myRect.height))
        if clickedImage == None:
            self.clickedImage = self.hoverImage.copy()
        else:
            self.clickedImage = pygame.transform.scale((clickedImage),(self.myRect.width, self.myRect.height))

    def __init__(self, DISPLAYSURF: pygame.surface.Surface, parentScenes: list, myRect: pygame.Rect,
                 defaultImage: pygame.surface.Surface, hoverImage: pygame.surface.Surface | None = None, clickedImage: pygame.surface.Surface | None = None,
                 onClickFunction: Callable = None, runFuncOnce: bool = True):
        """
        Dependencies:
            pygame
            
        Args:
            parentScenes (list): scenes to add self to
            myRect (pygame.Rect): Rect for this button
            defaultImage (pygame.surface.Surface): default image to display
            hoverImage (pygame.surface.Surface | None, optional): image to display on hover. Defaults to defaultImage.
            clickedImage (pygame.surface.Surface | None, optional): image to display on click. Defaults to defaultImage.
            onclickFunction (function, optional): function to run when button clicked. Defaults to None.
            runFuncOnce (bool, optional): if false onclickFunction will run every time process() is called. Defaults to True.
        """
        self.DISPLAYSURF = DISPLAYSURF

        self.onClickFunction = onClickFunction
        self.onReleaseFunction = None
        self.runFuncOnce = runFuncOnce
        
        self.ignoreNextPress = False
        self.alreadyPressed = False

        self.updateImages(defaultImage, hoverImage, clickedImage)
        
        self.myRect = myRect

        for num in range(len(parentScenes)):
            parentScenes[num].insert(0,self)

    def __repr__(self):
        return self.__name__
            
    def process(self, mousePos: tuple[int,int] | None) -> None:
        """
        draws button to DISPLAYSURF with appropriate image
        
        Args:
            mousePos (tuple[int,int]): mouse coordinates 
        """
          
        
        if mousePos == None:
            mousePos = pygame.mouse.get_pos()
   
        if self.myRect.collidepoint(mousePos):
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                self.DISPLAYSURF.blit(self.clickedImage, self.myRect)
            else:
                self.DISPLAYSURF.blit(self.hoverImage, self.myRect)
        else:
            self.DISPLAYSURF.blit(self.defaultImage, self.myRect)
        