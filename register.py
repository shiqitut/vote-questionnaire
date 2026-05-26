#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
注册蓝图模块
处理用户注册相关的路由和逻辑
"""

from flask import Blueprint, render_template, request, jsonify
from model import User
from settings import db

# 创建蓝图对象
register_page = Blueprint('register_page', __name__, template_folder='templates')


# 注册页面路由
@register_page.route('/register', methods=['GET'])
def register_page_view():
    """返回注册页面"""
    return render_template('register.html')


# 注册API
@register_page.route('/api/register', methods=['POST'])
def register():
    """处理用户注册请求"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        # 验证用户名
        if not username:
            return jsonify({'success': False, 'message': '请输入用户名'}), 400
        
        if len(username) < 2 or len(username) > 50:
            return jsonify({'success': False, 'message': '用户名长度必须在2-50个字符之间'}), 400
        
        # 验证邮箱
        if not email:
            return jsonify({'success': False, 'message': '请输入邮箱'}), 400
        
        if '@' not in email or '.' not in email.split('@')[-1]:
            return jsonify({'success': False, 'message': '请输入有效的邮箱地址'}), 400
        
        # 验证密码
        if not password:
            return jsonify({'success': False, 'message': '请输入密码'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': '密码长度至少为6位'}), 400
        
        # 检查用户名是否已存在
        if User.query.filter_by(username=username).first():
            return jsonify({'success': False, 'message': '该用户名已被注册'}), 409
        
        # 检查邮箱是否已存在
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': '该邮箱已被注册'}), 409
        
        # 创建新用户
        user = User(
            username=username,
            email=email,
            password=password
        )
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '注册成功',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_active': user.is_active
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500
