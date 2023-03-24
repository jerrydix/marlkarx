import os
from dotenv import load_dotenv

def load():
    global MUSIC_MAX_DURATION_MINS
    global MUSIC_QUEUE_PER_PAGE
    
    MUSIC_MAX_DURATION_MINS = 20
    MUSIC_QUEUE_PER_PAGE = 10
    
    # load_dotenv()

    #if len(os.getenv('MUSIC_MAX_DURATION_MINS')) > 0:
    #    MUSIC_MAX_DURATION_MINS = int(os.getenv('MUSIC_MAX_DURATION_MINS'))
    #if len(os.getenv('MUSIC_QUEUE_PER_PAGE')) > 0:
    #    MUSIC_QUEUE_PER_PAGE = int(os.getenv('MUSIC_QUEUE_PER_PAGE'))
