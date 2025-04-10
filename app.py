from flask import Flask, render_template, request, redirect, url_for, session
import json
import os
import random

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback-key-for-dev')

def load_questions(json_filename):
    with open(json_filename, 'r', encoding='utf-8') as f:
        # Using strict=False can help if there are unescaped control characters.
        content = f.read()
        data = json.loads(content, strict=False)
    return data.get('questions', [])

def get_current_questions():
    domain = session.get('domain')
    if not domain:
        return []
    json_path = os.path.join(os.getcwd(), 'question', domain)
    questions = load_questions(json_path)
    if 'shuffled_questions' not in session:
        shuffled = questions.copy()
        random.shuffle(shuffled)
        session['shuffled_questions'] = shuffled
    return session.get('shuffled_questions', [])

@app.route('/')
def select():
    # Landing page where user selects a domain
    return render_template('select.html')

@app.route('/set_domain', methods=['POST'])
def set_domain():
    domain = request.form.get('domain')
    if not domain:
        return redirect(url_for('select'))
    # Store only the selected domain filename in session.
    session['domain'] = domain
    session['current'] = 0
    session['score'] = 0
    return redirect(url_for('question'))

@app.route('/question', methods=['GET'])
def question():
    questions = get_current_questions()
    current = session.get('current', 0)
    if current >= len(questions):
        return redirect(url_for('result'))
    q = questions[current]
    return render_template('quiz.html', question=q, q_num=current+1, total=len(questions))

@app.route('/submit', methods=['POST'])
def submit():
    questions = get_current_questions()
    current = session.get('current', 0)
    if current >= len(questions):
        return redirect(url_for('result'))
    
    selected = request.form.get('option')
    q = questions[current]
    correct = q.get('correct_answer', '').strip()
    is_correct = (selected == correct)
    
    if is_correct:
        session['score'] = session.get('score', 0) + 1

    # Get justification from the justifications object for the correct answer.
    justification = q.get('justifications', {}).get(correct, "No justification provided.")
    
    session['last_answer'] = selected
    session['last_correct'] = correct
    session['last_justification'] = justification
    
    return redirect(url_for('feedback'))

@app.route('/feedback')
def feedback():
    selected = session.get('last_answer', '')
    correct = session.get('last_correct', '')
    justification = session.get('last_justification', '')
    
    return render_template('feedback.html', selected=selected, correct=correct, justification=justification)

@app.route('/next')
def next_question():
    session['current'] = session.get('current', 0) + 1
    questions = get_current_questions()
    if session['current'] >= len(questions):
        return redirect(url_for('result'))
    return redirect(url_for('question'))

@app.route('/result')
def result():
    score = session.get('score', 0)
    questions = get_current_questions()
    total = len(questions)
    return render_template('result.html', score=score, total=total)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
