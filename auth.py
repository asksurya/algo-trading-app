"""
Authentication Module

Simple password protection for the trading app.
"""

import streamlit as st
import hashlib

def check_password():
    """
    Returns True if the user had the correct password.
    Shows password input and manages authentication state.
    """
    
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # Get password from secrets or use default
        try:
            correct_password = st.secrets.get("APP_PASSWORD", "")
            if not correct_password:
                st.error("⚠️ No APP_PASSWORD set in secrets! App is unprotected!")
                return
        except:
            correct_password = ""
            st.error("⚠️ No APP_PASSWORD set! Please add to Streamlit secrets.")
            return
        
        # Hash the entered password
        entered_password = st.session_state["password"]
        entered_hash = hashlib.sha256(entered_password.encode()).hexdigest()
        correct_hash = hashlib.sha256(correct_password.encode()).hexdigest()
        
        if entered_hash == correct_hash:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    # Return True if password is correct
    if st.session_state.get("password_correct", False):
        return True

    # Show login form
    st.markdown("# 🔐 Algo Trading App - Login")
    st.markdown("---")
    
    st.warning("⚠️ **Authentication Required**")
    st.info("This app accesses live trading accounts. Please authenticate to continue.")
    
    st.text_input(
        "Password",
        type="password",
        on_change=password_entered,
        key="password",
        help="Enter the app password to access trading features"
    )
    
    if "password_correct" in st.session_state and not st.session_state["password_correct"]:
        st.error("😕 Password incorrect. Please try again.")
    
    st.markdown("---")
    st.caption("💡 **For app owner:** Set APP_PASSWORD in Streamlit Cloud secrets")
    
    return False


def logout():
    """Logout function to clear authentication state."""
    if "password_correct" in st.session_state:
        st.session_state["password_correct"] = False
    st.rerun()


def require_auth():
    """
    Decorator/function to require authentication.
    Use at the top of each page.
    """
    if not check_password():
        st.stop()  # Don't run the rest of the app
