# -*- coding: utf-8 -*-

import models
import logging
import uuid
import telegram
from models import User, Dong, UserDong, Expense, Article

reply_markup_report_type = telegram.ReplyKeyboardMarkup([['summary'],
                                                         ['detail 10'],
                                                         ['detail 50'],
                                                         ['detail all'],
                                                         ['cancel']])

reply_markup_confirm = telegram.ReplyKeyboardMarkup([['confirm'],
                                                     ['cancel']])

reply_markup_share_type = telegram.ReplyKeyboardMarkup([['equal'],
                                                        ['custom']])

reply_markup_hide = telegram.ReplyKeyboardHide()

def represents_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class BaseCWF:
    def __init__(self):
        pass


class State:
    Start, \
        GetExpense, \
        GetJoinKey, \
        GetDongTitle, \
        GetShareType, \
        GetWhichDong, \
        GetDesc, \
        Cofirmation, \
        ShowReport, \
        End = range(10)


class StartCWF(BaseCWF):
    def __init__(self, user_id, bot, update, args):
        super(StartCWF, self).__init__()
        self.state = State.Start
        self.user_id = user_id
        self.bot = bot
        self.update = update
        self.args = args


class CreateCWF(BaseCWF):
    def __init__(self, user_id, chat_id):
        self.state = State.Start
        self.user_id = user_id
        self.chat_id = chat_id
        self.session = models.Session()

    def start(self, bot, args):
        if len(args) > 0:
            self.state = State.GetDongTitle
            self.handle(bot, args[0])
        else:
            self.handle(bot, '')

    def stop(self):
        self.session.rollback()
        pass

    def handle(self, bot, message):
        if self.state == State.Start:
            bot.sendMessage(self.chat_id, text='Enter a dong title.', reply_markup=reply_markup_hide)
            self.state = State.GetDongTitle
            return
        if self.state == State.GetDongTitle:
            dong_title = message.encode('utf8')
            if dong_title == '':
                bot.sendMessage(self.chat_id, text='Dong Title is empty, insert a valid Dong title',
                                reply_markup=reply_markup_hide)
                return
            if self.session.query(Dong).join(Dong.user_dong).filter(UserDong.user_id == self.user_id) \
                    .filter(Dong.title == dong_title).count() > 0:
                logging.error('duplicate dong title')
                bot.sendMessage(self.chat_id, text='Dong title ({}) is duplicated, insert a new Dong title'
                                .format(dong_title), reply_markup=reply_markup_hide)
                return
            else:
                key = uuid.uuid4().hex[:6].upper()
                while self.session.query(Dong).filter(Dong.join_key == key).one_or_none() is not None:
                    key = uuid.uuid4().hex[:6].upper()

                # check that this user should not already have same dong or is joined in same dong
                dong = Dong(title=dong_title, join_key=key)
                self.session.add(dong)

                user_dong = UserDong(user_id=self.user_id, dong=dong, is_admin=True, balance=0)
                self.session.add(user_dong)

                try:
                    self.session.commit()
                except Exception as e:
                    logging.error(e)
                    bot.sendMessage(self.chat_id, text='The process failed', reply_markup=reply_markup_hide)

                bot.sendMessage(self.chat_id,
                                text='Send Join Key ({}) to other friends to join to this Dong ({})'
                                .format(key, dong_title), reply_markup=reply_markup_hide)
                self.state = State.End


class JoinCWF(BaseCWF):
    def __init__(self, user_id, chat_id):
        self.state = State.Start
        self.user_id = user_id
        self.chat_id = chat_id
        self.session = models.Session()

    def start(self, bot, args):
        if len(args) > 0:
            self.state = State.GetJoinKey
            self.handle(bot, args[0])
        else:
            self.handle(bot, '')

    def stop(self):
        self.session.rollback()
        pass

    def handle(self, bot, message):
        if self.state == State.Start:
            bot.sendMessage(self.chat_id, text='Enter a valid join key.')
            self.state = State.GetJoinKey
            return
        elif self.state == State.GetJoinKey:
            join_key = message
            if join_key == '':
                bot.sendMessage(self.chat_id, text='Join key is empty, insert a valid Join key',
                                reply_markup=reply_markup_hide)
                return
            dong = self.session.query(Dong).filter(Dong.join_key == join_key and Dong.joinable is True).one_or_none()
            if dong is None:
                logging.error('invalid join key')
                bot.sendMessage(self.chat_id, text='Join key ({}) is Invalid, insert a valid Join key'
                                .format(join_key), reply_markup=reply_markup_hide)
                return
            else:
                user_dong = UserDong(user_id=self.user_id, dong=dong, is_admin=False, balance=0)
                self.session.add(user_dong)
                try:
                    self.session.commit()
                except Exception as e:
                    logging.error(e)
                    bot.sendMessage(self.chat_id, text='The process failed', reply_markup=reply_markup_hide)
                bot.sendMessage(self.chat_id, text='You successfully joined to dong ({})'.format(dong.title),
                                reply_markup=reply_markup_hide)
                self.state = State.End


