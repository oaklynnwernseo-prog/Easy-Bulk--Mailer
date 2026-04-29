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

# -----------------------------------
# SESSION STATE
# -----------------------------------
if "accounts" not in st.session_state:
    st.session_state.accounts = {}

if "email_input" not in st.session_state:
    st.session_state.email_input = ""

if "pass_input" not in st.session_state:
    st.session_state.pass_input = ""

# -----------------------------------
# ADD ACCOUNT
# -----------------------------------
st.subheader("➕ Add Gmail Account")

st.text_input(
    "Gmail Address",
    key="email_input"
)

st.text_input(
    "App Password",
    type="password",
    key="pass_input"
)

if st.button("Add Account"):

    email = st.session_state.email_input.strip()
    password = st.session_state.pass_input.strip()

    if email and password:

        st.session_state.accounts[email] = password

        # CLEAR INPUT FIELDS
        st.session_state.email_input = ""
        st.session_state.pass_input = ""

        st.success("Account Added")
        st.rerun()

    else:
        st.warning("Enter email and password")

# -----------------------------------
# CHECK ACCOUNT
# -----------------------------------
if len(st.session_state.accounts) == 0:
    st.info("Add at least one Gmail account.")
    st.stop()

# -----------------------------------
# DROPDOWN LABEL FIX
# -----------------------------------
st.subheader("🔁 Select Sender Account")

emails = list(st.session_state.accounts.keys())

selected_email = st.selectbox(
    "Email List",
    options=emails,
    index=0
)

selected_pass = st.session_state.accounts[selected_email]

# -----------------------------------
# REMOVE ACCOUNT
# -----------------------------------
if st.button("❌ Remove Selected Account"):

    del st.session_state.accounts[selected_email]
    st.rerun()

# -----------------------------------
# EMAIL COMPOSE
# -----------------------------------
st.subheader("✉ Compose Email")

subject = st.text_input("Subject")

html_message = st_quill(
    placeholder="Write email here...",
    html=True
)

# -----------------------------------
# CSV UPLOAD
# -----------------------------------
file = st.file_uploader(
    "Upload CSV (email column only)",
    type=["csv"]
)

# -----------------------------------
# SEND
# -----------------------------------
if st.button("🚀 Start Sending"):

    if file is None:
        st.error("Upload CSV file")
        st.stop()

    if not subject:
        st.error("Enter subject")
        st.stop()

    if not html_message:
        st.error("Write email content")
        st.stop()

    # READ CSV
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
        st.error("CSV must contain email column only")
        st.stop()

    emails_to_send = (
        df["email"]
        .dropna()
        .astype(str)
        .str.strip()
        .tolist()
    )

    # SMTP LOGIN
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
        st.error("Login failed")
        st.stop()

    progress = st.progress(0)
    sent = 0

    # SEND LOOP
    for i, receiver in enumerate(emails_to_send):

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
            (i + 1) / len(emails_to_send)
        )

        if i < len(emails_to_send) - 1:
            time.sleep(
                random.randint(20, 30)
            )

    server.quit()

    st.success(
        f"Done! Sent {sent}/{len(emails_to_send)}"
    )
