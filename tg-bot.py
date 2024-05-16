import os
import subprocess
import logging
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext
import time
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

last_input_time = time.time()

# Function to handle user input
def handle_user_input(update: Update, context: CallbackContext) -> None:
    global last_input_time
    user_input = update.message.text
    user = update.message.from_user
    logger.info(f"User {user.first_name} sent: {user_input}")
    last_input_time = time.time()  # Update last input time

    # Check if the input is a Spotify URL
    if not user_input.startswith("https://open.spotify.com/"):
        update.message.reply_text('Please send a valid Spotify song, album, or playlist URL.')
        return

    update.message.reply_text('Downloading your song or songs...')

    # Download the song(s)
    result = subprocess.run(['spotdl', user_input], capture_output=True, text=True)
    logger.info(f"spotdl command output: {result.stdout}")
    if result.returncode != 0:
        logger.error(f"Error downloading song/album/playlist: {result.stderr}")
        update.message.reply_text('Failed to download the song/album/playlist. Please try again later.')
        return

    # Find the downloaded file/files
    song_files = [f for f in os.listdir('.') if f.endswith('.mp3')]
    if song_files:
        # Embed album art into the MP3 file(s)
        for song_file in song_files:
            embed_album_art(song_file)
            update.message.reply_audio(audio=open(song_file, 'rb'))
    else:
        update.message.reply_text('Could not find the downloaded song/album/playlist.')

# Function to embed album art into the MP3 file
def embed_album_art(file_path):
    audio = MP3(file_path, ID3=ID3)
    # Provide the full path to the album art file
    album_art_path = os.path.join(os.path.dirname(__file__), 'album_art.jpg')
    with open(album_art_path, 'rb') as img_file:
        album_art = APIC(
            encoding=3,  # 3 is for utf-8
            mime='image/jpeg',  # image/jpeg or image/png
            type=3,  # 3 is for the cover image
            desc=u'Cover',
            data=img_file.read()
        )
    audio.tags.add(album_art)
    audio.save()

# Function to periodically check idle time
# def check_idle_timeout(context: CallbackContext):
#     global last_input_time
#     current_time = time.time()
#     idle_duration = current_time - last_input_time
#     if idle_duration > 600:  # Check every 10 minutes
#         logger.info("Bot idle timeout reached")
#         updater.stop()  # Stop the updater when idle timeout is reached

# Main function to start the bot
def main() -> None:
    # Create the Updater and pass it your bot's token
    updater = Updater(os.getenv('TELEGRAM_BOT_TOKEN'))

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher

    # Register handlers
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_user_input))

    # Start the Bot
    updater.start_polling()

    # Schedule the check_idle_timeout function to run every 10 minutes
    # updater.job_queue.run_repeating(check_idle_timeout, interval=600, first=0)

    # Run the bot until you press Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT
    updater.idle()

if __name__ == '__main__':
    main()
