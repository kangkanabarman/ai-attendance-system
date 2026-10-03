from src.database.config import supabase
import bcrypt


def hash_pass(pwd):
    return bcrypt.hashpw(pwd.encode(),bcrypt.gensalt()).decode()

def check_pass(pwd, hashed):
    return bcrypt.checkpw(pwd.encode(),hashed.encode())


def check_teacher_exists(username):
    response=supabase.table("teachers").select("username").eq("username",username).execute()
    return len(response.data)>0

def create_teacher(username,password,name):

    data={"username" : username, "password": hash_pass(password), "name": name}
    response=supabase.table("teachers").insert(data).execute()
    return response.data

def teacher_login(username,password):
    response=supabase.table("teachers").select("*").eq("username",username).execute()
    if response.data:
        teacher=response.data[0]
        if check_pass(password, teacher['password']):
            return teacher
    return None

def get_all_students():
    response=supabase.table('students').select("*").execute()
    return response.data

def create_student(new_name, face_embedding=None, voice_embedding=None):
    data={'name':new_name,'face_embedding':face_embedding, "voice_embedding":voice_embedding}
    response=supabase.table('students').insert(data).execute()
    return response.data

def create_subject(subject_code, name, section, teacher_id):
    data= {"subject_code": subject_code,"name":name,"section":section,"teacher_id":teacher_id}
    response=supabase.table("subjects").insert(data).execute()
    return response.data

def get_teacher_subject(teacher_id):
    response= supabase.table('subjects').select("*, subject_students(count), attendance_logs(timestamp)").eq("teacher_id",teacher_id).execute()
    subjects= response.data


    for sub in subjects:
        sub['total_students']=sub.get("subject_students", [{}])[0].get('count', 0) if sub.get('subject_students') else 0
        attendance= sub.get('attendance_logs',[])
        unique_sessions=len(set(log['timestamp'] for log in attendance if 'timestamp' in log))
        sub['total_classes']=unique_sessions

        sub.pop('subject_students',None)
        sub.pop('attendance_logs',None)

    return subjects

def enroll_student_to_subject(student_id,subject_id):
    data={'student_id':student_id, "subject_id":subject_id}
    response=supabase.table('subject_students').insert(data).execute()
    return response.data

def unenroll_student_to_subject(student_id,subject_id):
    response=supabase.table('subject_students').delete().eq('student_id',student_id).eq('subject_id',subject_id).execute()
    return response.data

def get_student_subjects(student_id):
    response= supabase.table('subject_students').select('*,subjects(*)').eq('student_id',student_id).execute()
    return response.data

def get_student_attendance(student_id):
    response= supabase.table('attendance_logs').select('*,subjects(*)').eq('student_id',student_id).execute()
    return response.data

def get_subject_enrolled_students(subject_id):
    """Fetch all students enrolled in a specific subject with their profile details."""
    response = supabase.table('subject_students').select('student_id, students(*)').eq('subject_id', subject_id).execute()
    students = []
    if response.data:
        for row in response.data:
            if row.get('students'):
                students.append(row['students'])
    return students

def record_attendance_session(records):
    """Bulk insert attendance logs for a class session."""
    if not records:
        return []
    response = supabase.table('attendance_logs').insert(records).execute()
    return response.data

def get_subject_attendance_history(subject_id):
    """Retrieve full attendance logs for a subject with student names."""
    response = supabase.table('attendance_logs').select('*, students(name, student_id)').eq('subject_id', subject_id).order('timestamp', desc=True).execute()
    return response.data if response.data else []

def delete_attendance_session(subject_id, timestamp):
    """Delete an attendance session by subject and timestamp."""
    response = supabase.table('attendance_logs').delete().eq('subject_id', subject_id).eq('timestamp', timestamp).execute()
    return response.data

def delete_subject(subject_id):
    """Delete a subject and its associated enrollments and logs."""
    supabase.table('attendance_logs').delete().eq('subject_id', subject_id).execute()
    supabase.table('subject_students').delete().eq('subject_id', subject_id).execute()
    response = supabase.table('subjects').delete().eq('subject_id', subject_id).execute()
    return response.data