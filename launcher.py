import webbrowser
import os
import sys




# Lấy đường dẫn file app.py (nếu chạy exe thì sys._MEIPASS dùng)
if getattr(sys, 'frozen', False):
    app_path = os.path.join(sys._MEIPASS, "app.py")
else:
    app_path = "app.py"



# Chạy Streamlit app
os.system(f"streamlit run {app_path}")

