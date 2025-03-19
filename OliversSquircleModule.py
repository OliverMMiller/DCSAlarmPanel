#Version 2.1
#with event based button function execution
#author: OliverMMiller
import pygame

from typing import NewType
ValueInRange = NewType('ValueInRange', float)

def validate_value(value: float, min: float, max: float) -> ValueInRange:
    """
    Validates if a value is within a specified range.
    """
    if min <= value <= max:
        return ValueInRange(value)
    else:
        raise ValueError(f"Value {value} is out of the accepted range ({min}-{max})")

class squircle:
    """
    Class to represent a squircle shape.
    """
    def __init__(self, width: int, height: int, fillColor: pygame.Color | None, borderRadius: int = 50, borderWidth: int = 3, borderColor: pygame.Color | None = None):  
        """_summary_

        Args:
            width (int): width of the squircle
            height (int): height of the squircle
            fillColor (pygame.Color | None): color of the squircle
            borderRadius (int, optional): corner radius of the squircle, must be less than max(width,height)/2. Defaults to 50.
            borderWidth (int, optional): width of the border of the squircle. Defaults to 3.
            borderColor (pygame.Color | None, optional): color of the border of the squircle. Defaults to None.

        Raises:
            ValueError: _description_
        """
        self.width = width
        self.height = height
        self.borderColor = borderColor
        self.fillColor = fillColor
        self.ignoreTextOverflow = False
        self.mySurface = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        self.borderWidth = borderWidth
        self.borderRadius = borderRadius
        if not (self.borderColor and self.fillColor):
            raise ValueError("borderColor and/or fillColor must be provided")
        rect2 = pygame.Rect(self.borderWidth, self.borderWidth, self.width - (self.borderWidth * 2), self.height - (self.borderWidth * 2))
        if self.fillColor:
            pygame.draw.rect(self.mySurface, self.fillColor, rect2, 0, self.borderRadius)
        if self.borderColor:
            pygame.draw.rect(self.mySurface, self.borderColor, rect2, self.borderWidth, self.borderRadius)

    def updateText(self, **kwargs) -> None:
        """
        Updates the text on the squircle.
        """
        if "text" in kwargs and isinstance(kwargs["text"], str):
            self.text = kwargs["text"]
        if "font" in kwargs and isinstance(kwargs["font"], pygame.font.Font):
            self.font = kwargs["font"]
        if "textColor" in kwargs and isinstance(kwargs["textColor"], pygame.Color):
            self.textColor = kwargs["textColor"]
        if "justificationType" in kwargs and kwargs["justificationType"] in ("centered", "absolute"):
            self.justificationType = kwargs["justificationType"]
        if "xJustification" in kwargs:
            self.xJustification = validate_value(kwargs["xJustification"], 0, 1)
        if "yJustification" in kwargs:
            self.yJustification = validate_value(kwargs["yJustification"], 0, 1)

        size = self.font.size(self.text)
        if (size[0] > self.width or size[1] > self.height) and not self.ignoreTextOverflow:
            raise ValueError(f"Text too large to fit in squircle\nText: {self.text}")
        if self.justificationType == "centered":
            x = self.width * self.xJustification - size[0] / 2
            y = self.height * self.yJustification - size[1] / 2
        if self.justificationType == "absolute":
            x = self.xJustification
            y = self.yJustification
        self.mySurface.blit(self.font.render(self.text, True, self.textColor), (x, y))

    def setText(self, text: str, font: pygame.font.Font, color: pygame.Color, 
                justificationType: str = "centered", 
                xJustification: float = 0.5, yJustification: float = 0.5) -> None:
        """
        Sets the text on the squircle.
        """
        self.text = text
        self.font = font
        self.textColor = color
        self.justificationType = justificationType
        self.xJustification = validate_value(xJustification, 0, 1)
        self.yJustification = validate_value(yJustification, 0, 1)
        self.updateText()

    def redraw(self, **kwargs) -> pygame.Surface:
        """
        Redraws the squircle with updated properties.
        """
        for arg in kwargs:
            if arg in ("width", "height", "borderColor", "fillColor", "borderWidth", "borderRadius"):
                setattr(self, arg, kwargs[arg])

        if not (self.borderColor and self.fillColor):
            raise ValueError("borderColor and/or fillColor must be provided")
        rect2 = pygame.Rect(self.borderWidth, self.borderWidth, self.width - (self.borderWidth * 2), self.height - (self.borderWidth * 2))
        if self.fillColor:
            pygame.draw.rect(self.mySurface, self.fillColor, rect2, 0, self.borderRadius)
        if self.borderColor:
            pygame.draw.rect(self.mySurface, self.borderColor, rect2, self.borderWidth, self.borderRadius)

        self.updateText()
        return self.mySurface