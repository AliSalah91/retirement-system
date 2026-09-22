from datetime import datetime
import os
import pandas as pd
import psycopg2
import streamlit as st

st.set_page_config(
    page_title="نظام إدارة بيانات المحالين على التقاعد", layout="wide"
)

# تنسيق الواجهة (يبقى كما هو)
st.markdown(
    """
    <style>
    body, [data-testid="stAppViewContainer"] {
        direction: rtl;
        text-align: right;
        font-family: 'Cairo', Tahoma, sans-serif;
        background-color: #f4f6f9;
    }
    .official-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #0f172a 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
    }
    .official-header h2 { margin: 0; font-size: 24px; font-weight: bold; color: #f8fafc; }
    .official-header p { margin: 5px 0 0 0; font-size: 14px; color: #94a3b8; }
    .stForm {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] {
        text-align: right;
        color: #1e293b !important;
        background-color: #ffffff !important;
        font-weight: 500;
    }
    label[data-baseweb="checkbox"], .stTextInput label, .stSelectbox label {
        color: #1e293b !important;
        font-weight: bold !important;
    }
    .stButton>button { border-radius: 8px; font-weight: bold; }
    .stats-box {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 10px;
        border-right: 5px solid #2563eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-top: 10px;
        font-size: 14px;
        color: #334155;
    }
    .login-box {
        background-color: #ffffff;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        max-width: 450px;
        margin: 50px auto;
        border: 1px solid #e2e8f0;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="official-header">
        <h2>📌 شعبة التقاعد وسجل الخدمة ودعم ذوي الشهداء</h2>
        <p>محافظة ديالى — نظام إدارة بيانات المحالين على التقاعد </p>
        <p>برمجة وتصميم : الدكتور علي صلاح حميد </p>
    </div>
""",
    unsafe_allow_html=True,
)


# دالة الاتصال بقاعدة بيانات PostgreSQL باستخدام أسرار Streamlit
def get_db_connection():
  return psycopg2.connect(
      host=st.secrets["postgres"]["host"],
      database=st.secrets["postgres"]["database"],
      user=st.secrets["postgres"]["user"],
      password=st.secrets["postgres"]["password"],
      port=st.secrets["postgres"]["port"],
  )


