#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
问卷视图模块
处理问卷的创建、查看、提交、结果展示等路由
"""

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, current_app
from model import Survey, Question, Answer
import json
from app import db
from datetime import datetime

# 创建蓝图对象
survey_bp = Blueprint('survey', __name__, template_folder='templates')


# 首页路由
@survey_bp.route('/')
def index():
    """首页 - 展示问卷广场"""
    return redirect(url_for('survey.question_square'))


# 问卷广场
@survey_bp.route('/search/keyword', methods=['POST'])
def search_keyword():
    """智能搜索API - 根据关键词搜索问卷"""
    from model import Survey
    
    key_word = request.form.get('kw', '').strip()
    
    if not key_word:
        return jsonify({'code': 0, 'info': []})
    
    surveys = Survey.query.filter_by(status=1).filter(
        Survey.title.ilike(f'%{key_word}%') | 
        Survey.description.ilike(f'%{key_word}%')
    ).limit(10).all()
    
    result = []
    for survey in surveys:
        result.append({
            'title': survey.title,
            'category': survey.category
        })
    
    if result:
        return jsonify({'code': 1, 'info': result})
    else:
        return jsonify({'code': 0, 'info': []})

@survey_bp.route('/square')
def question_square():
    """问卷广场 - 展示所有公开问卷"""
    from sqlalchemy import func, case
    from model import Answer, Question
    
    page = request.args.get('page', 1, type=int)
    sort_by = request.args.get('sort', 'newest')
    category = request.args.get('category', 'all')
    search_query = request.args.get('q', '')
    
    query = Survey.query.filter_by(status=1)
    
    # 按分类筛选
    if category != 'all':
        query = query.filter_by(category=category)
    
    # 搜索筛选
    if search_query:
        query = query.filter(Survey.title.ilike(f'%{search_query}%') | 
                            Survey.description.ilike(f'%{search_query}%'))
    
    if sort_by == 'newest':
        # 最新发布：按创建时间倒序
        query = query.order_by(Survey.created_at.desc())
    elif sort_by == 'popular':
        # 参与最多：按回答数量倒序
        response_count = db.session.query(func.count(Answer.id)).join(Question).filter(
            Question.questionnaire_id == Survey.id
        ).correlate(Survey).scalar_subquery()
        query = query.outerjoin(Question).outerjoin(Answer).group_by(Survey.id).order_by(func.count(Answer.id).desc())
    elif sort_by == 'ending':
        # 即将结束：按截止时间升序（null值放最后）
        query = query.order_by(case((Survey.deadline == None, 1), else_=0), Survey.deadline.asc())
    
    pagination = query.paginate(page=page, per_page=9)
    surveys = pagination.items
    
    # 获取所有问卷标题用于搜索建议
    all_surveys = Survey.query.filter_by(status=1).all()
    survey_titles = [{'title': s.title, 'description': s.description or '', 'category': s.category} for s in all_surveys]
    
    return render_template('index.html', surveys=surveys, pagination=pagination, 
                           sort_by=sort_by, category=category, survey_titles=survey_titles)


# 创建问卷第一步 - 基础信息
@survey_bp.route('/create', methods=['GET', 'POST'])
def create_question():
    """创建问卷页面"""
    if request.method == 'POST':
        # 获取基础信息
        title = request.form.get('title')
        description = request.form.get('description')
        category = request.form.get('category', 'other')
        deadline_str = request.form.get('deadline')
        
        # 验证必填字段
        if not title:
            return jsonify({'success': False, 'message': '请输入问卷标题'}), 400
        
        # 解析截止日期
        deadline = None
        if deadline_str:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d').date()
        
        # 创建问卷
        survey = Survey(
            title=title,
            description=description,
            category=category,
            deadline=deadline,
            status=1
        )
        
        db.session.add(survey)
        db.session.commit()
        
        # 处理动态问题数据
        # 获取所有问题内容
        question_texts = request.form.getlist('question_text[]')
        question_types = request.form.getlist('question_type[]')
        
        for q_index, q_text in enumerate(question_texts):
            if not q_text.strip():
                continue
            
            # 获取问题类型
            q_type = question_types[q_index] if q_index < len(question_types) else 'single'
            
            # 转换问题类型为数字
            type_map = {
                'single': 1,
                'multiple': 2,
                'essay': 3
            }
            
            # 获取选项（如果是单选或多选）
            options_list = []
            if q_type != 'essay':
                options = request.form.getlist(f'options_{q_index}[]')
                for opt_text in options:
                    if opt_text.strip():
                        options_list.append(opt_text.strip())
            
            question = Question(
                questionnaire_id=survey.id,
                content=q_text,
                type=type_map.get(q_type, 1),
                options=json.dumps(options_list) if options_list else None,
                sort_order=q_index + 1
            )
            db.session.add(question)
        
        db.session.commit()
        
        # 返回成功提示页面，显示 alert 后跳转到首页
        return render_template('publish_success.html', survey_id=survey.id)
    
    return render_template('create.html')


# 查看问卷详情
@survey_bp.route('/survey/<int:survey_id>')
def view_survey(survey_id):
    """查看问卷详情"""
    survey = Survey.query.get_or_404(survey_id)
    
    if not survey.is_active:
        return render_template('survey_closed.html', survey=survey)
    
    questions = Question.query.filter_by(questionnaire_id=survey_id).order_by(Question.sort_order).all()
    
    # 为每个问题解析选项（JSON格式），使用列表推导式避免修改原始对象
    questions_with_options = []
    for q in questions:
        options = json.loads(q.options) if q.options else []
        questions_with_options.append({
            'id': q.id,
            'content': q.content,
            'type': q.type,
            'options': options,
            'sort_order': q.sort_order
        })
    
    return render_template('survey.html', survey=survey, questions=questions_with_options)


# 提交问卷
@survey_bp.route('/survey/<int:survey_id>/submit', methods=['POST'])
def submit_survey(survey_id):
    """提交问卷回答"""
    survey = Survey.query.get_or_404(survey_id)
    
    if not survey.is_active:
        return jsonify({'success': False, 'message': '问卷已结束'}), 400
    
    # 处理每个问题的回答
    questions = Question.query.filter_by(questionnaire_id=survey_id).all()
    
    for question in questions:
        answer_key = f'question_{question.id}'
        
        # 处理多选和单选
        if question.type in [1, 2]:  # 单选或多选
            answer_values = request.form.getlist(answer_key)
            if not answer_values:
                continue
            answer = Answer(
                question_id=question.id,
                content=json.dumps(answer_values)
            )
            db.session.add(answer)
        else:
            # 文本题
            answer_value = request.form.get(answer_key)
            if answer_value:
                answer = Answer(
                    question_id=question.id,
                    content=answer_value
                )
                db.session.add(answer)
    
    db.session.commit()
    
    return redirect(url_for('survey.thank_you', survey_id=survey_id))


# 感谢页面
@survey_bp.route('/survey/<int:survey_id>/thank-you')
def thank_you(survey_id):
    """提交成功感谢页面"""
    survey = Survey.query.get_or_404(survey_id)
    return render_template('thank_you.html', survey=survey)


# 查看问卷结果
@survey_bp.route('/survey/<int:survey_id>/results')
def view_results(survey_id):
    """查看问卷结果"""
    from sqlalchemy import func
    survey = Survey.query.get_or_404(survey_id)

    questions = Question.query.filter_by(questionnaire_id=survey_id).order_by(Question.sort_order).all()

    # 计算每个问题的统计结果
    results = []

    for question in questions:
        # 解析选项（JSON格式），不修改原始对象
        options = json.loads(question.options) if question.options else []

        if question.type in [1, 2]:  # 单选或多选
            # 获取该问题的所有回答
            answers = Answer.query.filter_by(question_id=question.id).all()

            # 统计每个选项的选择次数
            option_counts = {opt: 0 for opt in options}
            for answer in answers:
                try:
                    selected_options = json.loads(answer.content)
                    for opt in selected_options:
                        if opt in option_counts:
                            option_counts[opt] += 1
                except:
                    pass

            total_responses = len(answers)
            option_stats = []
            for opt_text in options:
                count = option_counts.get(opt_text, 0)
                percentage = round((count / total_responses) * 100, 1) if total_responses > 0 else 0
                option_stats.append({
                    'text': opt_text,
                    'count': count,
                    'percentage': percentage
                })

            results.append({
                'question': {
                    'id': question.id,
                    'content': question.content,
                    'type': question.type
                },
                'options': options,
                'stats': option_stats,
                'total': total_responses
            })
        else:
            # 文本题
            answers = Answer.query.filter_by(question_id=question.id).all()
            results.append({
                'question': {
                    'id': question.id,
                    'content': question.content,
                    'type': question.type
                },
                'answers': [a.content for a in answers],
                'total': len(answers)
            })

    # 获取每日参与人数统计（基于第一个问题的回答时间）
    daily_stats = []
    if questions:
        first_question = questions[0]
        daily_data = db.session.query(
            func.date(Answer.created_at).label('date'),
            func.count(Answer.id).label('count')
        ).filter(
            Answer.question_id == first_question.id
        ).group_by(
            func.date(Answer.created_at)
        ).order_by(
            func.date(Answer.created_at)
        ).all()

        daily_stats = [{'date': str(d.date), 'count': d.count} for d in daily_data]

    # 总参与人数（基于第一个问题的唯一回答数）
    total_responses = survey.response_count

    return render_template('results.html', survey=survey, results=results,
                           daily_stats=daily_stats, total_responses=total_responses)


# 添加问题
@survey_bp.route('/survey/<int:survey_id>/add-question', methods=['GET', 'POST'])
def add_question(survey_id):
    """为问卷添加问题"""
    survey = Survey.query.get_or_404(survey_id)
    
    if request.method == 'POST':
        question_text = request.form.get('question_text')
        question_type = request.form.get('question_type', 'single')
        options = request.form.getlist('options[]')
        
        if not question_text:
            return jsonify({'success': False, 'message': '请输入问题内容'}), 400
        
        # 转换问题类型为数字
        type_map = {
            'single': 1,
            'multiple': 2,
            'essay': 3
        }
        
        # 获取选项（如果是单选或多选）
        options_list = []
        if question_type != 'essay':
            for opt_text in options:
                if opt_text.strip():
                    options_list.append(opt_text.strip())
        
        # 创建问题
        question = Question(
            questionnaire_id=survey_id,
            content=question_text,
            type=type_map.get(question_type, 1),
            options=json.dumps(options_list) if options_list else None,
            sort_order=len(survey.questions) + 1
        )
        db.session.add(question)
        db.session.commit()
        
        return redirect(url_for('survey.view_survey', survey_id=survey_id))
    
    return render_template('add_question.html', survey=survey)


# 我的问卷（管理后台）
@survey_bp.route('/my-surveys')
def my_questions():
    """用户的问卷列表（管理后台）"""
    surveys = Survey.query.order_by(Survey.created_at.desc()).all()
    return render_template('admin.html', surveys=surveys)


# API: 搜索问卷
@survey_bp.route('/api/search', methods=['GET'])
def search_surveys():
    """搜索问卷"""
    keyword = request.args.get('keyword', '')
    
    if not keyword:
        surveys = Survey.query.filter_by(is_public=True).all()
    else:
        surveys = Survey.query.filter(
            (Survey.title.like(f'%{keyword}%')) | 
            (Survey.description.like(f'%{keyword}%'))
        ).filter_by(is_public=True).all()
    
    return jsonify({
        'success': True,
        'data': [s.to_dict() for s in surveys]
    })


# API: 切换问卷状态（启用/禁用）
@survey_bp.route('/api/survey/<int:survey_id>/toggle', methods=['POST'])
def toggle_survey(survey_id):
    """切换问卷状态"""
    survey = Survey.query.get_or_404(survey_id)
    survey.is_active = not survey.is_active
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '状态切换成功',
        'data': {'is_active': survey.is_active}
    })


# API: 删除问卷
@survey_bp.route('/api/survey/<int:survey_id>/delete', methods=['POST'])
def delete_survey(survey_id):
    """删除问卷"""
    survey = Survey.query.get_or_404(survey_id)
    db.session.delete(survey)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': '删除成功'
    })


# API: 获取分类统计
@survey_bp.route('/api/stats')
def get_stats():
    """获取统计数据"""
    total = Survey.query.filter_by(is_public=True).count()
    active = Survey.query.filter_by(is_public=True, is_active=True).count()
    
    return jsonify({
        'success': True,
        'data': {
            'total_surveys': total,
            'active_surveys': active
        }
    })
