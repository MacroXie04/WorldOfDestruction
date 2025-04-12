from pytube import YouTube
import pygame
import os

#Button Sound Effect
# --- Step 1: Download Audio from YouTube ---
yt_url = "https://www.youtube.com/watch?v=h8y0JMVwdmM&ab_channel=SoundLibrary" # Replace with your desired URL
yt = YouTube(yt_url)

# Get the first audio-only stream (usually .mp4 or .webm)
stream = yt.streams.filter(only_audio=True).first()

# Download it
print("Downloading audio...")
filename = "button_sound.mp4"
stream.download(filename=filename)
print("Download complete!")

# --- Step 2: Initialize Pygame and Play Sound on Key Press ---
pygame.init()
pygame.mixer.init()

# Load sound (convert format if needed)
pygame.mixer.music.load(filename)
pygame.display.set_caption("Button Sound Example")
screen = pygame.display.set_mode((400, 300))

font = pygame.font.SysFont(None, 36)
text = font.render("Click anywhere to play sound", True, (255, 255, 255))
running = True

while running:
    screen.fill((30, 30, 30))
    screen.blit(text, (40, 130))
    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            pygame.mixer.music.play()

pygame.quit()