class ExpenseCWF(BaseCWF):
    def __init__(self, user_id, chat_id):
        self.state = State.Start
        self.user_id = user_id
        self.chat_id = chat_id
        self.session = models.Session()
        self.expense = 0
        self.userdong = None
        self.valid_userdongs = None
        self.desc = ''
        self.articles = []

    def start(self, bot, args):
        if len(args) > 0:
            self.state = State.GetExpense
            self.handle(bot, args[0])
        else:
            self.handle(bot, '')

    def stop(self):
        self.session.rollback()
        pass

    def handle(self, bot, message):
        if self.state == State.Start:
            bot.sendMessage(self.chat_id, text='Enter expense value.(0 < x < 5000000)', reply_markup=reply_markup_hide)
            self.state = State.GetExpense
        elif self.state == State.GetExpense:
            expense = message
            if represents_int(expense) == False or int(expense) <= 0 or int(expense) > 5000000:
                bot.sendMessage(self.chat_id, text='Enter valid expense value.', reply_markup=reply_markup_hide)
                return
            self.expense = int(expense)

            self.valid_userdongs = self.session.query(UserDong).filter(UserDong.user_id == self.user_id).all()

            if len(self.valid_userdongs) == 0:
                bot.sendMessage(self.chat_id, text='You did not join to any dong!', reply_markup=reply_markup_hide)
                self.state = State.End
                return
            elif len(self.valid_userdongs) == 1:
                bot.sendMessage(self.chat_id, text='Enter description of this expense.', reply_markup=reply_markup_hide)
                self.userdong = self.valid_userdongs[0]
                self.state = State.GetDesc
                return
            else:
                dongs = []
                for userdong in self.valid_userdongs:
                    dongs.append([(userdong.dong.title + ' - ' + str(userdong.dong_id)).encode('utf8')])

                reply_markup_dongs = telegram.ReplyKeyboardMarkup(dongs)
                bot.sendMessage(self.chat_id, text='Which dong?', reply_markup=reply_markup_dongs)
                self.state = State.GetWhichDong
                return

        elif self.state == State.GetWhichDong:
            dong_id = message.split(" - ")[1]
            if represents_int(dong_id):
                self.userdong = self.session.query(UserDong)\
                    .filter(UserDong.user_id == self.user_id).filter(UserDong.dong_id == int(dong_id)).one_or_none()

            if self.userdong is None:
                bot.sendMessage(self.chat_id, text='Enter valid dong id.')
                return
            bot.sendMessage(self.chat_id, text='Enter description of this expense.', reply_markup=reply_markup_hide)
            self.state = State.GetDesc
            return

        elif self.state == State.GetDesc:
            self.desc = message.encode('utf8')
            bot.sendMessage(self.chat_id, text='Share type?', reply_markup=reply_markup_share_type)
            self.state = State.GetShareType
            return

        elif self.state == State.GetShareType:
            share_type = message
            if share_type != 'equal' and share_type != 'custom':
                bot.sendMessage(self.chat_id, text='Enter valid share type.')
                return
            if share_type == 'custom':
                bot.sendMessage(self.chat_id, text='Custom share type is not supported yet :(', reply_markup=reply_markup_hide)
                bot.sendMessage(self.chat_id, text='Share type?', reply_markup=reply_markup_share_type)
                return

            if share_type == 'equal':
                all_dong_users = self.session.query(UserDong).filter(UserDong.dong_id == self.userdong.dong_id).all()
                expense = Expense(user_dong=self.userdong, payment=self.expense, debit_type=1, description=self.desc)
                self.session.add(expense)
                print(str(all_dong_users))
                l = len(all_dong_users)
                share_debit = self.expense / l
                share_credit = (self.expense - share_debit) - (self.expense - (l * share_debit))

                print(self.expense)
                print(share_credit)
                print(share_debit)
                for user_dong in all_dong_users:
                    if user_dong is self.userdong:
                        article = Article(credit=share_credit, debit=0, expense=expense, user_dong=user_dong)
                        user_dong.balance += share_credit
                    else:
                        article = Article(credit=0, debit=share_debit, expense=expense, user_dong=user_dong)
                        user_dong.balance -= share_debit
                    self.session.add(article)
                    self.articles.append(article)

                bot.sendMessage(self.chat_id, text='Share for everyone {}, your credit {}?'
                                .format(share_debit, share_credit), reply_markup=reply_markup_confirm)
                self.state = State.Cofirmation
                return

        elif self.state == State.Cofirmation:
            confirm_resp = message
            if confirm_resp != 'confirm' and confirm_resp != 'cancel':
                bot.sendMessage(self.chat_id, text='Enter valid Confirmation code.')
                return
            if confirm_resp == 'cancel':
                bot.sendMessage(self.chat_id, text='This expense canceled.', reply_markup=reply_markup_hide)
                self.session.rollback()
                self.state = State.End
                return
            if confirm_resp == 'confirm':

                try:
                    self.session.commit()
                    bot.sendMessage(self.chat_id, text='This expense confirmed.', reply_markup=reply_markup_hide)
                    for article in self.articles:
                        if article.debit != 0:
                            chat_id = article.user_dong.user.chat_id
                            bot.sendMessage(chat_id, text='*** your debit to dong {} increased by {} for {} ***'
                                            .format(self.userdong.dong.title, article.debit, self.desc),
                                            reply_markup=reply_markup_hide)

                except Exception as e:
                    logging.error(e)
                    bot.sendMessage(self.chat_id, text='This expense failed due some errors.',
                                    reply_markup=reply_markup_hide)
                self.state = State.End
                return


