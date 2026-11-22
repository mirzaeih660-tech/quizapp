from flask import Flask, render_template_string, request, redirect, url_for, session
import socket

app = Flask(__name__)
app.secret_key = 'hasti_mirzaei_quiz_app'

# کاربران (استاد و دانشجوها)
users = {
    "استاد": {"password": "", "role": "teacher"} # رمز استاد حذف شد
}

# دیکشنری برای ذخیره آزمون‌ها (هر آزمون یک ID و لیست سوالات خودش رو داره)
exams = {} # { exam_id: {"title": "...", "questions": [ {...} ]} }
next_exam_id = 1

# ذخیره نتایج و پاسخ‌های دانشجویان: { exam_id: { student_name: {"correct": 0, "wrong": 0, "answers": {q_id: ans}} } }
results = {} 

# ==================== صدای کلیک ====================
CLICK_SOUND = '<audio id="clickSound" src="data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAIA+AAACABAAZGF0YQAAAAA=" preload="auto"></audio>'
JS_SOUND = """
<script>
    document.addEventListener('DOMContentLoaded', function() {
        const btns = document.querySelectorAll('.btn');
        const sound = document.getElementById('clickSound');
        btns.forEach(btn => {
            btn.addEventListener('click', () => {
                sound.currentTime = 0;
                sound.play().catch(e => {});
            });
        });
    });
</script>
"""

