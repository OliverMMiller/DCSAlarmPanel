import pygame
import numpy as np

def pitch_shift(sound, semitones):
    """Shift the pitch of a Pygame sound by a given number of semitones."""
    # Extract raw sound data
    sound_array = pygame.sndarray.array(sound)
    sample_rate = sound.get_length() / len(sound_array)
    
    # Calculate the pitch shift factor
    factor = 2 ** (semitones / 12.0)
    
    # Resample the sound
    indices = np.round(np.arange(0, len(sound_array), factor)).astype(int)
    indices = indices[indices < len(sound_array)]  # Ensure indices are valid
    shifted_sound_array = sound_array[indices]
    
    # Convert back to Pygame sound
    return pygame.sndarray.make_sound(shifted_sound_array)

# Initialize Pygame mixer
pygame.mixer.init()

# Load a sound
original_sound = pygame.mixer.Sound("sound/shipHorn.wav")

#[-0.5, 0, 2, 4, 6]

# Shift the pitch by x semitones
shifted_sound = pitch_shift(original_sound, 10)

if __name__ == "__main__":
    # Play the shifted sound
    shifted_sound.play()

    # Keep the program running to hear the sound
    pygame.time.wait(int(shifted_sound.get_length() * 1000))