# تهيئة قاعدة البيانات وإنشاء الجدول إذا لم يكن موجوداً
def init_db():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS applicants (
            id SERIAL PRIMARY KEY,
            serial TEXT,
            name TEXT,
            workplace TEXT,
            birth_date TEXT,
            degree TEXT,
            district TEXT,
            username TEXT
        )
    """)
  conn.commit()
  cursor.close()
  conn.close()


init_db()


# تحميل البيانات من PostgreSQL
def load_data():
  try:
    conn = get_db_connection()
    df = pd.read_sql(
        "SELECT serial AS 'التسلسل', name AS 'الاسم الثلاثي', workplace AS 'مكان العمل', birth_date AS 'تاريخ الميلاد', degree AS 'الشهادة', district AS 'القضاء', username AS 'الموظف المدخل' FROM applicants",
        conn,
    )
    conn.close()
    return df.fillna("")
  except Exception as e:
    return pd.DataFrame(columns=[
        "التسلسل",
        "الاسم الثلاثي",
        "مكان العمل",
        "تاريخ الميلاد",
        "الشهادة",
        "القضاء",
        "الموظف المدخل",
    ])


USERS = {"admin": "12345", "employee1": "1111", "employee2": "2222"}

if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "username" not in st.session_state:
  st.session_state.username = ""

if not st.session_state.logged_in:
  st.markdown(
      """
        <div class="login-box">
            <h3 style="text-align: center; color: #1e3a8a; margin-bottom: 20px;">🔐 تسجيل دخول الموظفين</h3>
        </div>
    """,
      unsafe_allow_html=True,
  )

  _, col2, _ = st.columns([1, 1.2, 1])
  with col2:
    with st.form("login_form"):
      username_input = st.text_input("اسم المستخدم")
      password_input = st.text_input("كلمة المرور", type="password")
      login_btn = st.form_submit_button(
          "تسجيل الدخول", use_container_width=True
      )

      if login_btn:
        if (
            username_input in USERS
            and USERS[username_input] == password_input
        ):
          st.session_state.logged_in = True
          st.session_state.username = username_input
          st.success("تم تسجيل الدخول بنجاح!")
          st.rerun()
        else:
          st.error("اسم المستخدم أو كلمة المرور غير صحيحة!")

else:
  df_data = load_data()

  districts_list = [
      "بعقوبة",
      "خانقين",
      "جلولاء",
      "قره تبة",
      "المقدادية",
      "خالص",
      "بلدروز",
  ]
  degrees_list = [
      "ابتدائية",
      "متوسطة",
      "إعدادية",
      "دبلوم",
      "بكالوريوس",
      "ماجستير",
      "دكتوراه",
  ]

  top_c1, top_c2 = st.columns([4, 1])
  with top_c1:
    st.info(f"👤 الموظف المتصل حالياً: **{st.session_state.username}**")
  with top_c2:
    if st.button("تسجيل الخروج", use_container_width=True):
      st.session_state.logged_in = False
      st.session_state.username = ""
      st.rerun()

  col_form, col_table = st.columns([1, 2.2], gap="large")

  with col_form:
    st.markdown("#### 📝 إضافة متقدم جديد")
    with st.form("entry_form", clear_on_submit=True):
      serial = st.text_input(
          "التسلسل", value=str(len(df_data) + 1) if not df_data.empty else "1"
      )
      name = st.text_input("الاسم الثلاثي")
      workplace = st.text_input("مكان العمل")

      st.markdown("تاريخ الميلاد:")
      col_y, col_m, col_d = st.columns(3)
      with col_y:
        year = st.selectbox(
            "السنة", [str(i) for i in range(2010, 1940, -1)], index=30
        )
      with col_m:
        month = st.selectbox("الشهر", [str(i) for i in range(1, 13)])
      with col_d:
        day = st.selectbox("اليوم", [str(i) for i in range(1, 32)])

      degree = st.selectbox("الشهادة", degrees_list)
      district = st.selectbox("القضاء", districts_list)

      submitted = st.form_submit_button(
          "💾 حفظ وإضافة السجل", use_container_width=True
      )

      if submitted:
        if not name or not workplace:
          st.error("يرجى ملء الاسم الثلاثي ومكان العمل على الأقل!")
        else:
          birth_date = f"{day}/{month}/{year}"

          # الحفظ في قاعدة بيانات PostgreSQL
          try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                """
                            INSERT INTO applicants (serial, name, workplace, birth_date, degree, district, username)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                (
                    serial,
                    name,
                    workplace,
                    birth_date,
                    degree,
                    district,
                    st.session_state.username,
                ),
            )
            conn.commit()
            cursor.close()
            conn.close()

            st.success(f"تمت إضافة المتقدم ({name}) بنجاح!")
            st.rerun()
          except Exception as e:
            st.error(f"حدث خطأ أثناء الحفظ: {e}")

  with col_table:
    st.markdown("#### 📊 جدول السجلات والبيانات المسجلة")

    c1, c2, c3 = st.columns([2.5, 1, 1])
    with c1:
      search_query = st.text_input(
          "🔍 بحث سريع:", placeholder="ابحث بالاسم، القضاء..."
      )

    display_df = df_data
    if search_query:
      mask = df_data.astype(str).apply(
          lambda x: x.str.contains(search_query, case=False, na=False)
      ).any(axis=1)
      display_df = df_data[mask]

    with c2:
      st.write("")
      if st.button("🖨️ طباعة", use_container_width=True):
        if not df_data.empty:
          html_report = f"""
                    <!DOCTYPE html>
                    <html lang="ar" dir="rtl">
                    <head>
                        <meta charset="UTF-8">
                        <title>تقرير جدول المتقدمين</title>
                        <style>
                            body {{ font-family: 'Cairo', Tahoma, sans-serif; margin: 25px; color: #222; }}
                            .report-header {{
                                display: flex;
                                justify-content: space-between;
                                align-items: center;
                                border-bottom: 2px solid #1e3a8a;
                                padding-bottom: 12px;
                                margin-bottom: 20px;
                            }}
                            .report-title {{
                                font-size: 18px;
                                font-weight: bold;
                                color: #1e3a8a;
                                text-align: right;
                            }}
                            .report-date {{
                                font-size: 14px;
                                color: #475569;
                                text-align: left;
                            }}
                            table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                            th, td {{ border: 1px solid #94a3b8; padding: 8px; text-align: center; font-size: 13px; }}
                            th {{ background-color: #1e3a8a; color: white; }}
                            tr:nth-child(even) {{ background-color: #f8fafc; }}
                        </style>
                    </head>
                    <body onload="window.print()">
                        <div class="report-header">
                            <div class="report-title">شعبة التقاعد وسجل الخدمة ودعم ذوي الشهداء - ديالى</div>
                            <div class="report-date">تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d')}</div>
                        </div>
                        {display_df.to_html(index=False, border=0)}
                    </body>
                    </html>
                    """
          st.download_button(
              "📄 تحميل تقرير الطباعة HTML",
              data=html_report.encode("utf-8"),
              file_name="report.html",
              mime="text/html",
              use_container_width=True,
          )
        else:
          st.warning("لا توجد بيانات للطباعة!")

    with c3:
      st.write("")
      if not df_data.empty:
        csv_data = df_data.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "📥 إكسل",
            data=csv_data,
            file_name="قائمة_المتقدمين.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.dataframe(display_df, use_container_width=True, height=400)

    if not df_data.empty:
      st.markdown(
          f"""
            <div class="stats-box">
                <b>📌 إحصائيات سريعة:</b> العدد الكلي للمتقدمين المسجلين: <b>{len(df_data)}</b> متقدم | عدد الأقضية المغطاة: <b>{df_data['القضاء'].nunique()}</b> أقضية
            </div>
        """,
          unsafe_allow_html=True,
      )

st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-weight: bold; font-size:"
    " 13px;'>برمجة وتصميم : الدكتور علي صلاح </div>",
    unsafe_allow_html=True,
)
