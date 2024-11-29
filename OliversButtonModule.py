import pygame
#from typing import Callable

class button():
    def updateImages(self, defaultImage: pygame.surface.Surface, 
                     hoverImage: pygame.surface.Surface | None = None, 
                     clickedImage: pygame.surface.Surface | None = None):
        self.defaultImage = pygame.transform.scale((defaultImage),(self.width, self.height))
        if hoverImage == None:
            self.hoverImage = self.defaultImage.copy()
        else:
            self.hoverImage = pygame.transform.scale((hoverImage),(self.width, self.height))
        if clickedImage == None:
            self.clickedImage = self.hoverImage.copy()
        else:
            self.clickedImage = pygame.transform.scale((clickedImage),(self.width, self.height))

    def __init__(self, DISPLAYSURF, parentScenes: list, x: int, y: int, width: int, height: int,
                 defaultImage: pygame.surface.Surface, hoverImage: pygame.surface.Surface | None = None, clickedImage: pygame.surface.Surface | None = None,
                 onclickFunction: ... = None, runFuncOnce: bool = True):
        """
        Dependencies:
            pygame
            
        Args:
            parentScenes (list): scenes to add self to
            x (int): x cord
            y (int): y cord
            width (int): button width
            height (int): button height
            defaultImage (pygame.surface.Surface): default image to display
            hoverImage (pygame.surface.Surface | None, optional): image to display on hover. Defaults to defaultImage.
            clickedImage (pygame.surface.Surface | None, optional): image to display on click. Defaults to defaultImage.
            onclickFunction (function, optional): function to run when button clicked. Defaults to None.
            runFuncOnce (bool, optional): if false onclickFunction will run every time process() is called. Defaults to True.
        """
        self.DISPLAYSURF = DISPLAYSURF
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onclickFunction = onclickFunction
        self.runFuncOnce = runFuncOnce
        
        self.ignoreNextPress = False
        self.alreadyPressed = False

        self.updateImages(defaultImage, hoverImage, clickedImage)
        
        self.buttonRect = self.defaultImage.get_rect()
        self.buttonRect.update((self.x, self.y),(self.width, self.height))

        for num in range(len(parentScenes)):
            parentScenes[num].insert(0,self)

    def __repr__(self):
        return self.__name__
            
    def process(self, mousePos: tuple[int,int]) -> None:
        """
        if clicked runs onclickFunction
        then draws button to DISPLAYSURF with appropriate image
        
        Args:
            mousePos (tuple[int,int]): mouse coordinates 
        """
        
        if self.runOnclickFunction:
            self.onclickFunction()
            self.runOnclickFunction = False
            
        
        if mousePos == None:
            mousePos = pygame.mouse.get_pos()
   
        if self.buttonRect.collidepoint(mousePos):
            if pygame.mouse.get_pressed(num_buttons=3)[0]:
                if self.ignoreNextPress:
                    self.ignoreNextPress = False
                    self.alreadyPressed = True
                    self.DISPLAYSURF.blit(self.hoverImage, self.buttonRect)
                    
                elif not self.runFuncOnce:
                    self.onclickFunction()
                    self.DISPLAYSURF.blit(self.clickedImage, self.buttonRect)
                    
                elif not self.alreadyPressed:
                    self.onclickFunction()
                    self.alreadyPressed = True
                    self.DISPLAYSURF.blit(self.clickedImage, self.buttonRect)
                else:
                    self.DISPLAYSURF.blit(self.clickedImage, self.buttonRect)
                
            else:
                self.alreadyPressed = False
                self.DISPLAYSURF.blit(self.hoverImage, self.buttonRect)
        else:
            self.ignoreNextPress = False
            self.alreadyPressed = False
            self.DISPLAYSURF.blit(self.defaultImage, self.buttonRect)