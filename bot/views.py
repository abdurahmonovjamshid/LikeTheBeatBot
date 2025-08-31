import json
import os
import traceback

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import telebot
from conf.settings import HOST, TELEGRAM_BOT_TOKEN, ADMINS, CHANNEL_ID
from telebot import TeleBot

from .models import TgUser, MusicFile, MusicSearch, MusicPlay
from .utils import search_music, format_results, make_keyboard

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
        file_id, file_name, caption = None, None, None
        performer, title, duration, file_size = None, None, None, None

        if message.audio:  # real music file
            file_id = message.audio.file_id
            performer = message.audio.performer
            title = message.audio.title
            caption = message.caption
            duration = message.audio.duration  # seconds
            file_size = message.audio.file_size  # bytes

            if performer and title:
                file_name = f"{performer} – {title}.mp3"
            else:
                file_name = message.audio.file_name

        elif message.document:  # mp3 sent as document
            if (message.document.mime_type == "audio/mpeg" or
                    (message.document.file_name and message.document.file_name.endswith(".mp3"))):
                file_id = message.document.file_id
                file_name = message.document.file_name
                caption = message.caption
                file_size = message.document.file_size
                duration = None  # not provided for documents

        if file_id:
            # Save to DB
            music = MusicFile.objects.create(
                file_id=file_id,
                file_name=file_name,
                performer=performer,
                title=title,
                caption=caption,
                duration=duration,
                file_size=file_size,
                source_channel=str(message.chat.id),
                source_message_id=message.message_id,
                mirrored_message_id=0
            )

            # Send to destination channel
            sent_msg = bot.send_audio(
                CHANNEL_ID,
                file_id,
                caption=caption,
                performer=performer,
                title=title,
                duration=duration
            )

            # Update mirrored_message_id
            music.mirrored_message_id = sent_msg.message_id
            music.save()

    except Exception as e:
        print("Error in music_file_handler:", e)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    query = message.text.strip()
    if not query:
        bot.reply_to(message, "❌ Please enter something to search.")
        return

    # Save search (statistics)
    MusicSearch.objects.create(user_id=message.from_user.id, query=query)

    # Search DB
    items, total = search_music(query, page=1)

    if not items:
        bot.send_message(message.chat.id, f"❌ No results for '{query}'")
        return

    text = format_results(query, items, total, 1)
    kb = make_keyboard(query, 1, total)
    bot.send_message(message.chat.id, text, reply_markup=kb)


@bot.callback_query_handler(func=lambda call: call.data.startswith("play:"))
def handle_play(call):
    _, query, page, idx = call.data.split(":")
    page, idx = int(page), int(idx)

    items, total = search_music(query, page)
    if idx <= len(items):
        music = items[idx - 1]  # 1-based index inside current page

        # Save play
        MusicPlay.objects.create(user_id=call.from_user.id, music=music)

        # Send the file
        bot.send_audio(
            call.message.chat.id,
            music.file_id,
            title=music.title,
            performer=music.performer,
            caption=music.caption or ""
        )

    bot.answer_callback_query(call.id)  # close loading animation


@bot.callback_query_handler(func=lambda call: call.data.startswith("page:"))
def handle_page(call):
    _, query, page = call.data.split(":")
    page = int(page)

    items, total = search_music(query, page)
    if not items:
        bot.answer_callback_query(call.id, "No more results.")
        return

    text = format_results(query, items, total, page)
    kb = make_keyboard(query, page, total)

    # Update message instead of sending a new one
    bot.edit_message_text(
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        text=text,
        reply_markup=kb
    )
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "close")
def handle_close(call):
    bot.delete_message(call.message.chat.id, call.message.message_id)
    bot.answer_callback_query(call.id, "Closed ✅")


bot.set_webhook(url="https://" + HOST + "/webhook/")
