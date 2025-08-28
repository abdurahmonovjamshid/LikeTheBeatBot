import json
import os
import traceback

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import telebot
from conf.settings import HOST, TELEGRAM_BOT_TOKEN, ADMINS, CHANNEL_ID
from telebot import TeleBot

from .models import TgUser, MusicFile

bot = TeleBot(TELEGRAM_BOT_TOKEN, threaded=False)


@csrf_exempt
def telegram_webhook(request):
    try:
        if request.method == 'POST':
            update_data = request.body.decode('utf-8')
            update_json = json.loads(update_data)
            update = telebot.types.Update.de_json(update_json)

            if update.message:
                tg_user = update.message.from_user
                telegram_id = tg_user.id
                first_name = tg_user.first_name
                last_name = tg_user.last_name
                username = tg_user.username
                is_bot = tg_user.is_bot
                language_code = tg_user.language_code

                deleted = False

                tg_user_instance, _ = TgUser.objects.update_or_create(
                    telegram_id=telegram_id,
                    defaults={
                        'first_name': first_name,
                        'last_name': last_name,
                        'username': username,
                        'is_bot': is_bot,
                        'language_code': language_code,
                        'deleted': deleted,
                    }
                )

            try:
                if update.my_chat_member.new_chat_member.status == 'kicked':
                    telegram_id = update.my_chat_member.from_user.id
                    user = TgUser.objects.get(telegram_id=telegram_id)
                    user.deleted = True
                    user.save()
            except:
                pass

            bot.process_new_updates(
                [telebot.types.Update.de_json(request.body.decode("utf-8"))])

        return HttpResponse("ok")
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        return HttpResponse("error")


@bot.message_handler(commands=['start'])
def start_handler(message):
    bot.send_message(message.chat.id, f"Salom, {message.from_user.full_name}!😊")

@bot.message_handler(content_types=['audio', 'document'])
def music_file_handler(message):
    try:
        file_id, file_name, caption, performer, title = None, None, None, None, None

        if message.audio:  # proper audio file
            file_id = message.audio.file_id
            performer = message.audio.performer
            title = message.audio.title
            caption = message.caption

            # Prefer performer + title as file_name if available
            if performer and title:
                file_name = f"{performer} – {title}.mp3"
            else:
                file_name = message.audio.file_name  # fallback (may be normalized)

        elif message.document:  # mp3 sent as document
            if (message.document.mime_type == "audio/mpeg" or
                (message.document.file_name and message.document.file_name.endswith(".mp3"))):
                file_id = message.document.file_id
                file_name = message.document.file_name
                caption = message.caption

        if file_id:
            # Save to DB
            music = MusicFile.objects.create(
                file_id=file_id,
                file_name=file_name,
                performer=performer,
                title=title,
                caption=caption,
                source_channel=str(message.chat.id),
                source_message_id=message.message_id,
                mirrored_message_id=0  # will update after sending
            )

            # Send to destination channel
            sent_msg = bot.send_audio(
                CHANNEL_ID,
                file_id,
                caption=caption,
                performer=performer,
                title=title
            )

            # Update mirrored_message_id
            music.mirrored_message_id = sent_msg.message_id
            music.save()

    except Exception as e:
        print("Error in music_file_handler:", e)



bot.set_webhook(url="https://" + HOST + "/webhook/")