class ReportCWF(BaseCWF):
    def __init__(self, user_id, chat_id):
        self.state = State.Start
        self.user_id = user_id
        self.chat_id = chat_id
        self.session = models.Session()
        self.expense = 0
        self.userdong = None
        self.valid_userdongs = None
        self.desc = ''
        self.articles = []

    def start(self, bot):
        self.handle(bot, '')

    def stop(self):
        self.session.rollback()
        pass

    def handle(self, bot, message):
        if self.state == State.Start:
            self.valid_userdongs = self.session.query(UserDong).filter(UserDong.user_id == self.user_id).all()

            if len(self.valid_userdongs) == 0:
                bot.sendMessage(self.chat_id, text='You did not join to any dong!', reply_markup=reply_markup_hide)
                self.state = State.End
                return
            elif len(self.valid_userdongs) == 1:
                bot.sendMessage(self.chat_id, text='Report type?', reply_markup=reply_markup_report_type)
                self.userdong = self.valid_userdongs[0]
                self.state = State.ShowReport
                return
            else:
                dongs = []
                for userdong in self.valid_userdongs:
                    dongs.append([(userdong.dong.title + ' - ' + str(userdong.dong_id)).encode('utf8')])

                reply_markup_dongs = telegram.ReplyKeyboardMarkup(dongs)
                bot.sendMessage(self.chat_id, text='Which dong?', reply_markup=reply_markup_dongs)

                self.state = State.GetWhichDong
                return

        elif self.state == State.GetWhichDong:
            dong_id = message.split(" - ")[1]
            if represents_int(dong_id):
                self.userdong = self.session.query(UserDong).filter(UserDong.user_id == self.user_id)\
                    .filter(UserDong.dong_id == int(dong_id)).one_or_none()

            if self.userdong is None:
                bot.sendMessage(self.chat_id, text='Enter valid dong id.')
                return
            bot.sendMessage(self.chat_id, text='Report type?', reply_markup=reply_markup_report_type)
            self.state = State.ShowReport
            return

        elif self.state == State.ShowReport:
            report_id = message
            if report_id == 'cancel':
                bot.sendMessage(self.chat_id, text='This report canceled.', reply_markup=reply_markup_hide)
                self.session.rollback()
                self.state = State.End
                return
            articles = self.session.query(Article).filter(Article.user_dong == self.userdong)\
                .order_by(Article.created_date).all()
            cc = len(articles)
            if report_id == 'detail 50':
                articles = articles[-max(cc, 50):]
            if report_id == 'detail 10':
                articles = articles[-max(cc, 10):]
            if report_id != 'summary':
                for article in articles:
                    if article.credit > 0:
                        message = '+' + str(article.credit)
                    elif article.debit > 0:
                        message = '-' + str(article.debit)
                    else:
                        message = str(article.debit)
                    message += ' for {}({})'.format(article.expense.description.encode('utf8'),
                                                    article.expense.payment)
                    bot.sendMessage(self.chat_id, text=message, reply_markup=reply_markup_hide)

            bot.sendMessage(self.chat_id, text='*** Your balance is {} ***'.format(self.userdong.balance),
                            reply_markup=reply_markup_hide)
            self.state = State.End
            return