# ==================== استایل‌ها ====================
STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700;900&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Vazirmatn', Tahoma, sans-serif; background: linear-gradient(135deg, #A8E6CF 0%, #DCEDC1 50%, #FFD3B6 100%); background-attachment: fixed; min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
    .container { background: rgba(255, 255, 255, 0.96); border-radius: 35px; padding: 45px; box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1); text-align: center; max-width: 950px; width: 100%; border: 3px solid #fff; }
    h1 { color: #FF8A65; margin-bottom: 35px; font-size: 36px; font-weight: 900; text-shadow: 2px 2px 4px rgba(255, 138, 101, 0.2); }
    h2 { color: #26A69A; margin-bottom: 20px; }
    h3 { color: #FF7043; margin-bottom: 10px; }
    
    .btn { display: inline-block; padding: 16px 35px; font-size: 18px; font-family: 'Vazirmatn', Tahoma, sans-serif; font-weight: bold; text-decoration: none; border-radius: 20px; border: none; cursor: pointer; transition: all 0.2s; margin: 10px; box-shadow: 0 6px 0 rgba(0,0,0,0.15), 0 10px 20px rgba(0,0,0,0.1); position: relative; top: 0; color: white; text-shadow: 1px 1px 2px rgba(0,0,0,0.2); }
    .btn:active { box-shadow: 0 2px 0 rgba(0,0,0,0.15); top: 4px; }
    .btn:hover { filter: brightness(1.1); }
    .btn-green { background: #66BB6A; }
    .btn-blue { background: #42A5F5; }
    .btn-pink { background: #FF7043; }
    .btn-red { background: #EF5350; }
    .btn-yellow { background: #FFCA28; color: #5D4037; text-shadow: none; }

    .form-box { background: #F1F8E9; padding: 35px; border-radius: 25px; margin-top: 25px; border: 2px solid #C5E1A5; text-align: right; }
    input[type="text"], input[type="password"], textarea { width: 100%; padding: 16px; margin-bottom: 15px; border: 2px solid #A5D6A7; border-radius: 15px; font-family: 'Vazirmatn', Tahoma, sans-serif; font-size: 16px; outline: none; background: white; transition: 0.3s; }
    input[type="text"]:focus, input[type="password"]:focus, textarea:focus { border-color: #42A5F5; box-shadow: 0 0 10px rgba(66, 165, 245, 0.3); }

    .avatars { display: flex; justify-content: center; gap: 40px; margin-top: 40px; flex-wrap: wrap; }
    .avatar-card { background: white; padding: 30px; border-radius: 30px; width: 230px; text-decoration: none; color: #333; transition: 0.3s; box-shadow: 0 10px 25px rgba(0,0,0,0.08); border: 3px solid #E0E0E0; }
    .avatar-card:hover { transform: translateY(-10px); border-color: #42A5F5; box-shadow: 0 15px 35px rgba(66, 165, 245, 0.2); }
    .avatar-circle { width: 130px; height: 130px; border-radius: 50%; display: flex; align-items: center; justify-content: center; margin: 0 auto 20px auto; font-size: 75px; box-shadow: inset 0 -8px 0 rgba(0,0,0,0.1); }
    .student-circle { background: #81D4FA; }
    .teacher-circle { background: #FFF59D; }

    .menu-box { margin-top: 40px; display: flex; flex-direction: column; gap: 20px; align-items: center; }
    .menu-box .btn { width: 80%; max-width: 450px; font-size: 22px; }

    table { width: 100%; border-collapse: collapse; margin-top: 25px; background: white; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }
    th, td { padding: 18px; text-align: center; border-bottom: 1px solid #EEEEEE; }
    th { background: #42A5F5; color: white; font-size: 18px; font-weight: bold; }
    
    .footer { margin-top: 45px; font-size: 16px; color: #FF7043; font-weight: bold; }
    
    .q-box { background: #E1F5FE; padding: 25px; border-radius: 25px; margin-bottom: 25px; border: 2px solid #81D4FA; text-align: right; }
    .q-box label { display: block; margin: 12px 0; cursor: pointer; font-size: 17px; padding: 12px; border-radius: 12px; transition: 0.2s; background: white; border: 1px solid transparent; }
    .q-box label:hover { border-color: #42A5F5; background: #E3F2FD; font-weight: bold; }

    .badge-green { color: white; background: #66BB6A; padding: 5px 10px; border-radius: 10px; font-weight: bold; }
    .badge-red { color: white; background: #EF5350; padding: 5px 10px; border-radius: 10px; font-weight: bold; }

    /* انیمیشن مدال‌ها */
    .medal { font-size: 30px; animation: pop 1s infinite alternate; display: inline-block; }
    @keyframes pop { from { transform: scale(1); } to { transform: scale(1.2); } }
    
    /* نمودار ستونی CSS */
    .chart-container { display: flex; align-items: flex-end; justify-content: space-around; height: 250px; background: #f9f9f9; padding: 20px; border-radius: 20px; margin-top: 30px; border-bottom: 3px solid #ccc; }
    .bar-wrap { display: flex; flex-direction: column; align-items: center; width: 12%; }
    .bar { width: 100%; background: #42A5F5; border-radius: 10px 10px 0 0; transition: height 1s; position: relative; }
    .bar span { position: absolute; top: -25px; width: 100%; text-align: center; font-weight: bold; color: #333; }
    .bar-label { margin-top: 10px; font-size: 14px; color: #555; text-align: center; }

    .flower { position: fixed; top: -50px; font-size: 30px; animation: fall linear forwards; z-index: 9999; pointer-events: none; }
    @keyframes fall { to { transform: translateY(105vh) rotate(360deg); opacity: 0; } }
</style>
"""

# ==================== صفحات ====================
MAIN_PAGE = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>سامانه آزمون آنلاین</h1>
    <div class="avatars">
        <a href="/login?role=student" class="avatar-card">
            <div class="avatar-circle student-circle">🎓</div>
            <h3 style="color: #0277BD;">ورود دانشجو</h3>
        </a>
        <a href="/login?role=teacher" class="avatar-card">
            <div class="avatar-circle teacher-circle">👨‍🏫</div>
            <h3 style="color: #F57F17;">ورود استاد</h3>
        </a>
    </div>
    <div style="margin-top: 30px;">
        <a href="/public_results" class="btn btn-yellow" style="width: 60%;">🏆 نمایش عمومی نتایج و مدال‌ها</a>
    </div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

LOGIN_PAGE = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>{{ role_title }}</h1>
    <div class="form-box">
        <form method="POST" style="text-align: center;">
            <input type="text" name="name" placeholder="نام و نام خانوادگی" required>
            {% if role == 'student' %}
                <input type="password" name="password" placeholder="رمز عبور" required>
            {% else %}
                <p style="color:#555; margin-bottom:15px;">(ورود استاد نیازی به رمز ندارد)</p>
            {% endif %}
            <button type="submit" class="btn btn-blue" style="width: 100%; margin-top: 15px;">ورود</button>
        </form>
    </div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

TEACHER_DASHBOARD = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>میز مدیریت استاد</h1>
    <p style="font-size: 24px; color: #26A69A; font-weight: bold; margin-bottom: 20px;">خوش آمدید {{ name }}</p>
    <div class="menu-box">
        <a href="/manage_students" class="btn btn-blue">مدیریت دانشجو</a>
        <a href="/results" class="btn btn-green">بررسی نتیجه</a>
        <a href="/add_exam" class="btn btn-pink">+ ساخت آزمون جدید</a>
        <a href="/view_exams" class="btn btn-yellow">مشاهده آزمون‌های آماده</a>
        <a href="/public_results" class="btn btn-blue" style="background:#8E24AA;">نمایش عمومی نتایج</a>
    </div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

MANAGE_STUDENTS = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>مدیریت دانشجویان</h1>
    <table>
        <tr><th>نام دانشجو</th><th>تعداد درست</th><th>تعداد غلط</th></tr>
        {% for name, info in users.items() %}
            {% if info.role == 'student' %}
            <tr>
                <td>{{ name }}</td>
                <td><span class="badge-green">{{ info.get('total_correct', 0) }} ✔</span></td>
                <td><span class="badge-red">{{ info.get('total_wrong', 0) }} ✘</span></td>
            </tr>
            {% endif %}
        {% endfor %}
    </table>
    <div style="margin-top: 40px;"><a href="/teacher" class="btn btn-blue">بازگشت</a></div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

VIEW_EXAMS = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>آزمون‌های آماده</h1>
    {% if exams %}
        {% for exam_id, exam in exams.items() %}
            <div class="q-box">
                <h3 style="color: #FF7043;">{{ exam.title }}</h3>
                <p>تعداد سوالات: {{ exam.questions|length }}</p>
            </div>
        {% endfor %}
    {% else %}
        <h2>هیچ آزمونی وجود ندارد.</h2>
    {% endif %}
    <div style="margin-top: 40px;"><a href="/teacher" class="btn btn-blue">بازگشت</a></div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

ADD_EXAM_PAGE = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>ساخت آزمون جدید</h1>
    <p style="font-size: 18px; color: #26A69A; font-weight: bold; margin-bottom: 25px;">تعداد سوالات ثبت شده در این آزمون: {{ count }}</p>
    
    <div class="form-box">
        <form method="POST">
            {% if count == 0 %}
                <label>عنوان آزمون جدید (اجباری):</label>
                <input type="text" name="title" required placeholder="مثلا: آزمون ایمنی">
            {% endif %}
            
            <label>متن سوال:</label>
            <textarea name="question" rows="3" required></textarea>
            
            <label>گزینه ۱:</label> <input type="text" name="opt1" required>
            <label>گزینه ۲:</label> <input type="text" name="opt2" required>
            <label>گزینه ۳:</label> <input type="text" name="opt3" required>
            <label>گزینه ۴:</label> <input type="text" name="opt4" required>
            
            <label>شماره گزینه صحیح (1 تا 4):</label>
            <input type="text" name="correct" required>
            
            <div style="display: flex; gap: 20px; margin-top: 30px;">
                <button type="submit" name="action" value="next" class="btn btn-blue" style="flex: 1;">ذخیره و سوال بعدی</button>
                <button type="submit" name="action" value="finish" class="btn btn-pink" style="flex: 1;">پایان و ثبت آزمون</button>
            </div>
        </form>
    </div>
    <div style="margin-top: 30px;"><a href="/teacher" class="btn btn-red">لغو و بازگشت</a></div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

RESULTS_PAGE = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>نتایج دانشجویان</h1>
    {% for exam_id, exam_results in results.items() %}
        <h2>آزمون: {{ exams[exam_id].title }}</h2>
        <table>
            <tr><th>نام دانشجو</th><th>تعداد درست</th><th>تعداد غلط</th><th>نمره (از {{ exams[exam_id].questions|length }})</th></tr>
            {% for student, data in exam_results.items() %}
            <tr>
                <td>{{ student }}</td>
                <td><span class="badge-green">{{ data.correct }}</span></td>
                <td><span class="badge-red">{{ data.wrong }}</span></td>
                <td style="color: #2E7D32; font-weight: bold; font-size: 20px;">{{ data.correct }}</td>
            </tr>
            {% endfor %}
        </table>
        <hr style="margin: 40px 0; border: 1px dashed #ccc;">
    {% else %}
        <h2>هنوز نتیجه‌ای ثبت نشده است.</h2>
    {% endfor %}
    <div style="margin-top: 30px;"><a href="/teacher" class="btn btn-blue">بازگشت</a></div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

STUDENT_EXAMS_LIST = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>آزمون‌های فعال</h1>
    {% if exams %}
        <div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: center;">
            {% for exam_id, exam in exams.items() %}
                <a href="/take_exam/{{ exam_id }}" class="btn btn-blue" style="font-size: 22px;">{{ exam.title }}</a>
            {% endfor %}
        </div>
    {% else %}
        <h2>هنوز آزمونی توسط استاد ساخته نشده است.</h2>
    {% endif %}
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

TAKE_EXAM_PAGE = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>{{ exam.title }}</h1>
    <form method="POST">
        {% for q in exam.questions %}
            <div class="q-box">
                <h3 style="color: #0277BD; margin-bottom: 15px;">سوال {{ loop.index }}: {{ q.question }}</h3>
                <label><input type="radio" name="ans_{{ loop.index0 }}" value="1" required> ۱) {{ q.opt1 }}</label>
                <label><input type="radio" name="ans_{{ loop.index0 }}" value="2"> ۲) {{ q.opt2 }}</label>
                <label><input type="radio" name="ans_{{ loop.index0 }}" value="3"> ۳) {{ q.opt3 }}</label>
                <label><input type="radio" name="ans_{{ loop.index0 }}" value="4"> ۴) {{ q.opt4 }}</label>
            </div>
        {% endfor %}
        <button type="submit" class="btn btn-red" style="width: 100%; font-size: 24px; padding: 20px;">پایان آزمون</button>
    </form>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

SUCCESS_PAGE = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <div class="success-box">
        <h2 style="color: #2E7D32; margin-bottom: 20px;">آزمون شما با موفقیت ثبت شد.</h2>
        <p style="font-size: 26px; color: #FF7043; font-weight: bold; margin-top: 20px;">با آرزوی موفقیت 🌸</p>
    </div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
<script>
    const flowers = ['🌸', '🌺', '🌼', '🌻', '🌷', '🌹'];
    setInterval(() => {
        const flower = document.createElement('div');
        flower.className = 'flower';
        flower.innerText = flowers[Math.floor(Math.random() * flowers.length)];
        flower.style.left = Math.random() * 100 + 'vw';
        flower.style.animationDuration = Math.random() * 3 + 2 + 's';
        document.body.appendChild(flower);
        setTimeout(() => { flower.remove(); }, 5000);
    }, 300);
</script>
"""

PUBLIC_RESULTS_PAGE = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>🏆 رتبه‌بندی و نتایج کلی</h1>
    
    <table style="font-size: 18px;">
        <tr><th>رتبه</th><th>مدال</th><th>نام دانشجو</th><th>نمره کل</th></tr>
        {% for student in leaderboard %}
            <tr>
                <td style="font-weight: bold; font-size: 22px;">{{ loop.index }}</td>
                <td>
                    {% if loop.index == 1 %}<span class="medal">🥇</span>
                    {% elif loop.index == 2 %}<span class="medal">🥈</span>
                    {% elif loop.index == 3 %}<span class="medal">🥉</span>
                    {% else %}-{% endif %}
                </td>
                <td style="font-weight: bold; color: #0277BD;">{{ student.name }}</td>
                <td style="color: #2E7D32; font-weight: bold; font-size: 22px;">{{ student.score }}</td>
            </tr>
        {% else %}
            <tr><td colspan="4">هنوز هیچ دانشجویی آزمون نداده است.</td></tr>
        {% endfor %}
    </table>

    <h2 style="margin-top: 50px;">📊 نمودار ستونی نمرات</h2>
    <div class="chart-container">
        {% for student in leaderboard %}
            <div class="bar-wrap">
                <div class="bar" style="height: {{ (student.score / max_score * 100) if max_score > 0 else 0 }}%; background: {{ ['#42A5F5', '#66BB6A', '#FFCA28', '#FF7043', '#AB47BC', '#26C6DA'][loop.index0 % 6] }};">
                    <span>{{ student.score }}</span>
                </div>
                <div class="bar-label">{{ student.name }}</div>
            </div>
        {% endfor %}
    </div>

    <div style="margin-top: 40px;"><a href="/" class="btn btn-blue">بازگشت به صفحه اصلی</a></div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""


# ==================== منطق برنامه ====================
@app.route("/")
def index():
    return render_template_string(MAIN_PAGE)

@app.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "student")
    role_title = "ورود دانشجو" if role == "student" else "ورود استاد"
    
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()
        
        if role == "teacher":
            session["name"] = "استاد"
            session["role"] = "teacher"
            return redirect(url_for("teacher_dashboard"))
            
        # دانشجو
        if not name: return "اسم نمی‌تونه خالی باشه"
        if name in users and users[name].get("role") == "student":
            if users[name]["password"] == password:
                session["name"] = name
                session["role"] = "student"
                return redirect(url_for("student_exams_list"))
            else:
                return render_template_string(LOGIN_PAGE, role_title=role_title, role=role, error="رمز اشتباه است")
        else:
            # ثبت‌نام خودکار دانشجوی جدید
            users[name] = {"password": password, "role": "student", "total_correct": 0, "total_wrong": 0}
            session["name"] = name
            session["role"] = "student"
            return redirect(url_for("student_exams_list"))

    return render_template_string(LOGIN_PAGE, role_title=role_title, role=role)

@app.route("/teacher")
def teacher_dashboard():
    if session.get("role") != "teacher": return redirect(url_for("index"))
    return render_template_string(TEACHER_DASHBOARD, name=session.get("name"))

@app.route("/manage_students")
def manage_students():
    if session.get("role") != "teacher": return redirect(url_for("index"))
    return render_template_string(MANAGE_STUDENTS, users=users)

@app.route("/view_exams")
def view_exams():
    if session.get("role") != "teacher": return redirect(url_for("index"))
    return render_template_string(VIEW_EXAMS, exams=exams)

# متغیر موقت برای ساخت آزمون جدید
current_new_exam = {"title": "", "questions": []}

@app.route("/add_exam", methods=["GET", "POST"])
def add_exam():
    global current_new_exam, next_exam_id
    if session.get("role") != "teacher": return redirect(url_for("index"))
    
    if request.method == "POST":
        action = request.form.get("action")
        
        if not current_new_exam["questions"]:
            current_new_exam["title"] = request.form.get("title", "بدون عنوان")
            
        q_data = {
            "question": request.form.get("question", ""),
            "opt1": request.form.get("opt1", ""), "opt2": request.form.get("opt2", ""),
            "opt3": request.form.get("opt3", ""), "opt4": request.form.get("opt4", ""),
            "correct": request.form.get("correct", "1")
        }
        current_new_exam["questions"].append(q_data)
        
        if action == "finish":
            exams[str(next_exam_id)] = current_new_exam.copy()
            next_exam_id += 1
            current_new_exam = {"title": "", "questions": []} # ریست کردن
            return redirect(url_for("teacher_dashboard"))
            
        return redirect(url_for("add_exam"))
        
    return render_template_string(ADD_EXAM_PAGE, count=len(current_new_exam["questions"]))

@app.route("/results")
def results_page():
    if session.get("role") != "teacher": return redirect(url_for("index"))
    return render_template_string(RESULTS_PAGE, results=results, exams=exams)

@app.route("/student_exams")
def student_exams_list():
    if session.get("role") != "student": return redirect(url_for("index"))
    return render_template_string(STUDENT_EXAMS_LIST, exams=exams)

@app.route("/take_exam/<exam_id>", methods=["GET", "POST"])
def take_exam(exam_id):
    if session.get("role") != "student" or exam_id not in exams: return redirect(url_for("index"))
    
    exam = exams[exam_id]
    if request.method == "POST":
        correct_count = 0
        wrong_count = 0
        student_name = session.get("name")
        
        for i, q in enumerate(exam["questions"]):
            ans = request.form.get(f"ans_{i}")
            if ans == q["correct"]:
                correct_count += 1
            else:
                wrong_count += 1
                
        if exam_id not in results: results[exam_id] = {}
        results[exam_id][student_name] = {"correct": correct_count, "wrong": wrong_count}
        
        # آپدیت آمار کل دانشجو
        users[student_name]["total_correct"] += correct_count
        users[student_name]["total_wrong"] += wrong_count
        
        return redirect(url_for("success"))
        
    return render_template_string(TAKE_EXAM_PAGE, exam=exam)

@app.route("/success")
def success():
    return render_template_string(SUCCESS_PAGE)

@app.route("/public_results")
def public_results():
    # محاسبه لیدربورد بر اساس مجموع نمرات در همه آزمون‌ها
    leaderboard = []
    for name, info in users.items():
        if info.get("role") == "student":
            leaderboard.append({"name": name, "score": info.get("total_correct", 0)})
            
    leaderboard.sort(key=lambda x: x["score"], reverse=True)
    max_score = leaderboard[0]["score"] if leaderboard else 1
    
    return render_template_string(PUBLIC_RESULTS_PAGE, leaderboard=leaderboard, max_score=max_score)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
