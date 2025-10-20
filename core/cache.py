
def cache_data(ttl=None):
    try:
        import streamlit as st
        return st.cache_data(ttl=ttl)
    except Exception:
        def decorator(fn):
            return fn
        return decorator
