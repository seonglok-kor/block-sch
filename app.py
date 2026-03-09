from flask import Flask, render_template_string, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# 로컬에서는 schedule.db 사용
# 배포(Render 등)에서는 환경변수 DB_NAME으로 경로 지정 가능
DB_NAME = os.environ.get("DB_NAME", "schedule.db")


def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_date TEXT NOT NULL,
            title TEXT NOT NULL,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            category TEXT,
            done INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()
  

def is_valid_time(value):
    try:
        datetime.strptime(value, "%H:%M")
        return True
    except ValueError:
        return False


@app.route("/")
def index():
    selected_date = request.args.get("date")
    if not selected_date:
        selected_date = datetime.today().strftime("%Y-%m-%d")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM blocks
        WHERE block_date = ?
        ORDER BY start_time
    """, (selected_date,))
    blocks = cur.fetchall()
    conn.close()

  html = """
    <!DOCTYPE html>
    <html lang="ko">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>BLOCK SCH</title>
        <style>
            * {
                box-sizing: border-box;
            }
            body {
                font-family: Arial, sans-serif;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px 16px 40px;
                background: #f7f7f7;
            }
            h1 {
                margin-bottom: 20px;
                font-size: 28px;
            }
            .topbar, .form-box, .block-card {
                background: white;
                border-radius: 12px;
                padding: 16px;
                margin-bottom: 16px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.06);
            }
            input, select, button {
                width: 100%;
                padding: 10px 12px;
                margin: 5px 0;
                border: 1px solid #ccc;
                border-radius: 8px;
                font-size: 14px;
            }
            button {
                cursor: pointer;
                background: #111827;
                color: white;
                border: none;
            }
            button:hover {
                opacity: 0.9;
            }
            .block-card {
                display: flex;
                justify-content: space-between;
                align-items: center;
                gap: 12px;
                border-left: 8px solid #999;
                flex-wrap: wrap;
            }
            .work { border-left-color: #3b82f6; }
            .study { border-left-color: #22c55e; }
            .health { border-left-color: #f97316; }
            .rest { border-left-color: #a855f7; }

            .done-text {
                color: #888;
                text-decoration: line-through;
            }
            .actions {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            .actions a {
                text-decoration: none;
                font-size: 14px;
                color: #2563eb;
            }
            .empty {
                color: #777;
            }
            .row {
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            .col {
                flex: 1 1 180px;
                min-width: 150px;
            }
            .small {
                color: #666;
                font-size: 14px;
                margin-top: 4px;
            }
                        .notice {
                background: #fff8db;
                border: 1px solid #f1e3a0;
                color: #6b5a00;
                padding: 12px;
                border-radius: 10px;
                margin-bottom: 16px;
                font-size: 14px;
            }
            @media (max-width: 600px) {
                h1 {
                    font-size: 24px;
                }
                .block-card {
                    align-items: flex-start;
                }
            }
        </style>
    </head>
    <body>
        <h1>BLOCK SCH</h1>

        <div class="notice">
            이 페이지는 공개 일정판입니다. 누구나 보고, 추가하고, 완료 처리하고, 삭제할 수 있습니다.
        </div>

        <div class="topbar">
            <form method="get" action="/">
                <label>날짜 선택</label>
                <input type="date" name="date" value="{{ selected_date }}">
                <button type="submit">보기</button>
            </form>
        </div>

                <div class="form-box">
            <h3>일정 추가</h3>
            <form method="post" action="/add">
                <input type="hidden" name="block_date" value="{{ selected_date }}">

                             <div class="row">
                    <div class="col">
                        <label>BLOCK</label>
                        <input name="title" required>
                    </div>
                    <div class="col">
                        <label>시작</label>
                        <input type="time" name="start_time" required>
                    </div>
                    <div class="col">
                        <label>종료</label>
                        <input type="time" name="end_time" required>
                    </div>
                                        <div class="col">
                        <label>카테고리</label>
                        <select name="category">
                            <option value="work">RUYA</option>
                            <option value="study">TRION</option>
                            <option value="health">조선</option>
                            <option value="rest">그외</option>
                        </select>
                    </div>
                </div>

                                <button type="submit">추가</button>
            </form>
        </div>

        <div class="form-box">
            <h3>{{ selected_date }} 일정</h3>

            {% if blocks %}
                {% for block in blocks %}
                    <div class="block-card {{ block['category'] }}">
                        <div>
                            <div class="{% if block['done'] %}done-text{% endif %}">
                                <strong>{{ block['title'] }}</strong>
                            </div>
                            <div class="small">
                                {{ block['start_time'] }} ~ {{ block['end_time'] }}
                                / {{ block['category'] }}
                                / {% if block['done'] %}완료{% else %}진행 전{% endif %}
                            </div>
                        </div>

                                                <div class="actions">
                            {% if not block['done'] %}
                                <a href="/done/{{ block['id'] }}?date={{ selected_date }}">완료</a>
                            {% endif %}
                            <a href="/delete/{{ block['id'] }}?date={{ selected_date }}" onclick="return confirm('삭제할까요?')">삭제</a>
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <p class="empty">등록된 일정이 없습니다.</p>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(html, blocks=blocks, selected_date=selected_date)


@app.route("/add", methods=["POST"])
def add_block():
    block_date = request.form["block_date"].strip()
    title = request.form["title"].strip()
    start_time = request.form["start_time"].strip()
    end_time = request.form["end_time"].strip()
    category = request.form["category"].strip()

    allowed_categories = {"work", "study", "health", "rest"}

    if not block_date:
        return "날짜가 비어 있습니다."
          if not title:
        return "제목이 비어 있습니다."

    if category not in allowed_categories:
        return "올바르지 않은 카테고리입니다."

    if not is_valid_time(start_time) or not is_valid_time(end_time):
        return "시간은 HH:MM 형식으로 입력하세요. 예: 09:00"

    if start_time >= end_time:
        return "종료 시간은 시작 시간보다 늦어야 합니다."

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO blocks (block_date, title, start_time, end_time, category)
        VALUES (?, ?, ?, ?, ?)
    """, (block_date, title, start_time, end_time, category))
    conn.commit()
    conn.close()

    return redirect(url_for("index", date=block_date))


@app.route("/done/<int:block_id>")
def mark_done(block_id):
    selected_date = request.args.get("date", datetime.today().strftime("%Y-%m-%d"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE blocks SET done = 1 WHERE id = ?", (block_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("index", date=selected_date))
  @app.route("/delete/<int:block_id>")
def delete_block(block_id):
    selected_date = request.args.get("date", datetime.today().strftime("%Y-%m-%d"))

    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM blocks WHERE id = ?", (block_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("index", date=selected_date))

# 앱 시작 시 DB 초기화
init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
