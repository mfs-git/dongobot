# -*- coding: utf-8 -*-

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
# from telegram import InlineQueryResultArticle, InputTextMessageContent
import models
from models import User
import logging
import DongCore
from CommandWorkFlows import CreateCWF, JoinCWF, ExpenseCWF, ReportCWF, State


class DongobotServer:
    def __init__(self, bot_token):
        self.updater = Updater(bot_token)
        self.dp = self.updater.dispatcher
        self.core = DongCore.DongCore()
        self.cwf_list = {}

    def run(self):
        models.create_models()
        create_dong_handler = CommandHandler('create', self.create_dong, pass_args=True)
        join_dong_handler = CommandHandler('join', self.join_dong, pass_args=True)
        expense_handler = CommandHandler('expense', self.expense_dong, pass_args=True)
        report_handler = CommandHandler('report', self.report_dong, pass_args=False)
        message_handler = MessageHandler([Filters.text], self.message_handler)
        self.dp.add_handler(create_dong_handler)
        self.dp.add_handler(join_dong_handler)
        self.dp.add_handler(expense_handler)
        self.dp.add_handler(report_handler)
        self.dp.add_handler(message_handler)


        self.updater.start_polling()
        # Run the bot until the you presses Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        self.updater.idle()
        self.updater.stop()

    def message_handler(self, bot, update):
        user = self.get_user(update)
        if user.id in self.cwf_list.keys() \
                and self.cwf_list[user.id] is not None\
                and self.cwf_list[user.id].state != State.End:
            self.cwf_list[user.id].handle(bot, update.message.text)
        else:
            bot.sendMessage(update.message.chat.id, text='What !?')

    def create_dong(self, bot, update, args):
        user = self.get_user(update)
        if user.id in self.cwf_list.keys() and self.cwf_list[user.id] is not None:
            self.cwf_list[user.id].stop()
        self.cwf_list[user.id] = CreateCWF(user.id, user.chat_id)
        self.cwf_list[user.id].start(bot, args)

    def join_dong(self, bot, update, args):
        user = self.get_user(update)
        if user.id in self.cwf_list.keys() and self.cwf_list[user.id] is not None:
            self.cwf_list[user.id].stop()
        self.cwf_list[user.id] = JoinCWF(user.id, user.chat_id)
        self.cwf_list[user.id].start(bot, args)

    def expense_dong(self, bot, update, args):
        user = self.get_user(update)
        if user.id in self.cwf_list.keys() and self.cwf_list[user.id] is not None:
            self.cwf_list[user.id].stop()
        self.cwf_list[user.id] = ExpenseCWF(user.id, user.chat_id)
        self.cwf_list[user.id].start(bot, args)

    def report_dong(self, bot, update):
        user = self.get_user(update)
        if user.id in self.cwf_list.keys() and self.cwf_list[user.id] is not None:
            self.cwf_list[user.id].stop()
        self.cwf_list[user.id] = ReportCWF(user.id, user.chat_id)
        self.cwf_list[user.id].start(bot)

    @staticmethod
    def get_user(update):
        tel_id = update.message.from_user.id
        fname = update.message.from_user.first_name
        lname = update.message.from_user.last_name
        chat_id = update.message.chat.id

        session = models.Session()
        user = session.query(User).filter(User.code == tel_id).one_or_none()
        if user is None:
            user = User(first_name=fname, last_name=lname, code=tel_id)
            session.add(user)

        user.chat_id = chat_id
        try:
            session.commit()
        except Exception as e:
            logging.error(e)
            return None
        return user
