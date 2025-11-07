import streamlit as st
import pymysql
from pymysql.cursors import DictCursor
from pymysql.constants import CLIENT
import hashlib
import time
import datetime

# --- 1. CONFIGURATION & SETUP ---
st.set_page_config(
    page_title="Job Application System",
    layout="centered",
    initial_sidebar_state="auto"
)

# --- 2. DATABASE CONNECTION (ใช้ PyMySQL) ---
@st.cache_resource
def init_connection():
    """เชื่อมต่อฐานข้อมูล MySQL (ใช้ PyMySQL)"""
    try:
        port_int = int(st.secrets["database"]["port"])
        # (FIX) เพิ่ม connect_timeout=10 วินาที
        return pymysql.connect(
            host=st.secrets["database"]["host"],
            port=port_int,
            user=st.secrets["database"]["user"],
            password=st.secrets["database"]["password"],
            database=st.secrets["database"]["database"],
            client_flag=CLIENT.SSL,
            cursorclass=DictCursor,
            connect_timeout=10 
        )
    except pymysql.Error as e:
        print(f"Database connection failed: {e}")
        return None
    except ValueError:
        print("Invalid Port number in Secrets.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in init_connection: {e}")
        return None

# --- 3. RUN QUERY FUNCTION (ปรับปรุงสำหรับ PyMySQL) ---
def run_query(query, params=None, commit=False, fetch_one=False, fetch_all=False):
    """ฟังก์ชันสำหรับรัน SQL Query (ใช้ PyMySQL)"""
    conn = init_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params)
                if commit:
                    conn.commit()
                    return True
                elif fetch_one:
                    return cursor.fetchone()
                elif fetch_all:
                    return cursor.fetchall()
        except pymysql.Error as e:
            st.error(f"Query Error: {e}")
            if e.args[0] in [2006, 2013]: # MySQL server has gone away or Connection lost
                st.cache_resource.clear() 
                st.error("Database connection lost. Please refresh the page.")
    else:
        # ถ้า conn เป็น None (เชื่อมต่อล้มเหลวตั้งแต่แรก)
        # Error นี้จะถูกจัดการในหน้า Splash Screen แล้ว
        pass 
    return None

