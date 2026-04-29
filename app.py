import streamlit as st
import pandas as pd
import smtplib
import time
import random
import io

from streamlit_quill import st_quill
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------------------
# PAGE CONFIG
# -----------------------------------
st.set_page_config(
    page_title="Multi Gmail Sender",
    page_icon="📧",
    layout="centered"
)

st.title("📧 Multi-Gmail Bulk Sender")

st.write("Add multiple Gmail accounts and switch anytime.")

# -----------------------------------
# SESSION STORAGE
# -----------------------------------
if "accounts" not in st.session_state:
    st.session_state.accounts = {}

if "new_email" not in st.session_state:
    st.session_state.new_email = ""

if "new_pass" not in st.session_state:
    st.session_state.new_pass = ""

# -----------------------------------
# ADD NEW ACCOUNT
# -----------------------------------
st.subheader("➕ Add Gmail Account")

st.text_input(
    "Gmail Address",
    key="new_email"
)

st.text_input(
    "App Password",
    type="password",
    key="new_pass"
)

if st.button("Add Account"):

    email = st.session_state.new_email.strip()
    password = st.session_state.new_pass.strip()

    if email and password:

        st.session_state.accounts[email] = password

        st.success(f"Added: {email}")

        # CLEAR INPUTS
        st.session_state.new_email = ""
        st.session_state.new_pass = ""

        st.rerun()

    else:
        st.warning("Enter email and password")

# -----------------------------------
# ACCOUNT SELECTOR
# -----------------------------------
st.subheader("🔁 Select Gmail Account")

if len(st.session_state.accounts) == 0:
    st.info("Add at least one Gmail account first.")
    st.stop()

selected_email = st.selectbox(
    "Choose Sender Gmail",
    list(st.session_state.accounts.keys())
)

selected_pass = st.session_state.accounts[selected_email]

# -----------------------------------
# REMOVE ACCOUNT
# -----------------------------------
if st.button("❌ Remove Selected Account"):

    del st.session_state.accounts[selected_email]

    st.rerun()

# -----------------------------------
# EMAIL COMPOSER
# -----------------------------------
st.subheader("✉ Compose Email")

subject = st.text_input("Email Subject")

html_message = st_quill(
    placeholder="Write your email here...",
    html=True
)

# -----------------------------------
# CSV UPLOAD
# -----------------------------------
file = st.file_uploader(
    "Upload CSV (ONLY email column)",
    type=["csv"]
)

st.info("CSV format:\nemail\nabc@gmail.com")

# -----------------------------------
# SEND BUTTON
# -----------------------------------
if st.button("🚀 Start Sending"):

    if file is None:
        st.error("Upload CSV first")
        st.stop()

    if not subject:
        st.error("Enter subject")
        st.stop()

    if not html_message:
        st.error("Write email content")
        st.stop()

    # -----------------------------------
    # READ CSV SAFELY
    # -----------------------------------
    content = file.getvalue().decode(
        "utf-8",
        errors="ignore"
    )

    df = pd.read_csv(io.StringIO(content))

    df = df.loc[
        :,
        ~df.columns.str.contains("Unnamed")
    ]

    df.columns = (
        df.columns.str.strip()
        .str.lower()
    )

    if len(df.columns) != 1 or df.columns[0] != "email":
        st.error("CSV must contain ONLY email column")
        st.stop()

    emails = (
        df["email"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    st.success(f"Total Emails: {len(emails)}")

    # -----------------------------------
    # LOGIN SMTP
    # -----------------------------------
    try:
        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            selected_email,
            selected_pass
        )

    except:
        st.error("Login failed. Check Gmail/App Password.")
        st.stop()

    progress = st.progress(0)
    sent = 0

    # -----------------------------------
    # SEND LOOP
    # -----------------------------------
    for i, receiver in enumerate(emails):

        msg = MIMEMultipart()
        msg["From"] = selected_email
        msg["To"] = receiver
        msg["Subject"] = subject

        msg.attach(
            MIMEText(
                html_message,
                "html"
            )
        )

        try:
            server.sendmail(
                selected_email,
                receiver,
                msg.as_string()
            )

            st.success(f"Sent → {receiver}")
            sent += 1

        except:
            st.error(f"Failed → {receiver}")

        progress.progress(
            (i + 1) / len(emails)
        )

        # 20–30 sec delay
        if i < len(emails) - 1:
            time.sleep(
                random.randint(8, 10)
            )

    server.quit()

    st.success(
        f"🎉 Done! Sent {sent}/{len(emails)} emails"
    )
