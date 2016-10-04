import models
from models import User, Dong, UserDong
import logging
import uuid


class DongCore:
    def __init__(self):
        pass


    def add_dong(self, user_tel_id, user_chat_id, first_name, last_name, dong_title):
        '''
        :param user_tel_id:
        :param dong_title:
        :return: None in failure or Join Key in success
        '''
        session = models.Session()
        try:
            user = session.query(User).filter(User.code == user_tel_id).one_or_none()
        except Exception as e:
            logger.error(e)

        if user is None:
            user = User(first_name=first_name, last_name=last_name, code=user_tel_id)
            session.add(user)
        user.chat_id = user_chat_id

        if session.query(Dong).join(Dong.user_dong).filter(UserDong.user == user) \
            .filter(Dong.title == dong_title).count() > 0:
            logger.error('duplicate dong title')
            return None

        key = uuid.uuid4().hex[:6].upper()
        while session.query(Dong).filter(Dong.join_key == key).one_or_none() is not None:
            key = uuid.uuid4().hex[:6].upper()

        # check that this user should not already have same dong or is joined in same dong
        dong = Dong(title=dong_title, join_key=key)
        session.add(dong)

        user_dong = UserDong(user=user, dong=dong, is_admin=True, balance=0)
        session.add(user_dong)

        try:
            session.commit()
        except Exception as e:
            logger.error(str(e))
            return None

        return key

    def join_dong(self, user_tel_id, user_chat_id, first_name, last_name, dong_key):
        session = models.Session()
        dong = session.query(Dong).filter(Dong.join_key == dong_key and Dong.joinable == True).one_or_none()

        try:
            user = session.query(User).filter(User.code == user_tel_id).one_or_none()
        except Exception as e:
            logger.error(e)

        if user is None:
            user = User(first_name=first_name, last_name=last_name, code=user_tel_id)
            session.add(user)
        user.chat_id = user_chat_id

        if dong is None:
            logger.error('Could not to join to this Dong')
            return None

        user_dong = UserDong(user=user, dong=dong, is_admin=False, balance=0)
        session.add(user_dong)

        try:
            session.commit()
        except Exception as e:
            logger.error(str(e))
            return None

        return dong.title
