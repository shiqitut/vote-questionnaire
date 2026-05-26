#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
数据模型定义文件
基于 settings.py 中的数据库配置实现 ORM 映射
"""

from settings import db
from datetime import datetime


# 用户信息表
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(256), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def set_password(self, password):
        self.password = password

    def check_password(self, password):
        return self.password == password

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<User {self.username}>'


# 问卷/投票信息表
class Survey(db.Model):
    __tablename__ = 'questionnaires'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50), default='other')
    deadline = db.Column(db.Date)
    status = db.Column(db.SmallInteger, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    questions = db.relationship('Question', backref='questionnaire', lazy=True, cascade='all, delete-orphan')

    @property
    def response_count(self):
        from sqlalchemy import func
        from model import Answer
        # 获取第一个问题
        first_question = Question.query.filter_by(questionnaire_id=self.id).order_by(Question.sort_order).first()
        if first_question:
            # 只统计第一个问题的回答数，这样一份问卷提交一次只算1人
            return db.session.query(func.count(Answer.id)).filter(Answer.question_id == first_question.id).scalar() or 0
        return 0

    @property
    def is_active(self):
        return self.status == 1

    @is_active.setter
    def is_active(self, value):
        self.status = 1 if value else 0

    @property
    def is_public(self):
        return True

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'is_active': self.is_active,
            'is_public': self.is_public,
            'response_count': self.response_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }

    def __repr__(self):
        return f'<Survey {self.title}>'


# 问卷问题表
class Question(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    questionnaire_id = db.Column(db.Integer, db.ForeignKey('questionnaires.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    type = db.Column(db.SmallInteger, nullable=False)
    options = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Question {self.content[:50]}>'


# 用户回答详情表
class Answer(db.Model):
    __tablename__ = 'answers'

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Answer {self.content[:20]}>'
