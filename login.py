
from flask import Blueprint, render_template, request, jsonify, session
from model import User

# 创建蓝图对象
login_page = Blueprint('login_page', __name__, template_folder='templates')


# 登录页面路由
@login_page.route('/login', methods=['GET'])
def login_page_view():
    """返回登录页面"""
    return render_template('login.html')


# 登录API
@login_page.route('/api/login', methods=['POST'])
def login():
    """处理用户登录请求"""
    try:
        # 获取请求数据
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        email = data.get('email', '').strip()
        password = data.get('password', '')
        
        if not email:
            return jsonify({'success': False, 'message': '请输入邮箱'}), 400
        
        if not password:
            return jsonify({'success': False, 'message': '请输入密码'}), 400
        
        # 查询用户
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'success': False, 'message': '邮箱或密码错误'}), 401
        
        # 验证密码（不加密）
        if user.password != password:
            return jsonify({'success': False, 'message': '邮箱或密码错误'}), 401
        
        # 设置session
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'data': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500


# 退出登录API
@login_page.route('/api/logout', methods=['POST'])
def logout():
    """处理用户退出登录请求"""
    # 清除session
    session.clear()
    return jsonify({'success': True, 'message': '退出登录成功'}), 200
