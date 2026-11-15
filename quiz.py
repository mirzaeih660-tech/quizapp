from flask import Flask, render_template_string, request, redirect, url_for, session
import socket

app = Flask(__name__)
app.secret_key = 'hasti_mirzaei_quiz_app'

users = {
    "استاد": {"password": "123", "role": "teacher"},
    "دانشجو تست": {"password": "123", "role": "student"}
}

# ==================== آزمون پیش‌فرض (بیماری‌های شغلی) ====================
final_exams = {
    "1": {
        "title": "آزمون بیماری‌های شغلی",
        "question": "کدام یک از بیماری‌های زیر جزو بیماری‌های شغلی ریوی محسوب می‌شود؟",
        "opt1": "سیلیکوزیس",
        "opt2": "دیابت نوع ۲",
        "opt3": "فشار خون بالا",
        "opt4": "آسم فصلی",
        "correct": "1"
    },
    "2": {
        "title": "آزمون بیماری‌های شغلی",
        "question": "کدام ماده شیمیایی می‌تواند باعث مسمومیت شغلی در کارگران شود؟",
        "opt1": "اکسیژن",
        "opt2": "سرب",
        "opt3": "نیتروژن",
        "opt4": "آب",
        "correct": "2"
    },
    "3": {
        "title": "آزمون بیماری‌های شغلی",
        "question": "بیماری «کمردرد مزمن» در کدام گروه از مشاغل شایع‌تر است؟",
        "opt1": "کارمندان اداری",
        "opt2": "رانندگان و کارگران ساختمانی",
        "opt3": "معلمان",
        "opt4": "برنامه‌نویسان",
        "correct": "2"
    }
}

current_questions = []
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