# --- 4. UTILITIES (เหมือนเดิม) ---
def make_hash(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def check_login(username, password):
    hashed_pw = make_hash(password)
    comp = run_query("SELECT * FROM Company WHERE c_username = %s AND c_password_hash = %s",
                     (username, hashed_pw), fetch_one=True)
    if comp: return "Company", comp
    seeker = run_query("SELECT * FROM JobSeeker WHERE js_username = %s AND js_password_hash = %s",
                       (username, hashed_pw), fetch_one=True)
    if seeker: return "JobSeeker", seeker
    return None, None

# --- 5. AUTHENTICATION PAGES (เหมือนเดิม) ---
def login_register_page():
    st.title("Job Application System")
    tab1, tab2 = st.tabs(["เข้าสู่ระบบ (Login)", "ลงทะเบียน (Register)"])
    with tab1:
        st.write("### ยินดีต้อนรับกลับมา!")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("เข้าสู่ระบบ", use_container_width=True):
            role, user = check_login(username, password)
            if user:
                st.session_state['logged_in'] = True
                st.session_state['user_role'] = role
                st.session_state['user_info'] = user
                st.toast(f"Login สำเร็จ! ยินดีต้อนรับ {username}")
                time.sleep(1); st.rerun()
            else:
                st.error("Username หรือ Password ไม่ถูกต้อง")
    with tab2:
        st.write("### สร้างบัญชีใหม่")
        user_type = st.selectbox("คุณคือใคร?", ["ผู้หางาน (Job Seeker)", "บริษัท (Company)"])
        if "Company" in user_type:
            with st.form("reg_company"):
                c_user, c_pass = st.text_input("Username *"), st.text_input("Password *", type="password")
                c_name, c_email = st.text_input("ชื่อบริษัท *"), st.text_input("Email *")
                c_addr, c_contact = st.text_area("ที่อยู่"), st.text_input("เบอร์ติดต่อ")
                if st.form_submit_button("ยืนดีต้อนรับการลงทะเบียน"):
                    if c_user and c_pass and c_name and c_email:
                        sql = "INSERT INTO Company (c_username, c_password_hash, c_name, c_email, c_address, c_contact_info) VALUES (%s,%s,%s,%s,%s,%s)"
                        if run_query(sql, (c_user, make_hash(c_pass), c_name, c_email, c_addr, c_contact), commit=True):
                            st.success("ลงทะเบียนบริษัทสำเร็จ! กรุณาเข้าสู่ระบบ")
                    else:
                        st.warning("กรุณากรอกช่องที่มีเครื่องหมาย * ให้ครบ")
        else:
             with st.form("reg_seeker"):
                j_user, j_pass = st.text_input("Username *"), st.text_input("Password *", type="password")
                j_name, j_email = st.text_input("ชื่อ-นามสกุล *"), st.text_input("Email *")
                j_edu, j_skill, j_exp = st.text_input("ระดับการศึกษา"), st.text_area("ทักษะ (Skills)"), st.text_area("ประสบการณ์")
                if st.form_submit_button("ยืนดีต้อนรับการลงทะเบียน"):
                     if j_user and j_pass and j_name and j_email:
                        sql = "INSERT INTO JobSeeker (js_username, js_password_hash, js_full_name, js_email, js_education, js_skills, js_experience) VALUES (%s,%s,%s,%s,%s,%s,%s)"
                        if run_query(sql, (j_user, make_hash(j_pass), j_name, j_email, j_edu, j_skill, j_exp), commit=True):
                            st.success("ลงทะเบียนผู้หางานสำเร็จ! กรุณาเข้าสู่ระบบ")
                     else:
                        st.warning("กรุณากรอกช่องที่มีเครื่องหมาย * ให้ครบ")

# --- 6. COMPANY DASHBOARD (ไม่มีการเปลี่ยนแปลง) ---
def company_dashboard(user):
    st.subheader(f"Dashboard: {user['c_name']}")
    tab1, tab2, tab3 = st.tabs(["ประกาศงานของคุณ", "ลงประกาศงานใหม่", "จัดการใบสมัคร"])
    with tab1:
        st.write("### งานที่คุณเปิดรับอยู่ในขณะนี้")
        jobs = run_query("SELECT * FROM JobPost WHERE j_company_id = %s ORDER BY j_post_date DESC", (user['c_id'],), fetch_all=True)
        if jobs:
            for job in jobs:
                with st.expander(f"{job['j_position']} (ปิดรับ: {job['j_closing_date']})"):
                    st.write(f"**รายละเอียด:** {job['j_description']}")
                    st.write(f"**คุณสมบัติ:** {job['j_requirements']}")
                    if st.button("ลบประกาศ", key=f"del_{job['j_id']}"):
                        run_query("DELETE FROM JobPost WHERE j_id = %s", (job['j_id'],), commit=True)
                        st.toast("ลบประกาศงานสำเร็จ!"); time.sleep(1); st.rerun()
        else:
            st.info("บริษัทของคุณยังไม่มีประกาศงานที่เปิดรับในขณะนี้")
    with tab2:
        st.write("### กรอกรายละเอียดตำแหน่งงาน")
        with st.form("post_job_form"):
            j_pos = st.text_input("ชื่อตำแหน่ง (Position) *", placeholder="เช่น Senior Marketing Officer")
            j_desc = st.text_area("รายละเอียดงาน (Job Description)", height=150)
            j_req = st.text_area("คุณสมบัติ (Requirements)", height=150, placeholder="เช่น วุฒิป.ตรี, ประสบการณ์ 2 ปี...")
            default_close = datetime.date.today() + datetime.timedelta(days=30)
            j_close = st.date_input("วันปิดรับสมัคร", value=default_close)
            if st.form_submit_button("ยืนยันการลงประกาศ"):
                if j_pos:
                    sql = "INSERT INTO JobPost (j_company_id, j_position, j_description, j_requirements, j_post_date, j_closing_date) VALUES (%s, %s, %s, %s, CURDATE(), %s)"
                    if run_query(sql, (user['c_id'], j_pos, j_desc, j_req, j_close), commit=True):
                        st.success(f"ลงประกาศตำแหน่ง '{j_pos}' เรียบร้อยแล้ว!"); time.sleep(1.5); st.rerun()
                else:
                    st.error("กรุณาระบุชื่อตำแหน่งงาน")
    
    with tab3:
        st.write("### รายชื่อผู้สมัครแยกตามตำแหน่งงาน")
        my_jobs = run_query("SELECT j_id, j_position FROM JobPost WHERE j_company_id = %s", (user['c_id'],), fetch_all=True)
        
        if my_jobs:
            job_ids = [job['j_id'] for job in my_jobs]
            
            # (FIX) สร้าง placeholder (%s, %s, %s)
            if job_ids: # ตรวจสอบว่ามีงานหรือไม่
                placeholders = ','.join(['%s'] * len(job_ids))
                
                sql_all_apps = f"""
                    SELECT Application.*, JobSeeker.js_full_name, JobSeeker.js_email, JobSeeker.js_skills, JobSeeker.js_experience
                    FROM Application
                    JOIN JobSeeker ON Application.app_job_seeker_id = JobSeeker.js_id
                    WHERE app_job_id IN ({placeholders})
                    ORDER BY app_apply_date DESC
                """
                all_applicants = run_query(sql_all_apps, tuple(job_ids), fetch_all=True)
                
                # (FIX) จัดกลุ่มผู้สมัครด้วย Python (เร็วกว่ายิง Query)
                applicants_by_job = {}
                if all_applicants:
                    for app in all_applicants:
                        job_id = app['app_job_id']
                        if job_id not in applicants_by_job:
                            applicants_by_job[job_id] = []
                        applicants_by_job[job_id].append(app)
            else:
                applicants_by_job = {}

            # (FIX) Loop นี้จะเร็วมาก เพราะดึงข้อมูลจาก Python Dict
            for job in my_jobs:
                job_id = job['j_id']
                applicants = applicants_by_job.get(job_id, []) # ดึงจาก Dict
                count = len(applicants)

                with st.expander(f"ตำแหน่ง: {job['j_position']} ({count} คนสมัคร)"):
                    if applicants:
                        for app in applicants:
                            with st.container(border=True):
                                col1, col2 = st.columns([3, 2])
                                with col1:
                                    st.write(f"**{app['js_full_name']}**")
                                    st.caption(f"Email: {app['js_email']} | สมัครเมื่อ: {app['app_apply_date']}")
                                    st.write(f"**Skills:** {app['js_skills']}")
                                    with st.expander("ดูประสบการณ์ทำงาน"): st.write(app['js_experience'])
                                with col2:
                                    st.write("#### อัปเดตสถานะ")
                                    status_options = ['pending', 'reviewing', 'interview', 'rejected', 'offered']
                                    current_index = status_options.index(app['app_status']) if app['app_status'] in status_options else 0
                                    new_status = st.selectbox("เลือกสถานะ:", status_options, index=current_index, key=f"st_{app['app_id']}")
                                    if st.button("บันทึก", key=f"save_{app['app_id']}"):
                                        run_query("UPDATE Application SET app_status = %s WHERE app_id = %s", (new_status, app['app_id']), commit=True)
                                        st.toast(f"อัปเดตสถานะของ {app['js_full_name']} แล้ว!"); time.sleep(1); st.rerun()
                    else:
                        st.info("ยังไม่มีผู้สมัครในตำแหน่งนี้")
        else:
            st.warning("กรุณาลงประกาศงานก่อน เพื่อให้มีผู้สมัคร")

# --- 7. JOB SEEKER DASHBOARD (OPTIMIZED) ---
def seeker_dashboard(user):
    st.subheader(f"สวัสดีคุณ {user['js_full_name']}")
    tab1, tab2 = st.tabs(["ค้นหางาน", "สถานะการสมัคร"])

    my_apps_data = run_query("SELECT app_job_id, app_status FROM Application WHERE app_job_seeker_id=%s", (user['js_id'],), fetch_all=True)
    applied_jobs = {app['app_job_id']: app['app_status'] for app in my_apps_data} if my_apps_data else {}

    with tab1:
        st.write("### ค้นหาตำแหน่งงานที่ใช่สำหรับคุณ")
        col1, col2 = st.columns([3, 1])
        with col1: search_query = st.text_input("ค้นหาจากชื่อตำแหน่ง หรือ ชื่อบริษัท", placeholder="พิมพ์คำค้นหา...")
        with col2: st.write(""); st.write(""); search_clicked = st.button("ค้นหา", use_container_width=True)
        
        sql = "SELECT JobPost.*, Company.c_name FROM JobPost JOIN Company ON JobPost.j_company_id = Company.c_id WHERE j_closing_date >= CURDATE()"
        params = []
        if search_query:
            sql += " AND (JobPost.j_position LIKE %s OR Company.c_name LIKE %s)"
            search_term = f"%{search_query}%"; params.extend([search_term, search_term])
        sql += " ORDER BY j_post_date DESC"
        
        jobs = run_query(sql, tuple(params) if params else None, fetch_all=True)
        
        if jobs:
            st.success(f"ค้นพบ {len(jobs)} ตำแหน่งงาน")
            for job in jobs:
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.write(f"### {job['j_position']}")
                        st.write(f"{job['c_name']} | ปิดรับ: {job['j_closing_date']}")
                    with c2:
                        job_id = job['j_id']
                        if job_id in applied_jobs:
                            st.info(f"สถานะ: {applied_jobs[job_id]}")
                        else:
                            if st.button("สมัครทันที", key=f"apply_{job_id}", use_container_width=True):
                                run_query("INSERT INTO Application (app_job_id, app_job_seeker_id, app_apply_date) VALUES (%s, %s, CURDATE())", (job_id, user['js_id']), commit=True)
                                st.toast("ส่งใบสมัครสำเร็จ!"); time.sleep(1); st.rerun()
                    with st.expander("รายละเอียดงาน"):
                        st.write(f"**Job Description:**\n{job['j_description']}")
                        st.write(f"**Requirements:**\n{job['j_requirements']}")
        else:
            st.warning("ไม่พบตำแหน่งงานที่คุณค้นหา")
            
    with tab2:
        st.write("### ประวัติการสมัครงานของคุณ")
        my_apps_display = run_query("SELECT Application.*, JobPost.j_position, Company.c_name FROM Application JOIN JobPost ON Application.app_job_id = JobPost.j_id JOIN Company ON JobPost.j_company_id = Company.c_id WHERE app_job_seeker_id = %s ORDER BY app_apply_date DESC", (user['js_id'],), fetch_all=True)
        if my_apps_display:
            for app in my_apps_display:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.write(f"**{app['j_position']}**"); c1.caption(app['c_name'])
                    status = app['app_status']
                    if status == 'pending': c2.warning("รอพิจารณา")
                    elif status == 'reviewing': c2.info("กำลังรีวิว")
                    elif status == 'interview': c2.success("เรียกสัมภาษณ์")
                    elif status == 'rejected': c2.error("ไม่ผ่าน")
                    else: c2.write(f"สถานะ: {status}")
                    if status in ['pending', 'reviewing']:
                        if c3.button("ยกเลิกสมัคร", key=f"cancel_{app['app_id']}", use_container_width=True):
                            run_query("DELETE FROM Application WHERE app_id = %s", (app['app_id'],), commit=True)
                            st.toast("ยกเลิกการสมัครเรียบร้อยแล้ว"); time.sleep(1); st.rerun()
                    else:
                        c3.write("")
        else:
            st.info("คุณยังไม่ได้สมัครงาน")

# --- 8. EDIT PROFILE PAGE (ไม่มีการเปลี่ยนแปลง) ---
def edit_profile_page(user, role):
    st.subheader("แก้ไขข้อมูลส่วนตัว")
    if role == "Company":
        with st.form("edit_company_profile"):
            st.write("### ข้อมูลบริษัท")
            c_name = st.text_input("ชื่อบริษัท", value=user.get('c_name', ''))
            c_email = st.text_input("Email", value=user.get('c_email', ''))
            
            # (FIXED) แก้ไขบั๊กที่คุณเจอ
            c_address = st.text_area("ที่อยู่", value=user.get('c_address', '')) 
            
            c_contact = st.text_input("ข้อมูลติดต่อ", value=user.get('c_contact_info', ''))
            if st.form_submit_button("บันทึกการเปลี่ยนแปลง"):
                sql = "UPDATE Company SET c_name = %s, c_email = %s, c_address = %s, c_contact_info = %s WHERE c_id = %s"
                if run_query(sql, (c_name, c_email, c_address, c_contact, user['c_id']), commit=True):
                    st.session_state['user_info']['c_name'] = c_name
                    st.session_state['user_info']['c_email'] = c_email
                    st.session_state['user_info']['c_address'] = c_address
                    st.session_state['user_info']['c_contact_info'] = c_contact
                    st.success("บันทึกข้อมูลบริษัทเรียบร้อยแล้ว"); time.sleep(1); st.rerun()
                else:
                    st.error("เกิดข้อผิดพลาดในการบันทึกข้อมูล")
    elif role == "JobSeeker":
        with st.form("edit_seeker_profile"):
            st.write("### ข้อมูลผู้หางาน")
            js_name = st.text_input("ชื่อ-นามสกุล", value=user.get('js_full_name', ''))
            js_email = st.text_input("Email", value=user.get('js_email', ''))
            js_edu = st.text_input("ระดับการศึกษา", value=user.get('js_education', ''))
            js_skills = st.text_area("ทักษะ (Skills)", value=user.get('js_skills', ''))
            js_exp = st.text_area("ประสบการณ์", value=user.get('js_experience', ''))
            if st.form_submit_button("บันทึกการเปลี่ยนแปลง"):
                sql = "UPDATE JobSeeker SET js_full_name = %s, js_email = %s, js_education = %s, js_skills = %s, js_experience = %s WHERE js_id = %s"
                params = (js_name, js_email, js_edu, js_skills, js_exp, user['js_id'])
                if run_query(sql, params, commit=True):
                    st.session_state['user_info']['js_full_name'] = js_name
                    st.session_state['user_info']['js_email'] = js_email
                    st.session_state['user_info']['js_education'] = js_edu
                    st.session_state['user_info']['js_skills'] = js_skills
                    st.session_state['user_info']['js_experience'] = js_exp
                    st.success("บันทึกข้อมูลส่วนตัวเรียบร้อยแล้ว"); time.sleep(1); st.rerun()
                else:
                    st.error("เกิดข้อผิดพลาดในการบันทึกข้อมูล")

# --- 9. MAIN APP CONTROLLER (Splash Screen V3: Better Feedback) ---
def main():
    if 'app_initialized' not in st.session_state:
        st.set_page_config(layout="centered", initial_sidebar_state="collapsed")
        
        st.title("Job Application System")
        st.write("Connecting talent with opportunity...")
        
        # (FIX) แสดง Progress Bar ที่ให้ข้อมูลถูกต้อง
        progress_bar = st.progress(0, text="Initializing...")
        time.sleep(0.1) # หน่วงเวลาเล็กน้อย
        
        # (FIX) บอก User ก่อนว่ากำลังเชื่อมต่อ
        progress_bar.progress(25, text="Connecting to database... (this may take a moment)")
        
        conn_check = init_connection() # <--- นี่คือส่วนที่นาน
        
        if conn_check is None:
            # ถ้าเชื่อมต่อล้มเหลว ให้หยุดแอปและแสดง Error
            st.error("Application failed to start: Could not connect to the database.")
            st.error("Please check the 'Secrets' configuration in Streamlit settings.")
            progress_bar.empty()
            return # หยุดการทำงานของแอป
        
        # ถ้าเชื่อมต่อสำเร็จ ให้โหลดต่อ
        progress_bar.progress(75, text="Loading interface...")
        time.sleep(0.1)
        progress_bar.progress(100, text="Ready!")
        time.sleep(0.1)
        progress_bar.empty()

        st.session_state.app_initialized = True
        st.set_page_config(layout="centered", initial_sidebar_state="auto"); st.rerun()
    
    else:
        # --- Main App Logic (เหมือนเดิม) ---
        if 'logged_in' not in st.session_state: st.session_state['logged_in'] = False
        if not st.session_state['logged_in']:
            login_register_page()
        else:
            user, role = st.session_state['user_info'], st.session_state['user_role']
            st.sidebar.header(f"บัญชีผู้ใช้: {role}")
            st.sidebar.write(f"สวัสดี, **{user.get('c_username') or user.get('js_username')}**")
            st.sidebar.divider()
            page_options = ["Dashboard (หน้าหลัก)", "แก้ไขข้อมูลส่วนตัว"]
            page = st.sidebar.radio("เมนูนำทาง", page_options)
            st.sidebar.divider()
            if st.sidebar.button("ออกจากระบบ"):
                st.session_state['logged_in'] = False
                st.session_state['user_role'] = None
                st.session_state['user_info'] = None
                st.rerun()
            if page == "Dashboard (หน้าหลัก)":
                if role == "Company": company_dashboard(user)
                elif role == "JobSeeker": seeker_dashboard(user)
            elif page == "แก้ไขข้อมูลส่วนตัว":
                edit_profile_page(user, role)

if __name__ == '__main__':
    main()