# ==================== استایل‌ها (تم پاستیلی زنده) ====================
STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700;900&display=swap');
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    /* بک گراند پاستیلی زنده با گرادیانت ملایم */
    body { 
        font-family: 'Vazirmatn', Tahoma, sans-serif; 
        background: linear-gradient(135deg, #A8E6CF 0%, #DCEDC1 50%, #FFD3B6 100%); 
        background-attachment: fixed;
        min-height: 100vh; 
        display: flex; 
        align-items: center; 
        justify-content: center;
        padding: 20px;
    }
    
    /* کادر اصلی */
    .container { 
        background: rgba(255, 255, 255, 0.96); 
        border-radius: 35px; 
        padding: 45px; 
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.1), 0 5px 15px rgba(0, 0, 0, 0.05); 
        text-align: center; 
        max-width: 900px; 
        width: 100%; 
        border: 3px solid #fff; 
    }
    
    h1 { 
        color: #FF8A65; /* نارنجی کورال زنده */
        margin-bottom: 35px; 
        font-size: 36px; 
        font-weight: 900; 
        text-shadow: 2px 2px 4px rgba(255, 138, 101, 0.2); 
    }
    h2 { color: #26A69A; margin-bottom: 20px; }
    
    /* دکمه‌های پاستیلی زنده (سه بعدی و براق) */
    .btn { 
        display: inline-block; 
        padding: 16px 35px; 
        font-size: 18px; 
        font-family: 'Vazirmatn', Tahoma, sans-serif; 
        font-weight: bold; 
        text-decoration: none; 
        border-radius: 20px; 
        border: none;
        cursor: pointer; 
        transition: all 0.2s; 
        margin: 10px; 
        box-shadow: 0 6px 0 rgba(0,0,0,0.15), 0 10px 20px rgba(0,0,0,0.1); 
        position: relative; 
        top: 0; 
        color: white;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
    }
    .btn:active { 
        box-shadow: 0 2px 0 rgba(0,0,0,0.15); 
        top: 4px; 
    }
    .btn:hover {
        filter: brightness(1.1);
    }
    
    /* رنگ‌های زنده و شاد */
    .btn-green { background: #66BB6A; } /* سبز زنده */
    .btn-blue { background: #42A5F5; } /* آبی روشن */
    .btn-pink { background: #FF7043; } /* کورال (نارنجی-صورتی) */
    .btn-red { background: #EF5350; } /* قرمز شاد */
    .btn-yellow { background: #FFCA28; color: #5D4037; text-shadow: none; } /* زرد آفتابی */

    .form-box { 
        background: #F1F8E9; 
        padding: 35px; 
        border-radius: 25px; 
        margin-top: 25px; 
        border: 2px solid #C5E1A5; 
        text-align: right; 
    }
    input[type="text"], input[type="password"], textarea { 
        width: 100%; 
        padding: 16px; 
        margin-bottom: 15px; 
        border: 2px solid #A5D6A7; 
        border-radius: 15px; 
        font-family: 'Vazirmatn', Tahoma, sans-serif; 
        font-size: 16px; 
        outline: none; 
        background: white; 
        transition: 0.3s;
    }
    input[type="text"]:focus, input[type="password"]:focus, textarea:focus { 
        border-color: #42A5F5; 
        box-shadow: 0 0 10px rgba(66, 165, 245, 0.3);
    }

    /* آدمک‌ها */
    .avatars { display: flex; justify-content: center; gap: 40px; margin-top: 40px; flex-wrap: wrap; }
    .avatar-card { 
        background: white; 
        padding: 30px; 
        border-radius: 30px; 
        width: 230px; 
        text-decoration: none; 
        color: #333; 
        transition: 0.3s; 
        box-shadow: 0 10px 25px rgba(0,0,0,0.08); 
        border: 3px solid #E0E0E0; 
    }
    .avatar-card:hover { 
        transform: translateY(-10px); 
        border-color: #42A5F5; 
        box-shadow: 0 15px 35px rgba(66, 165, 245, 0.2);
    }
    .avatar-circle { 
        width: 130px; 
        height: 130px; 
        border-radius: 50%; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        margin: 0 auto 20px auto; 
        font-size: 75px; 
        box-shadow: inset 0 -8px 0 rgba(0,0,0,0.1);
    }
    .student-circle { background: #81D4FA; }
    .teacher-circle { background: #FFF59D; }

    .menu-box { margin-top: 40px; display: flex; flex-direction: column; gap: 20px; align-items: center; }
    .menu-box .btn { width: 80%; max-width: 450px; font-size: 22px; }

    .success-box { 
        background: #FFF8E1; 
        border: 4px dashed #FFCA28; 
        padding: 50px; 
        border-radius: 35px; 
        margin-top: 20px; 
    }
    
    table { 
        width: 100%; 
        border-collapse: collapse; 
        margin-top: 25px; 
        background: white; 
        border-radius: 20px; 
        overflow: hidden; 
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
    }
    th, td { padding: 18px; text-align: center; border-bottom: 1px solid #EEEEEE; }
    th { background: #42A5F5; color: white; font-size: 18px; font-weight: bold; }
    
    .footer { margin-top: 45px; font-size: 16px; color: #FF7043; font-weight: bold; }
    
    .q-box { 
        background: #E1F5FE; 
        padding: 25px; 
        border-radius: 25px; 
        margin-bottom: 25px; 
        border: 2px solid #81D4FA; 
        text-align: right; 
    }
    .q-box label { display: block; margin: 12px 0; cursor: pointer; font-size: 17px; padding: 12px; border-radius: 12px; transition: 0.2s; background: white; border: 1px solid transparent; }
    .q-box label:hover { border-color: #42A5F5; background: #E3F2FD; font-weight: bold; }

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
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

LOGIN_PAGE = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>{{ role_title }}</h1>
    {% if error %}<p style="color: #EF5350; font-weight: bold; margin-bottom: 15px;">{{ error }}</p>{% endif %}
    <div class="form-box">
        <form method="POST" style="text-align: center;">
            <input type="text" name="name" placeholder="نام و نام خانوادگی" required>
            <input type="password" name="password" placeholder="رمز عبور" required>
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
        <a href="/add_exam" class="btn btn-pink">+ اضافه کردن آزمون</a>
        <a href="/view_exams" class="btn btn-yellow">مشاهده آزمون‌های آماده</a>
    </div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

MANAGE_STUDENTS = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>مدیریت دانشجویان</h1>
    <table>
        <tr><th>نام و نام خانوادگی</th><th>رمز عبور</th><th>عملیات</th></tr>
        {% for name, info in users.items() %}
            {% if info.role == 'student' %}
            <tr>
                <td>{{ name }}</td><td>{{ info.password }}</td>
                <td><button class="btn btn-green" style="padding: 8px 20px; border-radius: 15px;">+</button><button class="btn btn-red" style="padding: 8px 20px; border-radius: 15px;">-</button></td>
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
    {% if final_exams %}
        {% for id, q in final_exams.items() %}
            <div class="q-box">
                <h3 style="color: #FF7043; margin-bottom: 15px;">سوال {{ loop.index }}</h3>
                <p style="font-size: 18px; margin-bottom: 15px; font-weight: bold;">{{ q.question }}</p>
                <p style="line-height: 2;">۱) {{ q.opt1 }}</p>
                <p style="line-height: 2;">۲) {{ q.opt2 }}</p>
                <p style="line-height: 2;">۳) {{ q.opt3 }}</p>
                <p style="line-height: 2;">۴) {{ q.opt4 }}</p>
                <p style="color: #2E7D32; font-weight: bold; margin-top: 15px; font-size: 18px;">گزینه صحیح: {{ q.correct }}</p>
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
    <h1>اضافه کردن آزمون جدید</h1>
    <p style="font-size: 18px; color: #26A69A; font-weight: bold; margin-bottom: 25px;">تعداد سوالات ثبت شده در این جلسه: {{ count }}</p>
    
    <div class="form-box">
        <form method="POST">
            <label>عنوان آزمون:</label>
            <input type="text" name="title" required placeholder="عنوان آزمون" value="آزمون بیماری‌های شغلی">
            
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
    <table>
        <tr><th>نام دانشجو</th><th>عنوان آزمون</th><th>نمره</th></tr>
        {% for res in results_list %}
        <tr><td>{{ res.student }}</td><td>{{ res.title }}</td><td style="color: #2E7D32; font-weight: bold; font-size: 20px;">{{ res.score }}</td></tr>
        {% else %}
        <tr><td colspan="3">هنوز نتیجه‌ای ثبت نشده است.</td></tr>
        {% endfor %}
    </table>
    <div style="margin-top: 40px;"><a href="/teacher" class="btn btn-blue">بازگشت</a></div>
    <div class="footer">طراحی و توسعه: هستی میرزایی</div>
</div>
"""

STUDENT_EXAM_PAGE = STYLE + CLICK_SOUND + JS_SOUND + """
<div class="container">
    <h1>صفحه آزمون دانشجو</h1>
    {% if not final_exams %}
        <h2>هنوز آزمونی توسط استاد ساخته نشده است.</h2>
    {% else %}
        <form method="POST">
            {% for id, exam in final_exams.items() %}
                <div class="q-box">
                    <h3 style="color: #0277BD; margin-bottom: 15px;">سوال {{ loop.index }}: {{ exam.question }}</h3>
                    <label><input type="radio" name="ans_{{ id }}" value="1" required> ۱) {{ exam.opt1 }}</label>
                    <label><input type="radio" name="ans_{{ id }}" value="2"> ۲) {{ exam.opt2 }}</label>
                    <label><input type="radio" name="ans_{{ id }}" value="3"> ۳) {{ exam.opt3 }}</label>
                    <label><input type="radio" name="ans_{{ id }}" value="4"> ۴) {{ exam.opt4 }}</label>
                </div>
            {% endfor %}
            <button type="submit" class="btn btn-red" style="width: 100%; font-size: 24px; padding: 20px;">پایان آزمون</button>
        </form>
    {% endif %}
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

# ==================== مسیرها ====================
@app.route("/")
def index():
    return render_template_string(MAIN_PAGE)

@app.route("/login", methods=["GET", "POST"])
def login():
    role = request.args.get("role", "student")
    role_title = "ورود دانشجو" if role == "student" else "ورود استاد"
    error = ""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        password = request.form.get("password", "").strip()
        if name in users and users[name]["password"] == password and users[name]["role"] == role:
            session["name"] = name
            session["role"] = role
            return redirect(url_for("student_exam" if role == "student" else "teacher_dashboard"))
        else:
            if name not in users:
                users[name] = {"password": password, "role": role}
                session["name"] = name
                session["role"] = role
                return redirect(url_for("student_exam" if role == "student" else "teacher_dashboard"))
            else:
                error = "نام کاربری یا رمز عبور اشتباه است."
    return render_template_string(LOGIN_PAGE, role_title=role_title, error=error)

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
    return render_template_string(VIEW_EXAMS, final_exams=final_exams)

@app.route("/add_exam", methods=["GET", "POST"])
def add_exam():
    if session.get("role") != "teacher": return redirect(url_for("index"))
    global current_questions
    
    if request.method == "POST":
        action = request.form.get("action")
        q_data = {
            "title": request.form.get("title", "آزمون جدید"),
            "question": request.form.get("question", ""),
            "opt1": request.form.get("opt1", ""),
            "opt2": request.form.get("opt2", ""),
            "opt3": request.form.get("opt3", ""),
            "opt4": request.form.get("opt4", ""),
            "correct": request.form.get("correct", "1")
        }
        current_questions.append(q_data)
        
        if action == "finish":
            start_index = len(final_exams) + 1
            for i, q in enumerate(current_questions):
                final_exams[str(start_index + i)] = q
            current_questions = []
            return redirect(url_for("teacher_dashboard"))
            
        return redirect(url_for("add_exam"))
        
    return render_template_string(ADD_EXAM_PAGE, count=len(current_questions))

@app.route("/results")
def results_page():
    if session.get("role") != "teacher": return redirect(url_for("index"))
    return render_template_string(RESULTS_PAGE, results_list=results.values())

@app.route("/student_exam", methods=["GET", "POST"])
def student_exam():
    if session.get("role") != "student": return redirect(url_for("index"))
    if request.method == "POST":
        score = 0
        for id, exam in final_exams.items():
            ans = request.form.get("ans_" + id)
            if ans == exam["correct"]:
                score += 100 // len(final_exams) if final_exams else 0
        results[session["name"]] = {"student": session["name"], "title": "آزمون جامع", "score": score}
        return redirect(url_for("success"))
    return render_template_string(STUDENT_EXAM_PAGE, final_exams=final_exams)

@app.route("/success")
def success():
    if session.get("role") != "student": return redirect(url_for("index"))
    return render_template_string(SUCCESS_PAGE)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)